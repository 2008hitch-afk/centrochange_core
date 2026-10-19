#!/usr/bin/env python3
"""One gated #139 DEV installation; default dry-run is read-only.

Execution needs an Owner gate file naming the exact application commit and this
script's SHA-256. No automatic second attempt follows a failure. Private raw
backup and browser artifacts stay outside Git. Run with sudo python3 -I.
"""
from __future__ import annotations

import argparse
import ast
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
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

REPO = Path(__file__).resolve().parent.parent
STATE = Path('/home/empv26/.local/state/centrochange-single')
ENV = STATE / 'runtime.env'
SOURCE = 'a03386c41a78692fd4b6d370ec56b1d21d613841'
BASE_SOURCE = '17100e64bfbb178da4ef27278603cca6567037d5'
BASE_IMAGE = 'sha256:47d753955c81033b11317381b5fdc63aa5e438cec304e57e93a0b6c0215b6758'
BASE_TAG = 'centrochange-single:mvp-devfirst-17100e6'
BASE_ENV_SHA = '46cdc4dd93f2e199298b708e25abba1c8d6fbe2a7a5895f2cdfbaa2b3f712600'
BASE_OVERLAY_SHA = 'b5801f44bd42ca45fdf1d6a8097810e36399ab982be67899b98796b7762b5d68'
COMPOSE_SHA = {
    'compose.yaml': '5df3c081f4afff41e6e07222405a4d311bc75eeb1fa97c1045834115e5a0a67d',
    'compose.issue124.yaml': 'ced6e5d2af243bfefbd368ddc46e49de0381bf36c25d05109a13413b59bd7917',
    'compose.uat.yaml': '982fd1cd6253c331482af430a64f9a0b9d1ba205af8a37fd31a1e4cf2a10ade7',
}
COMPOSE_DIR = Path('/tmp/centrochange-issue124/infra')
OVERLAY = REPO / 'infra/compose.issue139_candidate.yaml'
FRONTEND_TEMPLATE = REPO / 'infra/issue139_frontend.conf.template'
IMAGE_FRONTEND_TEMPLATE = '/templates/nginx/frappe.conf.template'
BASE_OVERLAY = STATE / 'compose.goal02_candidate.yaml'
ACTIVE_OVERLAY = STATE / 'compose.issue139_candidate.yaml'
APP = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')
TECH = ('db', 'redis-cache', 'redis-queue')
PROJECT = 'centrochange-dev'
NETWORK_NAME = 'centrochange-dev-net'
LOOPBACK_IP = '127.0.0.1'
IMAGE = 'centrochange-single:mvp-devfirst-a03386c'
PLAYWRIGHT_PACKAGE = Path('/tmp/cc-browser-qa/node_modules/playwright/package.json')
CHROMIUM = Path('/home/empv26/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell')
BROWSER_LIBS = '/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu'
ACTIVE_OVERLAY_SHA = 'feea2e0523fb4e3fbd6acf2f9d711e59dfa0adc8b94541e76af96d46d328cbfb'
APP_PREFIX = 'app/centrochange_core/centrochange_core/'
IMAGE_PREFIX = '/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/'
BENCH = '/home/frappe/frappe-bench'
SITE = 'centrochange.local'
BRANCH_A = 'CC-HTTP-UAT0000001 A'
BRANCH_B = 'CC-HTTP-UAT0000001 B'
RUN_ROOT = STATE / 'issue139-install-runs'
DEPENDENCY_SHA = {
    'infra/browser/mvp_devfirst_readonly.cjs': '1d93bce1d200db259595fc5ba331b3eaa42481fda4e78836b26bf129e1c5261a',
    'infra/browser/issue139_asset_response.cjs': '30ab0eaa9a15674d4d67f42837b25d3e009727ae796b36903a5de315b5dc3b0a',
    'infra/issue139_frontend.conf.template': '8335c04ce44258137b84a511f790f207614e3f25135910fc22aa77f25c81d48b',
    'infra/compose.issue139_candidate.yaml': '520530eaad77a358545ac9db64e3a7c2bb3f49241d0678353e44be49cc6d2202',
    'infra/issue139_asset_cache_gate.py': '417450d4ec5c5639aea8c90d68b4fe6c15a7ed032b91ce3b3228f920e6af4361',
    'infra/goal02_install_one_command.py': '607578830188ab47a5c9d062e0848d5ef2c38c8a5422b503326f30d166592ac5',
    'infra/issue137_safe_security_run.py': '13e820df9f55e92807719751789e50d96187b091f4e515f20c2b196241da9783',
    'infra/security_acceptance.py': '071dfd7d52754855ed22c1e22b865db7174b875510776351b03917eaa7fb2324',
    'infra/browser/issue137_owner_uat_sweep.cjs': '62fa5855a3e8216c18015ba5fc399f614872577a249c615aa44889bb2baf17c9',
    'infra/browser/issue139_native_renderer.cjs': '1f7f2ade73f2eb046ce328f0ebf1f5aebe41fc80fb584f01bd9c4efabc208487',
    'infra/browser/issue139_admin_readonly.cjs': 'ba6b6eb45736018451f5b96a646fdf0255bf4b1ec28ba192b556af788767ad9a',
    'infra/finance_browser_acceptance.py': '1a4b9e9272c45efaf03cbc1aefc2b00a22b804248afd9ea67c1c277bda103e26',
    'infra/fixture_command.py': '8cd336c031c72c8bb3dad974020107e4e771b1e186b6dab01a8613f6f31f7566',
    'infra/reporting_acceptance.py': 'c9ba1eed489a49aa0bc5d578c44db3be2e40ee2f438fa15cbf34a6b7e5537fa0',
    'infra/browser/finance.cjs': '3053e7e926b412198cf59a908e380ae16930a1e434419583993fa59398ee4c1c',
    'infra/browser/native_reports.cjs': 'c8ad7ab0aaf2e90cd30f9bb25cf414370f6d4e95f080e3b51b63fee9550b7860',
    'infra/goal02_targeted_regression.py': '0c61ecef97ce25d9f8ef532a3c0fab1a8cda16256b7b6c7dea7158e5435b3926',
}
PRIVATE_LOG = None
OPERATION_END = None
TIME_LIMIT_ACTIVE = False


