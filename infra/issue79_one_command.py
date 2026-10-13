#!/usr/bin/env python3
"""Owner-run, fail-closed CSS-only deploy for issue #79 on the single DEV.

Use --dry-run without sudo for static validation. --apply is intended for one
interactive `sudo python3 ...` invocation by the Owner; it never asks for a
second password, changes privileges, or contacts GitHub during execution.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

REPO = Path(__file__).resolve().parent.parent
STATE = Path('/home/empv26/.local/state/centrochange-single')
ENV = STATE / 'runtime.env'
CHECKPOINT = STATE / 'issue79-checkpoint-20261013'
COMPOSE_DIR = Path('/tmp/centrochange-issue124/infra')
COMPOSE_NAMES = ('compose.yaml', 'compose.issue124.yaml', 'compose.uat.yaml')
OVERRIDE_SOURCE = REPO / 'infra/compose.issue79.yaml'
OVERRIDE = STATE / 'compose.issue79.yaml'
OVERRIDE_SHA = 'f68f3da5adc5ed8b3ec907602f8a5ff671735b5265aeb3a6c7fafeed4cdb4a8f'
COMPOSE_SHA = {
    'compose.yaml': '5df3c081f4afff41e6e07222405a4d311bc75eeb1fa97c1045834115e5a0a67d',
    'compose.issue124.yaml': 'ced6e5d2af243bfefbd368ddc46e49de0381bf36c25d05109a13413b59bd7917',
    'compose.uat.yaml': '982fd1cd6253c331482af430a64f9a0b9d1ba205af8a37fd31a1e4cf2a10ade7',
}
ORIGINAL_ENV_SHA = '6fba9cef0e66ca6472407489bb5886b300eedc316fcbb5f656b54cb39cde56ad'
DEPLOYED_ENV_SHA = 'd2e2e2849b0507f9bcfe8de78d48dc81cdb59d705aa62a765e96eea60429f080'
BASE_IMAGE = 'sha256:f38215267771e4db2e42af9312211931dc039b07ff17b69953c10f50026c6285'
ROLLBACK_TAG = 'centrochange-single:issue79-rollback-20261013'
NEW_TAG = 'centrochange-single:issue79-css-f3ab9d5ddf9f'
CSS_COMMIT = '1b2486d00754ba68fa4ee3c57a39060dc8cc781c'
CSS_REL = 'app/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.css'
IMAGE_CSS = '/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.css'
OLD_CSS_SHA = 'd3b04182dcb12029c492540c0eafc97f2d32a653d80b5a1dcf182e37e1b77c2b'
NEW_CSS_SHA = 'f3ab9d5ddf9f15e63b576a5656331169067af6d722cdea6d79b8c5ca644fe27d'
APP = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')
TECH = ('db', 'redis-cache', 'redis-queue')
FIXTURE = STATE / 'demo-owner.json'
NODE_MODULES = Path('/tmp/cc-browser-qa/node_modules')
CHROMIUM_LIBS = Path('/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu')
CHROMIUM = Path('/home/empv26/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell')
RECIPE_SHA = '37e533f77a0aa30d2723530a1319f01a1c6556f66ef19c278c76faf0f8ab1e10'
LIVE_HARNESS_SHA = '17c398de623b26ccdf5e9c7cfe85801ceef3390088034e3e42602e912cb366da'
INVENTORY_HARNESS_SHA = 'e0b8735163c112fcc0d3fa7d5cee48ff83659f60e1765051ad4be84384c2dcbb'


class Stop(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def require(ok: bool, message: str) -> None:
    if not ok:
        raise Stop(message)


def command(args: list[str], *, cwd: Path | None = None, env: dict | None = None,
            label: str = 'command', allow_fail: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode and not allow_fail:
        raise Stop(f'{label} failed (exit {result.returncode}); no secret output retained')
    return result


def git_bytes(ref: str) -> bytes:
    prefix = ['runuser', '-u', 'empv26', '--'] if os.geteuid() == 0 else []
    return subprocess.run(prefix + ['git', 'show', ref], cwd=REPO, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL).stdout


def git_call(*args: str, allow_fail: bool = False) -> subprocess.CompletedProcess:
    prefix = ['runuser', '-u', 'empv26', '--'] if os.geteuid() == 0 else []
    return command(prefix + ['git', *args], cwd=REPO, label='source verification', allow_fail=allow_fail)


def static_preflight(expected_script_sha: str) -> dict:
    require(file_sha(Path(__file__)) == expected_script_sha, 'script SHA-256 mismatch')
    require(file_sha(REPO / CSS_REL) == NEW_CSS_SHA, 'candidate CSS hash mismatch')
    old = git_bytes(f'{CSS_COMMIT}^:{CSS_REL}')
    new = git_bytes(f'{CSS_COMMIT}:{CSS_REL}')
    require(sha(old) == OLD_CSS_SHA and sha(new) == NEW_CSS_SHA, 'pinned CSS commit mismatch')
    rules = (b'.cc-client #modal-fields .cc-combobox{position:relative;min-width:0}\n',
             b'.cc-client #modal-fields .cc-combobox>.cc-options{position:absolute;top:calc(100% - 1.15rem);left:0;width:100%;max-height:16rem;overflow:auto;z-index:1080;padding:.25rem}\n')
    require(new.count(rules[0]) == 1 and new.count(rules[1]) == 1 and
            new.replace(rules[0] + rules[1], b'', 1) == old, 'CSS delta exceeds two approved rules')
    require((REPO / 'infra/Dockerfile.issue79').is_file(), 'versioned recipe missing')
    require(file_sha(REPO / 'infra/Dockerfile.issue79') == RECIPE_SHA, 'recipe SHA-256 mismatch')
    require(file_sha(REPO / 'infra/browser/issue79_unified_autocomplete.cjs') == LIVE_HARNESS_SHA,
            'live browser harness changed')
    require(file_sha(REPO / 'infra/browser/issue79_inventory.cjs') == INVENTORY_HARNESS_SHA,
            'inventory browser harness changed')
    recipe = (REPO / 'infra/Dockerfile.issue79').read_text()
    require(recipe.count('COPY ') == 1 and 'RUN ' not in recipe and
            f'FROM {ROLLBACK_TAG}' in recipe and IMAGE_CSS in recipe, 'recipe exceeds CSS-only scope')
    for name, expected in COMPOSE_SHA.items():
        require(file_sha(COMPOSE_DIR / name) == expected, f'{name} drift')
    require(file_sha(OVERRIDE_SOURCE) == OVERRIDE_SHA, 'backend-only override changed')
    require(OVERRIDE_SOURCE.read_text().splitlines()[-3:] ==
            ['  backend:', f'    image: {NEW_TAG}', '    pull_policy: never'],
            'backend-only override scope changed')
    require(ENV.is_file() and ENV.stat().st_mode & 0o077 == 0, 'private env missing or exposed')
    settings = read_env()
    require(settings.get('SITE_NAME') == 'centrochange.local', 'Site mismatch')
    require(settings.get('HTTP_PORT') == '8082', 'HTTP port mismatch')
    require(git_call('status', '--porcelain').stdout.strip() == '', 'issue-79 checkout not clean')
    require(git_call('merge-base', '--is-ancestor', CSS_COMMIT, 'HEAD',
                     allow_fail=True).returncode == 0, 'checkout does not contain approved CSS commit')
    return {'source_commit': CSS_COMMIT, 'css_before': OLD_CSS_SHA,
            'css_after': NEW_CSS_SHA, 'compose_sha256': COMPOSE_SHA,
            'env_sha256': file_sha(ENV), 'script_sha256': expected_script_sha}


def read_env() -> dict[str, str]:
    out = {}
    for line in ENV.read_text().splitlines():
        if not line or line.lstrip().startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def checkpoint_preflight(env_hash: str, owner_uid: int = 0) -> None:
    require(CHECKPOINT.is_dir() and CHECKPOINT.stat().st_uid == owner_uid and
            CHECKPOINT.stat().st_mode & 0o077 == 0, 'root-only checkpoint missing')
    files = [p for p in CHECKPOINT.rglob('*') if p.is_file() and p.stat().st_size < 2_000_000]
    hashes = {file_sha(p) for p in files}
    for name, digest in COMPOSE_SHA.items():
        require(digest in hashes, f'checkpoint lacks matching {name}')
    # The Owner checkpoint records an env checksum, never an env dump in Git.
    recorded = any(env_hash in p.read_text(errors='ignore') for p in files)
    require(env_hash in hashes or recorded, 'checkpoint env checksum mismatch')


def compose(*args: str, env_file: Path = ENV, target: bool = False,
            override_file: Path = OVERRIDE,
            label: str = 'Compose') -> subprocess.CompletedProcess:
    base = ['docker', 'compose', '--env-file', str(env_file), '-p', 'centrochange-dev']
    for name in COMPOSE_NAMES:
        base += ['-f', str(COMPOSE_DIR / name)]
    if target:
        base += ['-f', str(override_file)]
    return command(base + list(args), label=label)


def compose_files_value() -> str:
    return ':'.join(str(COMPOSE_DIR / name) for name in COMPOSE_NAMES) + ':' + str(OVERRIDE)


def configured_services(*, target: bool = False, env_file: Path = ENV,
                        override_file: Path = OVERRIDE) -> dict:
    data = json.loads(compose('config', '--format', 'json', env_file=env_file,
                              target=target, override_file=override_file,
                              label='Compose config').stdout)
    require(data.get('name') == 'centrochange-dev', 'Compose project mismatch')
    return data['services']


def require_backend_only(before: dict, after: dict, base_ref: str) -> None:
    require(before.keys() == after.keys(), 'Compose service set changed')
    require(before['backend']['image'] == base_ref, 'baseline backend image drift')
    for service in before:
        if service == 'backend':
            expected = dict(before[service]); expected['image'] = NEW_TAG
            expected['pull_policy'] = 'never'
            require(after[service] == expected, 'backend Compose config exceeds image override')
        else:
            require(after[service] == before[service], f'{service}: indirect Compose config change')
    require(all(after[s]['image'] == base_ref for s in APP if s != 'backend'),
            'another application image changed')


def require_default_compose(expected: dict) -> None:
    result = command(['docker', 'compose', '--env-file', str(ENV), '-p', 'centrochange-dev',
                      'config', '--format', 'json'], cwd=COMPOSE_DIR,
                     label='persistent default Compose config')
    actual = json.loads(result.stdout)
    require(actual.get('name') == 'centrochange-dev' and actual['services'] == expected,
            'future ordinary Compose config differs from backend-only target')


def image_id(ref: str) -> str:
    result = command(['docker', 'image', 'inspect', '--format', '{{.Id}}', ref], label='image inspect')
    return result.stdout.strip()


def image_css_sha(ref: str) -> str:
    result = command(['docker', 'run', '--rm', '--network', 'none', '--read-only',
                      '--entrypoint', 'sha256sum', ref, IMAGE_CSS], label='CSS image check')
    return result.stdout.split()[0]


def container_css_sha(container_id: str) -> str:
    result = command(['docker', 'exec', container_id, 'sha256sum', IMAGE_CSS],
                     label='running Page CSS check')
    return result.stdout.split()[0]


def snapshot() -> dict:
    result = {}
    for service in APP + TECH:
        ids = compose('ps', '-q', service, label='service inventory').stdout.splitlines()
        require(len(ids) == 1, f'{service}: expected one container')
        data = json.loads(command(['docker', 'inspect', ids[0]], label='container inspect').stdout)[0]
        labels = data['Config'].get('Labels') or {}
        require(labels.get('com.docker.compose.project') == 'centrochange-dev' and
                labels.get('com.docker.compose.service') == service, f'{service}: wrong Compose ownership')
        health = (data['State'].get('Health') or {}).get('Status')
        require(data['State']['Running'] and health in (None, 'healthy'), f'{service}: unhealthy')
        result[service] = {'id':data['Id'], 'image':data['Image'], 'health':health,
                           'mounts':sorted((m['Type'], m.get('Name'), m['Source'], m['Destination'])
                                           for m in data['Mounts'])}
    live = command(['docker','ps','-q','--filter','label=com.docker.compose.project=centrochange-dev'],
                   label='project inventory').stdout.splitlines()
    require(len(live) == 9 and {value[:12] for value in live} ==
            {row['id'][:12] for row in result.values()},
            'unexpected active project containers')
    return result


def browser_env() -> dict:
    return {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin', 'HOME':'/home/empv26',
            'NODE_PATH':str(NODE_MODULES),
            'LD_LIBRARY_PATH':str(CHROMIUM_LIBS), 'CC_ISSUE79_FIXTURE':str(FIXTURE),
            'CC_BASE_URL':'http://centrochange.local:8082'}


def unprivileged(args: list[str], *, label: str) -> subprocess.CompletedProcess:
    require(shutil.which('runuser') is not None, 'runuser unavailable')
    values = [f'{key}={value}' for key, value in browser_env().items()]
    return command(['runuser','-u','empv26','--','/usr/bin/env',*values,*args],
                   cwd=REPO, label=label)


def browser_preflight() -> None:
    require(FIXTURE.is_file() and FIXTURE.stat().st_mode & 0o077 == 0, 'private demo fixture missing or exposed')
    require((NODE_MODULES / 'playwright/package.json').is_file() and CHROMIUM.is_file(),
            'Playwright/Chromium prerequisites missing')
    require('not found' not in command(['ldd', str(CHROMIUM)], env=browser_env(),
                               label='Chromium libraries').stdout, 'Chromium library missing')
    unprivileged(['node', '-e', "require('playwright')"], label='Playwright module')


def browser(script: str, *, live: bool = False, output: Path | None = None) -> dict:
    args = []
    if live:
        args = ['/usr/bin/env','CC_ISSUE79_ASSET_MODE=live',f'CC_ISSUE79_OUTPUT={output}']
    result = unprivileged([*args,'node',str(REPO / 'infra/browser' / script)],
                          label='Chromium live test' if live else 'synthetic inventory')
    try:
        data = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        raise Stop('browser result is not valid JSON') from None
    require(data.get('status') == 'PASS' and data.get('mutations') == 'NONE', 'browser test failed')
    return data


def http_ready() -> None:
    for _ in range(30):
        try:
            request = urllib.request.Request('http://127.0.0.1:8082/login',
                                             headers={'Host':'centrochange.local'})
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise Stop('DEV HTTP health check failed')


def write_report(path: Path, report: dict) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    path.chmod(0o600)


def persist_compose_file(original: bytes, stat: os.stat_result) -> None:
    lines = original.decode().splitlines(keepends=True)
    require(sum(line.startswith('CC_UAT_IMAGE=') for line in lines) == 1,
            'env requires exactly one CC_UAT_IMAGE')
    require(not any(line.startswith('COMPOSE_FILE=') for line in lines),
            'COMPOSE_FILE already present')
    require(original.endswith(b'\n'), 'env needs a final newline')
    lines.append(f'COMPOSE_FILE={compose_files_value()}\n')
    fd, temp = tempfile.mkstemp(prefix='.issue79-env-', dir=ENV.parent)
    try:
        os.fchmod(fd, stat.st_mode & 0o777)
        os.fchown(fd, stat.st_uid, stat.st_gid)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(''.join(lines).encode())
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, ENV)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def persist_override() -> None:
    require(not OVERRIDE.exists(), 'persistent override already exists')
    fd, temp = tempfile.mkstemp(prefix='.issue79-compose-', dir=STATE)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(OVERRIDE_SOURCE.read_bytes()); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, OVERRIDE)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    require(file_sha(OVERRIDE) == OVERRIDE_SHA, 'persistent override checksum mismatch')


def remove_override() -> None:
    if OVERRIDE.exists():
        require(file_sha(OVERRIDE) == OVERRIDE_SHA, 'persistent override changed; unsafe cleanup')
        OVERRIDE.unlink()


def evidence_preflight(run_name: str) -> Path:
    root = STATE / 'browser-evidence'
    account = pwd.getpwnam('empv26')
    require(root.is_dir() and root.stat().st_uid == account.pw_uid and
            root.stat().st_mode & 0o077 == 0, 'browser evidence directory unavailable or exposed')
    output = root / run_name
    output.mkdir(mode=0o700, exist_ok=False)
    os.chown(output, account.pw_uid, account.pw_gid)
    unprivileged(['python3', '-c',
                  'import pathlib,sys; p=pathlib.Path(sys.argv[1])/".write-check"; '
                  'p.write_text("ok"); p.unlink()', str(output)],
                 label='browser evidence write check')
    return output


def restore_env(original: bytes, stat: os.stat_result) -> None:
    fd, temp = tempfile.mkstemp(prefix='.issue79-restore-', dir=ENV.parent)
    try:
        os.fchmod(fd, stat.st_mode & 0o777); os.fchown(fd, stat.st_uid, stat.st_gid)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(original); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, ENV)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def apply(static: dict) -> dict:
    require(sys.flags.isolated, 'run Python with -I')
    require(os.geteuid() == 0 and socket.gethostname() == 'srv2033673',
            'run as Owner-authorized root on srv2033673')
    require(Path('/var/run/docker.sock').exists(), 'Docker socket missing')
    require(shutil.disk_usage('/var/lib/docker').free >= 2 * 1024**3, 'less than 2 GiB Docker free')
    deployed = (read_env().get('COMPOSE_FILE') == compose_files_value())
    require(static['env_sha256'] == ORIGINAL_ENV_SHA or
            (deployed and static['env_sha256'] == DEPLOYED_ENV_SHA), 'runtime env drift')
    checkpoint_preflight(ORIGINAL_ENV_SHA)
    browser_preflight()
    require(image_id(ROLLBACK_TAG) == BASE_IMAGE, 'rollback image ID mismatch')
    require(image_css_sha(ROLLBACK_TAG) == OLD_CSS_SHA, 'rollback image CSS mismatch')
    config = configured_services()
    initial = snapshot()
    http_ready()
    require(container_css_sha(initial['backend']['id']) in (OLD_CSS_SHA, NEW_CSS_SHA),
            'running backend CSS unexpected')
    runtime_image = read_env().get('CC_UAT_IMAGE')
    if deployed:
        require(OVERRIDE.is_file() and file_sha(OVERRIDE) == OVERRIDE_SHA,
                'persistent backend override missing or changed')
        require(runtime_image != NEW_TAG and image_id(runtime_image) == BASE_IMAGE,
                'global app image drift')
        require_backend_only(config, configured_services(target=True), runtime_image)
        require_default_compose(configured_services(target=True))
        require(initial['backend']['image'] == image_id(NEW_TAG), 'partial prior deployment')
        require(all(initial[s]['image'] == BASE_IMAGE for s in APP if s != 'backend'),
                'other app image drift')
        require(all(config[s]['image'] == runtime_image for s in APP),
                'baseline Compose image drift')
        require(image_css_sha(NEW_TAG) == NEW_CSS_SHA, 'deployed CSS mismatch')
        require(container_css_sha(initial['backend']['id']) == NEW_CSS_SHA, 'deployed backend CSS mismatch')
        run_dir = STATE / 'issue79-runs' / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + f'-{os.getpid()}')
        run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        screenshots = evidence_preflight(run_dir.name)
        result = browser('issue79_unified_autocomplete.cjs', live=True, output=screenshots)
        records = browser('issue79_inventory.cjs')
        report_path = run_dir / 'report.json'
        write_report(report_path, {'status':'LIVE_TECHNICAL_PASS','already_deployed':True,
                                  'image_before':BASE_IMAGE,'image_after':image_id(NEW_TAG),
                                  'browser':result,'inventory':records})
        return {'status':'LIVE_TECHNICAL_PASS', 'already_deployed':True, 'report':str(report_path),
                'image_before':BASE_IMAGE, 'image_after':image_id(NEW_TAG)}
    require(static['env_sha256'] == ORIGINAL_ENV_SHA, 'runtime env changed')
    require(image_id(runtime_image) == BASE_IMAGE, 'configured image mismatch')
    require(all(initial[s]['image'] == BASE_IMAGE for s in APP), 'app image drift')
    require(container_css_sha(initial['backend']['id']) == OLD_CSS_SHA, 'running backend CSS mismatch')
    require(not OVERRIDE.exists(), 'unexpected persistent override exists')
    require(all(config[s]['image'] == runtime_image for s in APP), 'Compose image drift')
    require(config['backend'].get('volumes'), 'backend Site volume missing')
    target_config = configured_services(target=True, override_file=OVERRIDE_SOURCE)
    require_backend_only(config, target_config, runtime_image)
    before_data = browser('issue79_inventory.cjs')
    run_dir = STATE / 'issue79-runs' / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + f'-{os.getpid()}')
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    run_dir.chmod(0o700)
    screenshots = evidence_preflight(run_dir.name)
    report_path = run_dir / 'report.json'
    original = ENV.read_bytes(); original_stat = ENV.stat()
    backup = run_dir / 'runtime.env.before'
    backup.write_bytes(original); backup.chmod(0o600)
    report = {'status':'BLOCKED', 'source_commit':CSS_COMMIT, 'script_sha256':static['script_sha256'],
              'image_before':BASE_IMAGE, 'css_before':OLD_CSS_SHA, 'css_after':NEW_CSS_SHA,
              'env_before_sha256':sha(original), 'compose_sha256':COMPOSE_SHA,
              'inventory_before':before_data, 'backend_before':initial['backend']['id'],
              'technical_before':{s:initial[s]['id'] for s in TECH}, 'rollback_tag':ROLLBACK_TAG}
    write_report(report_path, report)
    switched = False
    try:
        context = run_dir / 'build'; context.mkdir(mode=0o700)
        (context / 'cc_unified_desk.css').write_bytes(git_bytes(f'{CSS_COMMIT}:{CSS_REL}'))
        shutil.copyfile(REPO / 'infra/Dockerfile.issue79', context / 'Dockerfile')
        require(file_sha(context / 'cc_unified_desk.css') == NEW_CSS_SHA, 'build CSS mismatch')
        require(file_sha(context / 'Dockerfile') == RECIPE_SHA, 'build recipe changed')
        existing = command(['docker','image','inspect','--format','{{.Id}}',NEW_TAG],
                           allow_fail=True, label='candidate inspect')
        if existing.returncode:
            command(['docker','build','--network','none','--pull=false','--no-cache',
                     '-t',NEW_TAG,'-f',str(context / 'Dockerfile'),str(context)],label='CSS-only image build')
        new_id = image_id(NEW_TAG)
        require(new_id != BASE_IMAGE and image_css_sha(NEW_TAG) == NEW_CSS_SHA, 'candidate image CSS mismatch')
        old_layers = json.loads(command(['docker','image','inspect',ROLLBACK_TAG],label='base layers').stdout)[0]['RootFS']['Layers']
        new_layers = json.loads(command(['docker','image','inspect',NEW_TAG],label='candidate layers').stdout)[0]['RootFS']['Layers']
        require(new_layers[:len(old_layers)] == old_layers and len(new_layers) == len(old_layers)+1,
                'candidate changes more than one image layer')
        old_config = json.loads(command(['docker','image','inspect',ROLLBACK_TAG],label='base config').stdout)[0]['Config']
        new_config = json.loads(command(['docker','image','inspect',NEW_TAG],label='candidate config').stdout)[0]['Config']
        for field in ('Entrypoint','Cmd','User','Env','WorkingDir','ExposedPorts','Volumes'):
            require(old_config.get(field) == new_config.get(field), f'candidate image changed {field}')
        # Recheck drift immediately before the first runtime/configuration change.
        require(file_sha(ENV) == ORIGINAL_ENV_SHA and snapshot() == initial,
                'runtime changed during preparation')
        require(browser('issue79_inventory.cjs')['sha256'] == before_data['sha256'],
                'synthetic records changed during preparation')
        switched = True
        persist_override()
        persist_compose_file(original, original_stat)
        require(file_sha(OVERRIDE) == OVERRIDE_SHA and
                read_env().get('COMPOSE_FILE') == compose_files_value() and
                read_env().get('CC_UAT_IMAGE') == runtime_image,
                'persistent Compose configuration drift')
        require_backend_only(config, configured_services(target=True), runtime_image)
        require_default_compose(target_config)
        compose('up','-d','--no-deps','--no-build','--force-recreate','backend',
                target=True, label='backend switch')
        http_ready()
        after = snapshot()
        require(after['backend']['image'] == new_id and
                all(after[s] == initial[s] for s in APP if s != 'backend') and
                all(after[s] == initial[s] for s in TECH), 'unexpected service change')
        require(after['backend']['mounts'] == initial['backend']['mounts'], 'Site volume changed')
        require(container_css_sha(after['backend']['id']) == NEW_CSS_SHA, 'backend did not load candidate CSS')
        live = browser('issue79_unified_autocomplete.cjs', live=True, output=screenshots)
        after_data = browser('issue79_inventory.cjs')
        require(after_data['sha256'] == before_data['sha256'], 'synthetic record fingerprint changed')
        report.update(status='LIVE_TECHNICAL_PASS', image_after=new_id,
                      backend_after=after['backend']['id'], browser=live,
                      inventory_after=after_data, env_after_sha256=file_sha(ENV),
                      screenshots=str(screenshots),
                      compose_file=compose_files_value(), override_sha256=OVERRIDE_SHA,
                      technical_after={s:after[s]['id'] for s in TECH})
        write_report(report_path, report)
        return {'status':'LIVE_TECHNICAL_PASS','report':str(report_path),'image_before':BASE_IMAGE,
                'image_after':new_id}
    except Exception as error:
        report['error'] = str(error) if isinstance(error, Stop) else type(error).__name__
        if switched:
            try:
                restore_env(original, original_stat)
                remove_override()
                require(file_sha(ENV) == ORIGINAL_ENV_SHA and not OVERRIDE.exists(),
                        'rollback Compose configuration mismatch')
                require(configured_services() == config, 'rollback Compose services changed')
                compose('up','-d','--no-deps','--no-build','--force-recreate','backend',label='backend rollback')
                http_ready()
                recovered = snapshot()
                require(recovered['backend']['image'] == BASE_IMAGE and
                        recovered['backend']['mounts'] == initial['backend']['mounts'] and
                        all(recovered[s] == initial[s] for s in APP + TECH if s != 'backend'),
                        'rollback service/volume mismatch')
                require(container_css_sha(recovered['backend']['id']) == OLD_CSS_SHA,
                        'rollback backend CSS mismatch')
                require(browser('issue79_inventory.cjs')['sha256'] == before_data['sha256'],
                        'rollback synthetic fingerprint mismatch')
                report.update(status='ROLLED_BACK', image_after=BASE_IMAGE,
                              backend_after=recovered['backend']['id'])
            except Exception as rollback_error:
                report['status'] = 'BLOCKED'
                report['rollback_error'] = (str(rollback_error) if isinstance(rollback_error, Stop)
                                            else type(rollback_error).__name__)
        write_report(report_path, report)
        return {'status':report['status'], 'report':str(report_path), 'reason':report['error']}


def main() -> int:
    os.umask(0o077)
    os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
    parser = argparse.ArgumentParser()
    parser.add_argument('--script-sha256', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        static = static_preflight(args.script_sha256)
        if args.dry_run:
            print(json.dumps({'status':'STATIC_DRY_RUN_PASS','checks':static,
                              'runtime_mutations':'NONE','runtime_preflight':'reserved for Owner sudo run'}))
            return 0
        lock = STATE / '.issue79-deploy.lock'
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Stop('another issue-79 executor holds the lock') from None
            outcome = apply(static)
        print(json.dumps(outcome, sort_keys=True))
        return 0 if outcome['status'] == 'LIVE_TECHNICAL_PASS' else 1
    except Exception as error:
        reason = str(error) if isinstance(error, Stop) else type(error).__name__
        outcome = {'status':'BLOCKED','reason':reason,'runtime_mutations':'NONE'}
        if args.apply and os.geteuid() == 0:
            try:
                run_dir = STATE / 'issue79-runs' / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + f'-{os.getpid()}')
                run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
                report_path = run_dir / 'report.json'
                write_report(report_path, outcome)
                outcome['report'] = str(report_path)
            except Exception:
                pass
        print(json.dumps(outcome))
        return 1


if __name__ == '__main__':
    sys.exit(main())
