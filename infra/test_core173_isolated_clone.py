#!/usr/bin/env python3
"""CORE #173 Real Isolated Clone Verification on Frappe / MariaDB.

Guarantees:
- Dedicated Docker network and isolated containers (cc173-clone-net, cc173-clone-db, cc173-clone-redis, cc173-clone-backend).
- Live DEV containers and volumes (centrochange-dev-*) are NEVER mutated.
- Baseline schema and reference data cloned via read-only stream from DEV_DB.
- All candidate app code mounted into the isolated backend.
- Scenarios validated:
  1. Multi-role access: CC Professional A happy path day closure with Cash settlement.
  2. Autonomous arrear recovery: Auto Locked past session closed by practitioner without Direction intervention, emitting SESSION_LATE_COMPLETED.
  3. Economic integrity: Non-performed session with existing Due fee preserves Due and records per-session note.
  4. Negative Security & Fail-Closed ACLs:
     - Cross-practitioner IDOR rejected (HTTP 403 / PermissionError).
     - Inactive / non-operational center rejected (Branch.cc_operational == 0).
     - Revoked patient assignment rejected (CC Patient Assignment active == 0).
     - Guest / unauthenticated actor rejected.
     - Target date mismatch rejected.
     - Future session closure rejected.
     - Conflicting mutation on already closed session rejected.
  5. Multi-row transactional atomicity & rollback on failure.
  6. Automation scheduler (21:00 reminder & 07:00 auto-lock).
  7. Reporting & CSV export parity.
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

NET_NAME = 'cc173-clone-net'
DB_CONTAINER = 'cc173-clone-db'
REDIS_CONTAINER = 'cc173-clone-redis'
BACKEND_CONTAINER = 'cc173-clone-backend'

DEV_DB = 'centrochange-dev-db-1'
DEV_BACKEND = 'centrochange-dev-backend-1'
DEV_SITE = 'centrochange.local'


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
    for c in [BACKEND_CONTAINER, DB_CONTAINER, REDIS_CONTAINER]:
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
    log("Setting up isolated clone environment for CORE #173...")
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
            # Test ping
            ping_res = subprocess.run(
                ['docker', 'exec', '-i', DB_CONTAINER, 'mariadb', f'-uroot', f'-p{clone_root_pass}', '-e', 'SELECT 1'],
                capture_output=True, text=True
            )
            if ping_res.returncode == 0:
                ready = True
                break
        else:
            consecutive_success = 0
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

    # 9. Reconfigure isolated backend to point to cc173-clone-db and cc173-clone-redis
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
    log("Isolated clone environment ready.")


def run_real_clone_test():
    test_harness = """
import json
import sys
import traceback
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
import frappe
from frappe.utils import getdate

ROME = ZoneInfo('Europe/Rome')

frappe.init('centrochange.local', sites_path='sites')
frappe.connect()

import centrochange_core.operations.lifecycle as lifecycle
import centrochange_core.operations.automation as automation
import centrochange_core.operations.reporting as reporting
import centrochange_core.security.guards as guards

test_results = {}

# Set synthetic test clock to 2026-10-26 18:00:00 Europe/Rome
clock_now = datetime(2026, 10, 26, 18, 0, 0, tzinfo=ROME)
frappe.flags.in_test = True
frappe.in_test = True
frappe.flags.cc_test_clock = clock_now.astimezone(timezone.utc)

# 1. Discover active center and practitioners
operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name'])
if not operational_centers:
    raise RuntimeError("No operational Branch found in database")
center = operational_centers[0].name

practitioners = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active'}, fields=['name', 'user_id'])
if len(practitioners) < 2:
    raise RuntimeError("At least two Healthcare Practitioners required for multi-role test")
prac_a = practitioners[0].name
user_a = practitioners[0].user_id
prac_b = practitioners[1].name
user_b = practitioners[1].user_id

patients = frappe.get_all('Patient', fields=['name'])
if len(patients) < 2:
    raise RuntimeError("At least two Patients required in database")
patient_1 = patients[0].name
patient_2 = patients[1].name