class Stop(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Stop(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def host_telemetry():
    vm = dict(line.split(None, 1) for line in Path('/proc/vmstat').read_text().splitlines()
              if line.startswith('oom_kill '))
    pressure = {}
    for resource in ('memory', 'io'):
        line = next(line for line in Path(f'/proc/pressure/{resource}').read_text().splitlines()
                    if line.startswith('full '))
        pressure[resource] = float(next(part.split('=', 1)[1] for part in line.split()
                                        if part.startswith('avg10=')))
    return {'oom_kill': int(vm.get('oom_kill', '0')),
            'memory_full_avg10': pressure['memory'], 'io_full_avg10': pressure['io'],
            'docker_free_bytes': shutil.disk_usage('/var/lib/docker').free}


def check_browser_libraries(output, returncode=0):
    missing = sorted(set(re.findall(r'^\s*(\S+)\s+=>\s+not found\s*$', output, re.MULTILINE)))
    require(returncode == 0 and not missing,
            'W5 Chromium shared libraries unavailable: ' + ', '.join(missing or ['ldd failed']))
    return {'missing_shared_libraries': []}


def browser_runtime_preflight():
    require(PLAYWRIGHT_PACKAGE.is_file() and CHROMIUM.is_file() and os.access(CHROMIUM, os.X_OK),
            'W5 Playwright/Chromium executable unavailable')
    package = json.loads(PLAYWRIGHT_PACKAGE.read_text())
    require(package.get('version') == '1.58.2', 'W5 Playwright version drift')
    result = run(['runuser', '-u', 'empv26', '--', '/usr/bin/env',
                  f'LD_LIBRARY_PATH={BROWSER_LIBS}', 'ldd', str(CHROMIUM)], check=False)
    libraries = check_browser_libraries(result.stdout + '\n' + result.stderr, result.returncode)
    return {'playwright': package['version'], 'chromium': str(CHROMIUM), **libraries}


def run(args, *, input_text=None, cwd=None, check=True):
    timeout = max(1, (OPERATION_END - datetime.now(timezone.utc)).total_seconds()) if TIME_LIMIT_ACTIVE else None
    try:
        result = subprocess.run(args, input=input_text, text=True, cwd=cwd,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise Stop(f'{Path(args[0]).name} exceeded Owner operation deadline') from error
    if check and result.returncode:
        if PRIVATE_LOG:
            private_write(PRIVATE_LOG, (result.stdout + '\n' + result.stderr).encode())
        raise Stop(f'{Path(args[0]).name} exit {result.returncode}; diagnostic retained privately')
    return result


def run_bytes(args):
    timeout = max(1, (OPERATION_END - datetime.now(timezone.utc)).total_seconds()) if TIME_LIMIT_ACTIVE else None
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise Stop(f'{Path(args[0]).name} exceeded Owner operation deadline') from error
    if result.returncode:
        if PRIVATE_LOG:
            private_write(PRIVATE_LOG, result.stderr)
        raise Stop(f'{Path(args[0]).name} exit {result.returncode}; binary output retained privately')
    return result.stdout


def old_probe():
    path = REPO / 'infra/goal02_install_one_command.py'
    spec = importlib.util.spec_from_file_location('goal02_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def asset_cache_probe():
    spec = importlib.util.spec_from_file_location('issue139_assets',
                                                  REPO / 'infra/issue139_asset_cache_gate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.probe()


def settings():
    return parse_settings(ENV.read_bytes())


def parse_settings(raw):
    lines = raw.decode().splitlines()
    value = dict(line.split('=', 1) for line in lines if '=' in line and not line.startswith('#'))
    require(value.get('SITE_NAME') == SITE and value.get('HTTP_PORT') == '8082', 'Site/port drift')
    return value


def compose_files(value):
    files = [Path(p) for p in value['COMPOSE_FILE'].split(':')]
    require(files == [*(COMPOSE_DIR / n for n in COMPOSE_SHA), BASE_OVERLAY, ACTIVE_OVERLAY],
            'ordinary Compose precedence drift')
    return files


def compose_config(files, extra=None):
    args = ['docker', 'compose', '--env-file', str(ENV), '-p', PROJECT]
    for path in files + ([extra] if extra else []):
        args += ['-f', str(path)]
    return json.loads(run(args + ['config', '--format', 'json']).stdout)


def compose(files, *args):
    cmd = ['docker', 'compose', '--env-file', str(ENV), '-p', PROJECT]
    for path in files:
        cmd += ['-f', str(path)]
    return run(cmd + list(args))


def compare_compose(before, proposed):
    require(before.keys() == proposed.keys(), 'Compose top-level drift')
    for key in before:
        if key != 'services':
            require(before[key] == proposed[key], f'Compose {key} drift')
    require(before['services'].keys() == proposed['services'].keys(), 'Compose service set drift')
    for name, prior in before['services'].items():
        expected = json.loads(json.dumps(prior))
        if name in APP:
            expected['image'] = IMAGE
            if name == 'frontend':
                network = expected['networks'][NETWORK_NAME] or {}
                network['aliases'] = ['centrochange.local']
                expected['networks'][NETWORK_NAME] = network
        require(proposed['services'][name] == expected, f'{name}: indirect Compose change')


def changed_files():
    result = run(['git', 'diff', '--name-status', BASE_SOURCE, SOURCE, '--', APP_PREFIX], cwd=REPO)
    rows = [line.split('\t', 1) for line in result.stdout.splitlines()]
    require(rows and all(status in ('M', 'A') and path.startswith(APP_PREFIX)
                         for status, path in rows), 'application delta includes deletion or unexpected status')
    return [path for _, path in rows]


def static_gate(executor_sha=None):
    if executor_sha:
        require(file_sha(__file__) == executor_sha, 'executor SHA mismatch')
    for relative, digest in DEPENDENCY_SHA.items():
        require(file_sha(REPO / relative) == digest, f'{relative}: dependency SHA mismatch')
    require(run(['git', 'rev-parse', SOURCE], cwd=REPO).stdout.strip() == SOURCE,
            'application source commit missing')
    require(run(['git', 'merge-base', SOURCE, 'HEAD'], cwd=REPO).stdout.strip() == SOURCE,
            'checkout no longer descends from candidate source')
    require(not run(['git', 'diff', '--name-only', SOURCE, 'HEAD', '--', APP_PREFIX], cwd=REPO).stdout,
            'application changed after candidate source pin')
    require(run(['git', 'merge-base', BASE_SOURCE, SOURCE], cwd=REPO).stdout.strip() == BASE_SOURCE,
            'candidate does not descend from installed source')
    excluded = '382042c493dc07db142ce1e1abc2159060444f49'
    require(run(['git', 'merge-base', excluded, SOURCE], cwd=REPO).stdout.strip() != excluded,
            '#78/#128 unexpectedly included')
    if executor_sha:
        require(not run(['git', 'status', '--porcelain'], cwd=REPO).stdout.strip(),
                'executor checkout not clean')
    return changed_files()


def branch_probe(module):
    source = '''import json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
field=frappe.db.has_column("Branch","cc_operational")
rows=frappe.get_all("Branch",fields=["name","branch"]+(["cc_operational"] if field else []),order_by="name",limit_page_length=0)
print("CC_BRANCHES="+json.dumps({"rows":rows,"field_present":field,"manager_enabled":bool(frappe.db.get_value("User",MANAGER,"enabled")),"manager_roles":frappe.get_roles(MANAGER),"native_backup_encryption":bool(frappe.get_system_settings("encrypt_backup"))}))
frappe.db.rollback();frappe.destroy()
'''
    fixture = json.loads((STATE / 'demo-owner.json').read_text())
    manager = (fixture.get('fixture') or fixture)['users']['m']['name']
    output = module.backend_python(source.replace('MANAGER', json.dumps(manager)))
    return json.loads(next(x.split('=', 1)[1] for x in output.splitlines() if x.startswith('CC_BRANCHES=')))


def schema_fingerprint(module):
    source = '''import hashlib,json,frappe,pathlib
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
types=("Custom Field","Custom DocPerm","Property Setter")
rows={dt:frappe.get_all(dt,fields=["name","modified"],order_by="name",limit_page_length=0) for dt in types}
rows["branch_columns"]=sorted(frappe.db.get_table_columns("Branch"))
value=json.dumps(rows,sort_keys=True,default=str,separators=(",",":"))
config=pathlib.Path("centrochange.local/site_config.json").read_bytes()
print("CC_SCHEMA="+json.dumps({"sha256":hashlib.sha256(value.encode()).hexdigest(),"config_sha256":hashlib.sha256(config).hexdigest(),"counts":{dt:len(rows[dt]) for dt in types}}))
frappe.db.rollback();frappe.destroy()
'''
    output = module.backend_python(source)
    return json.loads(next(x.split('=', 1)[1] for x in output.splitlines()
                           if x.startswith('CC_SCHEMA=')))


def permission_fingerprint(module):
    source = '''import hashlib,json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
rights=("read","write","create","delete","submit","cancel","amend","report","export","import","share","print","email","select")
spec={"Custom DocPerm":["parent","role","permlevel",*rights],"Has Role":["parent","role"],"User Permission":["user","allow","for_value","apply_to_all_doctypes"],"DocShare":["user","share_doctype","share_name","read","write","share","submit"]}
rows={}
for doctype,fields in spec.items():
    values=frappe.get_all(doctype,fields=fields,limit_page_length=0)
    rows[doctype]=sorted([tuple(str(row.get(field) or "") for field in fields) for row in values])
value=json.dumps(rows,sort_keys=True,separators=(",",":"))
print("CC_PERMISSIONS="+json.dumps({"sha256":hashlib.sha256(value.encode()).hexdigest(),"counts":{dt:len(v) for dt,v in rows.items()}}))
frappe.db.rollback();frappe.destroy()
'''
    output = module.backend_python(source)
    return json.loads(next(x.split('=', 1)[1] for x in output.splitlines()
                           if x.startswith('CC_PERMISSIONS=')))


def preflight(executor_sha=None):
    require(socket.gethostname() == 'srv2033673' and os.geteuid() == 0 and sys.flags.isolated,
            'requires sudo python3 -I on approved host')
    require(file_sha(ENV) == BASE_ENV_SHA and ENV.stat().st_mode & 0o077 == 0,
            'private runtime env changed or unsafe')
    require(file_sha(BASE_OVERLAY) == BASE_OVERLAY_SHA, 'base candidate overlay changed')
    require(ACTIVE_OVERLAY.is_file() and file_sha(ACTIVE_OVERLAY) == ACTIVE_OVERLAY_SHA
            and ACTIVE_OVERLAY.stat().st_mode & 0o077 == 0,
            'active candidate overlay changed or has unsafe permissions')
    for name, digest in COMPOSE_SHA.items():
        require(file_sha(COMPOSE_DIR / name) == digest, f'{name} drift')
    require(shutil.disk_usage('/var/lib/docker').free >= 8 * 1024**3, 'free disk below 8 GiB')
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line)
    require(int(mem['MemAvailable'].split()[0]) >= 3 * 1024**2, 'MemAvailable below 3 GiB')
    require(all(shutil.which(x) for x in ('docker', 'gpg', 'git', 'node')),
            'required build, backup or browser tool missing')
    fixture = STATE / 'demo-owner.json'
    require(fixture.is_file() and fixture.stat().st_mode & 0o077 == 0,
            'private synthetic account fixture unsafe or missing')
    browser_runtime = browser_runtime_preflight()
    evidence_root = STATE / 'browser-evidence'
    require(evidence_root.is_dir() and evidence_root.stat().st_uid == pwd.getpwnam('empv26').pw_uid
            and evidence_root.stat().st_mode & 0o077 == 0,
            'private browser evidence directory unsafe')
    value = settings()
    files = compose_files(value)
    baseline = compose_config(files)
    compare_compose(baseline, compose_config(files, OVERLAY))
    module = old_probe()
    services = module.snapshot()
    require(all(services[n]['image'] == BASE_IMAGE for n in APP), 'app image drift')
    baseline_image = json.loads(run(['docker', 'image', 'inspect', BASE_IMAGE]).stdout)[0]
    identity = run(['docker', 'run', '--rm', '--network=none', '--read-only', '--entrypoint', 'sh', BASE_TAG, '-c', 'id -u frappe; id -g frappe']).stdout.splitlines()
    require(identity == ['1000', '0'], 'pinned runtime frappe uid/gid drift')
    require(baseline_image['Config']['Labels'].get('centrochange.source') == BASE_SOURCE,
            'installed image source label drift')
    require(run(['docker', 'image', 'inspect', '--format', '{{.Id}}', BASE_TAG]).stdout.strip()
            == BASE_IMAGE, 'installed image tag drift')
    require(module.hooks() == module.GUARDS, 'six guard/language hooks drift')
    css = 'centro_change_core/page/cc_unified_desk/cc_unified_desk.css'
    require(module.app_hashes([css])[css] ==
            'f3ab9d5ddf9f15e63b576a5656331169067af6d722cdea6d79b8c5ca644fe27d',
            '#79 accepted autocomplete CSS changed')
    cache = asset_cache_probe()
    require(not cache['mismatch_keys_after'] and cache['all_files_present'],
            'CSS P0 cache repair regressed; no second invalidation authorized')
    sites_output = module.backend_python('''import json,pathlib
p=pathlib.Path("/home/frappe/frappe-bench/sites")
print("CC_SITES="+json.dumps(sorted(x.name for x in p.iterdir() if (x/"site_config.json").is_file())))
''')
    sites = json.loads(next(x.split('=', 1)[1] for x in sites_output.splitlines()
                            if x.startswith('CC_SITES=')))
    require(sites == [SITE], 'single Site inventory drift')
    data = module.runtime_fingerprint()
    branch = branch_probe(module)
    require({x['name'] for x in branch['rows']} == {BRANCH_A, BRANCH_B} and len(branch['rows']) == 2,
            'Branch inventory changed')
    require(branch['field_present'], 'installed baseline lacks operational-center migration')
    require({row['name']: int(row['cc_operational']) for row in branch['rows']} ==
            {BRANCH_A: 1, BRANCH_B: 0}, 'operational center state drift')
    require(branch['manager_enabled'] and 'CC Manager' in branch['manager_roles'],
            'demo manager unavailable for audited activation')
    require(not branch['native_backup_encryption'],
            'native backup encryption differs from verified restore path')
    require(value.get('CC_UAT_IMAGE') == 'centrochange-single:goal02-fixture-d1892e0',
            'base application env drift')
    require(ACTIVE_OVERLAY.is_file() and file_sha(ACTIVE_OVERLAY) == ACTIVE_OVERLAY_SHA
            and ACTIVE_OVERLAY.stat().st_mode & 0o077 == 0,
            'active candidate overlay drift')
    schema = schema_fingerprint(module)
    permissions = permission_fingerprint(module)
    return {'files': files, 'baseline': baseline, 'services': services, 'data': data,
            'schema': schema, 'permissions': permissions,
            'branch': branch, 'module': module, 'settings': value,
            'overlay_bytes': ACTIVE_OVERLAY.read_bytes(), 'overlay_stat': ACTIVE_OVERLAY.stat(),
            'host': host_telemetry(), 'browser_runtime': browser_runtime}


def private_dir():
    RUN_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(RUN_ROOT.stat().st_mode & 0o077 == 0, 'private run directory unsafe')
    path = RUN_ROOT / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + f'-{os.getpid()}')
    path.mkdir(mode=0o700)
    return path


def validate_owner_gate(path, executor_sha, *, recovery=False):
    require(path.stat().st_mode & 0o077 == 0, 'Owner gate file mode unsafe')
    gate = json.loads(path.read_text())
    required = {'issue', 'candidate', 'executor_sha256', 'authorize',
                'window_start_utc', 'operation_deadline_utc', 'recovery_deadline_utc'}
    require(set(gate) == required and gate['issue'] == 139 and gate['candidate'] == SOURCE
            and gate['executor_sha256'] == executor_sha
            and gate['authorize'] == 'DEV_FIRST_MVP_SCOPED_UPDATE_AND_LIVE_TESTS',
            'Owner gate does not match exact single installation')
    def parse(name):
        value = datetime.fromisoformat(gate[name].replace('Z', '+00:00'))
        require(value.tzinfo is not None, 'Owner gate time must include UTC timezone')
        return value.astimezone(timezone.utc)
    start, operation_end, recovery_end = (parse(name) for name in
        ('window_start_utc', 'operation_deadline_utc', 'recovery_deadline_utc'))
    now = datetime.now(timezone.utc)
    require(start <= now < (recovery_end if recovery else operation_end),
            'Owner gate window is not active')
    require(timedelta(0) < operation_end - start <= timedelta(hours=4)
            and timedelta(0) < recovery_end - operation_end <= timedelta(hours=1),
            'Owner gate exceeds 4h operation plus 1h recovery')
    return {'operation_end': operation_end, 'recovery_end': recovery_end}


def private_write(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.issue139-', delete=False) as stream:
        tmp = Path(stream.name)
        os.fchmod(stream.fileno(), 0o600)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def report_write(path, report):
    private_write(path, (json.dumps(report, sort_keys=True, indent=2) + '\n').encode())


def build_candidate(paths, output):
    context = output / 'build'
    context.mkdir(mode=0o700)
    commands = [f'FROM {BASE_TAG}', 'USER frappe', f'WORKDIR {BENCH}']
    for source in paths:
        relative = source.removeprefix(APP_PREFIX)
        target = context / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (REPO / source).read_bytes()
        require(sha(data) == sha(run_bytes(['git', '-C', str(REPO), 'show', f'{SOURCE}:{source}'])),
                f'{relative}: source content drift')
        target.write_bytes(data)
        commands.append(f'COPY --chown=1000:0 {relative} apps/centrochange_core/centrochange_core/{relative}')
    # The same frontend image serves host 8082 but listens on container 8080.
    # Frappe's pinned realtime worker fetches its Origin internally; install the
    # exact, versioned nginx template without patching a running container.
    template = FRONTEND_TEMPLATE.read_bytes()
    require(template.count(b'proxy_set_header Origin http://${FRAPPE_SITE_NAME_HEADER}:${NGINX_LISTEN_PORT};') == 1,
            'frontend internal Origin route missing or ambiguous')
    (context / 'issue139_frontend.conf.template').write_bytes(template)
    commands.append('USER root')
    commands.append(f'COPY issue139_frontend.conf.template {IMAGE_FRONTEND_TEMPLATE}')
    commands.append('USER frappe')
    commands.append(f'LABEL centrochange.source="{SOURCE}" centrochange.issue="139"')
    (context / 'Dockerfile').write_text('\n'.join(commands) + '\n')
    run(['docker', 'build', '--pull=false', '--network=none', '-t', IMAGE,
         '-f', str(context / 'Dockerfile'), str(context)])
    observed = json.loads(run(['docker', 'image', 'inspect', IMAGE]).stdout)[0]
    require(observed['Config']['Labels']['centrochange.source'] == SOURCE,
            'candidate source label mismatch')
    base = json.loads(run(['docker', 'image', 'inspect', BASE_IMAGE]).stdout)[0]
    for key in ('Entrypoint', 'Cmd', 'Env', 'ExposedPorts', 'Volumes'):
        require(observed['Config'].get(key) == base['Config'].get(key),
                f'candidate runtime configuration drift: {key}')
    require(observed['RootFS']['Layers'][:len(base['RootFS']['Layers'])] == base['RootFS']['Layers'],
            'candidate does not derive from verified baseline')
    payload = json.dumps([source.removeprefix(APP_PREFIX) for source in paths])
    check = 'import hashlib,json,pathlib; p=pathlib.Path(' + repr(IMAGE_PREFIX) + \
            '); print(json.dumps({x:hashlib.sha256((p/x).read_bytes()).hexdigest() for x in ' + payload + '}))'
    actual = json.loads(run(['docker', 'run', '--rm', '--network=none', '--read-only',
                             '--entrypoint', 'python', IMAGE, '-c', check]).stdout)
    require(all(actual[p.removeprefix(APP_PREFIX)] == file_sha(REPO / p) for p in paths),
            'candidate application file hashes mismatch')
    observed_template = run_bytes(['docker', 'run', '--rm', '--network=none', '--read-only',
                                   '--entrypoint', 'cat', IMAGE, IMAGE_FRONTEND_TEMPLATE])
    require(sha(observed_template) == sha(template), 'candidate nginx template mismatch')
    return observed['Id']


def backup(output):
    """Native four-part backup, encrypted to a private host checkpoint."""
    site_dir = f'{BENCH}/sites/{SITE}/private/backups'
    token = output.name
    names = {'db': f'{token}-database.sql.gz', 'public': f'{token}-files.tgz',
             'private': f'{token}-private-files.tgz', 'config': f'{token}-site_config.json'}
    paths = {kind: f'{site_dir}/{name}' for kind, name in names.items()}
    for path in paths.values():
        run(['docker', 'exec', 'centrochange-dev-backend-1', 'test', '!', '-e', path])
    manifest = {}
    try:
        command = ['docker', 'exec', '-w', BENCH, 'centrochange-dev-backend-1',
                   'bench', '--site', SITE, 'backup', '--with-files', '--compress',
                   '--backup-path-db', paths['db'], '--backup-path-files', paths['public'],
                   '--backup-path-private-files', paths['private'], '--backup-path-conf', paths['config']]
        run(command)
        key = output / 'backup.key'
        private_write(key, secrets.token_urlsafe(48).encode() + b'\n')
        for kind, source in paths.items():
            raw = output / names[kind]
            run(['docker', 'cp', f'centrochange-dev-backend-1:{source}', str(raw)])
            os.chmod(raw, 0o600)
            payload = raw.read_bytes()
            encrypted = output / (names[kind] + '.gpg')
            run(['gpg', '--batch', '--yes', '--pinentry-mode', 'loopback',
                 '--passphrase-file', str(key), '--symmetric', '--cipher-algo', 'AES256',
                 '--output', str(encrypted), str(raw)])
            decrypted = run_bytes(['gpg', '--batch', '--quiet', '--pinentry-mode', 'loopback',
                                   '--passphrase-file', str(key), '--decrypt', str(encrypted)])
            require(sha(decrypted) == sha(payload), f'{kind}: encrypted backup verify failed')
            manifest[kind] = {'file': encrypted.name, 'sha256': sha(payload), 'bytes': len(payload)}
            raw.unlink()
        report_write(output / 'backup-manifest.json', manifest)
    finally:
        # A backup failure must not leave plaintext dump/files in the shared Site.
        cleanup_failures = []
        for remote in paths.values():
            result = run(['docker', 'exec', 'centrochange-dev-backend-1', 'rm', '-f', '--', remote], check=False)
            if result.returncode:
                cleanup_failures.append(remote)
        require(not cleanup_failures, 'exact temporary Site backup cleanup failed')
    return manifest


def restore_backup(output, manifest, root_password):
    """Restore the original Site from the verified encrypted native checkpoint."""
    # The pinned image has uid 1000 (frappe) with gid 0 (root), and no
    # group named frappe. Refuse a changed identity before copying any files.
    identity = run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1',
                    'id', '-u', 'frappe']).stdout.strip()
    group = run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1',
                 'id', '-g', 'frappe']).stdout.strip()
    root_group = run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1',
                      'getent', 'group', 'root']).stdout.strip()
    frappe_group = run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1',
                        'getent', 'group', 'frappe'], check=False)
    require(identity == '1000' and group == '0' and root_group.startswith('root:x:0:')
            and frappe_group.returncode != 0, 'rollback image Unix identity drift')
    recovered = {}
    for kind, item in manifest.items():
        encrypted = output / item['file']
        plaintext = run_bytes(['gpg', '--batch', '--quiet', '--pinentry-mode', 'loopback',
                               '--passphrase-file', str(output / 'backup.key'), '--decrypt', str(encrypted)])
        require(sha(plaintext) == item['sha256'], f'{kind}: backup changed before restore')
        local = output / ('restore-' + kind + ('.sql.gz' if kind == 'db' else
                                              '.tgz' if kind != 'config' else '.json'))
        private_write(local, plaintext)
        remote = f'{BENCH}/sites/{SITE}/private/backups/{local.name}'
        run(['docker', 'cp', str(local), f'centrochange-dev-backend-1:{remote}'])
        run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1',
             'chown', 'frappe:root', remote])
        run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1', 'chmod', '600', remote])
        recovered[kind] = remote
        local.unlink()
    source = '''import json,sys,frappe
from frappe.commands.site import _restore
password=json.loads(sys.stdin.read())["db_root_password"]
frappe.init("centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
_restore(site="centrochange.local",sql_file_path=PATH_DB,db_root_password=password,
         with_public_files=PATH_PUBLIC,with_private_files=PATH_PRIVATE,force=True)
'''
    source = (source.replace('PATH_DB', repr(recovered['db']))
                    .replace('PATH_PUBLIC', repr(recovered['public']))
                    .replace('PATH_PRIVATE', repr(recovered['private'])))
    # Password is supplied through stdin to a fixed interpreter, never argv/logs.
    wrapper = 'import subprocess,sys; code=' + repr(source) + '; ' + \
              'payload=sys.stdin.read(); subprocess.run([sys.executable,"-c",code],input=payload,text=True,check=True)'
    run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', f'{BENCH}/sites',
         'centrochange-dev-backend-1', f'{BENCH}/env/bin/python', '-c', wrapper],
        input_text=json.dumps({'db_root_password': root_password}))
    config_bytes = run_bytes(['gpg', '--batch', '--quiet', '--pinentry-mode', 'loopback',
                              '--passphrase-file', str(output / 'backup.key'), '--decrypt',
                              str(output / manifest['config']['file'])])
    config = output / 'restore-site-config.json'
    private_write(config, config_bytes)
    run(['docker', 'cp', str(config),
         f'centrochange-dev-backend-1:{BENCH}/sites/{SITE}/site_config.json'])
    run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1', 'chown', 'frappe:root',
         f'{BENCH}/sites/{SITE}/site_config.json'])
    run(['docker', 'exec', '-u', '0', 'centrochange-dev-backend-1', 'chmod', '600',
         f'{BENCH}/sites/{SITE}/site_config.json'])
    config.unlink()
    for remote in recovered.values():
        run(['docker', 'exec', 'centrochange-dev-backend-1', 'rm', '--', remote])


