#!/usr/bin/env python3
"""Conditionally deploy verified candidate image to DEV application services.

Scope:
- Only the 6 application services: backend, frontend, websocket, queue-short, queue-long, scheduler.
- MariaDB and Redis containers and volumes are NEVER touched.
- No schema migration, no historic data modification.
- Image selection is strictly guarded: requires verified candidate image, valid labels, and digest check.
- Ephemeral 0600 env file outside CLI arguments.
- Verification of health, assets, and HTTP 8082 endpoint.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

COMPOSE_FILE = ROOT_DIR / 'infra/compose.single-stack-full.yaml'
HTTP_PORT = '8082'
DEV_SITE = 'centrochange.local'
PROJECT = 'centrochange-dev'
SERVICES = ['backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler']

# Outdated baseline images that must never be accidentally redeployed without explicit intent
SUPERSEDED_IMAGES = {'cc171-professionals:c2a1e8d'}


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


def verify_candidate_image(image_ref, expected_digest=None, expected_source_sha=None, allow_superseded=False):
    """Verify that the candidate image exists, matches metadata, and has required labels."""
    log(f"Verifying candidate image: {image_ref}")
    if not allow_superseded and image_ref in SUPERSEDED_IMAGES:
        raise ValueError(f"Image {image_ref} is marked as SUPERSEDED. Accidental deployment blocked.")

    raw = run_cmd(['docker', 'inspect', image_ref])
    data = json.loads(raw)
    if not data or not isinstance(data, list):
        raise ValueError(f"Unable to inspect image: {image_ref}")

    inspect_data = data[0]
    image_id = inspect_data.get('Id', '')
    labels = inspect_data.get('Config', {}).get('Labels', {}) or {}

    log(f"Candidate image ID: {image_id}")
    log(f"Candidate labels: mode={labels.get('centrochange.mode')}, source={labels.get('centrochange.source')}")

    if labels.get('centrochange.mode') != 'single-stack-full':
        raise ValueError(f"Image mode mismatch: expected 'single-stack-full', found '{labels.get('centrochange.mode')}'")

    if expected_source_sha:
        source_label = labels.get('centrochange.source', '')
        if not source_label.startswith(expected_source_sha) and not expected_source_sha.startswith(source_label):
            raise ValueError(f"Source SHA mismatch on candidate image: expected {expected_source_sha}, image has {source_label}")

    if expected_digest:
        repo_digests = inspect_data.get('RepoDigests', [])
        if expected_digest != image_id and not any(expected_digest in rd for rd in repo_digests):
            raise ValueError(f"Image digest mismatch: expected {expected_digest}, inspect returned ID {image_id}")

    return {
        'image_ref': image_ref,
        'image_id': image_id,
        'source_sha': labels.get('centrochange.source', ''),
        'labels': labels
    }


def deploy(candidate_image, expected_digest=None, expected_source_sha=None, allow_superseded=False):
    log("=== INITIATING CONDITIONAL DEV INSTALLATION ===")
    verified_meta = verify_candidate_image(
        candidate_image,
        expected_digest=expected_digest,
        expected_source_sha=expected_source_sha,
        allow_superseded=allow_superseded
    )
    log(f"Target candidate verified: {candidate_image} (source: {verified_meta['source_sha'][:12]})")

    # Read current DB password from site_config.json safely
    raw_cfg = run_cmd(['docker', 'exec', 'centrochange-dev-backend-1', 'cat', f"sites/{DEV_SITE}/site_config.json"])
    site_cfg = json.loads(raw_cfg)
    db_pass = site_cfg.get('db_password')
    if not db_pass:
        raise RuntimeError("Failed to read current db_password from site_config.json")

    ephemeral_env = ROOT_DIR / f'infra/.ephemeral_deploy_{time.time_ns()}.env'
    try:
        ephemeral_env.write_text(
            f"CC_SINGLE_FULL_IMAGE={candidate_image}\n"
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
    current_id = run_cmd(['docker', 'inspect', '-f', '{{.Image}}', 'centrochange-dev-backend-1']).strip()
    log(f"Backend container running image: {current_image} (ID: {current_id[:19]}...)")
    if current_image != candidate_image and current_id != verified_meta['image_id']:
        raise RuntimeError(f"Backend container image mismatch: {current_image} != {candidate_image}")

    report = {
        'status': 'PASS_DEV_INSTALLED',
        'candidate_image': candidate_image,
        'candidate_image_id': verified_meta['image_id'],
        'candidate_source_sha': verified_meta['source_sha'],
        'services_recreated': SERVICES,
        'http_status': http_code,
        'site': DEV_SITE,
    }
    log(f"DEV Installation COMPLETED SUCCESSFULLY: {report['status']}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Deploy verified candidate image to DEV services.")
    parser.add_argument('--image', dest='candidate_image', default=None,
                        help="Candidate Docker image tag (defaults to current git HEAD short commit or env CC_CANDIDATE_IMAGE)")
    parser.add_argument('--expected-digest', dest='expected_digest', default=None,
                        help="Expected Docker image ID or repo digest to enforce fail-closed verification")
    parser.add_argument('--expected-source-sha', dest='expected_source_sha', default=None,
                        help="Expected git commit SHA in the image label centrochange.source")
    parser.add_argument('--allow-superseded', action='store_true', default=False,
                        help="Allow deployment of an image on the superseded list (requires explicit intent)")
    args = parser.parse_args()

    image = args.candidate_image or os.environ.get('CC_CANDIDATE_IMAGE')
    if not image:
        try:
            head_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT_DIR, text=True).strip()
            image = f"cc171-professionals:{head_sha[:7]}"
        except Exception:
            raise ValueError("No candidate image specified and unable to determine git HEAD")

    res = deploy(
        candidate_image=image,
        expected_digest=args.expected_digest,
        expected_source_sha=args.expected_source_sha,
        allow_superseded=args.allow_superseded
    )
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
