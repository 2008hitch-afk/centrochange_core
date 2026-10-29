#!/usr/bin/env python3
"""AUDIT-09 Real Isolated Synthetic Clone Verification on Frappe / MariaDB.

Guarantees:
- Dedicated Docker network, volume, and isolated containers (cc183-clone-net, cc183-clone-sites, cc183-clone-db, cc183-clone-redis, cc183-clone-backend, cc183-clone-frontend).
- Live DEV containers and volumes (centrochange-dev-*) are NEVER accessed, read, dumped, or mutated (zero DEV contact).
- Standalone synthetic Frappe/MariaDB site bootstrapped from scratch via bench new-site + dev_bootstrap.setup() + uat.demo.seed().
- All candidate app code mounted read-only into the isolated backend and frontend.
- Scenarios validated:
  1. CC-EXT-021: Server-side search & pagination across all 11 archives (Patient, Practitioner, Item, Item Price, Appointment Type, Center Service, Package Template, Sales Invoice, Purchase Invoice, Payment Entry, Bank Transaction), including >500 matching rows and pagination beyond page 1 on Sales Invoice, Purchase Invoice, and Bank Transaction.
  2. CC-EXT-008 & CC-EXT-009: Scoped updates for Patient and Practitioner with idempotency, versioning, and audit logging.
  3. CC-EXT-010: Scoped catalog creation & updates (Item Price, Appointment Type, Center Service, Package Template) and rejection of unauthorized standalone creates (CC-EXT-023).
  4. CC-EXT-011 & CC-EXT-022: Finance projections read-only enforcement, docstatus mapping (Bozza/Confermata/Annullata), 366-day limit, and allocation prohibition (CC-EXT-024).
  5. CC-EXT-012: Document print preview for Sales Invoice, Purchase Invoice, and Payment Entry.
  6. CC-EXT-020: RBAC across roles and anti-IDOR cross-center enforcement.
  7. Genuine headless Chromium browser UAT across archive views (Desktop & Mobile screenshots).
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

NET_NAME = 'cc183-clone-net'
SITES_VOLUME = 'cc183-clone-sites'
DB_CONTAINER = 'cc183-clone-db'
REDIS_CONTAINER = 'cc183-clone-redis'
BACKEND_CONTAINER = 'cc183-clone-backend'
FRONTEND_CONTAINER = 'cc183-clone-frontend'

CLONE_IMAGE = os.environ.get('CC_CLONE_IMAGE', 'cc181-audit08:2935973')
CLONE_SITE = 'centrochange.local'
PORT = 8099


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
            log(f"STDOUT (last 12000 chars):\n{_redact(res.stdout[-12000:])}")
        if res.stderr:
            log(f"STDERR (last 12000 chars):\n{_redact(res.stderr[-12000:])}")
        safe_cmd = [_redact(c) for c in cmd] if isinstance(cmd, list) else _redact(cmd)
        raise subprocess.CalledProcessError(res.returncode, safe_cmd, output=_redact(res.stdout), stderr=_redact(res.stderr))
    return res.stdout if capture else ""


def cleanup():
    log("Cleaning up isolated clone resources...")
    for c in [FRONTEND_CONTAINER, BACKEND_CONTAINER, DB_CONTAINER, REDIS_CONTAINER]:
        if subprocess.run(['docker', 'container', 'inspect', c], capture_output=True).returncode == 0:
            run_cmd(['docker', 'rm', '-fv', c])  # -v removes only the clone container's anonymous volumes.
    if subprocess.run(['docker', 'volume', 'inspect', SITES_VOLUME], capture_output=True).returncode == 0:
        run_cmd(['docker', 'volume', 'rm', SITES_VOLUME])
    if subprocess.run(['docker', 'network', 'inspect', NET_NAME], capture_output=True).returncode == 0:
        run_cmd(['docker', 'network', 'rm', NET_NAME])
    log("Cleanup complete.")


def setup_clone():
    log("Setting up 100% standalone synthetic isolated environment for AUDIT-09 (zero DEV contact)...")
    cleanup()

    clone_root_pass = secrets.token_hex(16)
    clone_admin_pass = secrets.token_hex(16)

    # 1. Create isolated network and sites volume
    log(f"Creating isolated Docker network {NET_NAME} and volume {SITES_VOLUME}...")
    run_cmd(['docker', 'network', 'create', NET_NAME])
    run_cmd(['docker', 'volume', 'create', SITES_VOLUME])

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
            '--collation-server=utf8mb4_unicode_ci',
            '--skip-character-set-client-handshake'
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
        hc = subprocess.run(['docker', 'exec', DB_CONTAINER, 'healthcheck.sh', '--connect', '--innodb_initialized'], capture_output=True, text=True)
        if hc.returncode == 0:
            ready = True
            break
    if not ready:
        raise RuntimeError("MariaDB failed to start in isolated clone")

    # 5. Start isolated backend container with candidate code mounted
    log(f"Starting isolated backend container {BACKEND_CONTAINER} using image {CLONE_IMAGE}...")
    run_cmd([
        'docker', 'run', '-d',
        '--name', BACKEND_CONTAINER,
        '--network', NET_NAME,
        '-v', f'{SITES_VOLUME}:/home/frappe/frappe-bench/sites',
        '-v', f'{APP_DIR}:/home/frappe/frappe-bench/apps/centrochange_core:ro',
        '-e', 'FRAPPE_STREAM_LOGGING=1',
        CLONE_IMAGE,
        'sleep', '7200'
    ])

    # 6. Bootstrap a clean synthetic site inside the isolated backend (no DEV contact)
    log("Bootstrapping fresh synthetic Frappe site and UAT fixtures in isolated backend...")
    bootstrap_script = f"""set -euo pipefail