def select_candidate_overlay(pre):
    require(str(ACTIVE_OVERLAY) in pre['settings'].get('COMPOSE_FILE', '').split(':'),
            'active candidate overlay is not selected by ordinary Compose')
    prior = ACTIVE_OVERLAY.stat()
    private_write(ACTIVE_OVERLAY, OVERLAY.read_bytes())
    os.chmod(ACTIVE_OVERLAY, prior.st_mode & 0o777)
    os.chown(ACTIVE_OVERLAY, prior.st_uid, prior.st_gid)
    require(file_sha(ACTIVE_OVERLAY) == file_sha(OVERLAY), 'persistent candidate overlay hash mismatch')


def source_probe(module, paths):
    relative = [p.removeprefix(APP_PREFIX) for p in paths]
    actual = module.app_hashes(relative)
    require(all(actual[p] == file_sha(REPO / APP_PREFIX / p) for p in relative),
            'running candidate app source mismatch')


def asset_probe(paths):
    cache = asset_cache_probe()
    require(not cache['mismatch_keys_after'] and cache['all_files_present'],
            'Frappe asset manifest/cache mismatch')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    checked = 0
    for source in paths:
        relative = source.removeprefix(APP_PREFIX)
        if not relative.startswith('public/'):
            continue
        path = '/assets/centrochange_core/' + relative.removeprefix('public/')
        request = urllib.request.Request(f'http://{LOOPBACK_IP}:8082' + path,
                                         headers={'Host': SITE, 'Cache-Control': 'no-cache'})
        with opener.open(request, timeout=15) as response:
            require(response.status == 200 and sha(response.read()) == file_sha(REPO / source),
                    f'{relative}: served asset mismatch')
        checked += 1
    return {'manifest_mapping_count': cache['manifest_count'], 'direct_assets_verified': checked}


