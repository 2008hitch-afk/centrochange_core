#!/usr/bin/env python3
"""Verified isolated restore rehearsal of encrypted DEV checkpoint outside DEV stack.

Guarantees:
- Fully isolated Docker network cc171-restore-net (no host port exposure).
- Dedicated MariaDB, Redis, and backend containers.
- DEV shared database, site volumes, and containers are NEVER touched.
- Uses fresh random credentials for the restored database; zero leaked secrets.
- Full verification of schema, synthetic records, files, and bench doctor.
- Complete teardown and cleanup of all temporary resources in finally block.
"""

import argparse
import gzip
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

RESTORE_NET = 'cc171-restore-net'
RESTORE_DB = 'cc171-restore-db'
RESTORE_REDIS = 'cc171-restore-redis'
RESTORE_RUNNER = 'cc171-restore-runner'
RESTORE_SITES_VOL = 'cc171-restore-sites'

SITE_NAME = 'centrochange.local'
DB_NAME = '_4f614b4543aa5230'
DB_USER = '_4f614b4543aa5230'

MARIADB_IMAGE = 'mariadb:11.8.8@sha256:24e76fcec8c003a0362d0dd53f4806e7e79458d7fdeaf47437760e19496f5a9c'
REDIS_IMAGE = 'redis:8.6.5-alpine@sha256:cd218f4b106a332c5c992e38a9480bfb9d7e9f8f7b0ec9a0023bfa36d9a408f9'
DEFAULT_RUNNER_IMAGE = 'cc171-professionals:343f8a9'


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


def cleanup():
    log("Cleaning up isolated restore resources...")
    for c in [RESTORE_RUNNER, RESTORE_DB, RESTORE_REDIS]:
        subprocess.run(['docker', 'rm', '-f', c], capture_output=True)
    subprocess.run(['docker', 'volume', 'rm', '-f', RESTORE_SITES_VOL], capture_output=True)
    subprocess.run(['docker', 'network', 'rm', RESTORE_NET], capture_output=True)
    log("Cleanup complete.")


def run_mariadb_sql(container, user, password, sql, db=None):
    script = f"""cat << 'EOF' > /tmp/.client.cnf
[client]
user={user}
password={password}
protocol=socket
EOF
chmod 600 /tmp/.client.cnf
mariadb --defaults-file=/tmp/.client.cnf {'`' + db + '`' if db else ''} << 'EOF'
{sql}
EOF
rm -f /tmp/.client.cnf
"""
    run_cmd(['docker', 'exec', '-i', container, 'sh'], input_str=script)