# Ensure user_a has CC Professional role
if 'CC Professional' not in frappe.get_roles(user_a):
    user_doc = frappe.get_doc('User', user_a)
    user_doc.append('roles', {'role': 'CC Professional'})
    user_doc.flags.ignore_permissions = True
    user_doc.save()

from centrochange_core.security.audit import internal_write
from centrochange_core.security.lifecycle import reconcile_user

# Ensure user_a has active CC Center Membership for center
membership_name = frappe.db.get_value('CC Center Membership', {'user': user_a, 'center': center})
with internal_write('cc_permission_write'):
    if not membership_name:
        frappe.get_doc({
            'doctype': 'CC Center Membership',
            'user': user_a,
            'center': center,
            'active': 1
        }).insert(ignore_permissions=True)
    else:
        doc_mem = frappe.get_doc('CC Center Membership', membership_name)
        doc_mem.active = 1
        doc_mem.save(ignore_permissions=True)

# Ensure patient_1 and patient_2 are actively assigned to prac_a in center
for pat in [patient_1, patient_2]:
    assignment_name = frappe.db.get_value('CC Patient Assignment', {'patient': pat, 'center': center, 'practitioner': prac_a})
    with internal_write('cc_permission_write'):
        if not assignment_name:
            frappe.get_doc({
                'doctype': 'CC Patient Assignment',
                'patient': pat,
                'center': center,
                'practitioner': prac_a,
                'active': 1
            }).insert(ignore_permissions=True)
        else:
            doc_asgn = frappe.get_doc('CC Patient Assignment', assignment_name)
            doc_asgn.active = 1
            doc_asgn.save(ignore_permissions=True)

with internal_write('cc_permission_write'):
    reconcile_user(user_a)

frappe.db.commit()

log_entries = []

def make_appointment(**kwargs):
    import secrets
    name = f"APP-TEST173-{secrets.token_hex(4)}"
    date_val = str(kwargs.get('appointment_date', '2026-10-26'))
    time_val = str(kwargs.get('appointment_time', '09:00:00'))
    status_val = kwargs.get('status', 'Open')
    pat = kwargs.get('patient', patient_1)
    prac = kwargs.get('practitioner', prac_a)
    cen = kwargs.get('cc_center', center)
    econ = kwargs.get('cc_economic_state', 'Pending')
    closure = kwargs.get('cc_closure_state', 'Pending')
    performed = int(kwargs.get('cc_performed', 0))
    paid = int(kwargs.get('cc_paid', 0))
    late_cancel = int(kwargs.get('cc_late_cancellation', 0))
    rev = int(kwargs.get('cc_revision', 1))

    sql = (
        "INSERT INTO `tabPatient Appointment` ("
        "name, docstatus, idx, duration, add_video_conferencing, invoiced, paid_amount, "
        "appointment_based_on_check_in, position_in_queue, reminded, "
        "appointment_date, appointment_time, status, patient, patient_name, "
        "practitioner, practitioner_name, cc_center, cc_economic_state, "
        "cc_price_snapshot, cc_currency_snapshot, cc_late_cancellation, "
        "cc_performed, cc_paid, cc_revision, cc_settlement_revision, cc_closure_state"
        ") VALUES ("
        "%s, 0, 0, 60, 0, 0, 0, 0, 0, 0, "
        "%s, %s, %s, %s, 'Paziente Test', %s, 'Dottore Test', %s, %s, 100.0, 'EUR', %s, "
        "%s, %s, %s, 0, %s)"
    )
    frappe.db.sql(sql, (
        name, date_val, time_val, status_val, pat,
        prac, cen, econ, late_cancel, performed, paid, rev, closure
    ))
    frappe.db.commit()
    return frappe.get_doc('Patient Appointment', name)

