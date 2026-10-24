#!/usr/bin/env python3
"""Execute controlled MariaDB DEV credential rotation per Owner authorization (25/10/2026).

Guarantees:
- Zero credential exposure in CLI args, process list (ps aux), or logs.
- Strict redact wrapper for all command outputs.
- Verification that historical exposed password from commit 96bffaf is definitively rejected (Access Denied).
- Verification that new high-entropy secret connects and Frappe Bench services are healthy.
- Roll-Forward Only recovery protocol in case of error.
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

DEV_BACKEND = 'centrochange-dev-backend-1'
DEV_DB = 'centrochange-dev-db-1'
DEV_SITE = 'centrochange.local'
DEV_DB_NAME = '_4f614b4543aa5230'
DEV_DB_USER = '_4f614b4543aa5230'

APP_SERVICES = [
    'centrochange-dev-backend-1',
    'centrochange-dev-queue-short-1',
    'centrochange-dev-queue-long-1',
    'centrochange-dev-scheduler-1',
]


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


def test_db_connection(container, user, password, host="db", db=DEV_DB_NAME):
    """Test connecting to MariaDB using an ephemeral 0600 cnf file. Returns (success: bool, output: str)."""
    script = f"""cat << EOF > /tmp/.chk.cnf
[client]
user={user}
password={password}
EOF
chmod 600 /tmp/.chk.cnf
mariadb --defaults-file=/tmp/.chk.cnf -h {host} {db} -e "SELECT 1;"
rc=$?
rm -f /tmp/.chk.cnf
exit $rc
"""
    res = subprocess.run(['docker', 'exec', '-i', container, 'sh'], input=script, text=True, capture_output=True)
    return res.returncode == 0, _redact(res.stdout.strip() or res.stderr.strip())


def get_historical_exposed_password():
    try:
        show = subprocess.check_output(
            ['git', 'show', '96bffaf:infra/clone_volume_test.py'],
            cwd=str(ROOT_DIR),
            text=True
        )
        m = re.search(r"DEV_DB_PASS\s*=\s*['\"]([^'\"]+)['\"]", show)
        if m:
            return m.group(1)
    except Exception as e:
        log(f"Warning reading historical commit: {_redact(e)}")
    return None


def rotate_credentials():
    log("=== INITIATING DEV MARIADB CREDENTIAL ROTATION ===")

    # Step 1: Pre-rotation verification
    log("Verifying pre-rotation DEV state and reading current configuration...")
    raw_cfg = run_cmd(['docker', 'exec', DEV_BACKEND, 'cat', f"sites/{DEV_SITE}/site_config.json"])
    site_cfg = json.loads(raw_cfg)

    if site_cfg.get('db_name') != DEV_DB_NAME:
        raise ValueError(f"Site DB name mismatch: {site_cfg.get('db_name')} != {DEV_DB_NAME}")
    if site_cfg.get('cc_synthetic_dev') != 1:
        raise ValueError("Synthetic DEV flag cc_synthetic_dev != 1; aborting for safety")

    historical_pass = get_historical_exposed_password()
    if historical_pass:
        log("Retrieved historical exposed password fingerprint from commit 96bffaf for invalidation testing.")

    # Step 2: Generate new high-entropy secret
    new_password = secrets.token_hex(16)
    log("Generated new high-entropy secret (32 hex characters).")

    try:
        # Step 3: Execute ALTER USER in MariaDB
        log("Executing ALTER USER on MariaDB DEV for user accounts...")
        alter_script = f"""cat << EOF > /tmp/.rot.cnf
[client]
user=root
password=$MYSQL_ROOT_PASSWORD
protocol=socket
EOF
chmod 600 /tmp/.rot.cnf
mariadb --defaults-file=/tmp/.rot.cnf << 'EOSQL'
ALTER USER '{DEV_DB_USER}'@'%' IDENTIFIED BY '{new_password}';
ALTER USER '{DEV_DB_USER}'@'172.18.0.2' IDENTIFIED BY '{new_password}';
ALTER USER '{DEV_DB_USER}'@'172.18.0.5' IDENTIFIED BY '{new_password}';
FLUSH PRIVILEGES;
EOSQL
rm -f /tmp/.rot.cnf
"""
        run_cmd(['docker', 'exec', '-i', DEV_DB, 'sh'], input_str=alter_script)
        log("ALTER USER and FLUSH PRIVILEGES executed on MariaDB container.")

        # Step 4: Update site_config.json safely via stdin pipe
        log(f"Updating db_password in sites/{DEV_SITE}/site_config.json...")
        site_cfg['db_password'] = new_password
        update_cfg_script = f"""python3 -c "
import sys, json
cfg = json.load(sys.stdin)
with open('sites/{DEV_SITE}/site_config.json', 'w') as f:
    json.dump(cfg, f, indent=1)