def realtime_probe():
    rendered = run(['docker', 'exec', 'centrochange-dev-frontend-1',
                    'cat', '/etc/nginx/conf.d/frappe.conf']).stdout
    require('proxy_set_header Origin http://centrochange.local:8080;' in rendered
            and 'proxy_set_header Host centrochange.local;' in rendered
            and 'if ($cc_realtime_public_origin_valid = 0) { return 403; }' in rendered,
            'running frontend realtime proxy differs from pinned route')
    internal = run(['docker', 'exec', 'centrochange-dev-websocket-1', 'node', '-e',
                    'fetch("http://centrochange.local:8080/api/method/frappe.realtime.get_user_info")'
                    '.then(r=>process.exit(r.status<500?0:2)).catch(()=>process.exit(3))'],
                   check=False)
    require(internal.returncode == 0, 'websocket cannot reach Frappe via internal port 8080')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f'http://{LOOPBACK_IP}:8082/socket.io/?EIO=4&transport=polling'
    for host, origin, expected in [
        ('centrochange.local:8082', 'http://centrochange.local:8082', 200),
        ('127.0.0.1:8082', 'http://127.0.0.1:8082', 200),
        ('centrochange.local:8082', 'http://127.0.0.1:8082', 403),
        ('centrochange.local:8082', 'http://invalid.example', 403),
        ('invalid.example:8082', 'http://invalid.example:8082', 403),
    ]:
        request = urllib.request.Request(url, headers={'Host': host, 'Origin': origin})
        try:
            with opener.open(request, timeout=10) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
        require(status == expected, f'realtime Origin gate returned {status}, expected {expected}')
    return {'internal_frontend_port': 8080, 'public_browser_port': 8082,
            'canonical_and_tunnel_origins': 200, 'foreign_and_mismatched_origins': 403}