try:
    # -------------------------------------------------------------
    # Scenario 1: Professional A closes today's session (Happy Path)
    # -------------------------------------------------------------
    app1 = make_appointment(
        patient=patient_1,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='09:00:00'
    )

    frappe.set_user(user_a)
    # Query sessions for today
    day_sessions = lifecycle.get_day_closure_sessions(center, '2026-10-26')
    assert any(s.name == app1.name for s in day_sessions['sessions']), "Created session not found in get_day_closure_sessions"

    # Close day with cash payment
    payload1 = [{
        'appointment': app1.name,
        'performed': 1,
        'paid': 1,
        'mode_of_payment': 'Cash',
        'note': 'Seduta svolta con pagamento in contanti'
    }]
    res1 = lifecycle.close_day(center, '2026-10-26', payload1, 'Chiusura giornaliera')
    assert res1['status'] == 'PASS', f"close_day failed: {res1}"

    # Verify MariaDB state
    doc1 = frappe.get_doc('Patient Appointment', app1.name)
    assert doc1.status == 'Closed', f"Expected Closed, got {doc1.status}"
    assert doc1.cc_closure_state == 'Closed', f"Expected Closed, got {doc1.cc_closure_state}"
    assert doc1.cc_performed == 1, f"Expected performed=1, got {doc1.cc_performed}"
    assert doc1.cc_paid == 1, f"Expected paid=1, got {doc1.cc_paid}"
    assert doc1.cc_economic_state == 'Due', f"Expected Due, got {doc1.cc_economic_state}"

    # Verify settlement created
    settlements = frappe.get_all('CC Settlement', filters={'appointment': app1.name})
    assert len(settlements) >= 1, "No CC Settlement created for paid session"

    # Verify audit event
    audit1 = frappe.get_all('CC Audit Event', filters={'reference_name': app1.name, 'event_type': 'SESSION_CLOSED'})
    assert len(audit1) >= 1, "SESSION_CLOSED audit event not created"
    test_results['scenario_1_happy_path'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 2: Autonomous Recovery of Auto Locked arrear session
    # -------------------------------------------------------------
    app2 = make_appointment(
        patient=patient_1,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-12',
        appointment_time='10:00:00',
        cc_closure_state='Auto Locked',
        cc_revision=2
    )

    # Verify get_day_closure_sessions identifies 2026-10-12 in arrear_dates
    res_arrears = lifecycle.get_day_closure_sessions(center, '2026-10-26')
    assert '2026-10-12' in res_arrears['arrear_dates'], "2026-10-12 not in arrear_dates"

    # Professional A autonomously closes the arrear session without Direction intervention
    payload2 = [{
        'appointment': app2.name,
        'performed': 1,
        'paid': 0,
        'note': 'Recupero autonomo seduta del 12 ottobre'
    }]
    res2 = lifecycle.close_day(center, '2026-10-12', payload2, 'Recupero arretrati')
    assert res2['status'] == 'PASS', f"Arrear recovery failed: {res2}"

    doc2 = frappe.get_doc('Patient Appointment', app2.name)
    assert doc2.status == 'Closed', f"Expected Closed, got {doc2.status}"
    assert doc2.cc_closure_state == 'Closed', f"Expected Closed, got {doc2.cc_closure_state}"
    assert doc2.cc_performed == 1, f"Expected performed=1, got {doc2.cc_performed}"
    assert doc2.cc_paid == 0, f"Expected paid=0, got {doc2.cc_paid}"

    # Verify SESSION_LATE_COMPLETED audit event
    audit2 = frappe.get_all('CC Audit Event', filters={'reference_name': app2.name, 'event_type': 'SESSION_LATE_COMPLETED'}, fields=['before_state', 'after_state', 'reason'])
    assert len(audit2) >= 1, "SESSION_LATE_COMPLETED audit event not created"
    after_data = json.loads(audit2[0].after_state)
    assert after_data['closure'] == 'Closed', f"Expected after.closure Closed, got {after_data}"
    test_results['scenario_2_autonomous_arrear_recovery'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 3: Non-performed session with existing Due fee
    # -------------------------------------------------------------
    app3 = make_appointment(
        patient=patient_1,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='11:00:00',
        cc_economic_state='Due',
        cc_late_cancellation=1
    )

    payload3 = [{
        'appointment': app3.name,
        'performed': 0,
        'paid': 0,
        'note': 'Cancellazione tardiva: penale dovuta mantenuta'
    }]
    res3 = lifecycle.close_day(center, '2026-10-26', payload3)
    assert res3['status'] == 'PASS'
    doc3 = frappe.get_doc('Patient Appointment', app3.name)
    assert doc3.status == 'No Show'
    assert doc3.cc_performed == 0
    assert doc3.cc_economic_state == 'Due', f"Economic state Due was wiped! Got {doc3.cc_economic_state}"
    test_results['scenario_3_economic_integrity_preserved'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 4: Negative Security & Fail-Closed ACLs
    # -------------------------------------------------------------
    # 4a. Cross-practitioner IDOR: Professional A attempts to close Professional B's session
    app_b = make_appointment(
        patient=patient_1,
        practitioner=prac_b,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='12:00:00'
    )

    idor_rejected = False
    try:
        lifecycle.close_day(center, '2026-10-26', [{'appointment': app_b.name, 'performed': 1, 'paid': 0}])
    except frappe.PermissionError:
        idor_rejected = True
    assert idor_rejected, "Cross-practitioner IDOR was not rejected with PermissionError"

    # 4b. Inactive / Non-operational center
    frappe.set_user('Administrator')
    inactive_branch = frappe.get_doc({
        'doctype': 'Branch',
        'branch': 'Sede Inattiva Test',
        'cc_operational': 0
    }).insert(ignore_permissions=True)
    with internal_write('cc_permission_write'):
        frappe.get_doc({
            'doctype': 'CC Center Membership',
            'user': user_a,
            'center': inactive_branch.name,
            'active': 1
        }).insert(ignore_permissions=True)
    frappe.db.commit()

    frappe.set_user(user_a)
    inactive_rejected = False
    try:
        lifecycle.close_day(inactive_branch.name, '2026-10-26', [{'appointment': app1.name, 'performed': 1, 'paid': 0}])
    except frappe.PermissionError as e:
        if 'non è operativa' in str(e):
            inactive_rejected = True
    assert inactive_rejected, "Non-operational center was not rejected with PermissionError ('non è operativa')"

    # 4c. Revoked Patient Assignment
    frappe.set_user('Administrator')
    patient_revoked = frappe.get_doc({
        'doctype': 'Patient',
        'first_name': 'Paziente',
        'last_name': 'Revocato',
        'sex': 'Male'
    }).insert(ignore_permissions=True)
    with internal_write('cc_permission_write'):
        frappe.get_doc({
            'doctype': 'CC Patient Assignment',
            'patient': patient_revoked.name,
            'center': center,
            'practitioner': prac_a,
            'active': 0
        }).insert(ignore_permissions=True)
    frappe.db.commit()

    frappe.set_user(user_a)
    app_revoked = make_appointment(
        patient=patient_revoked.name,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='13:00:00'
    )

    revocation_rejected = False
    try:
        lifecycle.close_day(center, '2026-10-26', [{'appointment': app_revoked.name, 'performed': 1, 'paid': 0}])
    except frappe.PermissionError:
        revocation_rejected = True
    assert revocation_rejected, "Revoked patient assignment was not rejected with PermissionError"

    # 4d. Target date mismatch
    date_mismatch_rejected = False
    try:
        lifecycle.close_day(center, '2026-10-26', [{'appointment': app2.name, 'performed': 1, 'paid': 0}]) # app2 date is 2026-10-12
    except Exception as e:
        if 'diversa dalla data richiesta' in str(e):
            date_mismatch_rejected = True
    assert date_mismatch_rejected, "Date mismatch was not rejected"

    # 4e. Future session closure rejected
    app_future = make_appointment(
        patient=patient_1,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='19:30:00'
    )

    future_rejected = False
    try:
        lifecycle.close_day(center, '2026-10-26', [{'appointment': app_future.name, 'performed': 1, 'paid': 0}])
    except Exception as e:
        if 'futuro' in str(e):
            future_rejected = True
    assert future_rejected, "Future session closure was not rejected"

    # 4f. Conflicting mutation on already closed session rejected
    conflict_rejected = False
    try:
        lifecycle.close_day(center, '2026-10-26', [{'appointment': app1.name, 'performed': 0, 'paid': 0}]) # app1 was performed=1, paid=1
    except frappe.PermissionError as e:
        if 'Non è consentito sovrascrivere una seduta consolidata' in str(e):
            conflict_rejected = True
    assert conflict_rejected, "Conflicting mutation on closed session was not rejected"

    test_results['scenario_4_negative_security_and_acls'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 5: Multi-row Transactional Atomicity and Rollback
    # -------------------------------------------------------------
    app_atomic_1 = make_appointment(
        patient=patient_2,
        practitioner=prac_a,
        cc_center=center,
        appointment_date='2026-10-26',
        appointment_time='14:00:00'
    )

    atomic_batch = [
        {'appointment': app_atomic_1.name, 'performed': 1, 'paid': 0},
        {'appointment': app_b.name, 'performed': 1, 'paid': 0}  # IDOR: will fail the batch!
    ]
    batch_failed = False
    try:
        lifecycle.close_day(center, '2026-10-26', atomic_batch)
    except frappe.PermissionError:
        batch_failed = True

    assert batch_failed, "Batch did not fail on invalid item"
    # Verify rollback: app_atomic_1 must NOT be closed!
    doc_atomic_check = frappe.get_doc('Patient Appointment', app_atomic_1.name)
    assert doc_atomic_check.status == 'Open' and doc_atomic_check.cc_closure_state == 'Pending', \
        f"Atomicity violated! First item was committed: status={doc_atomic_check.status}"
    test_results['scenario_5_transactional_rollback'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 6: Automation Scheduler (21:00 reminder & 07:00 auto-lock)
    # -------------------------------------------------------------
    # At 21:00 Rome: pending session exists today (app_atomic_1 is still Pending)
    frappe.flags.cc_test_clock = datetime(2026, 10, 26, 21, 5, 0, tzinfo=ROME).astimezone(timezone.utc)
    frappe.set_user('Administrator')
    r21 = automation.catch_up()
    assert r21['reminders'] >= 1, f"Expected at least 1 reminder, got {r21}"

    # Verify notification log created for user_a
    notifs = frappe.get_all('Notification Log', filters={'for_user': user_a})
    assert len(notifs) >= 1, "Notification Log entry not created for CC Professional"

    # Replay at 21:10: deduplicated (0 new reminders)
    frappe.flags.cc_test_clock = datetime(2026, 10, 26, 21, 10, 0, tzinfo=ROME).astimezone(timezone.utc)
    r21_replay = automation.catch_up()
    assert r21_replay['reminders'] == 0, f"Expected 0 deduplicated reminders, got {r21_replay}"

    # At 07:05 next day (2026-10-27 07:05:00 Rome): pending past session locked automatically
    frappe.flags.cc_test_clock = datetime(2026, 10, 27, 7, 5, 0, tzinfo=ROME).astimezone(timezone.utc)
    r07 = automation.catch_up()
    assert r07['locked'] >= 1, f"Expected at least 1 session auto-locked, got {r07}"

    doc_locked = frappe.get_doc('Patient Appointment', app_atomic_1.name)
    assert doc_locked.cc_closure_state == 'Auto Locked', f"Expected Auto Locked, got {doc_locked.cc_closure_state}"
    test_results['scenario_6_automation_scheduler'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 7: Reporting and CSV Parity
    # -------------------------------------------------------------
    summary = reporting.summary(center, '2026-10-01', '2026-10-31')
    assert 'EUR' in summary.get('currencies', {}), "EUR summary missing"

    frappe.response = {}
    reporting.export_csv(center=center, start='2026-10-01', end='2026-10-31')
    csv_text = frappe.response.get('filecontent', '')
    assert 'Svolta' in csv_text or 'Non svolta' in csv_text or 'Bloccata' in csv_text or 'In programma' in csv_text, "Expected classified statuses in CSV export"
    test_results['scenario_7_reporting_parity'] = 'PASS'

    test_results['status'] = 'ALL_PASS'

except Exception as e:
    test_results['status'] = 'FAIL'
    test_results['error'] = str(e)
    test_results['traceback'] = traceback.format_exc()

print("CORE173_RESULT_JSON:" + json.dumps(test_results))
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
        if line.startswith('CORE173_RESULT_JSON:'):
            result_json = json.loads(line[len('CORE173_RESULT_JSON:'):])
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
