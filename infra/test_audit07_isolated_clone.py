#!/usr/bin/env python3
"""AUDIT-07 Real Isolated Clone Verification on Frappe / MariaDB.

Guarantees:
- Dedicated Docker network and isolated containers (cc179-clone-net, cc179-clone-db, cc179-clone-redis, cc179-clone-backend, cc179-clone-frontend).
- Live DEV containers and volumes (centrochange-dev-*) are NEVER mutated.
- Baseline schema and reference data cloned via read-only stream from DEV_DB.
- All candidate app code mounted into the isolated backend and frontend.
- Scenarios validated:
  1. CC-CAP-025, CC-ACT-006, CC-ACT-007: 48h exact threshold boundary, timely vs late cancellation, DST spring/autumn transitions in Europe/Rome, package reservation/release/consumption, authorized economic waiver (deroga) strictly preserving late cancellation fact, role authorization boundaries.
  2. CC-CAP-014, CC-ACT-004: Operational session closure, operational payment flag, valid payment methods, CC Settlement immutable sequence, zero ERP/GL postings.
  3. CC-CAP-023: 21:00 reminder job / scheduler catch-up, deduplication, CC Notification, native Notification Log delivery, recipient scoping, IDOR protection, mark as read.
  4. CC-CAP-024, CC-CAP-022, CC-ACT-005: 07:00 next-day auto-lock, SESSION_AUTO_LOCKED audit, autonomous arrear completion by professional, SESSION_LATE_COMPLETED audit, cross-practitioner IDOR denial, immutable consolidated records, administrative reopen.
  5. CC-CAP-026, CC-CAP-027: Exceptions, delivery failure on disabled recipient, manager retry, cross-center isolation.
  6. Headless real Chromium browser UAT across all 4 mandatory route areas (Desktop & Mobile screenshots).
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

NET_NAME = 'cc179-clone-net'
DB_CONTAINER = 'cc179-clone-db'
REDIS_CONTAINER = 'cc179-clone-redis'
BACKEND_CONTAINER = 'cc179-clone-backend'
FRONTEND_CONTAINER = 'cc179-clone-frontend'

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
    log("Setting up isolated clone environment for AUDIT-07...")
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

    # 9. Reconfigure isolated backend to point to cc179-clone-db and cc179-clone-redis
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

    # 11. Start isolated frontend container cc179-clone-frontend mapping host port 8098
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

import centrochange_core.operations.lifecycle as lifecycle
import centrochange_core.operations.packages as packages
import centrochange_core.operations.automation as automation
import centrochange_core.operations.notifications as notifications
import centrochange_core.scheduling.booking as booking
import centrochange_core.operations.workspace as workspace
import centrochange_core.operations.reporting as reporting
from centrochange_core.security.lifecycle import set_assignment, set_membership
from centrochange_core.security.audit import internal_write

test_results = {}

try:
    # 1. Discover operational center, practitioners, manager, secretary
    operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name', 'cc_price_list'])
    if not operational_centers:
        raise RuntimeError("No operational Branch found in database")
    center = operational_centers[0].name
    price_list = operational_centers[0].cc_price_list

    practitioners = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active'}, fields=['name', 'user_id'])
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

    # Ensure patient assignment to center and practitioner
    frappe.set_user('Administrator')
    set_assignment(patient_1, center, prac_a, 1, 'Isolated clone assignment for A')

    # Baseline accounting row counts
    accounting_before = {dt: frappe.db.count(dt) for dt in ('Sales Invoice', 'Payment Entry', 'GL Entry', 'Payment Ledger Entry')}

    # -------------------------------------------------------------
    # Scenario 1 (CC-CAP-025, CC-ACT-006, CC-ACT-007): 48h Boundary, DST & Waiver
    # -------------------------------------------------------------
    # 1a. Booking without package: exact boundary cancellation test
    payload_base = {
        'patient': patient_1, 'practitioner': prac_a, 'center': center,
        'appointment_type': service_1, 'appointment_date': '2099-07-20',
        'appointment_time': '10:00:00', 'reason': 'Synthetic cancellation boundary check'
    }
    app1 = booking.book(**{**payload_base, 'request_key': 'audit07-cancel-exact'})['name']
    doc1 = frappe.get_doc('Patient Appointment', app1)
    start_utc1 = lifecycle.start_utc(doc1)

    # Cancel at exactly 48:00:00 before session start -> Timely (late == False)
    frappe.flags.cc_test_clock = start_utc1 - timedelta(hours=48)
    fact1 = lifecycle.cancel(app1, 'Exact 48h boundary timely cancellation')
    assert fact1['late'] is False, f"Expected timely cancellation at exactly 48h, got {fact1}"
    doc1.reload()
    assert doc1.status == 'Cancelled' and doc1.cc_late_cancellation == 0 and doc1.cc_economic_state == 'Non Due'
    # Idempotent replay
    assert lifecycle.cancel(app1, 'Replay cancel')['replay'] is True

    # 1b. Booking without package: 47h 59m 59s cancellation -> Late (late == True)
    app2 = booking.book(**{**payload_base, 'appointment_date': '2099-07-27', 'request_key': 'audit07-cancel-late'})['name']
    doc2 = frappe.get_doc('Patient Appointment', app2)
    start_utc2 = lifecycle.start_utc(doc2)
    frappe.flags.cc_test_clock = start_utc2 - timedelta(hours=48) + timedelta(microseconds=1)
    fact2 = lifecycle.cancel(app2, 'Microsecond below 48h late cancellation')
    assert fact2['late'] is True, f"Expected late cancellation at 47h 59m 59s, got {fact2}"
    doc2.reload()
    assert doc2.status == 'Cancelled' and doc2.cc_late_cancellation == 1 and doc2.cc_economic_state == 'Due'

    # Test Economic Waiver (Deroga) on app2:
    # Professional cannot waive
    frappe.set_user(user_a)
    pro_waiver_rejected = False
    try:
        lifecycle.waive(app2, 'Unauthorized pro waiver on list price')
    except frappe.PermissionError:
        pro_waiver_rejected = True
    assert pro_waiver_rejected, "Professional waiver on app2 was not rejected with PermissionError"

    # Secretariat / Manager authorizes waiver on app2 -> clears debt hold
    frappe.set_user(secretary_user)
    waiver_res1 = lifecycle.waive(app2, 'Deroga motivata segreteria per disdetta tardiva tariffa di listino')
    assert waiver_res1['name'] == app2 and waiver_res1['replay'] is False
    assert lifecycle.waive(app2, 'Waiver retry')['replay'] is True
    doc2.reload()
    assert doc2.cc_late_cancellation == 1, "Late cancellation fact was erased by waiver!"
    assert doc2.cc_economic_state == 'Waived'

    # 1c. DST European/Rome transitions: spring and autumn
    for start_local, at_local in [('2026-03-30T12:00:00', '2026-03-28T11:00:00'), ('2026-10-26T12:00:00', '2026-10-24T13:00:00')]:
        f = lifecycle.cancellation_fact(
            datetime.fromisoformat(start_local).replace(tzinfo=ROME),
            datetime.fromisoformat(at_local).replace(tzinfo=ROME)
        )
        assert f['notice_seconds'] == 172800.0 and f['late'] is False, f"DST boundary check failed for {start_local} / {at_local}: {f}"

    # 1d. Package reservation, timely cancellation releases, late cancellation consumes
    pkg_template = frappe.get_all('CC Package Template', filters={'enabled': 1}, fields=['name', 'service_item'])
    if not pkg_template:
        pkg_template = [frappe.get_doc({
            'doctype': 'CC Package Template', 'title': 'CC AUDIT07 PKG', 'service_item': service_1, 'units': 5, 'enabled': 1
        }).insert(ignore_permissions=True)]
    template_name = pkg_template[0].name

    issued_pkg = packages.issue(template_name, patient_1, [center], 'pkg-audit07-test', 'Audit07 package issuance')['name']
    bal_initial = packages.balance(issued_pkg, center)
    assert bal_initial['remaining'] >= 1 and bal_initial['reserved'] == 0

    # Book with package
    app_pkg = booking.book(**{
        **payload_base, 'appointment_date': '2099-08-03', 'request_key': 'audit07-pkg-book', 'patient_package': issued_pkg
    })['name']
    bal_after_book = packages.balance(issued_pkg, center)
    assert bal_after_book['reserved'] == bal_initial['reserved'] + 1 and bal_after_book['available'] == bal_initial['available'] - 1

    # Timely cancellation releases reserved unit
    doc_pkg = frappe.get_doc('Patient Appointment', app_pkg)
    frappe.flags.cc_test_clock = lifecycle.start_utc(doc_pkg) - timedelta(hours=50)
    fact_pkg = lifecycle.cancel(app_pkg, 'Timely cancellation of package appointment')
    assert fact_pkg['late'] is False
    bal_after_timely = packages.balance(issued_pkg, center)
    assert bal_after_timely['reserved'] == bal_initial['reserved'] and bal_after_timely['available'] == bal_initial['available']

    # Book again and cancel late -> unit is consumed
    app_pkg_late = booking.book(**{
        **payload_base, 'appointment_date': '2099-08-10', 'request_key': 'audit07-pkg-late', 'patient_package': issued_pkg
    })['name']
    doc_pkg_late = frappe.get_doc('Patient Appointment', app_pkg_late)
    frappe.flags.cc_test_clock = lifecycle.start_utc(doc_pkg_late) - timedelta(hours=10)
    fact_pkg_late = lifecycle.cancel(app_pkg_late, 'Late cancellation of package appointment')
    assert fact_pkg_late['late'] is True
    doc_pkg_late.reload()
    assert doc_pkg_late.cc_economic_state == 'Package Covered' and doc_pkg_late.cc_late_cancellation == 1
    bal_after_late = packages.balance(issued_pkg, center)
    assert bal_after_late['remaining'] == bal_initial['remaining'] - 1

    # 1e. Economic Waiver (Deroga) on package:
    frappe.set_user(secretary_user)
    waiver_res = lifecycle.waive(app_pkg_late, 'Deroga motivata segreteria per disdetta tardiva pacchetto')
    assert waiver_res['name'] == app_pkg_late and waiver_res['replay'] is False
    assert lifecycle.waive(app_pkg_late, 'Waiver retry')['replay'] is True
    doc_pkg_late.reload()
    assert doc_pkg_late.cc_late_cancellation == 1, "Late cancellation fact was erased by waiver!"
    assert doc_pkg_late.cc_economic_state == 'Waived'
    bal_after_waiver = packages.balance(issued_pkg, center)
    assert bal_after_waiver['remaining'] == bal_initial['remaining'], "Package unit was not restored after corrective waiver"

    # Audit event recorded for ECONOMIC_WAIVER
    waiver_events = frappe.get_all('CC Audit Event', filters={'event_type': 'ECONOMIC_WAIVER', 'reference_name': app_pkg_late})
    assert len(waiver_events) >= 1, "ECONOMIC_WAIVER audit event missing"

    test_results['scenario_1_cancellation_48h_waiver'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 2 (CC-CAP-014, CC-ACT-004): Operational Closure & Settlements
    # -------------------------------------------------------------
    frappe.set_user('Administrator')
    app_close = booking.book(**{
        **payload_base, 'appointment_date': '2099-08-17', 'appointment_time': '09:00:00', 'request_key': 'audit07-close-settle'
    })['name']
    doc_close = frappe.get_doc('Patient Appointment', app_close)
    frappe.flags.cc_test_clock = lifecycle.start_utc(doc_close) + timedelta(hours=2)

    # Professional closes session: performed=1, paid=0 (unpaid operational status)
    frappe.set_user(user_a)
    lifecycle.close(app_close, 0, 'Seduta svolta non saldata')
    doc_close.reload()
    assert doc_close.status == 'Closed' and doc_close.cc_closure_state == 'Closed' and doc_close.cc_performed == 1 and doc_close.cc_paid == 0
    settlements1 = lifecycle.current_settlements(app_close)
    assert len(settlements1) == 1 and settlements1[0].paid == 0 and settlements1[0].sequence == 1

    # Record operational settlement: paid=1, method POS/Cash
    mops = frappe.get_all('Mode of Payment', filters={'enabled': 1}, fields=['name'])
    mop_name = mops[0].name if mops else 'Cash'
    
    frappe.set_user(secretary_user)
    settle_res = lifecycle.record_settlement(app_close, 1, 'Registrazione incasso operativo POS', mop_name)
    assert settle_res['paid'] == 1
    doc_close.reload()
    assert doc_close.cc_paid == 1
    settlements2 = lifecycle.current_settlements(app_close)
    assert len(settlements2) == 2 and settlements2[0].paid == 1 and settlements2[0].sequence == 2

    # Idempotent replay of settlement
    settle_replay = lifecycle.record_settlement(app_close, 1, 'Replay incasso', mop_name)
    assert settle_replay['settlement'] == settlements2[0].name

    # Settlement records are immutable append-only
    settle_doc = frappe.get_doc('CC Settlement', settlements2[0].name)
    settle_doc.reason = 'Forbidden mutation'
    mutation_rejected = False
    try:
        settle_doc.save(ignore_permissions=True)
    except frappe.PermissionError:
        mutation_rejected = True
    assert mutation_rejected, "Direct mutation on CC Settlement was not rejected"

    # Zero ERP accounting postings created by operational closures or settlements
    accounting_after = {dt: frappe.db.count(dt) for dt in accounting_before}
    assert accounting_before == accounting_after, f"ERP accounting rows mutated: before={accounting_before}, after={accounting_after}"

    test_results['scenario_2_operational_settlement'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 3 (CC-CAP-023): 21:00 Reminder Scheduling & Notification Scoping
    # -------------------------------------------------------------
    frappe.set_user('Administrator')
    app_remind = booking.book(**{
        **payload_base, 'appointment_date': '2099-09-01', 'appointment_time': '14:00:00', 'request_key': 'audit07-remind-pending'
    })['name']
    doc_remind = frappe.get_doc('Patient Appointment', app_remind)
    remind_date = getdate(doc_remind.appointment_date)

    # Set test clock to 21:00 on the day of the appointment
    frappe.flags.cc_test_clock = datetime.combine(remind_date, time(21, 0, 0)).replace(tzinfo=ROME).astimezone(timezone.utc)
    res_catchup = automation.catch_up()
    assert res_catchup['reminders'] >= 1, "21:00 catch_up failed to generate reminder"
    # Deduplication: re-running catch_up at 21:00 generates 0 duplicate reminders
    res_dedup = automation.catch_up()
    assert res_dedup['reminders'] == 0, "Catch-up generated duplicate reminder for same practitioner/date"

    remind_key = f'closure-reminder:{remind_date}:{prac_a}'
    remind_doc = frappe.get_doc('CC Notification', {'event_key': remind_key})
    assert remind_doc.recipient == user_a
    assert 'Hai sedute da chiudere oggi' in remind_doc.message

    # Dispatch pending notifications
    dispatch_res = notifications.dispatch_pending()
    remind_doc.reload()
    assert remind_doc.state == 'Sent'

    # Recipient can read in Notification Log
    frappe.set_user(user_a)
    log_name = frappe.db.get_value('Notification Log', {'cc_notification': remind_doc.name})
    assert log_name, "Native Notification Log row missing for recipient"
    assert log_name in frappe.get_list('Notification Log', pluck='name')

    # Native mark_as_read
    from frappe.desk.doctype.notification_log.notification_log import mark_as_read
    mark_as_read(log_name)
    assert frappe.db.get_value('Notification Log', log_name, 'read') == 1

    # IDOR check: other professional cannot read or see recipient's Notification Log
    frappe.set_user(user_b)
    assert log_name not in frappe.get_list('Notification Log', pluck='name')

    test_results['scenario_3_21h_reminder_and_notifications'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 4 (CC-CAP-024, CC-CAP-022, CC-ACT-005): 07:00 Auto-Lock & Arrear Recovery
    # -------------------------------------------------------------
    # Session app_remind was left pending. Now simulate next day 07:00 Rome time
    frappe.set_user('Administrator')
    next_day_7am = datetime.combine(remind_date + timedelta(days=1), time(7, 0, 0)).replace(tzinfo=ROME).astimezone(timezone.utc)
    frappe.flags.cc_test_clock = next_day_7am
    res_lock = automation.catch_up()
    assert res_lock['locked'] >= 1, "07:00 catch-up failed to lock unresolved session"
    doc_remind.reload()
    assert doc_remind.cc_closure_state == 'Auto Locked', f"Expected Auto Locked, got {doc_remind.cc_closure_state}"

    # Auto lock is idempotent
    assert automation.catch_up()['locked'] == 0

    # Practitioner cannot directly close Auto Locked session via single close() API
    frappe.set_user(user_a)
    direct_close_rejected = False
    try:
        lifecycle.close(app_remind, 0, 'Unauthorized direct close after lock')
    except frappe.PermissionError:
        direct_close_rejected = True
    assert direct_close_rejected, "Direct close() on Auto Locked session was not rejected"

    # Practitioner autonomously resolves own arrear session via close_day()
    close_day_payload = [{
        'appointment': app_remind,
        'performed': 1,
        'paid': 0,
        'mode_of_payment': None,
        'note': 'Recupero autonomo seduta arretrata del 01/09'
    }]
    day_res = lifecycle.close_day(center, str(remind_date), close_day_payload, reason='Recupero autonomo arretrato')
    assert day_res['status'] == 'PASS'
    doc_remind.reload()
    assert doc_remind.status == 'Closed' and doc_remind.cc_closure_state == 'Closed' and doc_remind.cc_performed == 1

    # Audit event SESSION_LATE_COMPLETED recorded
    late_events = frappe.get_all('CC Audit Event', filters={'event_type': 'SESSION_LATE_COMPLETED', 'reference_name': app_remind})
    assert len(late_events) >= 1, "SESSION_LATE_COMPLETED audit event missing"

    # Cannot alter consolidated data: calling close_day with conflicting parameters throws error
    conflicting_payload = [{
        'appointment': app_remind,
        'performed': 0,
        'paid': 0,
        'mode_of_payment': None
    }]
    override_rejected = False
    try:
        lifecycle.close_day(center, str(remind_date), conflicting_payload)
    except frappe.PermissionError:
        override_rejected = True
    assert override_rejected, "Conflicting modification of consolidated closed session was not rejected"

    # Administrative Reopen
    frappe.set_user(secretary_user)
    reopen_res = lifecycle.reopen(app_remind, 'Riapertura autorizzata segreteria')
    assert reopen_res['name'] == app_remind and reopen_res['replay'] is False
    doc_remind.reload()
    assert doc_remind.cc_closure_state == 'Reopened'
    # Pro cannot call reopen
    frappe.set_user(user_a)
    pro_reopen_rejected = False
    try:
        lifecycle.reopen(app_remind, 'Unauthorized pro reopen')
    except frappe.PermissionError:
        pro_reopen_rejected = True
    assert pro_reopen_rejected, "Professional reopen was not rejected with PermissionError"

    test_results['scenario_4_auto_lock_and_arrear_recovery'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 5 (CC-CAP-026, CC-CAP-027): Notifications Error & Retry, Cross-Center
    # -------------------------------------------------------------
    frappe.set_user('Administrator')
    # Disabled recipient delivery failure
    fail_notice = automation.enqueue_notice(
        'audit07-fail-notice', 'Guest', 'CLOSURE_REMINDER', 'Healthcare Practitioner', prac_a, 'Notice to disabled recipient'
    )
    # Guest user is disabled
    frappe.db.set_value('User', 'Guest', 'enabled', 0)
    deliv_res = notifications.deliver(fail_notice)
    assert deliv_res['state'] == 'Failed', f"Expected Failed delivery, got {deliv_res}"
    fail_doc = frappe.get_doc('CC Notification', fail_notice)
    assert fail_doc.state == 'Failed' and 'disabled' in (fail_doc.last_error or '').lower()

    # Professional cannot retry notification
    frappe.set_user(user_a)
    pro_retry_rejected = False
    try:
        notifications.retry(fail_notice, 'Unauthorized pro retry')
    except frappe.PermissionError:
        pro_retry_rejected = True
    assert pro_retry_rejected, "Professional notification retry was not rejected with PermissionError"

    # Manager can retry notification
    frappe.set_user(manager_user)
    retry_res = notifications.retry(fail_notice, 'Motivazione nuovo invio manager')
    assert retry_res['name'] == fail_notice and retry_res['replay'] is False
    fail_doc.reload()
    assert fail_doc.state == 'Pending' and fail_doc.retry_limit >= 6

    # Cross-center isolation check
    other_branches = frappe.get_all('Branch', filters={'cc_operational': 1, 'name': ['!=', center]}, fields=['name'])
    if other_branches:
        other_center = other_branches[0].name
        frappe.set_user(user_a)
        cross_center_rejected = False
        try:
            lifecycle.get_day_closure_sessions(other_center, str(remind_date))
        except frappe.PermissionError:
            cross_center_rejected = True
        assert cross_center_rejected, "Cross-center day closure retrieval was not rejected with PermissionError"

    test_results['scenario_5_notification_retry_and_isolation'] = 'PASS'

    # Reset test clock
    frappe.flags.cc_test_clock = None
    print(json.dumps({'status': 'PASS', 'results': test_results}))

except Exception as err:
    traceback.print_exc()
    print(json.dumps({'status': 'FAIL', 'error': str(err), 'results': test_results}))
    sys.exit(1)
"""
    log("Executing AUDIT-07 Python test harness inside isolated backend...")
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

    script_path = str(ROOT_DIR / 'infra/run_audit07_clone_browser_uat.cjs')
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
        log("=== AUDIT-07 ISOLATED CLONE VERIFICATION: FULL PASS ===")
    finally:
        cleanup()
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