def security_command(expected_data, expected_communication, *, isolated_project=None, env_file=None):
    # The child runner refuses non-isolated Python. sys.executable alone does
    # not preserve -I from this executor's own command line.
    command = [sys.executable, '-I', str(REPO / 'infra/issue137_safe_security_run.py'),
               '--expected-data', expected_data,
               '--expected-communication', expected_communication]
    if isolated_project:
        require(isolated_project == 'cc139-w5-isolated' and env_file is not None,
                'unsupported isolated security target')
        command += ['--isolated-project', isolated_project, '--env-file', str(env_file)]
    return command


def browser(script, output, *, role=None, width=None):
    account = pwd.getpwnam('empv26')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chown(output, account.pw_uid, account.pw_gid)
    env = ['PATH=/usr/sbin:/usr/bin:/sbin:/bin', 'HOME=/home/empv26',
           'NODE_PATH=/tmp/cc-browser-qa/node_modules',
           'LD_LIBRARY_PATH=/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
           'CC_BASE_URL=http://centrochange.local:8082',
           f'CC_ISSUE137_FIXTURE={STATE / "demo-owner.json"}',
           f'CC_ISSUE137_OUTPUT={output}']
    if role:
        env.append(f'CC_ISSUE137_ROLE={role}')
    if width:
        env.append(f'CC_ISSUE137_WIDTH={width}')
    result = run(['runuser', '-u', 'empv26', '--', '/usr/bin/env', *env,
                  'node', str(REPO / 'infra/browser' / script)], cwd=REPO, check=False)
    if result.returncode:
        private_write(output / 'runner-error.log', result.stderr.encode())
        raise Stop(f'{script} exit {result.returncode}; private diagnostic saved')
    return result.stdout


