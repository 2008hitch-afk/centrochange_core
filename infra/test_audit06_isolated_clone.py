#!/usr/bin/env python3
"""AUDIT-06 Real Isolated Clone Verification on Frappe / MariaDB.

Guarantees:
- Dedicated Docker network and isolated containers (cc177-clone-net, cc177-clone-db, cc177-clone-redis, cc177-clone-backend, cc177-clone-frontend).
- Live DEV containers and volumes (centrochange-dev-*) are NEVER mutated.
- Baseline schema and reference data cloned via read-only stream from DEV_DB.
- All candidate app code mounted into the isolated backend and frontend.
- Scenarios validated:
  1. CC-CAP-007: Recurring schedule multi-slot intra-day, optimistic concurrency, overlap rejection, absence creation/replay/cancel, audit logging, role boundary.
  2. CC-CAP-011: Service catalog and appointment types records, duration validation, service toggle, non-manager role denial.
  3. CC-CAP-012: Item Price records scoped to center price list, future valid_from creation, collision rejection on same date, rate validation.
  4. CC-CAP-013: Booking snapshot immutability; subsequent catalog rate/duration mutations preserve historical appointments; direct snapshot mutation rejected.
  5. CC-EXT-010: Scoped editor boundaries, deny_extra injection prevention, cross-center isolation, zero standalone item creation.
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

NET_NAME = 'cc177-clone-net'
DB_CONTAINER = 'cc177-clone-db'
REDIS_CONTAINER = 'cc177-clone-redis'
BACKEND_CONTAINER = 'cc177-clone-backend'
FRONTEND_CONTAINER = 'cc177-clone-frontend'

DEV_DB = 'centrochange-dev-db-1'
DEV_BACKEND = 'centrochange-dev-backend-1'
DEV_SITE = 'centrochange.local'
PORT = 8097


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
    log("Setting up isolated clone environment for AUDIT-06...")
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

    # 9. Reconfigure isolated backend to point to cc177-clone-db and cc177-clone-redis
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

    # 11. Start isolated frontend container cc177-clone-frontend mapping host port 8097
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

import centrochange_core.catalog as catalog
import centrochange_core.scheduling.availability as availability
import centrochange_core.scheduling.booking as booking
import centrochange_core.security.guards as guards

test_results = {}

try:
    # 1. Discover operational center, practitioners, and manager
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

    patients = frappe.get_all('Patient', fields=['name'])
    patient_1 = patients[0].name

    # -------------------------------------------------------------
    # Scenario 1 (CC-CAP-007): Orari ricorrenti e assenze
    # -------------------------------------------------------------
    frappe.set_user(user_a)
    
    # Check current schedule
    sched_name = frappe.db.get_value('Practitioner Schedule', {'cc_practitioner': prac_a, 'cc_center': center})
    sched_doc = frappe.get_doc('Practitioner Schedule', sched_name) if sched_name else None
    exp_mod = str(sched_doc.modified) if sched_doc else ''

    # Multi-slot intra-day availability update
    slots = [
        {'day': 'Monday', 'from_time': '09:00:00', 'to_time': '13:00:00'},
        {'day': 'Monday', 'from_time': '14:30:00', 'to_time': '18:30:00'},
        {'day': 'Wednesday', 'from_time': '10:00:00', 'to_time': '16:00:00'}
    ]
    set_res = availability.set_schedule(prac_a, center, slots, 'Orario autunno 2026', expected_modified=exp_mod)
    assert set_res['name'], "Failed to set schedule"
    
    # Verify audit event for SCHEDULE_CHANGED
    events = frappe.get_all('CC Audit Event', filters={'event_type': 'SCHEDULE_CHANGED', 'reference_name': set_res['name']})
    assert len(events) >= 1, "SCHEDULE_CHANGED audit event not recorded"

    # Overlapping slot rejection
    overlap_slots = [
        {'day': 'Tuesday', 'from_time': '09:00:00', 'to_time': '13:00:00'},
        {'day': 'Tuesday', 'from_time': '12:00:00', 'to_time': '15:00:00'}
    ]
    overlap_rejected = False
    try:
        availability.set_schedule(prac_a, center, overlap_slots, 'Overlap test')
    except Exception as e:
        if 'sovrappongono' in str(e):
            overlap_rejected = True
    assert overlap_rejected, "Overlapping slots were not rejected"

    # Inverted time rejection
    inverted_slots = [{'day': 'Friday', 'from_time': '17:00:00', 'to_time': '09:00:00'}]
    inverted_rejected = False
    try:
        availability.set_schedule(prac_a, center, inverted_slots, 'Inverted test')
    except Exception as e:
        if 'precedere' in str(e):
            inverted_rejected = True
    assert inverted_rejected, "Inverted time interval was not rejected"

    # Optimistic concurrency (stale expected_modified)
    stale_rejected = False
    try:
        availability.set_schedule(prac_a, center, slots, 'Stale test', expected_modified='2020-01-01 00:00:00')
    except Exception as e:
        if 'cambiato' in str(e):
            stale_rejected = True
    assert stale_rejected, "Stale concurrency was not rejected"

    # Absence creation, idempotency, and cancellation (on Monday 2026-11-16 overlapping schedule)
    abs_res = availability.create_absence(prac_a, center, '2026-11-16', '2026-11-16', '09:00:00', '13:00:00', 'Ferie autunno')
    abs_name = abs_res['name']
    assert abs_name, "Absence creation failed"

    # Duplicate call returns same name (idempotency)
    abs_dup = availability.create_absence(prac_a, center, '2026-11-16', '2026-11-16', '09:00:00', '13:00:00', 'Ferie duplicate')
    assert abs_dup['name'] == abs_name, "Idempotent absence creation did not return existing name"

    # Cancel absence
    cancel_res = availability.cancel_absence(abs_name, 'Annullamento ferie')
    assert cancel_res['name'] == abs_name and cancel_res['replay'] is False, "Cancel absence failed"

    # Cancel replay (idempotent replay)
    cancel_dup = availability.cancel_absence(abs_name, 'Annullamento replay')
    assert cancel_dup['replay'] is True, "Idempotent absence cancel replay failed"

    # Role boundary: Doctor B cannot mutate Doctor A's schedule
    frappe.set_user(user_b)
    cross_pro_rejected = False
    try:
        availability.set_schedule(prac_a, center, slots, 'Cross pro update')
    except frappe.PermissionError:
        cross_pro_rejected = True
    assert cross_pro_rejected, "Cross-practitioner mutation was not rejected with PermissionError"

    test_results['scenario_1_availability_cap007'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 2 (CC-CAP-011): Catalogo servizi e tipi seduta
    # -------------------------------------------------------------
    frappe.set_user(manager_user)
    
    # Read services and appointment types
    srv_records = catalog.records(center, 'CC Center Service')
    assert len(srv_records['rows']) > 0, "No CC Center Service found"
    first_srv = srv_records['rows'][0]

    at_records = catalog.records(center, 'Appointment Type')
    assert len(at_records['rows']) > 0, "No Appointment Type found"
    first_at = at_records['rows'][0]

    # Appointment Type duration save
    orig_dur = first_at.default_duration or 50
    new_dur = 45 if orig_dur != 45 else 50
    at_save_res = catalog.appointment_type_save(center, first_at.name, new_dur, str(first_at.modified), 'REQ-AT-01', 'Modifica durata test')
    assert at_save_res['name'] == first_at.name, "Appointment type save failed"

    # Invalid duration rejection
    inv_dur_rejected = False
    try:
        catalog.appointment_type_save(center, first_at.name, -10, str(at_save_res['name']), 'REQ-AT-INV', 'Negativo')
    except Exception as e:
        if 'Durata non valida' in str(e):
            inv_dur_rejected = True
    assert inv_dur_rejected, "Invalid duration was not rejected"

    # Toggle service enabled state
    srv_save_res = catalog.service_save(center, first_srv.name, 0, str(first_srv.modified), 'REQ-SRV-01', 'Disabilitazione test')
    assert srv_save_res['name'] == first_srv.name, "Service toggle to 0 failed"
    # Toggle back to enabled
    fresh_srv_mod = str(frappe.db.get_value('CC Center Service', first_srv.name, 'modified'))
    srv_save_res2 = catalog.service_save(center, first_srv.name, 1, fresh_srv_mod, 'REQ-SRV-02', 'Riabilitazione test')
    assert srv_save_res2['name'] == first_srv.name, "Service toggle to 1 failed"

    # Role denial: Doctor A cannot mutate catalog
    frappe.set_user(user_a)
    non_mgr_rejected = False
    try:
        catalog.service_save(center, first_srv.name, 0, 'dummy', 'REQ-PRO-DENIED', 'Non autorizzato')
    except frappe.PermissionError:
        non_mgr_rejected = True
    assert non_mgr_rejected, "Non-manager mutating catalog was not rejected with PermissionError"

    test_results['scenario_2_catalogue_cap011'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 3 (CC-CAP-012): Tariffe per listino centro
    # -------------------------------------------------------------
    frappe.set_user(manager_user)

    price_records = catalog.records(center, 'Item Price')
    assert len(price_records['rows']) > 0, "No Item Price records found for center price list"
    first_price = price_records['rows'][0]

    # Create new future tariff
    test_future_date = '2028-01-01'
    existing_future = frappe.db.get_value('Item Price', {'item_code': first_price.item_code, 'price_list': price_list, 'valid_from': test_future_date})
    if existing_future:
        frappe.delete_doc('Item Price', existing_future, force=True)

    pr_create_res = catalog.price_create(center, first_price.item_code, test_future_date, '95.00', 'REQ-PR-CREATE-01', 'Listino futuro test')
    assert pr_create_res['name'], "Price create failed"

    # Collision rejection: duplicate valid_from for same item and price list
    dup_date_rejected = False
    try:
        catalog.price_create(center, first_price.item_code, test_future_date, '99.00', 'REQ-PR-DUP', 'Collisione test')
    except Exception as e:
        if 'già presente per questa decorrenza' in str(e):
            dup_date_rejected = True
    assert dup_date_rejected, "Duplicate valid_from was not rejected"

    # Price save validation (bounds)
    invalid_rate_rejected = False
    try:
        catalog.price_save(center, pr_create_res['name'], '-15.00', 'dummy', 'REQ-PR-NEG', 'Tariffa negativa')
    except Exception as e:
        if 'Tariffa non valida' in str(e):
            invalid_rate_rejected = True
    assert invalid_rate_rejected, "Negative rate was not rejected"

    test_results['scenario_3_prices_cap012'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 4 (CC-CAP-013): Snapshot servizio, durata e prezzo alla prenotazione
    # -------------------------------------------------------------
    # Snapshot generation
    snap = booking.snapshot(first_at.name, center, patient_1)
    assert snap['cc_price_snapshot'] is not None, "Missing cc_price_snapshot in booking.snapshot"
    assert snap['duration'] is not None, "Missing duration in booking.snapshot"
    assert snap['cc_booking_date'] == date.today(), "cc_booking_date mismatch"
    initial_price_snap = float(snap['cc_price_snapshot'])
    initial_duration_snap = int(snap['duration'])

    # Ensure patient assignment to practitioner in center exists
    asg_list = frappe.get_all('CC Patient Assignment', filters={'practitioner': prac_a, 'center': center, 'active': 1}, fields=['patient'])
    if asg_list:
        patient_1 = asg_list[0].patient
    else:
        from centrochange_core.security.audit import internal_write
        with internal_write('cc_relationship_write'):
            frappe.get_doc({
                'doctype': 'CC Patient Assignment',
                'patient': patient_1,
                'practitioner': prac_a,
                'center': center,
                'active': 1
            }).insert(ignore_permissions=True)

    # Book appointment
    future_appt_date = date.today() + timedelta(days=7)
    # Ensure weekday matches schedule (Monday or Wednesday)
    while future_appt_date.weekday() not in (0, 2):  # 0=Monday, 2=Wednesday
        future_appt_date += timedelta(days=1)
    future_appt_str = future_appt_date.isoformat()
    
    frappe.set_user(user_a)
    book_key = f'UAT-AUDIT06-SNAP-{secrets.token_hex(6)}'
    book_res = booking.book(
        patient=patient_1,
        practitioner=prac_a,
        center=center,
        appointment_type=first_at.name,
        appointment_date=future_appt_str,
        appointment_time='15:00:00',
        request_key=book_key,
        reason='Test snapshot AUDIT-06'
    )
    assert book_res['name'], "Booking failed"
    appt_name = book_res['name']

    # Verify appointment captured snapshot
    appt_doc = frappe.get_doc('Patient Appointment', appt_name)
    assert float(appt_doc.cc_price_snapshot) == initial_price_snap, f"Price snapshot mismatch: {appt_doc.cc_price_snapshot} vs {initial_price_snap}"
    assert int(appt_doc.duration) == initial_duration_snap, f"Duration snapshot mismatch: {appt_doc.duration} vs {initial_duration_snap}"

    # Mutate catalog: modify price and duration in catalog
    frappe.set_user(manager_user)
    fresh_at_mod = str(frappe.db.get_value('Appointment Type', first_at.name, 'modified'))
    catalog.appointment_type_save(center, first_at.name, 75, fresh_at_mod, 'REQ-AT-MUT-SNAP', 'Mutazione durata catalogo')
    fresh_pr_mod = str(frappe.db.get_value('Item Price', first_price.name, 'modified'))
    catalog.price_save(center, first_price.name, initial_price_snap + 30.0, fresh_pr_mod, 'REQ-PR-MUT-SNAP', 'Mutazione tariffa catalogo')

    # Re-verify that existing booked appointment retained historical snapshot unchanged!
    appt_recheck = frappe.get_doc('Patient Appointment', appt_name)
    assert float(appt_recheck.cc_price_snapshot) == initial_price_snap, \
        f"Historical price mutated! Got {appt_recheck.cc_price_snapshot}, expected {initial_price_snap}"
    assert int(appt_recheck.duration) == initial_duration_snap, \
        f"Historical duration mutated! Got {appt_recheck.duration}, expected {initial_duration_snap}"

    # Direct mutation of snapshot field on booked appointment must be rejected by AppointmentMixin
    appt_recheck.flags.ignore_permissions = False
    frappe.flags.cc_appointment_write = True
    appt_recheck.cc_price_snapshot = 999.00
    direct_mut_rejected = False
    try:
        appt_recheck.save()
    except Exception as e:
        if 'dati storici della seduta non possono essere modificati' in str(e):
            direct_mut_rejected = True
    frappe.flags.cc_appointment_write = False
    assert direct_mut_rejected, "Direct mutation of historical snapshot was not rejected by AppointmentMixin"

    test_results['scenario_4_snapshot_cap013'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 5 (CC-EXT-010): Contratto ristretto, deny_extra e isolamento
    # -------------------------------------------------------------
    frappe.set_user(manager_user)
    
    # Extra field injection denied
    extra_rejected = False
    try:
        catalog.service_save(center, first_srv.name, 1, 'dummy', 'REQ-EXTRA', 'Motivo', injected_malicious='payload')
    except frappe.PermissionError:
        extra_rejected = True
    assert extra_rejected, "deny_extra did not reject arbitrary parameter injection"

    # Cross-center mutation denied
    cross_rejected = False
    try:
        catalog.service_save('INEXISTENT-CENTER', first_srv.name, 1, 'dummy', 'REQ-CROSS', 'Motivo')
    except frappe.PermissionError:
        cross_rejected = True
    assert cross_rejected, "Cross-center catalog mutation was not rejected"

    # Verification: no standalone item_create exists in catalog
    assert not hasattr(catalog, 'item_create'), "Violated DECISION-063: item_create endpoint exists in catalog"

    test_results['scenario_5_scoped_editor_ext010'] = 'PASS'
    test_results['status'] = 'ALL_PASS'

except Exception as e:
    test_results['status'] = 'FAIL'
    test_results['error'] = str(e)
    test_results['traceback'] = traceback.format_exc()

print("AUDIT06_RESULT_JSON:" + json.dumps(test_results))
"""
    log("Executing real isolated clone test harness inside backend container...")
    proc = subprocess.run(
        ['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', BACKEND_CONTAINER, 'env/bin/python'],
        input=test_harness,
        text=True,
        capture_output=True,
        timeout=180
    )
    if proc.returncode != 0:
        log(f"Backend test failed with exit code {proc.returncode}")
        log(f"STDOUT:\n{proc.stdout}")
        log(f"STDERR:\n{proc.stderr}")
        raise RuntimeError(f"Real isolated clone test execution failed: {proc.stderr}")

    result_json = None
    for line in proc.stdout.splitlines():
        if line.startswith('AUDIT06_RESULT_JSON:'):
            result_json = json.loads(line[len('AUDIT06_RESULT_JSON:'):])
            break

    if not result_json:
        log(f"STDOUT:\n{proc.stdout}")
        log(f"STDERR:\n{proc.stderr}")
        raise RuntimeError("No result JSON returned by isolated clone test")

    log("Isolated Clone Test Results:")
    for k, v in result_json.items():
        if k != 'traceback':
            log(f"  {k}: {v}")

    if result_json.get('status') != 'ALL_PASS':
        if 'traceback' in result_json:
            log(f"Traceback:\n{result_json['traceback']}")
        raise RuntimeError(f"Isolated clone test failed: {result_json.get('error')}")

    # Run real headless browser UAT against clone port 8097
    log(f"Executing real headless browser UAT against isolated clone port {PORT}...")
    env = dict(os.environ)
    env['NODE_PATH'] = str(ROOT_DIR / 'frontend/premium/node_modules')
    browser_proc = subprocess.run(
        ['node', str(ROOT_DIR / 'infra/run_audit06_clone_browser_uat.cjs')],
        env=env,
        capture_output=True,
        text=True,
        timeout=120
    )
    if browser_proc.returncode != 0:
        log(f"Browser UAT failed (code {browser_proc.returncode}):\n{browser_proc.stderr}\n{browser_proc.stdout}")
        raise RuntimeError(f"Real clone browser UAT failed: {browser_proc.stderr}")
    log(f"Browser UAT completed successfully:\n{browser_proc.stdout}")

    evidence_dir = ROOT_DIR / 'docs/evidence/issue-177'
    required_shots = [
        'audit06-servizi-desktop.png',
        'audit06-servizi-mobile.png',
        'audit06-disponibilita-modal-desktop.png',
        'audit06-disponibilita-modal-mobile.png',
        'audit06-assenza-modal-desktop.png',
        'audit06-archivi-tariffe-desktop.png',
        'audit06-archivi-tariffe-mobile.png',
        'audit06-agenda-snapshot-desktop.png',
        'audit06-agenda-snapshot-mobile.png',
    ]
    for shot in required_shots:
        p = evidence_dir / shot
        assert p.exists() and p.stat().st_size > 1000, f"Screenshot missing or empty: {shot}"
        log(f"Verified real browser screenshot: {shot} ({p.stat().st_size} bytes)")
    result_json['browser_uat'] = 'PASS'

    return result_json


def main():
    try:
        setup_clone()
        res = run_real_clone_test()
        log("Real isolated clone verification: SUCCESS - ALL SCENARIOS PASS.")
    finally:
        cleanup()


if __name__ == '__main__':
    main()
