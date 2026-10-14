#!/usr/bin/env python3
"""Run the actual #139 execute and rollback paths on one isolated clone only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parent.parent
STATE_PARENT = Path('/home/empv26/.local/state/centrochange-single/issue139-full-rehearsal')
SOURCE_BACKUP = Path('/home/empv26/.local/state/centrochange-single/issue139-restore-rehearsal/cc139-restore-20261014180948')
PROJECT = 'cc139-w5-isolated'
BASE = 'centrochange-single:goal02-abc-fixture-83f8f4f'
SERVICES = ('db', 'redis-cache', 'redis-queue', 'backend', 'websocket',
            'queue-short', 'queue-long', 'scheduler', 'frontend')


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(args, *, input_text=None, check=True):
    result = subprocess.run(args, input=input_text, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f'{Path(args[0]).name} command failed with exit {result.returncode}; private diagnostic retained')
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clone_compose(state):
    return ['docker', 'compose', '--env-file', str(state / 'runtime.env'), '-p', PROJECT,
            '-f', str(state / 'compose.yaml'), '-f', str(state / 'base-overlay.yaml')]


def cleanup_clone_tags(state, image):
    """Remove exact rehearsal tags only, after the clone is fully stopped."""
    if command(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={PROJECT}', '-q']).stdout.strip():
        raise RuntimeError('clone containers remain; image cleanup refused')
    if command(['docker', 'volume', 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip():
        raise RuntimeError('clone volumes remain; image cleanup refused')
    if command(['docker', 'network', 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip():
        raise RuntimeError('clone network remains; image cleanup refused')
    tags = [image]
    for run_dir in (state / 'runs').glob('*'):
        if not run_dir.is_dir() or not re.fullmatch(r'\d{8}T\d{6}Z-\d+', run_dir.name):
            raise RuntimeError('unexpected clone checkpoint directory')
        tags.extend(f'centrochange-single:issue139-rollback-{run_dir.name}-{name}'
                    for name in ('backend', 'frontend', 'websocket', 'queue-short',
                                 'queue-long', 'scheduler'))
    for tag in tags:
        if command(['docker', 'image', 'inspect', tag], check=False).returncode == 0:
            command(['docker', 'image', 'rm', tag])
    return len(tags)


def setup_clone(state, gate, adapter, image):
    if command(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={PROJECT}', '-q']).stdout.strip():
        raise RuntimeError('isolated project already exists')
    for operation in ('volume', 'network'):
        if command(['docker', operation, 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip():
            raise RuntimeError('isolated resource already exists')
    if command(['docker', 'image', 'inspect', image], check=False).returncode == 0:
        raise RuntimeError('isolated candidate tag already exists')
    if shutil.disk_usage('/var/lib/docker').free < 8 * 1024**3:
        raise RuntimeError('Docker disk reserve below 8 GiB')
    mem_kib = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines()
                       if x.startswith('MemAvailable:')))
    if mem_kib < 3 * 1024**2:
        raise RuntimeError('MemAvailable below 3 GiB')
    source = (REPO / 'infra/compose.yaml').read_text()
    if source.count('centrochange-dev') < 10:
        raise RuntimeError('pinned Compose topology changed')
    source = source.replace('centrochange-dev', PROJECT)
    source = source.replace('127.0.0.1:${HTTP_PORT', '127.0.0.2:${HTTP_PORT')
    if 'centrochange-dev' in source or '127.0.0.2:${HTTP_PORT' not in source:
        raise RuntimeError('clone Compose still references DEV')
    (state / 'compose.yaml').write_text(source)
    overlay = 'services:\n'
    for service in (*SERVICES, 'configurator'):
        if service in ('db', 'redis-cache', 'redis-queue'):
            continue
        overlay += (f'  {service}:\n    image: {BASE}\n    pull_policy: never\n'
                    f'    volumes:\n      - {PROJECT}-{service}-logs:/home/frappe/frappe-bench/logs\n')
    overlay += 'volumes:\n'
    for service in (*SERVICES, 'configurator'):
        if service not in ('db', 'redis-cache', 'redis-queue'):
            overlay += f'  {PROJECT}-{service}-logs:\n    name: {PROJECT}-{service}-logs\n'
    (state / 'base-overlay.yaml').write_text(overlay)
    candidate = (REPO / 'infra/compose.issue139_candidate.yaml').read_text()
    candidate = candidate.replace('centrochange-dev-net', PROJECT + '-net')
    candidate = candidate.replace(gate.IMAGE, image)
    if 'centrochange-dev' in candidate or image not in candidate:
        raise RuntimeError('candidate clone overlay drift')
    (state / 'candidate-overlay.yaml').write_text(candidate)
    original = {}
    for line in (Path('/home/empv26/.local/state/centrochange-single/runtime.env')).read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            original[key] = value
    if original.get('SITE_NAME') != gate.SITE or original.get('HTTP_PORT') != '8082':
        raise RuntimeError('private source env Site/port differs')
    db_password = secrets.token_urlsafe(30)
    text = (f'SITE_NAME={gate.SITE}\nHTTP_PORT=8082\nDB_PASSWORD={db_password}\n'
            f'ADMIN_PASSWORD={original["ADMIN_PASSWORD"]}\n'
            f'CC_UAT_IMAGE=centrochange-single:goal02-fixture-d1892e0\n'
            f'COMPOSE_FILE={state / "compose.yaml"}:{state / "base-overlay.yaml"}\n')
    (state / 'runtime.env').write_text(text)
    (state / 'runtime.env').chmod(0o600)
    compose = clone_compose(state)
    config = json.loads(command(compose + ['config', '--format', 'json']).stdout)
    if config['name'] != PROJECT or config['services']['frontend']['ports'][0]['host_ip'] != '127.0.0.2' or \
            set(config['services']['frontend']['networks']) != {PROJECT + '-net'} or \
            set(config['networks']) != {PROJECT + '-net'} or \
            any(not item.startswith(PROJECT + '-') for item in config['volumes']):
        raise RuntimeError('isolated Compose config differs')
    for name in SERVICES:
        if name not in ('db', 'redis-cache', 'redis-queue') and config['services'][name]['image'] != BASE:
            raise RuntimeError('clone baseline app image differs')
    command(compose + ['up', '-d', '--no-deps', 'db', 'redis-cache', 'redis-queue'])
    for _ in range(45):
        rows = command(compose + ['ps', '--format', 'json']).stdout
        if rows.count('healthy') >= 3:
            break
        time.sleep(2)
    else:
        raise RuntimeError('isolated technical services unhealthy')
    volume = PROJECT + '-sites'
    command(['docker', 'run', '--rm', '--network', 'none', '-u', '0', '-v',
             volume + ':/target', '--entrypoint', 'sh', BASE, '-c',
             'cp -a /home/frappe/frappe-bench/sites/. /target/ && '
             'mkdir -p /target/centrochange.local/private/backups && chown -R 1000:0 /target'])
    manifest = json.loads((SOURCE_BACKUP / 'report.json').read_text())['backup']
    for kind, filename in (('db', 'database.sql.gz'), ('public', 'files.tgz'),
                           ('private', 'private-files.tgz'), ('config', 'site_config.json')):
        if sha(SOURCE_BACKUP / filename) != manifest[kind]['sha256']:
            raise RuntimeError('verified synthetic backup changed')
    command(['docker', 'run', '--rm', '--network', 'none', '-u', '0',
             '-v', volume + ':/target', '-v', str(SOURCE_BACKUP) + ':/source:ro',
             '--entrypoint', 'sh', BASE, '-c',
             'cp /source/site_config.json /target/centrochange.local/site_config.json && '
             'cp /source/database.sql.gz /source/files.tgz /source/private-files.tgz '
             '/target/centrochange.local/private/backups/ && '
             'cp /source/common_site_config.json /target/common_site_config.json && '
             'chown -R 1000:0 /target/centrochange.local /target/common_site_config.json'])
    restore = ['bench', '--site', gate.SITE, 'restore',
               f'{gate.BENCH}/sites/{gate.SITE}/private/backups/database.sql.gz',
               '--db-root-password', db_password,
               '--with-public-files', f'{gate.BENCH}/sites/{gate.SITE}/private/backups/files.tgz',
               '--with-private-files', f'{gate.BENCH}/sites/{gate.SITE}/private/backups/private-files.tgz',
               '--force']
    command(compose + ['run', '--rm', '--no-deps', 'backend', *restore])
    site_config = json.loads((SOURCE_BACKUP / 'site_config.json').read_text())
    db_name, user_password = site_config['db_name'], site_config['db_password']
    if not re.fullmatch(r'_[a-z0-9]+', db_name) or "'" in user_password:
        raise RuntimeError('isolated Site DB account unsafe')
    sql = (f"CREATE USER IF NOT EXISTS '{db_name}'@'%' IDENTIFIED BY '{user_password}'; "
           f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_name}'@'%'; FLUSH PRIVILEGES;")
    command(['docker', 'exec', '-i', f'{PROJECT}-db-1', 'sh', '-c',
             'mariadb -uroot -p"$MYSQL_ROOT_PASSWORD"'], input_text=sql)
    command(compose + ['up', '-d', '--no-deps', 'backend', 'websocket',
                       'queue-short', 'queue-long', 'scheduler', 'frontend'])
    module = adapter.load_clone_module()
    module.http_ready()
    data = module.runtime_fingerprint()
    if data['sha256'] != gate.BASE_DATA_SHA or data['communication_sha256'] != gate.BASE_COMM_SHA:
        raise RuntimeError('restored clone fingerprint differs from DEV baseline')
    return data


def install_scope(gate, adapter, scope, state, image):
    original_run, original_bytes = gate.run, gate.run_bytes
    gate.STATE = state
    gate.ENV = state / 'runtime.env'
    gate.COMPOSE_DIR = state
    gate.COMPOSE_SHA = {'compose.yaml': sha(state / 'compose.yaml')}
    gate.BASE_OVERLAY = state / 'base-overlay.yaml'
    gate.BASE_OVERLAY_SHA = sha(gate.BASE_OVERLAY)
    gate.ACTIVE_OVERLAY = state / 'active-overlay.yaml'
    gate.OVERLAY = state / 'candidate-overlay.yaml'
    gate.BASE_ENV_SHA = sha(gate.ENV)
    gate.RUN_ROOT = state / 'runs'
    gate.IMAGE = image
    gate.PROJECT = PROJECT
    gate.NETWORK_NAME = PROJECT + '-net'
    gate.LOOPBACK_IP = '127.0.0.2'
    gate.old_probe = adapter.load_clone_module

    def cache_probe():
        assets = load('infra/issue139_asset_cache_gate.py', 'issue139_clone_asset_probe')
        text = assets.PROBE.replace('INVAL', 'False')
        output = adapter.load_clone_module().backend_python(text)
        return json.loads(next(x.split('=', 1)[1] for x in output.splitlines()
                               if x.startswith('CC_ASSET_GATE=')))

    gate.asset_cache_probe = cache_probe
    original_security = gate.security_command
    gate.security_command = lambda data, communication: original_security(
        data, communication, isolated_project=PROJECT, env_file=state / 'runtime.env')

    def rehearsal_gate(path, executor_sha, *, recovery=False):
        payload = json.loads(path.read_text())
        if path.stat().st_mode & 0o077 or payload != {
                'authorize': 'ISOLATED_EXECUTOR_REHEARSAL',
                'project': PROJECT, 'executor_sha256': executor_sha}:
            raise RuntimeError('isolated rehearsal gate differs')
        return {'operation_end': datetime.now(timezone.utc) + timedelta(hours=2),
                'recovery_end': datetime.now(timezone.utc) + timedelta(hours=3)}

    gate.validate_owner_gate = rehearsal_gate

    def routed(args):
        scoped = scope.scope_command(args, root=state, image=image)
        if scoped[0] == 'runuser':
            if 'node' not in scoped or not any('infra/browser/issue13' in x for x in scoped):
                raise scope.IsolationError('non-browser runuser command')
            scoped.insert(scoped.index('node'), 'CC_ISSUE139_BROWSER_IP=127.0.0.2')
        elif scoped[0] == 'gpg':
            if not all(not item.startswith('/') or Path(item).resolve().is_relative_to(state.resolve())
                       for item in scoped[1:]):
                raise scope.IsolationError('GPG path outside clone checkpoint')
        elif scoped[0] == 'git':
            if not any(item in ('diff', 'show', 'rev-parse', 'merge-base', 'status') for item in scoped):
                raise scope.IsolationError('Git mutation in rehearsal')
        return scoped

    def safe_run(args, **kwargs):
        return original_run(routed(args), **kwargs)

    def safe_bytes(args):
        return original_bytes(routed(args))

    gate.run = safe_run
    gate.run_bytes = safe_bytes


def main():
    if os.geteuid() != 0 or sys.flags.isolated != 1 or os.uname().nodename != 'srv2033673':
        raise SystemExit('requires sudo python3 -I on pinned host')
    gate = load('infra/issue139_install_gate.py', 'issue139_actual_executor')
    adapter = load('infra/issue139_clone_adapter.py', 'issue139_clone_adapter')
    scope = load('infra/issue139_rehearsal_scope.py', 'issue139_rehearsal_scope')
    now = datetime.now(timezone.utc)
    STATE_PARENT.mkdir(mode=0o700, parents=True, exist_ok=True)
    STATE_PARENT.chmod(0o700)
    account = pwd.getpwnam('empv26')
    os.chown(STATE_PARENT, account.pw_uid, account.pw_gid)
    state = STATE_PARENT / (now.strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}')
    state.mkdir(mode=0o700, parents=True, exist_ok=False)
    state.chmod(0o700)
    os.chown(state, account.pw_uid, account.pw_gid)
    fixture = Path('/home/empv26/.local/state/centrochange-single/demo-owner.json')
    (state / 'demo-owner.json').write_bytes(fixture.read_bytes())
    (state / 'demo-owner.json').chmod(0o600)
    os.chown(state / 'demo-owner.json', account.pw_uid, account.pw_gid)
    browser = state / 'browser-evidence'; browser.mkdir(mode=0o700)
    os.chown(browser, account.pw_uid, account.pw_gid)
    command(['runuser', '-u', 'empv26', '--', 'test', '-r', str(state / 'demo-owner.json')])
    command(['runuser', '-u', 'empv26', '--', 'test', '-w', str(browser)])
    image = 'centrochange-single:issue139-e2e-' + now.strftime('%Y%m%d%H%M%S')
    dev = load('infra/goal02_install_one_command.py', 'issue139_shared_readonly')
    before_dev = {'services': dev.snapshot(), 'data': dev.runtime_fingerprint(),
                  'hooks': dev.hooks()}
    result = {'status': 'BLOCKED', 'candidate': gate.SOURCE,
              'executor_sha256': hashlib.sha256((REPO / 'infra/issue139_install_gate.py').read_bytes()).hexdigest(),
              'clone_project': PROJECT, 'dev_unchanged': None}
    compose = clone_compose(state)
    try:
        setup_clone(state, gate, adapter, image)
        original_data = adapter.load_clone_module().runtime_fingerprint()
        install_scope(gate, adapter, scope, state, image)
        executor_sha = result['executor_sha256']
        private_gate = state / 'rehearsal-gate.json'
        private_gate.write_text(json.dumps({'authorize': 'ISOLATED_EXECUTOR_REHEARSAL',
                                            'project': PROJECT, 'executor_sha256': executor_sha}))
        private_gate.chmod(0o600)
        pre = gate.preflight(executor_sha)
        env_bytes, env_stat = gate.ENV.read_bytes(), gate.ENV.stat()
        print(json.dumps({'phase': 'BASELINE_CLONE_PASS', 'project': PROJECT,
                          'data_sha256': original_data['sha256']}), flush=True)
        install = gate.execute(executor_sha, private_gate)
        result['executor_status'] = install['status']
        result['executor_tests'] = install.get('tests')
        result['candidate_image'] = install.get('candidate_image')
        result['executor_failure'] = install.get('failure')
        if install['status'] != 'LIVE_TECHNICAL_PASS':
            raise RuntimeError('actual executor did not finish isolated W5')
        print(json.dumps({'phase': 'EXECUTOR_W5_PASS', 'routes':
                          install['tests']['w5_readonly']['routes'], 'security':
                          install['tests']['security']}), flush=True)
        checkpoint = Path(install['checkpoint'])
        gate.restore_services(pre, env_bytes, env_stat,
                              data_backup=install['backup'], output=checkpoint)
        restored = adapter.load_clone_module()
        if restored.runtime_fingerprint() != pre['data'] or \
                gate.schema_fingerprint(restored) != pre['schema'] or \
                gate.permission_fingerprint(restored) != pre['permissions'] or \
                restored.hooks() != restored.GUARDS:
            raise RuntimeError('actual executor rollback did not restore clone')
        restored.http_ready()
        result['rollback'] = 'PASS'
        result['status'] = 'FULL_END_TO_END_REHEARSAL_PASS'
    except Exception as error:
        result['failure'] = f'{type(error).__name__}: {str(error)[:160]}'
    finally:
        command(compose + ['down', '-v', '--remove-orphans'], check=False)
        if command(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={PROJECT}', '-q']).stdout.strip() or \
                command(['docker', 'volume', 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip() or \
                command(['docker', 'network', 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip():
            result['status'] = 'CLEANUP_FAILED'
        else:
            try:
                result['clone_image_tags_cleaned'] = cleanup_clone_tags(state, image)
            except Exception:
                result['status'] = 'CLEANUP_FAILED'
        after_dev = {'services': dev.snapshot(), 'data': dev.runtime_fingerprint(),
                     'hooks': dev.hooks()}
        result['dev_unchanged'] = before_dev == after_dev
        if not result['dev_unchanged']:
            result['status'] = 'SECURITY_STOP'
        (state / 'summary.json').write_text(json.dumps(result, sort_keys=True, indent=2))
        print(json.dumps({key: result.get(key) for key in
                          ('status', 'executor_status', 'executor_failure', 'rollback',
                           'dev_unchanged', 'failure')}), flush=True)
    return 0 if result['status'] == 'FULL_END_TO_END_REHEARSAL_PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