def w5_readonly(output):
    total = 0
    summary = {}
    for role in 'msabcft':
        for width in (1440, 390):
            folder = output / f'sweep-{role}-{width}'
            browser('issue137_owner_uat_sweep.cjs', folder, role=role, width=width)
            result = json.loads((folder / f'issue137-{role}-{width}.json').read_text())
            total += result['uniqueRoutes']
            require(result['summary']['fail'] == 0 and not result['unexpectedMutations'],
                    f'{role}/{width}: browser route or mutation failure')
            summary[f'{role}-{width}'] = result['summary']
    require(total >= 128, f'W5 route coverage below 128: {total}')
    for width in (1440, 390):
        folder = output / f'native-{width}'
        browser('issue139_native_renderer.cjs', folder, width=width)
        result = json.loads((folder / f'issue139-native-{width}.json').read_text())
        require(len(result['results']) == 11 and result['summary']['fail'] == 0,
                f'{width}: native List/Form failure')
    return {'routes': total, 'roles': summary, 'native_list_form_pairs': 22}


def live_acceptance(output, script_name, args):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    result = run([sys.executable, str(REPO / 'infra' / script_name), *args],
                 cwd=REPO / 'infra', check=False)
    private_write(output / 'runner.log', (result.stdout + '\n' + result.stderr).encode())
    if result.returncode == 0:
        return {'status': 'PASS', 'result_lines': len(result.stdout.splitlines())}
    # Only explicitly diagnosed preparation/render timeouts are noncritical.
    # Assertions, authorization errors, unknown failures and cleanup failures
    # remain fail-closed. A separate mandatory invariant gate follows even FAIL.
    log = result.stdout + '\n' + result.stderr
    cleanup = any(line.strip().startswith('{') and '"cleanup": "PASS"' in line
                  for line in result.stdout.splitlines())
    validation = ('FixtureCommandError:' in log and 'frappe.exceptions.ValidationError:' in log
                  and 'rollback failed' not in log.lower())
    browser_logs = ''.join(p.read_text() for p in output.glob('*.log') if p.name != 'runner.log')
    timeout = 'TimeoutError:' in browser_logs and 'AssertionError' not in browser_logs
    application_validation = False
    for line in log.splitlines():
        if line.startswith('AssertionError: ('):
            try:
                failure = ast.literal_eval(line.removeprefix('AssertionError: '))
                application_validation = (isinstance(failure, tuple) and len(failure) == 5
                    and failure[1:4] == (417, 200, 'ValidationError'))
            except (ValueError, SyntaxError):
                pass
    require(cleanup and (validation or timeout or application_validation),
            f'{script_name}: unclassified or critical failure; private diagnostics retained')
    return {'status': 'BLOCKED', 'classification': 'fixture_validation' if validation else ('application_validation' if application_validation else 'browser_timeout'),
            'diagnostic': str(output / 'runner.log'), 'cleanup': 'PASS'}


def functional_gate(output, script_name, args, pre, candidate_id):
    result = live_acceptance(output, script_name, args)
    # Never let a noncritical test verdict bypass dataset or security checks.
    require(PROJECT == 'centrochange-dev', 'DEV-FIRST is restricted to DEV')
    require(pre['module'].runtime_fingerprint() == pre['data'], 'functional cleanup changed baseline data')
    require(permission_fingerprint(pre['module']) == pre['permissions'], 'functional permission drift')
    require(pre['module'].hooks() == pre['module'].GUARDS, 'functional security hook drift')
    observed = pre['module'].snapshot()
    require(all(observed[n]['image'] == candidate_id for n in APP), 'essential application image drift')
    require(all(observed[n] == pre['services'][n] for n in TECH), 'technical service drift')
    pre['module'].http_ready()
    return result


def restore_services(pre, original_env, env_stat, *, data_backup=None, output=None):
    """One rollback; caller never retries installation after this function."""
    original_files = pre['files']
    active_files = original_files
    compose(active_files, 'stop', '-t', '60', *APP)
    private_write(ACTIVE_OVERLAY, pre['overlay_bytes'])
    os.chmod(ACTIVE_OVERLAY, pre['overlay_stat'].st_mode & 0o777)
    os.chown(ACTIVE_OVERLAY, pre['overlay_stat'].st_uid, pre['overlay_stat'].st_gid)
    require(ENV.read_bytes() == original_env, 'runtime.env changed unexpectedly; refusing rollback drift')
    compose(original_files, 'up', '-d', '--no-deps', '--no-build', '--force-recreate', 'backend')
    if data_backup:
        require(output is not None, 'database backup path missing')
        password = pre['settings'].get('DB_PASSWORD', '').strip().strip('"').strip("'")
        require(password, 'private database root password unavailable')
        restore_backup(output, data_backup, password)
        compose(original_files, 'up', '-d', '--no-deps', '--no-build', '--force-recreate', 'backend')
    compose(original_files, 'up', '-d', '--no-deps', '--no-build', '--force-recreate',
            'websocket', 'queue-short', 'queue-long', 'scheduler', 'frontend')
    pre['module'].http_ready()
    observed = pre['module'].snapshot()
    require(all(observed[name]['image'] == pre['services'][name]['image'] for name in APP + TECH),
            'rollback image mapping incomplete')
    require(pre['module'].runtime_fingerprint() == pre['data'],
            'rollback did not restore Owner/Communication fingerprint')
    require(schema_fingerprint(pre['module']) == pre['schema'],
            'rollback did not restore schema/config fingerprint')
    require(permission_fingerprint(pre['module']) == pre['permissions'],
            'rollback did not restore permission fingerprint')
    require(pre['module'].hooks() == pre['module'].GUARDS, 'rollback guard hooks changed')
    return observed