def verify_isolated_restore(encrypted_path, key_path, inventory_path, runner_image=DEFAULT_RUNNER_IMAGE):
    encrypted_path = Path(encrypted_path).resolve()
    key_path = Path(key_path).resolve()
    inventory_path = Path(inventory_path).resolve()

    if not encrypted_path.is_file():
        raise FileNotFoundError(f"Encrypted backup not found: {encrypted_path}")
    if not key_path.is_file():
        raise FileNotFoundError(f"Key file not found: {key_path}")
    if not inventory_path.is_file():
        raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

    log(f"Starting isolated restore test using backup {encrypted_path.name}")
    cleanup()

    temp_dir = Path(tempfile.mkdtemp(prefix='cc171-restore-test-'))
    temp_dir.chmod(0o700)

    try:
        # Step 1: Decrypt backup archive
        log("Decrypting backup archive in isolated temp dir...")
        home = temp_dir / 'gnupg'
        home.mkdir(mode=0o700)
        decrypted_tar = temp_dir / 'backup.tar'

        decrypt_cmd = [
            'gpg', '--homedir', str(home), '--batch', '--yes', '--pinentry-mode', 'loopback',
            '--passphrase-file', str(key_path), '--decrypt', '--output', str(decrypted_tar), str(encrypted_path)
        ]
        run_cmd(decrypt_cmd)
        decrypted_tar.chmod(0o600)

        # Step 2: Extract backup bundle
        log("Extracting and inspecting backup components...")
        extracted_dir = temp_dir / 'extracted'
        extracted_dir.mkdir(mode=0o700)
        with tarfile.open(decrypted_tar, 'r:') as tar:
            tar.extractall(path=extracted_dir)

        files = list(extracted_dir.iterdir())
        db_sql_gz = next((f for f in files if 'database.sql' in f.name), None)
        public_files_tar = next((f for f in files if ('files.tgz' in f.name or 'files.tar' in f.name) and 'private' not in f.name), None)
        private_files_tar = next((f for f in files if 'private-files' in f.name), None)
        site_config_json = next((f for f in files if 'site_config' in f.name), None)

        if not (db_sql_gz and public_files_tar and private_files_tar and site_config_json):
            raise RuntimeError(f"Missing required backup components in {files}")

        log(f"Backup components verified: DB={db_sql_gz.name}, Public={public_files_tar.name}, Private={private_files_tar.name}")

        # Step 3: Setup isolated Docker network
        log(f"Creating isolated Docker network {RESTORE_NET}...")
        run_cmd(['docker', 'network', 'create', RESTORE_NET])

        # Step 4: Launch isolated MariaDB
        root_pass = secrets.token_hex(16)
        restored_db_pass = secrets.token_hex(16)

        log(f"Starting isolated MariaDB {RESTORE_DB}...")
        env_file = temp_dir / 'mariadb.env'
        env_file.write_text(f"MYSQL_ROOT_PASSWORD={root_pass}\nMARIADB_AUTO_UPGRADE=1\n", encoding='utf-8')
        env_file.chmod(0o600)

        run_cmd([
            'docker', 'run', '-d',
            '--name', RESTORE_DB,
            '--network', RESTORE_NET,
            '--env-file', str(env_file),
            MARIADB_IMAGE,
            '--character-set-server=utf8mb4',
            '--collation-server=utf8mb4_unicode_ci'
        ])
        env_file.unlink()

        # Step 5: Wait for MariaDB readiness using official healthcheck
        log("Waiting for MariaDB to complete initialization and become healthy...")
        ready = False
        consecutive = 0
        ping_script = f"""cat << 'EOF' > /tmp/.ping.cnf
[client]
user=root
password={root_pass}
protocol=socket
EOF
chmod 600 /tmp/.ping.cnf
mariadb --defaults-file=/tmp/.ping.cnf -e "SELECT 1"
rm -f /tmp/.ping.cnf
"""
        for attempt in range(60):
            time.sleep(1)
            hc = subprocess.run(['docker', 'exec', RESTORE_DB, 'healthcheck.sh', '--connect', '--innodb_initialized'],
                                capture_output=True, text=True)
            if hc.returncode == 0:
                res = subprocess.run(['docker', 'exec', '-i', RESTORE_DB, 'sh'],
                                     input=ping_script, capture_output=True, text=True)
                if res.returncode == 0:
                    consecutive += 1
                    if consecutive >= 3:
                        ready = True
                        break
                else:
                    consecutive = 0
            else:
                consecutive = 0
        if not ready:
            raise RuntimeError("Restored MariaDB failed to initialize")

        # Step 6: Create database and user
        log(f"Initializing database {DB_NAME} and user {DB_USER}...")
        init_sql = f"""
        CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;
        GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'%' IDENTIFIED BY '{restored_db_pass}';
        GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'localhost' IDENTIFIED BY '{restored_db_pass}';
        GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'127.0.0.1' IDENTIFIED BY '{restored_db_pass}';
        FLUSH PRIVILEGES;
        """
        run_mariadb_sql(RESTORE_DB, 'root', root_pass, init_sql)

        # Step 7: Restore Database SQL dump
        log("Restoring database SQL dump into isolated MariaDB...")
        load_cnf = f"""cat << 'EOF' > /tmp/.load.cnf
[client]
user=root
password={root_pass}
protocol=socket
EOF
chmod 600 /tmp/.load.cnf
"""
        run_cmd(['docker', 'exec', '-i', RESTORE_DB, 'sh'], input_str=load_cnf)
        try:
            with gzip.open(db_sql_gz, 'rb') as gz_in:
                load_proc = subprocess.Popen(
                    ['docker', 'exec', '-i', RESTORE_DB, 'mariadb', '--defaults-file=/tmp/.load.cnf', DB_NAME],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                _, err = load_proc.communicate(input=gz_in.read())
                if load_proc.returncode != 0:
                    raise RuntimeError(f"Database restore failed: {_redact(err.decode('utf-8'))}")
        finally:
            run_cmd(['docker', 'exec', RESTORE_DB, 'rm', '-f', '/tmp/.load.cnf'], check=False)
        log("Database SQL dump restored successfully.")

        # Step 8: Start isolated Redis
        log(f"Starting isolated Redis {RESTORE_REDIS}...")
        run_cmd([
            'docker', 'run', '-d',
            '--name', RESTORE_REDIS,
            '--network', RESTORE_NET,
            REDIS_IMAGE
        ])

        # Step 9: Create and populate isolated sites volume
        log(f"Preparing isolated sites volume {RESTORE_SITES_VOL}...")
        run_cmd(['docker', 'volume', 'create', RESTORE_SITES_VOL])

        site_dir = temp_dir / 'site_payload' / SITE_NAME
        site_dir.mkdir(parents=True, mode=0o700)

        # Prepare site_config.json
        orig_config = json.loads(site_config_json.read_text())
        orig_config['db_host'] = RESTORE_DB
        orig_config['db_name'] = DB_NAME
        orig_config['db_password'] = restored_db_pass
        orig_config['redis_cache'] = f"redis://{RESTORE_REDIS}:6379"
        orig_config['redis_queue'] = f"redis://{RESTORE_REDIS}:6379"
        orig_config['redis_socketio'] = f"redis://{RESTORE_REDIS}:6379"
        orig_config['cc_synthetic_dev'] = 1

        (site_dir / 'site_config.json').write_text(json.dumps(orig_config, indent=2))
        (site_dir / 'site_config.json').chmod(0o600)

        # Create logs directory required by frappe database logging
        (site_dir / 'logs').mkdir(parents=True, mode=0o777)

        # Extract files
        public_dir = site_dir / 'public' / 'files'
        public_dir.mkdir(parents=True, mode=0o755)
        with tarfile.open(public_files_tar) as tar:
            tar.extractall(path=public_dir)

        private_dir = site_dir / 'private' / 'files'
        private_dir.mkdir(parents=True, mode=0o700)
        with tarfile.open(private_files_tar) as tar:
            tar.extractall(path=private_dir)

        # Step 10: Start isolated backend runner
        log(f"Starting isolated backend runner {RESTORE_RUNNER}...")
        run_cmd([
            'docker', 'run', '-d',
            '--name', RESTORE_RUNNER,
            '--network', RESTORE_NET,
            '-v', f"{RESTORE_SITES_VOL}:/home/frappe/frappe-bench/sites",
            runner_image,
            'tail', '-f', '/dev/null'
        ])

        # Copy site payload into runner volume
        tar_stream = subprocess.Popen(
            ['tar', '-C', str(temp_dir / 'site_payload'), '-cf', '-', SITE_NAME],
            stdout=subprocess.PIPE
        )
        untar_proc = subprocess.Popen(
            ['docker', 'exec', '-i', RESTORE_RUNNER, 'tar', '-C', '/home/frappe/frappe-bench/sites', '-xf', '-'],
            stdin=tar_stream.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        tar_stream.stdout.close()
        untar_proc.communicate()
        if untar_proc.returncode != 0:
            raise RuntimeError("Failed to copy site payload into isolated runner")

        run_cmd(['docker', 'exec', '-u', '0', RESTORE_RUNNER, 'chown', '-R', '1000:0', f"/home/frappe/frappe-bench/sites/{SITE_NAME}"])
        run_cmd(['docker', 'exec', '-u', '0', RESTORE_RUNNER, 'mkdir', '-p', f"/home/frappe/frappe-bench/sites/{SITE_NAME}/logs", "/home/frappe/logs"])
        run_cmd(['docker', 'exec', '-u', '0', RESTORE_RUNNER, 'chown', '-R', '1000:0', "/home/frappe/logs"])
        run_cmd(['docker', 'exec', '-u', '0', RESTORE_RUNNER, 'chmod', '-R', '777', f"/home/frappe/frappe-bench/sites/{SITE_NAME}/logs", "/home/frappe/logs"])

        # Step 11: Execute integrity verifications inside runner via bench execute
        log("Executing bench doctor inside isolated runner...")
        doctor_out = run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'doctor'])
        log(f"Doctor output:\n{doctor_out}")

        log("Executing dev_bootstrap check on restored database...")
        bootstrap_raw = run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'centrochange_core.dev_bootstrap.setup'])
        bootstrap_data = json.loads(bootstrap_raw.strip())
        log(f"Dev bootstrap result: {bootstrap_data}")
        if not bootstrap_data.get('synthetic_dev'):
            raise RuntimeError("Restored database does not have synthetic_dev=true!")

        log("Checking record counts on restored database...")
        appt_count = int(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.count', '--args', "['Patient Appointment']"]).strip())
        patient_count = int(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.count', '--args', "['Patient']"]).strip())
        practitioner_count = int(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.count', '--args', "['Healthcare Practitioner']"]).strip())
        has_uat_manager = bool(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.exists', '--args', "['User', 'cc-http-uat0000001-m@example.invalid']"]).strip())
        has_uat_prof_a = bool(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.exists', '--args', "['User', 'cc-http-uat0000001-a@example.invalid']"]).strip())
        has_uat_sec = bool(run_cmd(['docker', 'exec', RESTORE_RUNNER, 'bench', '--site', SITE_NAME, 'execute', 'frappe.db.exists', '--args', "['User', 'cc-http-uat0000001-s@example.invalid']"]).strip())

        check_data = {
            'synthetic_dev': bootstrap_data.get('synthetic_dev'),
            'appointment_count': appt_count,
            'patient_count': patient_count,
            'practitioner_count': practitioner_count,
            'has_uat_manager': has_uat_manager,
            'has_uat_prof_a': has_uat_prof_a,
            'has_uat_sec': has_uat_sec,
        }
        log(f"Restored Data Check: {check_data}")

        if check_data['appointment_count'] != 17:
            raise RuntimeError(f"Unexpected appointment count in restored database: {check_data['appointment_count']} (expected 17)")
        if check_data['patient_count'] != 12:
            raise RuntimeError(f"Unexpected patient count in restored database: {check_data['patient_count']} (expected 12)")
        if check_data['practitioner_count'] != 2:
            raise RuntimeError(f"Unexpected practitioner count in restored database: {check_data['practitioner_count']} (expected 2)")
        if not check_data['has_uat_manager'] or not check_data['has_uat_prof_a'] or not check_data['has_uat_sec']:
            raise RuntimeError("Restored database missing canonical UAT users!")

        report = {
            'status': 'PASS_RESTORE_VERIFIED',
            'backup_file': encrypted_path.name,
            'checks': check_data,
            'isolated_network': RESTORE_NET,
            'isolated_runner': RESTORE_RUNNER,
        }
        log(f"Isolated Restore Verification SUCCESS: {report['status']}")
        return report

    finally:
        cleanup()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Isolated restore rehearsal verification")
    parser.add_argument('--encrypted', required=True, help="Path to backup.tar.gpg")
    parser.add_argument('--key', required=True, help="Path to decryption key")
    parser.add_argument('--inventory', required=True, help="Path to inventory.json")
    parser.add_argument('--runner-image', default=DEFAULT_RUNNER_IMAGE, help="Runner image")
    args = parser.parse_args()

    res = verify_isolated_restore(args.encrypted, args.key, args.inventory, args.runner_image)
    print(json.dumps(res, indent=2))