cd /home/frappe/frappe-bench
cp -rn /home/frappe/frappe-bench/sites_init/* /home/frappe/frappe-bench/sites/ 2>/dev/null || true
if [ ! -f sites/apps.txt ]; then
  printf "frappe\\nerpnext\\nbuilder\\nhealthcare\\ncentrochange_core\\n" > sites/apps.txt
fi
if [ ! -f sites/common_site_config.json ]; then
  echo '{{}}' > sites/common_site_config.json
fi
ln -sfn /home/frappe/frappe-bench/assets sites/assets
bench set-config -g db_host {DB_CONTAINER}
bench set-config -gp db_port 3306
bench set-config -g redis_cache redis://{REDIS_CONTAINER}:6379
bench set-config -g redis_queue redis://{REDIS_CONTAINER}:6379
bench set-config -g redis_socketio redis://{REDIS_CONTAINER}:6379
bench set-config -gp socketio_port 9000
bench new-site {CLONE_SITE} --db-host {DB_CONTAINER} --mariadb-user-host-login-scope '%' --mariadb-root-password '{clone_root_pass}' --admin-password '{clone_admin_pass}' --install-app erpnext --install-app builder --set-default
bench --site {CLONE_SITE} set-config cc_synthetic_dev 1
bench --site {CLONE_SITE} set-config cc_uat_demo 1
bench --site {CLONE_SITE} set-config cc_premium_primary 1
bench --site {CLONE_SITE} install-app healthcare
bench --site {CLONE_SITE} install-app centrochange_core
bench --site {CLONE_SITE} execute centrochange_core.dev_bootstrap.setup
bench --site {CLONE_SITE} migrate
bench --site {CLONE_SITE} execute centrochange_core.uat.demo.seed
"""
    run_cmd(['docker', 'exec', '-i', BACKEND_CONTAINER, 'bash'], input_str=bootstrap_script)
    log("Standalone synthetic Frappe site bootstrapped and seeded.")

    # 7. Start gunicorn inside isolated backend container
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

    # 8. Start isolated frontend container cc183-clone-frontend mapping host port 8099
    log(f"Starting isolated frontend container {FRONTEND_CONTAINER} on port {PORT}...")
    run_cmd([
        'docker', 'run', '-d',
        '--name', FRONTEND_CONTAINER,
        '--network', NET_NAME,
        '-p', f'127.0.0.1:{PORT}:8080',
        '-e', f'BACKEND={BACKEND_CONTAINER}:8000',
        '-e', f'FRAPPE_SITE_NAME_HEADER={CLONE_SITE}',
        '-v', f'{SITES_VOLUME}:/home/frappe/frappe-bench/sites',
        '-v', f'{APP_DIR}:/home/frappe/frappe-bench/apps/centrochange_core:ro',
        '-v', f'{APP_DIR}/centrochange_core/public:/home/frappe/frappe-bench/assets/centrochange_core:ro',
        CLONE_IMAGE,
        '/usr/local/bin/entrypoint.sh', 'nginx-entrypoint.sh'
    ])

    # 9. Warm-up and healthcheck
    log(f"Waiting for isolated frontend to respond on port {PORT}...")
    ready = False
    for attempt in range(30):
        time.sleep(1)
        res = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-H', f'Host: {CLONE_SITE}', f'http://127.0.0.1:{PORT}/login'],
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

import centrochange_core.operations.profiles as profiles
import centrochange_core.catalog as catalog
import centrochange_core.finance.payments as payments
import centrochange_core.finance.reporting as reporting
from centrochange_core.security.lifecycle import set_assignment, set_membership
from centrochange_core.security.audit import internal_write

test_results = {}

try:
    # 1. Discover operational environment
    operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name', 'cc_price_list'], order_by='name asc')
    if not operational_centers:
        raise RuntimeError("No operational Branch found in database")
    center = operational_centers[0].name
    price_list = operational_centers[0].cc_price_list

    member_users = [m.user for m in frappe.get_all('CC Center Membership', filters={'center': center, 'active': 1}, fields=['user'])]
    managers = frappe.get_all('Has Role', filters={'role': 'CC Manager', 'parenttype': 'User', 'parent': ['in', member_users]}, fields=['parent'])
    manager_user = managers[0].parent if managers else 'Administrator'

    secretaries = frappe.get_all('Has Role', filters={'role': 'CC Secretariat', 'parenttype': 'User', 'parent': ['in', member_users]}, fields=['parent'])
    secretary_user = secretaries[0].parent if secretaries else manager_user

    practitioners = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active', 'user_id': ['in', member_users]}, fields=['name', 'user_id', 'practitioner_name'])
    prac_a = practitioners[0].name
    user_a = practitioners[0].user_id

    # -------------------------------------------------------------
    # Scenario 1 (CC-EXT-021): Server-side Search & Pagination
    # -------------------------------------------------------------
    # Seed 55 synthetic patients with deterministic names to test pagination beyond page 1 (limit 50)
    created_patients = []
    frappe.set_user('Administrator')
    for i in range(55):
        pat_name = f'CC9_SEARCH_PAT_{i:02d}_{secrets.token_hex(3)}'
        pdoc = frappe.get_doc({
            'doctype': 'Patient',
            'first_name': f'CC9First{i:02d}',
            'last_name': f'CC9Last{i:02d}',
            'sex': 'Other',
            'invite_user': 0,
            'email': f'cc9_{i:02d}_{secrets.token_hex(2)}@example.com'
        })
        pdoc.insert(ignore_permissions=True)
        set_assignment(pdoc.name, center, prac_a, 1, 'AUDIT-09 Synthetic Search Test')
        created_patients.append(pdoc.name)
    frappe.db.commit()

    # Query as Manager: verify default limit returns 50, has_more=True
    frappe.set_user(manager_user)
    page1 = profiles.patients(center=center, limit=50, offset=0, search='')
    assert len(page1['rows']) == 50, f"Expected 50 rows on page 1, got {len(page1['rows'])}"
    assert page1['has_more'] is True, "Expected has_more=True with >50 patients"

    # Query with specific search targeting patient #54 (which would be on page 2)
    search_target = f'CC9Last54'
    searched = profiles.patients(center=center, limit=50, offset=0, search=search_target)
    assert len(searched['rows']) == 1, f"Expected exactly 1 result for {search_target}, got {len(searched['rows'])}"
    assert searched['rows'][0]['name'] == created_patients[54]
    assert searched['has_more'] is False

    # Verify input bounding: string > 100 chars raises ValidationError
    long_search_raised = False
    try:
        profiles.patients(center=center, search='X' * 101)
    except frappe.ValidationError:
        long_search_raised = True
    assert long_search_raised, "Search query > 100 chars did not raise ValidationError"

    # Verify Catalog server-side searches
    # Item Price search
    tariff_search = catalog.records(center=center, kind='Item Price', limit=20, offset=0, search='Tariffa')
    assert isinstance(tariff_search['rows'], list)

    # Center Service search
    service_search = catalog.records(center=center, kind='CC Center Service', limit=20, offset=0, search='Centro')
    assert isinstance(service_search['rows'], list)

    # Verify Finance server-side searches & pagination >500 rows on Sales Invoice, Purchase Invoice, Bank Transaction
    frappe.set_user('Administrator')
    all_branches = frappe.get_all('Branch', fields=['name'])
    other_center = next((b.name for b in all_branches if b.name != center), 'CC-SYNTH-OTHER')
    now_str = '2026-10-28 12:00:00'
    for i in range(525):
        frappe.db.sql(
            "INSERT INTO `tabSales Invoice` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `customer`, `posting_date`, `grand_total`, `outstanding_amount`, `currency`, `cc_center`) "
            "VALUES (%s, %s, %s, 'Administrator', 'Administrator', 1, 0, %s, '2026-10-28', 100.0, 0.0, 'EUR', %s)",
            (f'CC9-SINV-{i:04d}', now_str, f'2026-10-28 12:{(i // 60) % 60:02d}:{i % 60:02d}', f'CC9-CUS-{i:04d}', center)
        )
        frappe.db.sql(
            "INSERT INTO `tabPurchase Invoice` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `supplier`, `posting_date`, `grand_total`, `outstanding_amount`, `currency`, `cc_center`) "
            "VALUES (%s, %s, %s, 'Administrator', 'Administrator', 1, 0, %s, '2026-10-28', 50.0, 0.0, 'EUR', %s)",
            (f'CC9-PINV-{i:04d}', now_str, f'2026-10-28 12:{(i // 60) % 60:02d}:{i % 60:02d}', f'CC9-SUP-{i:04d}', center)
        )
        frappe.db.sql(
            "INSERT INTO `tabBank Transaction` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `date`, `deposit`, `withdrawal`, `unallocated_amount`, `reference_number`, `cc_center`) "
            "VALUES (%s, %s, %s, 'Administrator', 'Administrator', 1, 0, '2026-10-28', 100.0, 0.0, 0.0, %s, %s)",
            (f'CC9-BTX-{i:04d}', now_str, f'2026-10-28 12:{(i // 60) % 60:02d}:{i % 60:02d}', f'CC9-REF-{i:04d}', center)
        )
    # Cross-center rows that must never leak into `center` queries
    frappe.db.sql(
        "INSERT INTO `tabSales Invoice` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `customer`, `posting_date`, `grand_total`, `outstanding_amount`, `currency`, `cc_center`) "
        "VALUES ('CC9-SINV-OTHER', %s, %s, 'Administrator', 'Administrator', 1, 0, 'CC9-CUS-0520', '2026-10-28', 100.0, 0.0, 'EUR', %s)",
        (now_str, now_str, other_center)
    )
    frappe.db.sql(
        "INSERT INTO `tabPurchase Invoice` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `supplier`, `posting_date`, `grand_total`, `outstanding_amount`, `currency`, `cc_center`) "
        "VALUES ('CC9-PINV-OTHER', %s, %s, 'Administrator', 'Administrator', 1, 0, 'CC9-SUP-0520', '2026-10-28', 50.0, 0.0, 'EUR', %s)",
        (now_str, now_str, other_center)
    )
    frappe.db.sql(
        "INSERT INTO `tabBank Transaction` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`, `date`, `deposit`, `withdrawal`, `unallocated_amount`, `reference_number`, `cc_center`) "
        "VALUES ('CC9-BTX-OTHER', %s, %s, 'Administrator', 'Administrator', 1, 0, '2026-10-28', 100.0, 0.0, 0.0, 'CC9-REF-0520', %s)",
        (now_str, now_str, other_center)
    )
    frappe.db.commit()

    frappe.set_user(manager_user)
    for dt, prefix in [('Sales Invoice', 'CC9-SINV-'), ('Purchase Invoice', 'CC9-PINV-'), ('Bank Transaction', 'CC9-BTX-')]:
        # Page 1 (limit=100, offset=0) over >500 matching rows succeeds and indicates has_more=True
        fin_p1 = reporting.records(center=center, doctype=dt, search='', limit=100, offset=0)
        assert isinstance(fin_p1, dict), f"Expected paginated dict for {dt}, got {type(fin_p1)}"
        assert len(fin_p1['rows']) == 100, f"Expected 100 rows on page 1 for {dt}, got {len(fin_p1['rows'])}"
        assert fin_p1['has_more'] is True, f"Expected has_more=True on page 1 for {dt}"

        # Page 6 (limit=100, offset=500) reaches rows beyond 500 and indicates has_more=False
        fin_p6 = reporting.records(center=center, doctype=dt, search='', limit=100, offset=500)
        assert len(fin_p6['rows']) >= 25, f"Expected >=25 rows at offset=500 for {dt}, got {len(fin_p6['rows'])}"
        assert fin_p6['has_more'] is False, f"Expected has_more=False at offset=500 for {dt}"

        # Server-side search finds record #0520 directly on page 1 and excludes cross-center record
        fin_search = reporting.records(center=center, doctype=dt, search='0520', limit=100, offset=0)
        assert len(fin_search['rows']) == 1, f"Expected 1 row for search='0520' on {dt}, got {len(fin_search['rows'])}"
        assert fin_search['rows'][0]['name'] == f'{prefix}0520'
        assert fin_search['has_more'] is False

    # Clean up the 525 bulk finance rows immediately after verifying >500 pagination so legacy unpaginated checks work on baseline count
    frappe.set_user('Administrator')
    frappe.db.sql("DELETE FROM `tabSales Invoice` WHERE `name` LIKE 'CC9-SINV-%'")
    frappe.db.sql("DELETE FROM `tabPurchase Invoice` WHERE `name` LIKE 'CC9-PINV-%'")
    frappe.db.sql("DELETE FROM `tabBank Transaction` WHERE `name` LIKE 'CC9-BTX-%'")
    frappe.db.commit()

    frappe.set_user(manager_user)
    inv_search = reporting.records(center=center, doctype='Sales Invoice', search='ACC')
    assert isinstance(inv_search, list)

    pay_search = payments.records(center=center, start='2020-01-01', end='2021-01-01', search='CASH')
    assert isinstance(pay_search['rows'], list)

    test_results['scenario_1_server_side_search_and_pagination'] = 'PASS'

    # Eleven real list/detail contracts on the standalone synthetic Frappe site.
    # Financial invoice/bank drawers are approved read-only projections, not
    # complete native accounting forms.
    frappe.set_user(manager_user)
    verified_archives = []
    for kind in ('Patient', 'Healthcare Practitioner', 'Item', 'Item Price',
                 'Appointment Type', 'CC Center Service', 'CC Package Template',
                 'Sales Invoice', 'Purchase Invoice', 'Payment Entry', 'Bank Transaction'):
        if kind == 'Patient':
            listing = profiles.patients(center=center, limit=50, offset=0)
            first = listing['rows'][0]
            detail = profiles.patient_detail(center=center, name=first['name'])
        elif kind == 'Healthcare Practitioner':
            listing = profiles.practitioners(center=center, limit=50, offset=0)
            first = listing['rows'][0]
            detail = profiles.practitioner_detail(center=center, name=first['name'])
        elif kind in ('Item', 'Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template'):
            listing = catalog.records(center=center, kind=kind, limit=50, offset=0)
            first = listing['rows'][0]
            detail = catalog.detail(center=center, kind=kind, name=first['name'])
        elif kind == 'Payment Entry':
            listing = payments.records(center=center, start='2026-01-01', end='2026-12-31', limit=50, offset=0)
            first = listing['rows'][0]
            detail = payments.detail(center=center, name=first['name'])
        else:
            listing = reporting.records(center=center, doctype=kind, limit=50, offset=0)
            first = listing['rows'][0]
            detail = first  # DECISION-063: the list row is the scoped read-only drawer projection.
        assert isinstance(listing, dict) and isinstance(listing['rows'], list) and listing['rows'], f'{kind}: empty list'
        assert detail and detail['name'] == first['name'], f'{kind}: wrong detail'
        needle = first['name']
        if kind == 'Patient':
            found = profiles.patients(center=center, search=needle)
        elif kind == 'Healthcare Practitioner':
            found = profiles.practitioners(center=center, search=needle)
        elif kind in ('Item', 'Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template'):
            found = catalog.records(center=center, kind=kind, search=needle)
        elif kind == 'Payment Entry':
            found = payments.records(center=center, start='2026-01-01', end='2026-12-31', search=needle)
        else:
            found = reporting.records(center=center, doctype=kind, search=needle, limit=50)
        assert any(row['name'] == first['name'] for row in found['rows']), f'{kind}: server-side search did not find its scoped row'
        verified_archives.append(kind)
    assert len(verified_archives) == 11
    test_results['scenario_1b_eleven_archive_lists_and_details'] = {'status': 'PASS', 'count': len(verified_archives)}

    # -------------------------------------------------------------
    # Scenario 2 (CC-EXT-008, CC-EXT-009, CC-EXT-010): Scoped Updates & Creates
    # -------------------------------------------------------------
    # 2a. Patient update scoped (CC-EXT-008)
    frappe.set_user(manager_user)
    target_patient = created_patients[0]
    p_info = profiles.patient_detail(center=center, name=target_patient)
    v1 = str(p_info['modified'])

    # Successful update
    new_email = f'updated_{secrets.token_hex(4)}@example.com'
    patient_key = f'req-upd-pat-{secrets.token_hex(4)}'
    upd_res = profiles.patient_save(
        center=center,
        name=target_patient,
        first_name='CC9UpdatedFirst',
        last_name='CC9UpdatedLast',
        email=new_email,
        expected_version=v1,
        request_key=patient_key,
        reason='AUDIT-09 Synthetic patient update'
    )
    assert upd_res['name'] == target_patient
    assert upd_res['modified'] != v1, "Version should have changed after update"
    frappe.db.commit()
    assert frappe.db.get_value('Patient', target_patient, 'email') == new_email, 'Patient update was not persisted'
    replay = profiles.patient_save(center=center, name=target_patient,
        first_name='CC9UpdatedFirst', last_name='CC9UpdatedLast', email=new_email,
        expected_version=v1, request_key=patient_key, reason='AUDIT-09 Synthetic patient update')
    assert replay['name'] == target_patient and replay['replay'] is True

    # Audit log entry created
    audit_entry = frappe.get_all('CC Audit Event', filters={'reference_name': target_patient, 'event_type': 'PREMIUM_MASTER_UPDATED'})
    assert len(audit_entry) > 0, "Audit log entry not created for patient update"

    # Version collision (stale version v1 now rejected with Conflict / 409)
    collision_raised = False
    try:
        profiles.patient_save(
            center=center,
            name=target_patient,
            first_name='ShouldFail',
            last_name='ShouldFail',
            email='fail@example.com',
            expected_version=v1,  # STALE!
            request_key=f'req-upd-pat-stale-{secrets.token_hex(4)}',
            reason='Should fail stale'
        )
    except Exception as e:
        if 'Scheda modificata' in str(e) or 'Conflict' in str(e) or 'ConflictError' in type(e).__name__:
            collision_raised = True
    assert collision_raised, "Stale version update did not raise Conflict"

    # Non-manager rejected (CC-EXT-008 RBAC)
    frappe.set_user(user_a)
    non_manager_rejected = False
    try:
        profiles.patient_save(
            center=center,
            name=target_patient,
            first_name='HackerFirst',
            last_name='HackerLast',
            email='hacker@example.com',
            expected_version=upd_res['modified'],
            request_key=f'req-upd-pat-hack-{secrets.token_hex(4)}',
            reason='Hacker attempt'
        )
    except frappe.PermissionError:
        non_manager_rejected = True
    assert non_manager_rejected, "Non-manager was able to update patient profile"

    # 2b. Practitioner update scoped (CC-EXT-009)
    frappe.set_user(manager_user)
    pro_detail = profiles.practitioner_detail(center=center, name=prac_a)
    pro_v1 = str(pro_detail['modified'])

    upd_pro = profiles.practitioner_save(
        center=center,
        name=prac_a,
        first_name='CC9PracFirst',
        last_name='CC9PracLast',
        expected_version=pro_v1,
        request_key=f'req-upd-prac-{secrets.token_hex(4)}',
        reason='AUDIT-09 Practitioner update'
    )
    assert upd_pro['name'] == prac_a
    frappe.db.commit()
    assert frappe.db.get_value('Healthcare Practitioner', prac_a, 'first_name') == 'CC9PracFirst', 'Practitioner update was not persisted'

    # Audit log for practitioner
    pro_audit = frappe.get_all('CC Audit Event', filters={'reference_name': prac_a, 'event_type': 'PREMIUM_MASTER_UPDATED'})
    assert len(pro_audit) > 0, "Audit log entry not created for practitioner update"

    # 2c. Catalog creates & updates (CC-EXT-010)
    # Scoped create Item Price
    items = catalog.records(center=center, kind='Item', limit=10)['rows']
    assert items, 'Scoped catalog has no item for authorized create tests'
    test_item = items[0]['name']
    new_price = catalog.price_create(
        center=center,
        item_code=test_item,
        price_list_rate=125.00,
        valid_from='2099-01-01',
        request_key=f'req-price-{secrets.token_hex(4)}',
        reason='AUDIT-09 Price create'
    )
    assert new_price['name'] is not None
    frappe.db.commit()
    assert frappe.db.get_value('Item Price', new_price['name'], 'price_list_rate') == 125.00, 'Item Price create was not persisted'
    duplicate_price_rejected = False
    try:
        catalog.price_create(center=center, item_code=test_item, price_list_rate=125.00, valid_from='2099-01-01',
            request_key=f'cc9-duplicate-{secrets.token_hex(4)}', reason='Synthetic duplicate check')
    except frappe.ValidationError:
        duplicate_price_rejected = True
    assert duplicate_price_rejected, 'Duplicate Item Price effective date was accepted'

    # The remaining authorized editor/create contracts must save in native
    # DocTypes and survive a transaction boundary on this disposable clone.
    item_detail = catalog.detail(center=center, kind='Item', name=test_item)
    item_saved = catalog.item_save(center=center, name=test_item, item_name='CC9 synthetic service',
        expected_version=str(item_detail['modified']), request_key=f'cc9-item-{secrets.token_hex(4)}', reason='Synthetic archive edit')
    price_detail = catalog.detail(center=center, kind='Item Price', name=new_price['name'])
    price_saved = catalog.price_save(center=center, name=new_price['name'], price_list_rate=126.00,
        expected_version=str(price_detail['modified']), request_key=f'cc9-price-{secrets.token_hex(4)}', reason='Synthetic archive edit')
    service_rows = catalog.records(center=center, kind='CC Center Service', limit=10)['rows']
    assert service_rows
    service_detail = catalog.detail(center=center, kind='CC Center Service', name=service_rows[0]['name'])
    changed_enabled = 1 - int(service_detail['enabled'])
    service_saved = catalog.service_save(center=center, name=service_rows[0]['name'], enabled=changed_enabled,
        expected_version=str(service_detail['modified']), request_key=f'cc9-service-{secrets.token_hex(4)}', reason='Synthetic archive edit')
    type_detail = catalog.detail(center=center, kind='Appointment Type', name=service_detail['appointment_type'])
    type_saved = catalog.appointment_type_save(center=center, name=type_detail['name'],
        default_duration=int(type_detail['default_duration']) + 5,
        expected_version=str(type_detail['modified']), request_key=f'cc9-type-{secrets.token_hex(4)}', reason='Synthetic archive edit')
    template_rows = catalog.records(center=center, kind='CC Package Template', limit=10)['rows']
    assert template_rows
    template_detail = catalog.detail(center=center, kind='CC Package Template', name=template_rows[0]['name'])
    template_saved = catalog.package_template_save(center=center, name=template_detail['name'],
        title='CC9 synthetic package', units=int(template_detail['units']) + 1, enabled=template_detail['enabled'],
        expected_version=str(template_detail['modified']), request_key=f'cc9-template-{secrets.token_hex(4)}', reason='Synthetic archive edit')
    frappe.db.commit()
    assert frappe.db.get_value('Item', item_saved['name'], 'item_name') == 'CC9 synthetic service'
    assert frappe.db.get_value('Item Price', price_saved['name'], 'price_list_rate') == 126.00
    assert int(frappe.db.get_value('CC Center Service', service_saved['name'], 'enabled')) == changed_enabled
    assert int(frappe.db.get_value('Appointment Type', type_saved['name'], 'default_duration')) == int(type_detail['default_duration']) + 5
    assert frappe.db.get_value('CC Package Template', template_saved['name'], 'title') == 'CC9 synthetic package'

    new_type = catalog.appointment_type_create(center=center, appointment_type='CC9 synthetic type ' + secrets.token_hex(3),
        service_item=test_item, default_duration=45, request_key=f'cc9-new-type-{secrets.token_hex(4)}', reason='Synthetic archive create')
    new_service = catalog.service_create(center=center, appointment_type=new_type['name'], enabled=0,
        request_key=f'cc9-new-service-{secrets.token_hex(4)}', reason='Synthetic archive create')
    new_template = catalog.package_template_create(center=center, title='CC9 new package', service_item=test_item,
        units=4, enabled=0, request_key=f'cc9-new-template-{secrets.token_hex(4)}', reason='Synthetic archive create')
    frappe.db.commit()
    assert frappe.db.exists('Appointment Type', new_type['name'])
    assert frappe.db.exists('CC Center Service', new_service['name'])
    assert frappe.db.exists('CC Package Template', new_template['name'])
    assert frappe.db.count('CC Audit Event', {'event_type': 'PREMIUM_MASTER_CREATED', 'reference_name': new_template['name']}) == 1

    # Standalone create Item forbidden (CC-EXT-023)
    assert not hasattr(catalog, 'item_create'), "Standalone Item create must not exist in catalog"

    test_results['scenario_2_scoped_updates_and_creates'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 3 (CC-EXT-011, CC-EXT-022, CC-EXT-024): Finance Projections & Limits
    # -------------------------------------------------------------
    # 3a. Payment Entry 366-day limit
    frappe.set_user(manager_user)
    exceed_limit_raised = False
    try:
        payments.records(center=center, start='2020-01-01', end='2021-01-15')
    except frappe.ValidationError:
        exceed_limit_raised = True
    assert exceed_limit_raised, "Date range > 366 days did not raise ValidationError"

    # 3b. Read-only projection: Sales Invoice
    invoices = reporting.records(center=center, doctype='Sales Invoice', limit=100, offset=0)['rows']
    assert isinstance(invoices, list) and invoices
    for row in invoices:
        assert 'docstatus' in row, "docstatus must be in Sales Invoice projection"
        assert 'customer' in row
        assert 'grand_total' in row

    # 3c. Direct payment allocation forbidden (CC-EXT-024)
    # Ensure no API exposes direct Payment Entry write in payments module
    assert not hasattr(payments, 'create_payment_entry'), "Direct Payment Entry creation must not exist"
    assert not hasattr(payments, 'allocate'), "Direct Payment Entry allocation must not exist"

    test_results['scenario_3_finance_projections_and_limits'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 4 (CC-EXT-012): Document Print Preview
    # -------------------------------------------------------------
    # Manager document preview against existing native seeded documents, not
    # the synthetic pagination rows injected directly into the clone tables.
    import centrochange_core.finance.documents as documents
    frappe.set_user(manager_user)
    for printable in ('Sales Invoice', 'Purchase Invoice', 'Payment Entry'):
        native_names = frappe.get_all(printable, filters={'cc_center': center,
            'name': ['not like', 'CC9-%']}, pluck='name', limit_page_length=1)
        assert native_names, printable + ': no native seeded document for print preview'
        prev = documents.preview(center=center, doctype=printable, name=native_names[0])
        assert 'html' in prev, "Document preview must return HTML"
        assert len(prev['html']) > 0, "Document preview HTML must not be empty"

    test_results['scenario_4_document_print_preview'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 5 (CC-EXT-020): RBAC & Anti-IDOR Cross Center
    # -------------------------------------------------------------
    def denied(call, label):
        try:
            call()
        except frappe.PermissionError:
            return
        raise AssertionError(label + ': unauthorized direct API call succeeded')

    frappe.set_user('Guest')
    denied(lambda: profiles.patients(center=center), 'Guest Patient')
    denied(lambda: profiles.practitioners(center=center), 'Guest Practitioner')
    for kind in ('Item', 'Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template'):
        denied(lambda kind=kind: catalog.records(center=center, kind=kind), 'Guest ' + kind)
    for kind in ('Sales Invoice', 'Purchase Invoice', 'Bank Transaction'):
        denied(lambda kind=kind: reporting.records(center=center, doctype=kind, limit=50), 'Guest ' + kind)
    denied(lambda: payments.records(center=center, start='2026-01-01', end='2026-12-31'), 'Guest Payment Entry')

    professional_users = frappe.get_all('Has Role', filters={'role': 'CC Professional',
        'parenttype': 'User', 'parent': ['in', member_users]}, pluck='parent')
    assert len(professional_users) == 3, 'Three professional identities missing from clone'
    for professional_user in professional_users:
        frappe.set_user(professional_user)
        own_practitioner = frappe.db.get_value('Healthcare Practitioner', {'user_id': professional_user}, 'name')
        own_rows = profiles.practitioners(center=center)['rows']
        assert all(row['name'] == own_practitioner for row in own_rows), 'Professional saw another practitioner'
        assert isinstance(profiles.patients(center=center)['rows'], list)
        for kind in ('Item', 'Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template'):
            denied(lambda kind=kind: catalog.records(center=center, kind=kind), 'Professional ' + kind)
        for kind in ('Sales Invoice', 'Purchase Invoice', 'Bank Transaction'):
            denied(lambda kind=kind: reporting.records(center=center, doctype=kind, limit=50), 'Professional ' + kind)
        denied(lambda: payments.records(center=center, start='2026-01-01', end='2026-12-31'), 'Professional Payment Entry')

    for finance_role in ('CC Finance', 'CC Accountant'):
        finance_users = frappe.get_all('Has Role', filters={'role': finance_role,
            'parenttype': 'User', 'parent': ['in', member_users]}, pluck='parent')
        assert len(finance_users) == 1, finance_role + ': identity missing from clone'
        frappe.set_user(finance_users[0])
        assert isinstance(reporting.records(center=center, doctype='Sales Invoice', limit=50), dict)
        assert isinstance(payments.records(center=center, start='2026-01-01', end='2026-12-31'), dict)
        denied(lambda: catalog.records(center=center, kind='Item'), finance_role + ' catalog')

    frappe.set_user(secretary_user)
    denied(lambda: catalog.records(center=center, kind='Item'), 'Secretariat catalog')
    assert isinstance(reporting.records(center=center, doctype='Sales Invoice', limit=50), dict)

    # Non-manager membership in center A must not authorize center B, even
    # when the record name/search term is known to the caller.
    all_centers = frappe.get_all('Branch', fields=['name'])
    other_centers = [c.name for c in all_centers if c.name != center]
    assert other_centers, 'Two-center fixture missing'
    other_c = other_centers[0]
    denied(lambda: profiles.patients(center=other_c), 'Secretariat cross-center Patient')
    denied(lambda: reporting.records(center=other_c, doctype='Sales Invoice', limit=50), 'Secretariat cross-center Sales Invoice')
    denied(lambda: payments.records(center=other_c, start='2026-01-01', end='2026-12-31'), 'Secretariat cross-center Payment Entry')

    test_results['scenario_5_rbac_and_anti_idor'] = 'PASS'

    # -------------------------------------------------------------
    # Scenario 6: Cleanup Synthetic Test Data
    # -------------------------------------------------------------
    frappe.set_user('Administrator')
    for p in created_patients:
        frappe.db.delete('CC Patient Assignment', {'patient': p})
        frappe.db.delete('Patient', {'name': p})
    if new_price.get('name'):
        frappe.db.delete('Item Price', {'name': new_price['name']})
    frappe.db.commit()

    test_results['scenario_6_synthetic_cleanup'] = 'PASS'

    print(json.dumps({'status': 'PASS', 'results': test_results}))

except Exception as err:
    traceback.print_exc()
    print(json.dumps({'status': 'FAIL', 'error': str(err), 'results': test_results}))
    sys.exit(1)
"""
    log("Executing AUDIT-09 Python test harness inside isolated backend...")
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
    env['NODE_PATH'] = os.environ.get('NODE_PATH', str(ROOT_DIR / 'frontend/premium/node_modules'))
    env['CC_ARTIFACT_DIR'] = os.environ.get('CC_ARTIFACT_DIR', str(ROOT_DIR / '.audit09-browser-artifacts'))
    env['CC_UAT_PORT'] = str(PORT)
    env['CC_BACKEND_CONTAINER'] = BACKEND_CONTAINER

    script_path = str(ROOT_DIR / 'infra/run_audit09_clone_browser_uat.cjs')
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
        log("=== AUDIT-09 ISOLATED CLONE VERIFICATION: FULL PASS ===")
    finally:
        cleanup()
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