def execute(executor_sha, gate_path):
    global PRIVATE_LOG, OPERATION_END, TIME_LIMIT_ACTIVE
    paths = static_gate(executor_sha)
    window = validate_owner_gate(gate_path, executor_sha)
    OPERATION_END = window['operation_end']
    pre = preflight(executor_sha)
    require(run(['docker', 'image', 'inspect', IMAGE], check=False).returncode != 0,
            'candidate image tag already exists; no retry')
    output = private_dir()
    PRIVATE_LOG = output / 'last-command.log'
    report = {'status': 'BLOCKED', 'candidate': SOURCE, 'executor_sha256': executor_sha,
              'baseline_image': BASE_IMAGE, 'baseline_data_sha256': pre['data']['sha256'],
              'baseline_communication_sha256': pre['data']['communication_sha256'], 'tests': {},
              'baseline_schema': pre['schema'], 'baseline_permissions': pre['permissions'],
              'baseline_host': pre['host'],
              'operation_deadline_utc': window['operation_end'].isoformat(),
              'recovery_deadline_utc': window['recovery_end'].isoformat(),
              'checkpoint': str(output),
              'runtime_mutations': []}
    report_path = output / 'report.json'
    report_write(report_path, report)
    env_bytes = ENV.read_bytes()
    env_stat = ENV.stat()
    private_write(output / 'runtime.env.checkpoint', env_bytes)
    for path in pre['files']:
        private_write(output / (path.name + '.checkpoint'), path.read_bytes())
    private_write(output / (ACTIVE_OVERLAY.name + '.checkpoint'), pre['overlay_bytes'])
    checkpoint = {'files': [str(path) for path in pre['files']],
                  'services': pre['services'], 'data': pre['data'],
                  'schema': pre['schema'], 'permissions': pre['permissions'],
                  'overlay': {'path': str(ACTIVE_OVERLAY), 'mode': pre['overlay_stat'].st_mode & 0o777,
                              'uid': pre['overlay_stat'].st_uid, 'gid': pre['overlay_stat'].st_gid}}
    report_write(output / 'checkpoint.json', checkpoint)
    site_config = f'{BENCH}/sites/{SITE}/site_config.json'
    run(['docker', 'cp', f'centrochange-dev-backend-1:{site_config}',
         str(output / 'site_config.checkpoint.json')])
    os.chmod(output / 'site_config.checkpoint.json', 0o600)
    for name in APP:
        tag = f'centrochange-single:issue139-rollback-{output.name}-{name}'
        run(['docker', 'tag', pre['services'][name]['image'], tag])
        require(run(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag]).stdout.strip()
                == pre['services'][name]['image'], f'{name}: rollback tag mismatch')
    report['rollback_images_verified'] = True
    report_write(report_path, report)
    candidate_id = build_candidate(paths, output)
    report['candidate_image'] = candidate_id
    report['source_paths'] = len(paths)
    report_write(report_path, report)
    # Recheck immediately before stopping ingress or any Site write.
    current = preflight(executor_sha)
    require(current['services'] == pre['services'] and current['data'] == pre['data'],
            'DEV changed while candidate image built')
    require(current['host']['oom_kill'] == pre['host']['oom_kill'],
            'host OOM event during candidate build')
    validate_owner_gate(gate_path, executor_sha)
    TIME_LIMIT_ACTIVE = True
    backup_manifest = None
    fixture_tests_started = False
    try:
        report['runtime_mutations'].append('application_stop_started')
        report_write(report_path, report)
        compose(pre['files'], 'stop', '-t', '60',
                'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')
        report_write(report_path, report)
        backup_manifest = backup(output)
        require(pre['module'].runtime_fingerprint() == pre['data']
                and schema_fingerprint(pre['module']) == pre['schema'],
                'Owner data or schema changed while creating checkpoint')
        report['backup'] = backup_manifest
        report_write(report_path, report)
        select_candidate_overlay(pre)
        compare_compose(pre['baseline'], compose_config(pre['files']))
        compose(pre['files'], 'up', '-d', '--no-deps', '--no-build',
                '--force-recreate', 'backend')
        running_backend = run(['docker', 'inspect', '--format', '{{.Image}}',
                               'centrochange-dev-backend-1']).stdout.strip()
        require(running_backend == candidate_id,
                'candidate backend image not served')
        # Branch schema and the audited A/B state already exist on this baseline.
        # The candidate contains no patches/schema changes, so do not rerun migrations.
        migrated = branch_probe(pre['module'])
        require(migrated['field_present'] and {r['name']: int(r['cc_operational']) for r in migrated['rows']}
                == {BRANCH_A: 1, BRANCH_B: 0}, 'pre-migrated center state changed')
        after_data = pre['data']
        require(permission_fingerprint(pre['module']) == pre['permissions'],
                'effective permissions changed during update')
        report['activation'] = {'center_a': 'already active and audited; preserved',
                                'center_b': 'inactive; preserved'}
        report['runtime_mutations'].append('candidate_backend_started; schema_and_centers_preserved')
        report_write(report_path, report)
        compose(pre['files'], 'up', '-d', '--no-deps', '--no-build',
                '--force-recreate', 'websocket', 'queue-short', 'queue-long', 'scheduler', 'frontend')
        pre['module'].http_ready()
        observed = pre['module'].snapshot()
        require(all(observed[n]['image'] == candidate_id for n in APP),
                'six application images do not match candidate')
        require(all(observed[n] == pre['services'][n] for n in TECH),
                'technical service identity changed')
        network = json.loads(run(['docker', 'inspect', 'centrochange-dev-frontend-1']).stdout)[0]
        aliases = network['NetworkSettings']['Networks'][NETWORK_NAME]['Aliases']
        require('centrochange.local' in aliases, 'frontend realtime hostname alias missing')
        require(run(['docker', 'exec', 'centrochange-dev-websocket-1',
                     'getent', 'hosts', 'centrochange.local'], check=False).returncode == 0,
                'websocket cannot resolve realtime Origin host')
        source_probe(pre['module'], paths)
        report['tests']['assets'] = asset_probe(paths)
        report['tests']['realtime_proxy'] = realtime_probe()
        require(pre['module'].hooks() == pre['module'].GUARDS, 'security hooks changed')
        require(pre['module'].runtime_fingerprint() == after_data,
                'data changed during application start')
        require(permission_fingerprint(pre['module']) == pre['permissions'],
                'post-start permission fingerprint drift')
        account = pwd.getpwnam('empv26')
        evidence = STATE / 'browser-evidence' / ('issue139-' + output.name)
        evidence.mkdir(mode=0o700)
        os.chown(evidence, account.pw_uid, account.pw_gid)
        readonly_output = evidence / 'devfirst-readonly'
        browser('mvp_devfirst_readonly.cjs', readonly_output)
        readonly = json.loads((readonly_output / 'devfirst-readonly.json').read_text())
        require(readonly['status'] == 'ESSENTIAL_PASS', 'essential read-only authorization gate failed')
        report['tests']['essential_readonly'] = readonly
        report['installation_essential_status'] = 'PASS'
        report_write(report_path, report)
        admin_folder = evidence / 'administrator'
        admin_folder.mkdir(mode=0o700)
        os.chown(admin_folder, account.pw_uid, account.pw_gid)
        admin_fixture = admin_folder / 'admin-login.json'
        password = pre['settings'].get('ADMIN_PASSWORD', '').strip().strip('"').strip("'")
        require(password, 'private Administrator credential unavailable')
        private_write(admin_fixture, json.dumps({'name': 'Administrator',
                                                  'password': password}).encode())
        os.chown(admin_fixture, account.pw_uid, account.pw_gid)
        try:
            env = ['PATH=/usr/sbin:/usr/bin:/sbin:/bin', 'HOME=/home/empv26',
                   'NODE_PATH=/tmp/cc-browser-qa/node_modules',
                   'LD_LIBRARY_PATH=/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
                   'CC_BASE_URL=http://centrochange.local:8082',
                   f'CC_ISSUE139_ADMIN_FIXTURE={admin_fixture}',
                   f'CC_ISSUE137_OUTPUT={admin_folder}']
            admin = run(['runuser', '-u', 'empv26', '--', '/usr/bin/env', *env,
                         'node', str(REPO / 'infra/browser/issue139_admin_readonly.cjs')],
                        cwd=REPO, check=False)
            if admin.returncode:
                private_write(output / 'admin-browser-error.log', admin.stderr.encode())
            require(admin.returncode == 0 and json.loads(admin.stdout.splitlines()[-1])['status'] == 'PASS',
                    'Administrator technical Desk browser check failed')
            report['tests']['administrator'] = 'PASS'
        finally:
            admin_fixture.unlink(missing_ok=True)
        require(pre['module'].runtime_fingerprint() == after_data,
                'read-only W5 altered Owner data')
        # Phase B cannot reuse the unresolved committed accounting cleanup.
        # No fixture writes means a blocked acceptance test cannot trigger a
        # database restore. Essential read-only authorization gates above remain mandatory.
        report['tests']['financial_acceptance'] = {
            'status': 'BLOCKED', 'reason': 'Native retained ledger and MariaDB 1020 cleanup risk unresolved; no fixture writes attempted'}
        report['tests']['security_38_mutative'] = {
            'status': 'BLOCKED', 'reason': 'Shared fixture cleanup requires separate verification; essential API denial checks executed read-only'}
        require(pre['module'].runtime_fingerprint() == after_data, 'read-only acceptance changed Owner data')
        require(permission_fingerprint(pre['module']) == pre['permissions'], 'acceptance permission drift')
        require(pre['module'].hooks() == pre['module'].GUARDS, 'acceptance hook drift')
        require(host_telemetry()['oom_kill'] == pre['host']['oom_kill']
                and host_telemetry()['docker_free_bytes'] >= 8 * 1024**3,
                'host OOM or disk reserve safety event')
        verdict = 'DEV_UPDATED_WITH_GAPS' if any(isinstance(v, dict) and v.get('status') in ('FAIL', 'BLOCKED') for v in report['tests'].values()) else 'LIVE_TECHNICAL_PASS'
        report.update(status=verdict, after_data=after_data,
                      evidence_directory=str(evidence))
        report_write(report_path, report)
        return report
    except BaseException as error:
        TIME_LIMIT_ACTIVE = False
        report['failure'] = str(error)[:240]
        try:
            report_write(report_path, report)
        except Exception:
            pass  # Reporting failure cannot prevent the one allowed rollback.
        try:
            restore_services(pre, env_bytes, env_stat,
                             data_backup=backup_manifest if fixture_tests_started else None,
                             output=output)
            report['status'] = 'ROLLED_BACK'
        except Exception as rollback_error:
            report['status'] = 'ROLLBACK_FAILED'
            report['rollback_failure'] = str(rollback_error)[:240]
        report_write(report_path, report)
        return report


