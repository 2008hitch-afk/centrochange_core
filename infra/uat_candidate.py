#!/usr/bin/env python3
"""Build/deploy a named synthetic DEV candidate from an exact committed tree.

No volume destruction, production deployment, credentials or automatic Git merge.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-ref', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--env-file', required=True)
    parser.add_argument('--existing-site-ui', action='store_true', help='Deploy only app services to an initialized site; skip configurator/migrate')
    args = parser.parse_args()
    if not re.fullmatch(r'goal02-[0-9]{8}-rc[0-9]+', args.name):
        raise ValueError('Explicit GOAL-02 candidate name required')
    root = Path(__file__).resolve().parent.parent
    values = {line.split('=', 1)[0]: line.split('=', 1)[1] for line in Path(args.env_file).read_text().splitlines() if '=' in line and not line.startswith('#')}
    if values.get('SITE_NAME') != 'centrochange.local':
        raise ValueError('Only the fixed synthetic DEV site is authorized')
    source = subprocess.check_output(['git', 'rev-parse', args.source_ref + '^{commit}'], cwd=root, text=True).strip()
    image = 'centrochange-uat:' + args.name
    existing = subprocess.run(['docker', 'image', 'inspect', image], capture_output=True, text=True)
    if existing.returncode == 0:
        raise ValueError('Named candidate image already exists; do not overwrite immutable build identity')
    archive = subprocess.check_output(['git', 'archive', source], cwd=root)
    log = Path('/tmp/cc-uat-' + args.name + '-build.log')
    with tempfile.TemporaryDirectory(prefix='cc-uat-source-') as temporary:
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            stream.extractall(temporary, filter='data')
        with log.open('w') as stream:
            os.chmod(log, 0o600)
            result = subprocess.run(['docker', 'build', '--label', 'org.opencontainers.image.revision=' + source,
                '--label', 'org.opencontainers.image.version=' + args.name, '-t', image, '-f', 'infra/Dockerfile', '.'],
                cwd=temporary, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError('Candidate build failed; external trace: ' + str(log))
    environment = dict(os.environ, CC_UAT_IMAGE=image)
    command = ['docker', 'compose', '-f', 'infra/compose.yaml', '-f', 'infra/compose.uat.yaml', '--env-file', str(Path(args.env_file).resolve())]
    startup = ['up', '-d', '--no-build']
    if args.existing_site_ui:
        health = subprocess.run(['docker', 'exec', 'centrochange-dev-backend-1', 'bench', '--site', 'centrochange.local', 'list-apps'], capture_output=True, text=True)
        if health.returncode or 'centrochange_core' not in health.stdout or 'healthcare' not in health.stdout:
            raise RuntimeError('UI-only deployment requires initialized DEV site')
        startup += ['--no-deps', 'backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler']
    result = subprocess.run(command + startup, cwd=root, env=environment, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Candidate DEV startup failed; inspect fixed DEV Compose services')
    # Redis persists across images: invalidate app hooks/website cache after controlled restart.
    for attempt in range(60):
        cleared = subprocess.run(['docker','exec','centrochange-dev-backend-1','bench','--site','centrochange.local','clear-cache'], capture_output=True, text=True)
        if cleared.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Candidate app cache invalidation failed')
    identity = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]
    print(json.dumps({'status': 'PASS', 'candidate': args.name, 'image': image, 'image_id': identity['Id'],
        'schema_migration': not args.existing_site_ui, 'app_cache_invalidated': True, 'source_commit': source, 'source_export': 'git archive of exact commit', 'production': False,
        'note': 'Build/deploy proof only; acceptance remains required'}))


if __name__ == '__main__':
    os.umask(0o077)
    main()
