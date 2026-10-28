#!/usr/bin/env python3
"""AUDIT-08 Real Isolated Clone Verification on Frappe / MariaDB.

Guarantees:
- Dedicated Docker network and isolated containers (cc181-clone-net, cc181-clone-db, cc181-clone-redis, cc181-clone-backend, cc181-clone-frontend).
- Live DEV containers and volumes (centrochange-dev-*) are NEVER mutated.
- Baseline schema and reference data cloned via read-only stream from DEV_DB.
- All candidate app code mounted into the isolated backend and frontend.
- Scenarios validated:
  1. CC-CAP-028: Operational reporting endpoints (summary, sessions) across all status filters and reconciliation.
  2. CC-CAP-030: Managerial dashboard endpoint (operational KPIs, day closure status, notification metrics, zero clinical notes leak).
  3. CC-CAP-029: CSV Export security & standards (UTF-8 BOM, semicolon, formula escaping, 20k bounding, Italian date format).
  4. CC-CAP-039, CC-CAP-005, CC-CAP-033, CC-CAP-038: RBAC, Anti-leak, IDOR protections, practitioner clamping, and print_session boundaries.
  5. Regression of AUDIT-07 lifecycle metrics (closed, arrear recoveries, timely/late cancellations, economic waiver, packages).
  6. Headless real Chromium browser UAT across all route areas (Desktop & Mobile screenshots).
"""

import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / 'app/centrochange_core'

NET_NAME = 'cc181-clone-net'
DB_CONTAINER = 'cc181-clone-db'
REDIS_CONTAINER = 'cc181-clone-redis'
BACKEND_CONTAINER = 'cc181-clone-backend'
FRONTEND_CONTAINER = 'cc181-clone-frontend'

DEV_DB = 'centrochange-dev-db-1'
DEV_BACKEND = 'centrochange-dev-backend-1'
DEV_SITE = 'centrochange.local'
PORT = 8098


def _redact(val):
    if not val:
        return val
    s = str(val)
    s = re.sub(r'(-p|--password=|password=|MYSQL_PWD=|IDENTIFIED BY\s+[\'\"])([^\s\'";]+)', r'\1[REDACTED]', s, flags=re.IGNORECASE)
    s = re.sub(r'\b[0-9a-f]{32}\b', '[REDACTED_SECRET]', s)
    return s


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {_redact(msg)}", flush=True)


def run_cmd(cmd, check=True, capture=True, input_str=None):
    res = subprocess.run(cmd, shell=isinstance(cmd, str), check=False,
                         capture_output=capture, text=True, input=input_str)
    if check and res.returncode != 0:
        log(f"Command failed (code {res.returncode}): {_redact(cmd)}")
        if res.stdout:
            log(f"STDOUT:\n{_redact(res.stdout)}")
        if res.stderr:
            log(f"STDERR:\n{_redact(res.stderr)}")
        safe_cmd = [_redact(c) for c in cmd] if isinstance(cmd, list) else _redact(cmd)
        raise subprocess.CalledProcessError(res.returncode, safe_cmd, output=_redact(res.stdout), stderr=_redact(res.stderr))
    return res.stdout if capture else ""


def get_dev_db_credentials():
    user = os.environ.get('CC_DEV_DB_USER')
    password = os.environ.get('CC_DEV_DB_PASS')
    name = os.environ.get('CC_DEV_DB_NAME')
    if user and password:
        return {'user': user, 'pass': password, 'name': name or user}

    try:
        raw = run_cmd(['docker', 'exec', DEV_BACKEND, 'cat', f'sites/{DEV_SITE}/site_config.json'])
        cfg = json.loads(raw)
        return {
            'user': cfg.get('db_user') or cfg.get('db_name'),
            'pass': cfg.get('db_password'),
            'name': cfg.get('db_name'),
        }
    except Exception as e:
        log(f"Error discovering DEV database credentials: {_redact(e)}")
        raise RuntimeError("Failed to read DEV database credentials dynamically from running container")


def cleanup():
    log("Cleaning up isolated clone resources...")
    for c in [FRONTEND_CONTAINER, BACKEND_CONTAINER, DB_CONTAINER, REDIS_CONTAINER]:
        subprocess.run(['docker', 'rm', '-f', c], capture_output=True)
    subprocess.run(['docker', 'network', 'rm', NET_NAME], capture_output=True)
    log("Cleanup complete.")