def recover(executor_sha, gate_path, checkpoint_dir):
    """Recover an interrupted one-shot run; never starts a second installation."""
    static_gate(executor_sha)
    validate_owner_gate(gate_path, executor_sha, recovery=True)
    root = checkpoint_dir.resolve()
    require(root.parent == RUN_ROOT.resolve() and root.stat().st_mode & 0o077 == 0,
            'checkpoint path or mode unsafe')
    report_path = root / 'report.json'
    report = json.loads(report_path.read_text())
    require(report['candidate'] == SOURCE and report['executor_sha256'] == executor_sha
            and report['status'] in ('BLOCKED', 'ROLLBACK_FAILED')
            and report['runtime_mutations'], 'checkpoint is not an interrupted run')
    checkpoint = json.loads((root / 'checkpoint.json').read_text())
    original_env = (root / 'runtime.env.checkpoint').read_bytes()
    require(sha(original_env) == BASE_ENV_SHA, 'checkpoint environment drift')
    pre = {'files': [Path(p) for p in checkpoint['files']],
           'services': checkpoint['services'], 'data': checkpoint['data'],
           'schema': checkpoint['schema'], 'permissions': checkpoint['permissions'],
           'settings': parse_settings(original_env), 'module': old_probe()}
    require(pre['files'] == [*(COMPOSE_DIR / n for n in COMPOSE_SHA), BASE_OVERLAY, ACTIVE_OVERLAY],
            'checkpoint Compose scope drift')
    overlay = checkpoint['overlay']
    pre['overlay_bytes'] = (root / (ACTIVE_OVERLAY.name + '.checkpoint')).read_bytes()
    pre['overlay_stat'] = types.SimpleNamespace(st_mode=overlay['mode'], st_uid=overlay['uid'], st_gid=overlay['gid'])
    manifest_path = root / 'backup-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    stat = ENV.stat()
    try:
        restore_services(pre, original_env, stat, data_backup=manifest, output=root)
        report['status'] = 'ROLLED_BACK'
    except Exception as error:
        report['status'] = 'ROLLBACK_FAILED'
        report['rollback_failure'] = str(error)[:240]
    report_write(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--recover', action='store_true')
    parser.add_argument('--executor-sha256')
    parser.add_argument('--owner-gate-file', type=Path)
    parser.add_argument('--checkpoint-dir', type=Path)
    args = parser.parse_args()
    require(sum((args.dry_run, args.execute, args.recover)) == 1, 'choose exactly one mode')
    if args.dry_run:
        paths = static_gate()
        pre = preflight()
        print(json.dumps({'status': 'DRY_RUN_PASS', 'candidate': SOURCE,
                          'baseline_image': BASE_IMAGE, 'app_changed_files': len(paths),
                          'services': len(pre['services']), 'centers': len(pre['branch']['rows']),
                          'compose_delta': 'six app images plus frontend network alias',
                          'data_sha256': pre['data']['sha256']}))
        return 0
    require(args.executor_sha256 and args.owner_gate_file,
            'exact executor SHA and distinct Owner gate file required')
    if args.recover:
        require(args.checkpoint_dir, 'exact private checkpoint directory required')
        report = recover(args.executor_sha256, args.owner_gate_file, args.checkpoint_dir)
    else:
        report = execute(args.executor_sha256, args.owner_gate_file)
    print(json.dumps({key: report.get(key) for key in
                      ('status', 'candidate', 'executor_sha256', 'candidate_image', 'failure',
                       'rollback_failure', 'checkpoint')}))
    return 0 if report['status'] in ('LIVE_TECHNICAL_PASS', 'DEV_UPDATED_WITH_GAPS') else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Stop as error:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(error)}), file=sys.stderr)
        raise SystemExit(2)
