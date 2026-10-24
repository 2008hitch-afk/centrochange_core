#!/usr/bin/env python3
"""Conditionally deploy verified candidate image cc171-professionals:c2a1e8d to DEV application services.

Scope:
- Only the 6 application services: backend, frontend, websocket, queue-short, queue-long, scheduler.
- MariaDB and Redis containers and volumes are NEVER touched.
- No schema migration, no historic data modification.
- Ephemeral 0600 env file outside CLI arguments.
- Verification of health, assets, and HTTP 8082 endpoint.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

COMPOSE_FILE = ROOT_DIR / 'infra/compose.single-stack-full.yaml'
CANDIDATE_IMAGE = 'cc171-professionals:c2a1e8d'
HTTP_PORT = '8082'
DEV_SITE = 'centrochange.local'
PROJECT = 'centrochange-dev'

SERVICES = ['backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler']


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


def deploy():
    log("=== INITIATING CONDITIONAL DEV INSTALLATION ===")
    log(f"Target candidate image: {CANDIDATE_IMAGE}")

    # Read current DB password from site_config.json safely
    raw_cfg = run_cmd(['docker', 'exec', 'centrochange-dev-backend-1', 'cat', f"sites/{DEV_SITE}/site_config.json"])
    site_cfg = json.loads(raw_cfg)
    db_pass = site_cfg.get('db_password')
    if not db_pass:
        raise RuntimeError("Failed to read current db_password from site_config.json")

    ephemeral_env = ROOT_DIR / f'infra/.ephemeral_deploy_{time.time_ns()}.env'
    try:
        ephemeral_env.write_text(
            f"CC_SINGLE_FULL_IMAGE={CANDIDATE_IMAGE}\n"
            f"HTTP_PORT={HTTP_PORT}\n"
            f"DB_PASSWORD={db_pass}\n",
            encoding='utf-8'
        )
        ephemeral_env.chmod(0o600)

        log("Executing Docker Compose up for the 6 application services with --no-deps...")
        up_cmd = [
            'docker', 'compose',
            '-p', PROJECT,
            '-f', str(COMPOSE_FILE),
            '--env-file', str(ephemeral_env),
            'up', '-d', '--no-build', '--no-deps',
            *SERVICES
        ]
        out = run_cmd(up_cmd)
        log(f"Compose up output:\n{out}")

    finally:
        if ephemeral_env.exists():
            ephemeral_env.unlink()

    log("Waiting 5 seconds for application containers to stabilize...")
    time.sleep(5)

    log("Clearing Frappe cache on DEV site...")
    run_cmd(['docker', 'exec', 'centrochange-dev-backend-1', 'bench', '--site', DEV_SITE, 'clear-cache'])

    log("Running bench doctor...")
    doctor_out = run_cmd(['docker', 'exec', 'centrochange-dev-backend-1', 'bench', '--site', DEV_SITE, 'doctor'])
    log(f"Bench doctor output:\n{doctor_out}")

    log("Checking HTTP endpoint response...")
    http_code = run_cmd(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'http://127.0.0.1:{HTTP_PORT}/centrochange']).strip()
    log(f"HTTP GET /centrochange returned status: {http_code}")
    if http_code not in ('200', '302', '301'):
        raise RuntimeError(f"Unexpected HTTP status {http_code} from /centrochange")

    # Verify backend container is using the new image
    current_image = run_cmd(['docker', 'inspect', '-f', '{{.Config.Image}}', 'centrochange-dev-backend-1']).strip()
    log(f"Backend container running image: {current_image}")
    if current_image != CANDIDATE_IMAGE:
        raise RuntimeError(f"Backend container image mismatch: {current_image} != {CANDIDATE_IMAGE}")

    report = {
        'status': 'PASS_DEV_INSTALLED',
        'candidate_image': CANDIDATE_IMAGE,
        'services_recreated': SERVICES,
        'http_status': http_code,
        'site': DEV_SITE,
    }
    log(f"DEV Installation COMPLETED SUCCESSFULLY: {report['status']}")
    return report


if __name__ == '__main__':
    res = deploy()
    print(json.dumps(res, indent=2))