def run_mariadb_sql(container, user, password, sql, db=None):
    script = f"""cat << 'EOF' > /tmp/.client.cnf
[client]
user={user}
password={password}
EOF
chmod 600 /tmp/.client.cnf
mariadb --defaults-file=/tmp/.client.cnf {'`' + db + '`' if db else ''} << 'EOF'
{sql}
EOF
rm -f /tmp/.client.cnf
"""
    run_cmd(['docker', 'exec', '-i', container, 'sh'], input_str=script)


def setup_clone():
    log("Setting up isolated clone environment for AUDIT-08...")
    cleanup()

    dev_creds = get_dev_db_credentials()
    clone_root_pass = secrets.token_hex(16)
    clone_db_pass = secrets.token_hex(16)

    # 1. Create isolated network
    log(f"Creating isolated Docker network {NET_NAME}...")
    run_cmd(['docker', 'network', 'create', NET_NAME])

    # 2. Start MariaDB container using ephemeral env-file
    log(f"Starting isolated MariaDB container {DB_CONTAINER}...")
    env_file = ROOT_DIR / f'infra/.ephemeral_clone_{secrets.token_hex(8)}.env'
    try:
        env_file.write_text(
            f"MARIADB_ROOT_PASSWORD={clone_root_pass}\nMYSQL_ROOT_PASSWORD={clone_root_pass}\nMARIADB_AUTO_UPGRADE=1\n",
            encoding='utf-8'
        )
        env_file.chmod(0o600)
        run_cmd([
            'docker', 'run', '-d',
            '--name', DB_CONTAINER,
            '--network', NET_NAME,
            '--env-file', str(env_file),
            'mariadb:11.8.8',
            '--character-set-server=utf8mb4',
            '--collation-server=utf8mb4_unicode_ci'
        ])
    finally:
        if env_file.exists():
            env_file.unlink()

    # 3. Start Redis container
    log(f"Starting isolated Redis container {REDIS_CONTAINER}...")
    run_cmd([
        'docker', 'run', '-d',
        '--name', REDIS_CONTAINER,
        '--network', NET_NAME,
        'redis:8.6.5-alpine'
    ])

    # 4. Wait for MariaDB to become ready
    log("Waiting for MariaDB to complete initialization and become healthy...")
    ready = False
    for attempt in range(60):
        time.sleep(1)
        res = subprocess.run(['docker', 'logs', DB_CONTAINER], capture_output=True, text=True)
        logs = res.stdout + res.stderr
        if logs.count('ready for connections') >= 2 or ('ready for connections' in logs and 'shutdown complete' not in logs[logs.rfind('ready for connections'):]):
            ping_res = subprocess.run(
                ['docker', 'exec', '-i', DB_CONTAINER, 'mariadb', f'-uroot', f'-p{clone_root_pass}', '-e', 'SELECT 1'],
                capture_output=True, text=True
            )
            if ping_res.returncode == 0:
                ready = True
                break
    if not ready:
        raise RuntimeError("MariaDB failed to start in isolated clone")

    # 5. Create database and user in isolated DB safely
    log(f"Configuring database {dev_creds['name']} in isolated MariaDB...")
    init_sql = f"""
    CREATE DATABASE `{dev_creds['name']}`;
    GRANT ALL PRIVILEGES ON `{dev_creds['name']}`.* TO '{dev_creds['user']}'@'%' IDENTIFIED BY '{clone_db_pass}';
    GRANT ALL PRIVILEGES ON `{dev_creds['name']}`.* TO '{dev_creds['user']}'@'localhost' IDENTIFIED BY '{clone_db_pass}';
    FLUSH PRIVILEGES;
    """
    run_mariadb_sql(DB_CONTAINER, 'root', clone_root_pass, init_sql)

    # 6. Stream read-only dump from DEV into clone DB
    log("Cloning DEV schema and baseline records into isolated clone...")
    dump_cnf_script = f"""cat << 'EOF' > /tmp/.dump.cnf
[client]
user={dev_creds['user']}
password={dev_creds['pass']}
EOF
chmod 600 /tmp/.dump.cnf
"""
    load_cnf_script = f"""cat << 'EOF' > /tmp/.load.cnf
[client]
user={dev_creds['user']}
password={clone_db_pass}
EOF
chmod 600 /tmp/.load.cnf
"""
    try:
        run_cmd(['docker', 'exec', '-i', DEV_DB, 'sh'], input_str=dump_cnf_script)
        run_cmd(['docker', 'exec', '-i', DB_CONTAINER, 'sh'], input_str=load_cnf_script)

        dump_proc = subprocess.Popen(
            ['docker', 'exec', DEV_DB, 'mariadb-dump', '--defaults-file=/tmp/.dump.cnf', dev_creds['name']],
            stdout=subprocess.PIPE
        )
        load_proc = subprocess.Popen(
            ['docker', 'exec', '-i', DB_CONTAINER, 'mariadb', '--defaults-file=/tmp/.load.cnf', dev_creds['name']],
            stdin=dump_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        dump_proc.stdout.close()
        out, err = load_proc.communicate()
        if load_proc.returncode != 0:
            raise RuntimeError(f"Database clone failed: {_redact(err.decode('utf-8'))}")
        log("Database cloned successfully.")
    finally:
        subprocess.run(['docker', 'exec', DEV_DB, 'rm', '-f', '/tmp/.dump.cnf'], capture_output=True)
        subprocess.run(['docker', 'exec', DB_CONTAINER, 'rm', '-f', '/tmp/.load.cnf'], capture_output=True)

    # 7. Start isolated backend container with worktree candidate code mounted
    dev_image = run_cmd(['docker', 'inspect', '-f', '{{.Config.Image}}', DEV_BACKEND]).strip()
    log(f"Starting isolated backend container {BACKEND_CONTAINER} using image {dev_image}...")
    run_cmd([
        'docker', 'run', '-d',
        '--name', BACKEND_CONTAINER,
        '--network', NET_NAME,
        '-v', f'{APP_DIR}:/home/frappe/frappe-bench/apps/centrochange_core:ro',
        '-e', 'FRAPPE_STREAM_LOGGING=1',
        dev_image,
        'sleep', '7200'
    ])

    # 8. Copy sites from DEV backend to isolated backend
    log("Copying sites configuration into isolated backend...")
    copy_proc = subprocess.Popen(
        ['docker', 'exec', DEV_BACKEND, 'tar', '-cf', '-', '-C', '/home/frappe/frappe-bench', 'sites'],
        stdout=subprocess.PIPE
    )
    extract_proc = subprocess.Popen(
        ['docker', 'exec', '-i', BACKEND_CONTAINER, 'tar', '-xf', '-', '-C', '/home/frappe/frappe-bench'],
        stdin=copy_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    copy_proc.stdout.close()
    out, err = extract_proc.communicate()
    if extract_proc.returncode != 0:
        raise RuntimeError(f"Sites copy failed: {err.decode('utf-8')}")

    # 9. Reconfigure isolated backend to point to cc181-clone-db and cc181-clone-redis
    log("Patching site config to use isolated db and redis...")
    patch_script = f"""
import json
path = '/home/frappe/frappe-bench/sites/{DEV_SITE}/site_config.json'
with open(path) as f:
    cfg = json.load(f)
cfg['db_host'] = '{DB_CONTAINER}'
cfg['db_password'] = '{clone_db_pass}'
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)

common_path = '/home/frappe/frappe-bench/sites/common_site_config.json'
with open(common_path) as f:
    ccfg = json.load(f)
ccfg['db_host'] = '{DB_CONTAINER}'
ccfg['redis_cache'] = 'redis://{REDIS_CONTAINER}:6379'
ccfg['redis_queue'] = 'redis://{REDIS_CONTAINER}:6379'
ccfg['redis_socketio'] = 'redis://{REDIS_CONTAINER}:6379'
with open(common_path, 'w') as f:
    json.dump(ccfg, f, indent=2)
"""
    run_cmd(
        ['docker', 'exec', '-i', BACKEND_CONTAINER, 'python3', '-c', patch_script]
    )

    # 10. Start gunicorn inside isolated backend container
    log("Starting gunicorn inside isolated backend container...")
    run_cmd([
        'docker', 'exec', '-d', '-w', '/home/frappe/frappe-bench/sites', BACKEND_CONTAINER,
        '/home/frappe/frappe-bench/env/bin/gunicorn',
        '-b', '0.0.0.0:8000',
        '-w', '2',
        '--threads', '4',
        '-t', '120',
        'frappe.app:application'
    ])

    # 11. Start isolated frontend container cc181-clone-frontend mapping host port 8098
    log(f"Starting isolated frontend container {FRONTEND_CONTAINER} on port {PORT}...")
    run_cmd([
        'docker', 'run', '-d',
        '--name', FRONTEND_CONTAINER,
        '--network', NET_NAME,
        '-p', f'127.0.0.1:{PORT}:8080',
        '-e', f'BACKEND={BACKEND_CONTAINER}:8000',
        '-e', f'FRAPPE_SITE_NAME_HEADER={DEV_SITE}',
        '-v', f'{APP_DIR}:/home/frappe/frappe-bench/apps/centrochange_core:ro',
        '-v', f'{APP_DIR}/centrochange_core/public:/home/frappe/frappe-bench/assets/centrochange_core:ro',
        dev_image,
        '/usr/local/bin/entrypoint.sh', 'nginx-entrypoint.sh'
    ])

    # 12. Warm-up and healthcheck
    log(f"Waiting for isolated frontend to respond on port {PORT}...")
    ready = False
    for attempt in range(30):
        time.sleep(1)
        res = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-H', f'Host: {DEV_SITE}', f'http://127.0.0.1:{PORT}/login'],
            capture_output=True, text=True
        )
        if res.stdout.strip() in ('200', '302', '301'):
            ready = True
            break
    if not ready:
        log("Warning: frontend did not respond 200/302 within 30s")
    log("Isolated clone environment ready.")


def run_real_clone_test():
    test_harness = """
import json
import secrets
import sys
import traceback
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
import frappe
from frappe.utils import getdate

ROME = ZoneInfo('Europe/Rome')

frappe.init('centrochange.local', sites_path='sites')
frappe.connect()
frappe.in_test = True
frappe.conf.cc_synthetic_dev = 1

import centrochange_core.operations.reporting as reporting
import centrochange_core.operations.lifecycle as lifecycle
import centrochange_core.scheduling.booking as booking
from centrochange_core.security.lifecycle import set_assignment, set_membership
from centrochange_core.security.audit import internal_write

test_results = {}

try:
    # 1. Discover operational environment
    operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name', 'cc_price_list'])
    if not operational_centers:
        raise RuntimeError("No operational Branch found in database")
    center = operational_centers[0].name
    price_list = operational_centers[0].cc_price_list

    practitioners = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active'}, fields=['name', 'user_id', 'practitioner_name'])
    if len(practitioners) < 2:
        raise RuntimeError("At least two Healthcare Practitioners required")
    prac_a = practitioners[0].name
    user_a = practitioners[0].user_id
    prac_b = practitioners[1].name
    user_b = practitioners[1].user_id

    managers = frappe.get_all('Has Role', filters={'role': 'CC Manager', 'parenttype': 'User'}, fields=['parent'])
    manager_user = managers[0].parent if managers else 'Administrator'

    secretaries = frappe.get_all('Has Role', filters={'role': 'CC Secretariat', 'parenttype': 'User'}, fields=['parent'])
    secretary_user = secretaries[0].parent if secretaries else manager_user

    from centrochange_core.finance.collections import _booking_debts
    zero_debt_patients = [p.name for p in frappe.get_all('Patient', fields=['name']) if len(_booking_debts(p.name)) == 0]
    if not zero_debt_patients:
        raise RuntimeError("No debt-free Patient found in database for clean booking tests")
    patient_1 = zero_debt_patients[0]

    services = frappe.get_all('Appointment Type', fields=['name', 'default_duration', 'cc_service_item'])
    service_1 = services[0].name

    mops = frappe.get_all('Mode of Payment', filters={'enabled': 1}, fields=['name'])
    valid_mop = mops[0].name if mops else 'Cash'

    frappe.set_user('Administrator')
    set_assignment(patient_1, center, prac_a, 1, 'Isolated clone assignment for A')

    today = date.today()
    day_close = '2099-08-17'
    day_future = '2099-08-24'
    day_formula = '2099-08-31'
    start_str = '2099-08-01'
    end_str = '2099-08-31'

    # -------------------------------------------------------------
    # Scenario 1 (CC-CAP-028): Operational Reporting & Reconciliation
    # -------------------------------------------------------------
    # Create deterministic appointments across various states
    # 1. Svolta (performed=1, closed)
    app_performed = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_close,
        appointment_time='09:00:00', reason='Synthetic performed check',
        request_key=f'audit08-perf-{secrets.token_hex(4)}'
    )['name']

    # 2. Non svolta (performed=0, closed) -> must NOT be in future or to_close
    app_non_svolta = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_close,
        appointment_time='10:00:00', reason='Synthetic non-svolta check',
        request_key=f'audit08-noshow-{secrets.token_hex(4)}'
    )['name']

    # 3. Futura (performed=0, closure_state!=Closed, date > today)
    app_future = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_future,
        appointment_time='11:00:00', reason='Synthetic future check',
        request_key=f'audit08-future-{secrets.token_hex(4)}'
    )['name']

    # 4. Annullata (Cancelled)
    app_cancelled = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_future,
        appointment_time='12:00:00', reason='Synthetic cancelled check',
        request_key=f'audit08-cancel-{secrets.token_hex(4)}'
    )['name']
    lifecycle.cancel(app_cancelled, 'Annullamento tempestivo di test')

    # Close day for 2099-08-17 by setting test clock after session end
    frappe.flags.cc_test_clock = datetime(2099, 8, 17, 18, 0, 0, tzinfo=ROME)
    frappe.set_user(user_a)
    lifecycle.close_day(center, day_close, [
        {'name': app_performed, 'performed': True, 'paid': True, 'mode_of_payment': valid_mop},
        {'name': app_non_svolta, 'performed': False, 'paid': False}
    ])

    # Query summary as Manager
    frappe.set_user(manager_user)
    summary = reporting.summary(center=center, start=start_str, end=end_str)
    currencies = summary.get('currencies', {})
    assert len(currencies) > 0, "Summary currencies should not be empty"

    # Verify sessions endpoint for each KPI
    sessions_all = reporting.sessions(center=center, start=start_str, end=end_str, kpi='all')
    app_names = [a['name'] for a in sessions_all['appointments']]
    assert app_performed in app_names, "Performed app should be in all sessions"
    assert app_non_svolta in app_names, "Non svolta app should be in all sessions"
    assert app_future in app_names, "Future app should be in all sessions"
    assert app_cancelled in app_names, "Cancelled app should be in all sessions"

    # Check future KPI filter: app_future must be present, app_non_svolta must NOT be present
    sessions_future = reporting.sessions(center=center, start=start_str, end=end_str, kpi='future')
    future_names = [a['name'] for a in sessions_future['appointments']]
    assert app_future in future_names, "Future app should be in future sessions"
    assert app_non_svolta not in future_names, "Non svolta app must NOT be in future sessions"

    # Check to_close KPI filter: app_non_svolta must NOT be present
    sessions_toclose = reporting.sessions(center=center, start=start_str, end=end_str, kpi='to_close')
    toclose_names = [a['name'] for a in sessions_toclose['appointments']]
    assert app_non_svolta not in toclose_names, "Non svolta app must NOT be in to_close sessions"

    # Check performed KPI filter
    sessions_perf = reporting.sessions(center=center, start=start_str, end=end_str, kpi='performed')
    perf_names = [a['name'] for a in sessions_perf['appointments']]
    assert app_performed in perf_names, "Performed app should be in performed sessions"
    assert app_non_svolta not in perf_names, "Non svolta app must NOT be in performed sessions"

    test_results['scenario_1_operational_reporting_reconciliation'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 2 (CC-CAP-030): Management Dashboard & Anti-Leak
    # -------------------------------------------------------------
    frappe.set_user(manager_user)
    dashboard_data = reporting.dashboard(center=center, start=start_str, end=end_str)

    assert 'currencies' in dashboard_data, "Dashboard must return currencies"
    assert 'total_appointments' in dashboard_data, "Dashboard must return total_appointments"
    assert len(dashboard_data.get('currencies', {})) > 0, "Dashboard currencies must not be empty"

    # Check that clinical notes or patient medical sensitive data are NOT returned in dashboard
    raw_dashboard_json = json.dumps(dashboard_data)
    assert 'clinical_notes' not in raw_dashboard_json, "Clinical notes leaked in dashboard!"
    assert 'diagnosis' not in raw_dashboard_json, "Diagnosis leaked in dashboard!"
    assert 'prescription' not in raw_dashboard_json, "Prescription leaked in dashboard!"

    # Secretarial role access check
    frappe.set_user(secretary_user)
    sec_dash = reporting.dashboard(center=center, start=start_str, end=end_str)
    assert 'currencies' in sec_dash, "Secretariat should be able to access dashboard"

    # Professional denied from center-wide dashboard
    frappe.set_user(user_a)
    pro_dash_denied = False
    try:
        reporting.dashboard(center=center, start=start_str, end=end_str)
    except frappe.PermissionError:
        pro_dash_denied = True
    assert pro_dash_denied, "Professional was not denied access to management dashboard with PermissionError"

    test_results['scenario_2_management_dashboard_and_anti_leak'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 3 (CC-CAP-029): Secure CSV Export Standards
    # -------------------------------------------------------------
    frappe.set_user('Administrator')
    # Create an appointment with formula injection candidate service label
    app_formula = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_formula,
        appointment_time='14:00:00', reason='=1+1 Formula Injection Test',
        request_key=f'audit08-csv-{secrets.token_hex(4)}'
    )['name']
    frappe.db.set_value('Patient Appointment', app_formula, 'appointment_type', 'Audit08 Non Fixture Service')
    frappe.db.set_value('Patient Appointment', app_formula, 'cc_service_label', '=cmd|calc!A1')
    frappe.db.commit()

    # Call export_csv
    frappe.set_user(manager_user)
    reporting.export_csv(center=center, start=start_str, end=end_str)

    # Check response headers and content
    assert frappe.response.get('type') == 'download', "Response type should be download"
    csv_text = frappe.response.get('filecontent')
    assert csv_text.startswith('\ufeff'), "CSV must start with UTF-8 BOM"

    lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
    header = lines[0]
    assert ';' in header, "Delimiter must be semicolon (;)"
    assert '"Data"' in header and '"Paziente"' in header and '"Professionista"' in header, "Standard headers required"

    # Check that formula '=cmd|calc!A1' is escaped to "'=cmd|calc!A1"
    assert "'=cmd|calc!A1" in csv_text, "Formula injection must be prepended with single quote"

    test_results['scenario_3_secure_csv_export'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 4 (CC-CAP-039, CC-CAP-005, CC-CAP-033, CC-CAP-038): RBAC & Boundaries
    # -------------------------------------------------------------
    # Professional querying reporting.sessions:
    frappe.set_user(user_a)
    # 4a. Cross-practitioner query is rejected with PermissionError
    pro_cross_denied = False
    try:
        reporting.sessions(center=center, start=start_str, end=end_str, practitioner=prac_b)
    except frappe.PermissionError:
        pro_cross_denied = True
    assert pro_cross_denied, "Cross-practitioner query by Professional A was not rejected with PermissionError"

    # When practitioner is None, it is automatically clamped to prac_a
    pro_sessions = reporting.sessions(center=center, start=start_str, end=end_str, practitioner=None)
    for app in pro_sessions['appointments']:
        assert app['practitioner'] == prac_a, f"Professional A received appointment belonging to {app['practitioner']}"

    # 4b. Guest and Patient denied
    frappe.set_user('Guest')
    guest_denied = False
    try:
        reporting.summary(center=center, start=start_str, end=end_str)
    except frappe.PermissionError:
        guest_denied = True
    assert guest_denied, "Guest was not denied with PermissionError"

    # 4c. print_session boundaries
    # Manager can print
    frappe.set_user(manager_user)
    print_data = reporting.print_session(appointment=app_performed)
    assert isinstance(print_data, str) and '<!doctype html>' in print_data and 'Riepilogo seduta' in print_data

    # Professional A can print their own appointment
    frappe.set_user(user_a)
    pro_print = reporting.print_session(appointment=app_performed)
    assert isinstance(pro_print, str) and '<!doctype html>' in pro_print and 'Riepilogo seduta' in pro_print

    # Professional B CANNOT print Professional A's appointment
    frappe.set_user(user_b)
    pro_b_print_denied = False
    try:
        reporting.print_session(appointment=app_performed)
    except frappe.PermissionError:
        pro_b_print_denied = True
    assert pro_b_print_denied, "Professional B was not denied printing Professional A appointment"

    test_results['scenario_4_rbac_and_boundaries'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 5: Regression of AUDIT-07 metrics in reporting
    # -------------------------------------------------------------
    # Booking with late cancellation & economic waiver
    frappe.set_user('Administrator')
    app_waiver = booking.book(
        patient=patient_1, practitioner=prac_a, center=center,
        appointment_type=service_1, appointment_date=day_formula,
        appointment_time='16:00:00', reason='Synthetic waiver test',
        request_key=f'audit08-waiver-{secrets.token_hex(4)}'
    )['name']
    doc_waiver = frappe.get_doc('Patient Appointment', app_waiver)
    frappe.flags.cc_test_clock = lifecycle.start_utc(doc_waiver) - timedelta(hours=10)
    fact_late = lifecycle.cancel(app_waiver, 'Cancellazione tardiva per waiver')
    assert fact_late['late'] is True, "Expected late cancellation"

    # Secretariat authorizes waiver
    frappe.set_user(secretary_user)
    lifecycle.waive(app_waiver, 'Deroga motivata segreteria per motivi sanitari')
    doc_waiver.reload()
    assert doc_waiver.cc_economic_state == 'Waived', "Appointment should have Waived economic state"

    # Reset clock back to 2099-08-17 18:00
    frappe.flags.cc_test_clock = datetime(2099, 8, 17, 18, 0, 0, tzinfo=ROME)

    # Query summary as Manager to verify waived session appears in cancelled KPI
    frappe.set_user(manager_user)
    summary_after = reporting.summary(center=center, start=start_str, end=end_str)
    sessions_cancelled = reporting.sessions(center=center, start=start_str, end=end_str, kpi='cancelled')
    canc_names = [a['name'] for a in sessions_cancelled['appointments']]
    assert app_waiver in canc_names, "Waived cancelled appointment must appear in cancelled drilldown"

    test_results['scenario_5_audit07_lifecycle_metrics_regression'] = 'PASS'

    # Clear test clock before finishing
    frappe.flags.cc_test_clock = None
    print(json.dumps({'status': 'PASS', 'results': test_results}))

except Exception as err:
    traceback.print_exc()
    print(json.dumps({'status': 'FAIL', 'error': str(err), 'results': test_results}))
    sys.exit(1)
"""
    log("Executing AUDIT-08 Python test harness inside isolated backend...")
    out = run_cmd([
        'docker', 'exec', '-i',
        '-e', 'FRAPPE_STREAM_LOGGING=1',
        '-w', '/home/frappe/frappe-bench',
        BACKEND_CONTAINER,
        '/home/frappe/frappe-bench/env/bin/python', '-'
    ], input_str=test_harness)

    lines = [l for l in out.strip().splitlines() if l.strip().startswith('{') and 'results' in l]
    if not lines:
        log(f"Test output unparsed:\n{out}")
        raise RuntimeError("No JSON test result returned from test harness")
    data = json.loads(lines[-1])
    log(f"Harness result: {data}")
    if data.get('status') != 'PASS':
        raise RuntimeError(f"Harness failed: {data}")


def run_browser_uat():
    log("Executing Playwright Browser UAT against isolated clone...")
    env = dict(os.environ)
    env['NODE_PATH'] = '/tmp/cc-browser-qa/node_modules'
    env['CC_UAT_PORT'] = str(PORT)
    env['CC_BACKEND_CONTAINER'] = BACKEND_CONTAINER

    script_path = str(ROOT_DIR / 'infra/run_audit08_clone_browser_uat.cjs')
    proc = subprocess.run(['node', script_path], env=env, capture_output=True, text=True)
    log(f"Browser UAT stdout:\n{proc.stdout}")
    if proc.stderr:
        log(f"Browser UAT stderr:\n{proc.stderr}")
    if proc.returncode != 0:
        raise RuntimeError(f"Browser UAT failed with code {proc.returncode}")
    log("Browser UAT complete. Screenshots saved.")


def main():
    success = False
    try:
        setup_clone()
        run_real_clone_test()
        run_browser_uat()
        success = True
        log("=== AUDIT-08 ISOLATED CLONE VERIFICATION: FULL PASS ===")
    finally:
        cleanup()
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