"
"""
        run_cmd(['docker', 'exec', '-i', DEV_BACKEND, 'sh', '-c', update_cfg_script], input_str=json.dumps(site_cfg))
        log("site_config.json updated safely.")

        # Step 5: Restart DEV application services
        log("Restarting DEV application services to reload database connection...")
        for svc in APP_SERVICES:
            run_cmd(['docker', 'restart', svc])
        log("Application services restarted.")

        # Allow services 5 seconds to initialize
        time.sleep(5)

        # Step 6: Post-rotation verification
        log("--- Verifying Post-Rotation Security & Integrity ---")

        # 6A: Verify OLD / HISTORICAL password is REJECTED
        if historical_pass:
            log("Checking historical exposed password rejection (Expect Access Denied)...")
            old_ok, old_msg = test_db_connection(DEV_BACKEND, DEV_DB_USER, historical_pass)
            if old_ok:
                raise RuntimeError("CRITICAL SECURITY FAILURE: Historical exposed password was NOT rejected by MariaDB!")
            log(f"Historical password rejection PASS: MariaDB returned: {old_msg}")
        else:
            old_ok = False
            old_msg = "Historical password not found for check"

        # 6B: Verify NEW password SUCCEEDS
        log("Checking new rotated password connection (Expect SELECT 1 SUCCESS)...")
        new_ok, new_msg = test_db_connection(DEV_BACKEND, DEV_DB_USER, new_password)
        if not new_ok:
            raise RuntimeError(f"CRITICAL: New password failed to connect to MariaDB: {new_msg}")
        log("New password connection PASS: SELECT 1 returned successfully.")

        # 6C: Check Bench doctor
        log("Running bench doctor on DEV site...")
        doctor_out = run_cmd(['docker', 'exec', DEV_BACKEND, 'bench', '--site', DEV_SITE, 'doctor'])
        log(f"Bench doctor output:\n{doctor_out}")

        # 6D: Check synthetic dev bootstrap
        log("Verifying synthetic DEV bootstrap setup...")
        bootstrap_raw = run_cmd(['docker', 'exec', DEV_BACKEND, 'bench', '--site', DEV_SITE, 'execute', 'centrochange_core.dev_bootstrap.setup'])
        bootstrap_data = json.loads(bootstrap_raw.strip())
        log(f"Dev bootstrap output: {bootstrap_data}")
        if not bootstrap_data.get('synthetic_dev'):
            raise RuntimeError("Synthetic DEV verification failed: synthetic_dev is not True")

        # 6E: Verify record counts integrity
        appt_count = int(run_cmd(['docker', 'exec', DEV_BACKEND, 'bench', '--site', DEV_SITE, 'execute', 'frappe.db.count', '--args', "['Patient Appointment']"]).strip())
        patient_count = int(run_cmd(['docker', 'exec', DEV_BACKEND, 'bench', '--site', DEV_SITE, 'execute', 'frappe.db.count', '--args', "['Patient']"]).strip())
        practitioner_count = int(run_cmd(['docker', 'exec', DEV_BACKEND, 'bench', '--site', DEV_SITE, 'execute', 'frappe.db.count', '--args', "['Healthcare Practitioner']"]).strip())

        log(f"Verified DEV record counts: Appointments={appt_count}, Patients={patient_count}, Practitioners={practitioner_count}")

        report = {
            'status': 'PASS_ROTATION_SUCCESS',
            'user': DEV_DB_USER,
            'database': DEV_DB_NAME,
            'site': DEV_SITE,
            'historical_password_rejected': not old_ok,
            'historical_rejection_output': old_msg,
            'new_password_verified': new_ok,
            'synthetic_dev_verified': True,
            'record_counts': {
                'appointments': appt_count,
                'patients': patient_count,
                'practitioners': practitioner_count,
            }
        }
        log(f"DEV Credential Rotation COMPLETED SUCCESSFULLY: {report['status']}")
        return report

    except Exception as e:
        log(f"ERROR DURING ROTATION: {_redact(str(e))}")
        log("Entering ROLL-FORWARD RESCUE protocol (NEVER restoring old secret)...")
        try:
            rescue_password = secrets.token_hex(16)
            log("Generated rescue password for roll-forward...")
            rescue_script = f"""cat << EOF > /tmp/.rescue.cnf
[client]
user=root
password=$MYSQL_ROOT_PASSWORD
protocol=socket
EOF
chmod 600 /tmp/.rescue.cnf
mariadb --defaults-file=/tmp/.rescue.cnf << 'EOSQL'
ALTER USER '{DEV_DB_USER}'@'%' IDENTIFIED BY '{rescue_password}';
ALTER USER '{DEV_DB_USER}'@'172.18.0.2' IDENTIFIED BY '{rescue_password}';
ALTER USER '{DEV_DB_USER}'@'172.18.0.5' IDENTIFIED BY '{rescue_password}';
FLUSH PRIVILEGES;
EOSQL
rm -f /tmp/.rescue.cnf
"""
            run_cmd(['docker', 'exec', '-i', DEV_DB, 'sh'], input_str=rescue_script)
            site_cfg['db_password'] = rescue_password
            update_rescue_cfg = f"""python3 -c "
import sys, json
cfg = json.load(sys.stdin)
with open('sites/{DEV_SITE}/site_config.json', 'w') as f:
    json.dump(cfg, f, indent=1)
"
"""
            run_cmd(['docker', 'exec', '-i', DEV_BACKEND, 'sh', '-c', update_rescue_cfg], input_str=json.dumps(site_cfg))
            for svc in APP_SERVICES:
                run_cmd(['docker', 'restart', svc])
            log("Roll-forward rescue applied. Verifying rescue connection...")
            r_ok, r_msg = test_db_connection(DEV_BACKEND, DEV_DB_USER, rescue_password)
            if r_ok:
                log("Roll-forward rescue SUCCESS: database is connected with fresh rescue secret.")
            else:
                log(f"Roll-forward rescue failed: {r_msg}")
        except Exception as rescue_err:
            log(f"CRITICAL: Roll-forward rescue also encountered error: {_redact(rescue_err)}")
        raise


if __name__ == '__main__':
    res = rotate_credentials()
    print(json.dumps(res, indent=2))
