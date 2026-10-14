#!/usr/bin/env python3
"""One GOAL-02 A+B DEV attempt, only after renewed Owner authorization.

The script has no network fetch and never changes the Site, database, grants or
technical services. Failure before switch is BLOCKED; failure after switch gets
one rollback. Reports remain private until manually sanitized for GitHub.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
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
AB_SOURCE = '90817de65312becb6888ef60a8caa5c679248fb0'
SOURCE = '83f8f4f97b74e25e73710b6fc3667be0ae473fce'
BASE = '2f0aa47f51d452a3e711cb838b1dd350611cb6cb'
EXCLUDED = '382042c493dc07db142ce1e1abc2159060444f49'
BASE_IMAGE = 'sha256:f38215267771e4db2e42af9312211931dc039b07ff17b69953c10f50026c6285'
CSS_IMAGE = 'centrochange-single:issue79-css-f3ab9d5ddf9f'
CSS_SHA = 'f3ab9d5ddf9f15e63b576a5656331169067af6d722cdea6d79b8c5ca644fe27d'
PRIOR_CANDIDATE = 'centrochange-single:goal02-abc-90817de'
TARGET = 'centrochange-single:goal02-abc-fixture-83f8f4f'
RETAINED_CANDIDATE_IMAGE = 'sha256:5ec8db83748fdc9d46bfd862a85930b9e8416aec1049afabca21faa15a5cdf1e'
EXPECTED_DATA_SHA = '0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a'
EXPECTED_ENV_SHA = 'd2e2e2849b0507f9bcfe8de78d48dc81cdb59d705aa62a765e96eea60429f080'
OLD_OVERRIDE_SHA = 'f68f3da5adc5ed8b3ec907602f8a5ff671735b5265aeb3a6c7fafeed4cdb4a8f'
STALE_CANDIDATE_OVERRIDE_SHA = '36bfbc37da334893385da8046f1df639e690eff15748ca5332a52858cd23c4f6'
COMPOSE_DIR = Path('/tmp/centrochange-issue124/infra')
COMPOSE_NAMES = ('compose.yaml', 'compose.issue124.yaml', 'compose.uat.yaml')
COMPOSE_SHA = ('5df3c081f4afff41e6e07222405a4d311bc75eeb1fa97c1045834115e5a0a67d',
               'ced6e5d2af243bfefbd368ddc46e49de0381bf36c25d05109a13413b59bd7917',
               '982fd1cd6253c331482af430a64f9a0b9d1ba205af8a37fd31a1e4cf2a10ade7')
OVERRIDE_SOURCE = REPO / 'infra/compose.goal02_retry.yaml'
OVERRIDE = STATE / 'compose.goal02_candidate.yaml'
APP = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')
TECH = ('db', 'redis-cache', 'redis-queue')
REL = 'app/centrochange_core/centrochange_core/'
IMAGE_REL = '/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/'
CSS_FILE = 'centro_change_core/page/cc_unified_desk/cc_unified_desk.css'
CHANGED = ('public/css/workspace.css', 'public/js/audit_view.js',
           'public/js/finance_workspace.js', 'public/js/ui_labels.js',
           'public/js/workspace.js')
FIXTURE_CHANGED = ('security/dev_acceptance.py', 'security/fixture_cleanup.py')
GUARDS = ['centrochange_core.finance.request_guard.before_request',
          'centrochange_core.security.diagnostics.before_request',
          'centrochange_core.security.api.before_request',
          'centrochange_core.operations.notes.request_guard',
          'centrochange_core.operations.website_brand.client_language',
          'centrochange_core.operations.website_brand.login_language']
NODE_MODULES = '/tmp/cc-browser-qa/node_modules'
CHROMIUM_LIBS = '/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu'
CHROMIUM = '/home/empv26/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell'


class Stop(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Stop(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return digest(path.read_bytes())


def run(args, *, cwd=None, input=None, env=None, allow_fail=False):
    result = subprocess.run(args, cwd=cwd, input=input, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode and not allow_fail:
        raise Stop(f'{args[0]} failed with exit {result.returncode}; private output suppressed')
    return result


def git(*args):
    prefix = ['runuser', '-u', 'empv26', '--'] if os.geteuid() == 0 else []
    return run(prefix + ['git', *args], cwd=REPO)


def git_file(ref, relative):
    prefix = ['runuser', '-u', 'empv26', '--'] if os.geteuid() == 0 else []
    result = subprocess.run(prefix + ['git', 'show', f'{ref}:{REL}{relative}'], cwd=REPO,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    require(result.returncode == 0, f'pinned source file missing: {relative}')
    return result.stdout


def static_gate(script_sha):
    require(file_sha(Path(__file__)) == script_sha, 'executor SHA mismatch')
    require(git('merge-base', SOURCE, 'HEAD').stdout.strip() == SOURCE,
            'executor checkout does not descend from exact approved commit')
    # The executor branch may add only its own recipe, tests and evidence.
    executor_delta = git('diff', '--name-only', SOURCE, 'HEAD').stdout.splitlines()
    require(all(x.startswith(('infra/goal02_install_one_command.py',
                                'infra/compose.goal02_candidate.yaml',
                                'infra/browser/goal02_abc_live.cjs',
                                'infra/browser/issue79_unified_autocomplete.cjs',
                                'infra/tests/test_goal02_install.py',
                                'infra/tests/test_goal02_package_c.py',
                                'infra/tests/test_goal02_cleanup.py',
                                'infra/goal02_targeted_regression.py',
                                'infra/goal02_orphan_cleanup.py',
                                'infra/compose.goal02_retry.yaml',
                                'docs/evidence/goal-02/GOAL02-CONTROLLED-INSTALL-',
                                'docs/evidence/goal-02/GOAL02-ROLLBACK-DIAGNOSIS-',
                                'docs/evidence/goal-02/GOAL02-ROLLBACK-RECOVERY-PLAN-',
                                'docs/evidence/goal-02/GOAL02-CONTROLLED-RETRY-ROLLBACK-FAILED-',
                                'docs/evidence/goal-02/GOAL02-CLEANUP-')) for x in executor_delta),
            'executor branch includes unapproved application changes')
    require(not git('status', '--porcelain').stdout.strip(), 'executor checkout is not clean')
    require(git('merge-base', BASE, AB_SOURCE).stdout.strip() == BASE, '#129 is not ancestor')
    require(git('merge-base', AB_SOURCE, SOURCE).stdout.strip() == AB_SOURCE,
            'fixture source does not descend from exact approved A+B candidate')
    for ancestor in ('6f8a8f5f28ebc39f8e25eecd10086a601fc21419',
                     'cb21cc2f74d3c99a31c9d9b82b080bc39bea5b87',
                     'dbb02b389e83f2cff0b05dde2689793797fe3e6f',
                     'f0521445257a8298c35d8056c94f7a7b64254f0e',
                     'f403a60166b99aaad3fc9374bfb2eb1ebc4cb438',
                     'cf662ed7f5d46902badc3a034fc1322a9e8ee090'):
        require(git('merge-base', ancestor, AB_SOURCE).stdout.strip() == ancestor,
                'approved PR ancestry drift')
    require(git('merge-base', EXCLUDED, SOURCE).stdout.strip() != EXCLUDED, '#128 unexpectedly included')
    require(git('diff', '--name-only', BASE, AB_SOURCE, '--', REL).stdout.splitlines() ==
            sorted(REL + path for path in CHANGED), 'candidate application delta differs from A+B')
    require(git('diff', '--name-only', AB_SOURCE, SOURCE, '--', REL).stdout.splitlines() ==
            sorted(REL + path for path in FIXTURE_CHANGED), 'fixture candidate source delta drift')
    for relative in CHANGED + FIXTURE_CHANGED + (CSS_FILE, 'hooks.py'):
        require(git_file(SOURCE, relative), f'missing pinned file: {relative}')
    require(all(digest(git_file(AB_SOURCE, path)) == digest(git_file(SOURCE, path))
                for path in CHANGED + (CSS_FILE, 'hooks.py')),
            'approved A+B/CSS/security baseline drift')
    require(digest(git_file(SOURCE, CSS_FILE)) == CSS_SHA, '#79 CSS missing from candidate')
    for name, sha in zip(COMPOSE_NAMES, COMPOSE_SHA):
        require(file_sha(COMPOSE_DIR / name) == sha, f'{name} drift')
    require(file_sha(STATE / 'compose.issue79.yaml') == OLD_OVERRIDE_SHA, '#79 override drift')
    require(file_sha(ENV) == EXPECTED_ENV_SHA and ENV.stat().st_mode & 0o077 == 0,
            'private runtime env drift or unsafe mode')
    require(OVERRIDE_SOURCE.is_file() and OVERRIDE.exists() and
            file_sha(OVERRIDE) == STALE_CANDIDATE_OVERRIDE_SHA,
            'inactive prior candidate override missing or changed')
    raw = ENV.read_text()
    settings = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line and not line.startswith('#'))
    expected_files = ':'.join(str(COMPOSE_DIR / x) for x in COMPOSE_NAMES) + ':' + str(STATE / 'compose.issue79.yaml')
    require(settings.get('SITE_NAME') == 'centrochange.local' and settings.get('HTTP_PORT') == '8082' and
            settings.get('COMPOSE_FILE') == expected_files, 'Site, port or Compose precedence drift')
    require(settings.get('CC_UAT_IMAGE') == 'centrochange-single:goal02-fixture-d1892e0',
            'configured five-service base image drift')
    require(str(OVERRIDE) not in settings['COMPOSE_FILE'], 'prior candidate override unexpectedly active')
    require(Path(NODE_MODULES, 'playwright/package.json').is_file() and Path(CHROMIUM).is_file(),
            'Chromium prerequisites unavailable')
    return settings


def compose(*args, override=None, env_file=ENV):
    cmd = ['docker', 'compose', '--env-file', str(env_file), '-p', 'centrochange-dev']
    for name in COMPOSE_NAMES:
        cmd += ['-f', str(COMPOSE_DIR / name)]
    cmd += ['-f', str(override or STATE / 'compose.issue79.yaml')]
    return run(cmd + list(args))


def config(override=None, env_file=ENV):
    value = json.loads(compose('config', '--format', 'json', override=override, env_file=env_file).stdout)
    require(value['name'] == 'centrochange-dev', 'Compose project drift')
    return value


def image_id(ref):
    return run(['docker', 'image', 'inspect', '--format', '{{.Id}}', ref]).stdout.strip()


def retained_candidate_present():
    existing = run(['docker','image','inspect',PRIOR_CANDIDATE], allow_fail=True)
    require(existing.returncode == 0,
            'approved A+B candidate image is unavailable')
    require(image_id(PRIOR_CANDIDATE) == RETAINED_CANDIDATE_IMAGE,
            'approved A+B candidate tag differs from verified build')
    return True


def snapshot():
    result = {}
    for service in APP + TECH:
        ids = compose('ps', '-q', service).stdout.splitlines()
        require(len(ids) == 1, f'{service}: expected one container')
        data = json.loads(run(['docker', 'inspect', ids[0]]).stdout)[0]
        labels = data['Config'].get('Labels') or {}
        require(labels.get('com.docker.compose.project') == 'centrochange-dev' and
                labels.get('com.docker.compose.service') == service, f'{service}: ownership drift')
        health = (data['State'].get('Health') or {}).get('Status')
        require(data['State']['Running'] and health in (None, 'healthy'), f'{service}: unhealthy')
        result[service] = {'id': data['Id'], 'image': data['Image'], 'health': health,
                           'mounts': sorted((m['Type'], m.get('Name'), m['Source'], m['Destination'])
                                            for m in data['Mounts'])}
    active = run(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=centrochange-dev']).stdout.splitlines()
    require(len(active) == 9 and {x[:12] for x in active} == {x['id'][:12] for x in result.values()},
            'project service count drift')
    return result


def backend_python(code):
    # Frappe resolves ../logs and <site>/logs relative to the sites directory.
    # Stream logging keeps these read-only probes from creating log files.
    return run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1',
                '-w', '/home/frappe/frappe-bench/sites', 'centrochange-dev-backend-1',
                '/home/frappe/frappe-bench/env/bin/python'], input=code).stdout


def runtime_fingerprint():
    code = '''import hashlib,json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
assert frappe.conf.get("cc_synthetic_dev")==1 and frappe.conf.get("cc_uat_demo")==1
assert frappe.conf.get("db_name")
frappe.set_user("Administrator")
types=["Patient","Healthcare Practitioner","Patient Appointment","Sales Invoice","Purchase Invoice","Payment Entry","Bank Transaction","CC Audit Event","CC Booking Confirmation","CC Fiscal Transaction","CC Professional Comparison"]
rows={dt:frappe.get_all(dt,fields=["name","modified"],order_by="name",limit_page_length=0) for dt in types}
value=json.dumps(rows,sort_keys=True,default=str,separators=(",",":"))
print("CC_PREFLIGHT_JSON="+json.dumps({"counts":{dt:len(v) for dt,v in rows.items()},"sha256":hashlib.sha256(value.encode()).hexdigest(),"db_sha256":hashlib.sha256(frappe.conf.db_name.encode()).hexdigest()}))
frappe.db.rollback();frappe.destroy()
'''
    output = backend_python(code)
    return json.loads(next(x.split('=', 1)[1] for x in output.splitlines() if x.startswith('CC_PREFLIGHT_JSON=')))


def hooks():
    code = '''import json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
app=frappe.get_hooks("before_request",app_name="centrochange_core")
effective=frappe.get_hooks("before_request")
print("CC_HOOKS_JSON="+json.dumps({"app":app,"effective":effective}))
frappe.db.rollback();frappe.destroy()
'''
    output = backend_python(code)
    observed = json.loads(next(x.split('=', 1)[1] for x in output.splitlines() if x.startswith('CC_HOOKS_JSON=')))
    require(observed['app'] == GUARDS and all(observed['effective'].count(hook) == 1 for hook in GUARDS),
            'runtime guard/language hooks missing, duplicated or reordered')
    return observed['app']


def app_hashes(paths):
    code = '''import hashlib,json,pathlib
base=pathlib.Path("/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core")
paths=json.loads(''' + repr(json.dumps(paths)) + ''')
print("CC_FILES_JSON="+json.dumps({p:hashlib.sha256((base/p).read_bytes()).hexdigest() for p in paths}))
'''
    output = backend_python(code)
    return json.loads(next(x.split('=', 1)[1] for x in output.splitlines() if x.startswith('CC_FILES_JSON=')))


def http_ready():
    for _ in range(30):
        try:
            request = urllib.request.Request('http://127.0.0.1:8082/api/method/ping', headers={'Host':'centrochange.local'})
            with urllib.request.urlopen(request, timeout=4) as response:
                if response.status == 200 and json.load(response)['message'] == 'pong':
                    return
        except Exception:
            pass
        time.sleep(2)
    raise Stop('DEV HTTP health failed')


def served_assets():
    result = {}
    for relative in CHANGED:
        path = '/assets/centrochange_core/' + relative.removeprefix('public/')
        request = urllib.request.Request('http://127.0.0.1:8082' + path,
                                         headers={'Host':'centrochange.local','Cache-Control':'no-cache'})
        with urllib.request.urlopen(request, timeout=15) as response:
            require(response.status == 200, f'asset {relative} unavailable')
            result[relative] = digest(response.read())
    return result


def verify_environment():
    require(socket.gethostname() == 'srv2033673' and os.geteuid() == 0 and sys.flags.isolated,
            'requires sudo python3 -I on authorized host')
    require(shutil.disk_usage('/var/lib/docker').free >= 3 * 1024**3, 'Docker free space below 3 GiB')
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line)
    available_kib = int(mem['MemAvailable'].strip().split()[0])
    require(available_kib >= 3 * 1024**2, 'MemAvailable below 3 GiB')
    require((STATE / 'issue79-checkpoint-20261013').is_dir(), '#79 checkpoint missing')
    fixture = STATE / 'demo-owner.json'
    require(fixture.is_file() and fixture.stat().st_mode & 0o077 == 0, 'private synthetic fixture unavailable')
    root = STATE / 'browser-evidence'
    require(root.is_dir() and root.stat().st_mode & 0o077 == 0 and
            root.stat().st_uid == pwd.getpwnam('empv26').pw_uid, 'private browser evidence directory unsafe')


def preflight():
    verify_environment()
    retained_candidate_present()
    before = snapshot()
    require(image_id('centrochange-single:goal02-fixture-d1892e0') == BASE_IMAGE,
            'baseline image ID drift')
    css_id = image_id(CSS_IMAGE)
    require(css_id != BASE_IMAGE and before['backend']['image'] == css_id and
            all(before[x]['image'] == BASE_IMAGE for x in APP if x != 'backend'),
            'six application image mapping drift')
    current = config()
    require(current['services']['backend']['image'] == CSS_IMAGE and
            all(current['services'][x]['image'] == 'centrochange-single:goal02-fixture-d1892e0'
                for x in APP if x != 'backend'), 'resolved Compose image mapping drift')
    require(hooks() == GUARDS, 'runtime six-hook order or membership drift')
    paths = list(CHANGED) + [CSS_FILE, 'hooks.py', 'security/dev_acceptance.py']
    actual = app_hashes(paths)
    for path in CHANGED:
        require(actual[path] == digest(git_file(BASE, path)), f'installed base differs at {path}')
    for path in (CSS_FILE, 'hooks.py', 'security/dev_acceptance.py'):
        require(actual[path] == digest(git_file(SOURCE, path)), f'installed prerequisite differs at {path}')
    require(actual[CSS_FILE] == CSS_SHA, 'live backend #79 CSS drift')
    require(len([x for x in before['backend']['mounts'] if x[3].endswith('/sites')]) == 1,
            'single Site volume not verified')
    site_info = json.loads(backend_python('''import json,pathlib,hashlib
p=pathlib.Path("/home/frappe/frappe-bench/sites"); names=sorted(x.name for x in p.iterdir() if x.is_dir() and (x/"site_config.json").exists())
print("CC_SITE_JSON="+json.dumps({"sites":names,"config_sha256":hashlib.sha256((p/"centrochange.local/site_config.json").read_bytes()).hexdigest()}))
''').split('CC_SITE_JSON=', 1)[1].splitlines()[0])
    require(site_info['sites'] == ['centrochange.local'], 'multiple or unexpected Sites')
    http_ready()
    require(all(served_assets()[p] == digest(git_file(BASE, p)) for p in CHANGED),
            'currently served A+B base asset drift')
    before_data = runtime_fingerprint()
    require(before_data['counts']['Patient'] > 0, 'synthetic data inventory unexpectedly empty')
    require(before_data['sha256'] == EXPECTED_DATA_SHA, 'restored synthetic data fingerprint drift')
    require(run(['docker','image','inspect',TARGET],allow_fail=True).returncode != 0,
            'new candidate tag unexpectedly exists before the authorized build')
    return before, current, before_data, site_info


def compare_config(old, new):
    require(old.keys() == new.keys(), 'Compose top-level keys changed')
    for key in old:
        if key != 'services':
            require(old[key] == new[key], f'Compose {key} drift')
    require(old['services'].keys() == new['services'].keys(), 'Compose service set drift')
    for name, prior in old['services'].items():
        if name in APP:
            expected = dict(prior)
            expected['image'] = TARGET
            require(new['services'][name] == expected, f'{name}: indirect Compose change')
        else:
            require(new['services'][name] == prior, f'{name}: technical service changed')


def atomic_bytes(path, content, mode, owner=None):
    fd, temporary = tempfile.mkstemp(prefix='.goal02-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        if owner:
            os.fchown(fd, *owner)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(content)
            handle.flush();os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def browser(script, output):
    env = ['PATH=/usr/sbin:/usr/bin:/sbin:/bin', 'HOME=/home/empv26',
           f'NODE_PATH={NODE_MODULES}', f'LD_LIBRARY_PATH={CHROMIUM_LIBS}',
           f'CC_CHROMIUM={CHROMIUM}', 'CC_BASE_URL=http://centrochange.local:8082',
           f'CC_ISSUE79_FIXTURE={STATE / "demo-owner.json"}',
           'CC_ISSUE79_ASSET_MODE=live', f'CC_ISSUE79_OUTPUT={output}',
           'CC_ISSUE79_ROLES=m,s,a,b',
           f'CC_GOAL02_ADMIN_FIXTURE={output / "admin-login.json"}',
           f'CC_GOAL02_OUTPUT={output}']
    result = run(['runuser', '-u', 'empv26', '--', '/usr/bin/env', *env,
                  'node', str(REPO / 'infra/browser' / script)], cwd=REPO, allow_fail=True)
    if result.returncode:
        lines = result.stderr.splitlines()
        relevant = [line.strip() for line in lines if any(marker in line for marker in
                    ('Error:', 'AssertionError', 'Timeout ', 'locator.', 'page.waitFor',
                     'Call log:', 'waiting for', 'at login ',
                     'at testRole ', 'at principal ', 'at administrator ', 'TEST '))]
        excerpt = ' | '.join(relevant[:8])[:1000]
        excerpt = re.sub(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '[email]', excerpt, flags=re.I)
        excerpt = re.sub(r'(?i)(password|passwd|token|cookie|authorization|pwd)[=:]\s*[^\s|]+',
                         r'\1=[redacted]', excerpt)
        raise Stop(f'Chromium {script} failed (exit {result.returncode}): {excerpt or "no diagnostic line"}')
    data = json.loads(result.stdout.strip().splitlines()[-1])
    require(data.get('status') == 'PASS' and data.get('mutations') == 'NONE',
            f'{script}: live check failed')
    return data


def targeted_regression():
    result = run(['python3', str(REPO / 'infra/goal02_targeted_regression.py')],
                 cwd=REPO, allow_fail=True)
    if result.returncode:
        private = re.search(r'/home/empv26/\.local/state/centrochange-single/goal02-install-runs/'
                            r'targeted-regression-[A-Za-z0-9_-]+\.log', result.stderr)
        location = private.group(0) if private else 'no private diagnostic file reported'
        raise Stop(f'targeted regression failed (exit {result.returncode}); {location}')
    try:
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise Stop('targeted regression result missing or invalid') from None
    require(outcome.get('status') == 'PASS' and outcome.get('persistent_rows_sha256_unchanged') is True,
            'targeted regression PASS/integrity result missing')
    return 'PASS'


def write_report(path, report):
    atomic_bytes(path, (json.dumps(report, indent=2, sort_keys=True) + '\n').encode(), 0o600)


def apply(script_sha):
    settings = static_gate(script_sha)
    before, old_config, before_data, site_info = preflight()
    proposed = config(override=OVERRIDE_SOURCE)
    compare_config(old_config, proposed)
    # Recheck the normal Compose entry point, including the persistent #79 override.
    require(settings['COMPOSE_FILE'].endswith('/compose.issue79.yaml'), 'ordinary Compose precedence drift')
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + f'-{os.getpid()}'
    run_dir = STATE / 'goal02-install-runs' / stamp
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    run_dir.chmod(0o700)
    evidence = STATE / 'browser-evidence' / ('goal02-' + stamp)
    evidence.mkdir(mode=0o700, exist_ok=False)
    account = pwd.getpwnam('empv26')
    os.chown(evidence, account.pw_uid, account.pw_gid)
    require(run(['runuser','-u','empv26','--','test','-w',str(evidence)]).returncode == 0,
            'browser evidence is not writable')
    original = ENV.read_bytes(); original_stat = ENV.stat()
    old_override = OVERRIDE.read_bytes(); old_override_stat = OVERRIDE.stat()
    checkpoint = run_dir / 'checkpoint'
    checkpoint.mkdir(mode=0o700)
    for path in [ENV, *(COMPOSE_DIR / x for x in COMPOSE_NAMES), STATE / 'compose.issue79.yaml', OVERRIDE]:
        target = checkpoint / path.name
        target.write_bytes(path.read_bytes());target.chmod(0o600)
        require(file_sha(target) == file_sha(path), 'checkpoint copy mismatch')
    report_path = run_dir / 'report.json'
    report = {'status':'BLOCKED','candidate_commit':SOURCE,'executor_sha256':script_sha,
              'before_images':{s:before[s]['image'] for s in APP + TECH},
              'before_data':before_data,'before_site':site_info,
              'before_env_sha256':digest(original),'checkpoint':str(checkpoint),
              'source_delta':list(CHANGED + FIXTURE_CHANGED),'tests':{}}
    write_report(report_path, report)
    # Immutable rollback tags for all six app services; no service is switched yet.
    for name in APP:
        tag = f'centrochange-single:goal02-rollback-{stamp}-{name}'
        run(['docker', 'tag', before[name]['image'], tag])
        require(image_id(tag) == before[name]['image'], f'{name}: rollback tag mismatch')
    report['rollback_tags'] = {s:f'centrochange-single:goal02-rollback-{stamp}-{s}' for s in APP}
    write_report(report_path, report)
    changed = False
    activation_started = False
    try:
        build = run_dir / 'build';build.mkdir(mode=0o700)
        for relative in FIXTURE_CHANGED:
            target = build / relative;target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git_file(SOURCE, relative))
            require(file_sha(target) == digest(git_file(SOURCE, relative)), 'build context mismatch')
        recipe = ['FROM ' + PRIOR_CANDIDATE, 'USER frappe', 'WORKDIR /home/frappe/frappe-bench']
        for relative in FIXTURE_CHANGED:
            recipe.append('COPY --chown=frappe:frappe ' + relative + ' apps/centrochange_core/centrochange_core/' + relative)
        recipe += ['LABEL centrochange.goal="02" centrochange.source="'+SOURCE+'"', '']
        (build / 'Dockerfile').write_text('\n'.join(recipe))
        retained_candidate_present()
        run(['docker','build','--pull=false','--no-cache','-t',TARGET,'-f',str(build / 'Dockerfile'),str(build)])
        report['prior_candidate_reused'] = True
        target_id = image_id(TARGET)
        require(target_id != before['backend']['image'], 'candidate image unchanged')
        # Image labels and exact contents, including retained #79 CSS.
        candidate = json.loads(run(['docker','image','inspect',TARGET]).stdout)[0]
        require(candidate['Config']['Labels']['centrochange.source'] == SOURCE, 'candidate source label mismatch')
        base_image = json.loads(run(['docker','image','inspect',PRIOR_CANDIDATE]).stdout)[0]
        base_layers = base_image['RootFS']['Layers']
        require(candidate['RootFS']['Layers'][:len(base_layers)] == base_layers and
                len(candidate['RootFS']['Layers']) > len(base_layers),
                'candidate image does not derive from approved A+B/#79 image')
        for key in ('Entrypoint','Cmd','User','Env','WorkingDir','ExposedPorts','Volumes'):
            require(candidate['Config'].get(key) == base_image['Config'].get(key),
                    f'candidate runtime config changed: {key}')
        check = run(['docker','run','--rm','--network','none','--read-only','--entrypoint','python',TARGET,
                     '-c', 'import hashlib,json,pathlib; p=pathlib.Path("'+IMAGE_REL+'"); '
                           'print(json.dumps({x:hashlib.sha256((p/x).read_bytes()).hexdigest() for x in '+
                           repr(list(CHANGED + FIXTURE_CHANGED) + [CSS_FILE])+ '}))'])
        image_files = json.loads(check.stdout)
        require(all(image_files[p] == digest(git_file(SOURCE,p)) for p in image_files),
                'candidate app file mismatch')
        # Last read-only gate immediately before configuration change.
        require(file_sha(ENV) == EXPECTED_ENV_SHA and snapshot() == before and
                runtime_fingerprint() == before_data and hooks() == GUARDS,
                'concurrent DEV drift during build')
        changed = True
        atomic_bytes(OVERRIDE, OVERRIDE_SOURCE.read_bytes(), 0o644)
        require(file_sha(OVERRIDE) == file_sha(OVERRIDE_SOURCE), 'persistent override mismatch')
        updated = original.replace(str(STATE / 'compose.issue79.yaml').encode(), str(OVERRIDE).encode())
        require(updated != original and updated.count(str(OVERRIDE).encode()) == 1,
                'cannot update Compose precedence exactly once')
        atomic_bytes(ENV, updated, original_stat.st_mode & 0o777,
                     (original_stat.st_uid, original_stat.st_gid))
        compare_config(old_config, config(override=OVERRIDE))
        # No dependencies are recreated. The configurator must never run.
        activation_started = True
        compose('up','-d','--no-deps','--no-build','--force-recreate',*APP,override=OVERRIDE)
        http_ready()
        after = snapshot()
        require(all(after[s]['image'] == target_id and after[s]['mounts'] == before[s]['mounts'] for s in APP),
                'candidate application image or mount mismatch')
        require(all(after[s] == before[s] for s in TECH), 'database or Redis changed')
        require(hooks() == GUARDS and runtime_fingerprint() == before_data,
                'security hooks or synthetic records changed')
        require(app_hashes(list(CHANGED + FIXTURE_CHANGED) + [CSS_FILE]) == image_files,
                'running candidate source differs from image')
        live_assets = served_assets()
        require(all(live_assets[p] == digest(git_file(SOURCE,p)) for p in CHANGED),
                'served candidate assets do not match authorized commit')
        report['tests']['served_asset_hashes'] = live_assets
        admin_fixture = evidence / 'admin-login.json'
        password = settings['ADMIN_PASSWORD'].strip().strip('"').strip("'")
        require(bool(password), 'Administrator credential unavailable')
        atomic_bytes(admin_fixture, json.dumps({'name':'Administrator','password':password}).encode(),
                     0o600, (account.pw_uid, account.pw_gid))
        try:
            report['tests']['issue79'] = browser('issue79_unified_autocomplete.cjs', evidence)
            report['tests']['goal02_live'] = browser('goal02_abc_live.cjs', evidence)
        finally:
            admin_fixture.unlink(missing_ok=True)
        # Fixture suite creates only its own synthetic rows and tears them down.
        run(['python3',str(REPO / 'infra/security_acceptance.py'),'--env-file',str(ENV),
             '--with-booking','--with-operations'],cwd=REPO)
        report['tests']['security_acceptance'] = 'PASS'
        report['tests']['goal02_targeted_regression'] = targeted_regression()
        require(runtime_fingerprint() == before_data, 'post-test synthetic fingerprint changed')
        require(all(snapshot()[s] == before[s] for s in TECH), 'technical services changed after tests')
        report.update(status='LIVE_TECHNICAL_PASS', candidate_image=target_id,
                      after_data=runtime_fingerprint(), screenshots=str(evidence))
        write_report(report_path, report)
        return report['status'], report_path
    except Exception as error:
        report['failure'] = str(error) if isinstance(error, Stop) else type(error).__name__
        if changed:
            try:
                atomic_bytes(ENV, original, original_stat.st_mode & 0o777,
                             (original_stat.st_uid, original_stat.st_gid))
                require(file_sha(ENV) == EXPECTED_ENV_SHA, 'rollback env mismatch')
                require(config() == old_config, 'rollback Compose config mismatch')
                if activation_started:
                    compose('up','-d','--no-deps','--no-build','--force-recreate',*APP)
                http_ready()
                recovered = snapshot()
                require(all(recovered[s]['image'] == before[s]['image'] and
                            recovered[s]['mounts'] == before[s]['mounts'] for s in APP),
                        'rollback app image or mount mismatch')
                require(all(recovered[s] == before[s] for s in TECH), 'rollback technical service mismatch')
                require(hooks() == GUARDS and runtime_fingerprint() == before_data and
                        app_hashes([CSS_FILE])[CSS_FILE] == CSS_SHA, 'rollback security, data or #79 mismatch')
                require(all(served_assets()[p] == digest(git_file(BASE,p)) for p in CHANGED),
                        'rollback served assets mismatch')
                atomic_bytes(OVERRIDE, old_override, old_override_stat.st_mode & 0o777,
                             (old_override_stat.st_uid, old_override_stat.st_gid))
                require(file_sha(OVERRIDE) == STALE_CANDIDATE_OVERRIDE_SHA,
                        'rollback inactive candidate override mismatch')
                report['status'] = 'ROLLED_BACK' if activation_started else 'BLOCKED'
            except Exception as rollback_error:
                report['status'] = 'ROLLBACK_FAILED'
                report['rollback_failure'] = (str(rollback_error) if isinstance(rollback_error, Stop)
                                              else type(rollback_error).__name__)
        write_report(report_path, report)
        return report['status'], report_path


def main():
    os.umask(0o077)
    os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
    parser = argparse.ArgumentParser()
    parser.add_argument('--script-sha256', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        static_gate(args.script_sha256)
        if args.dry_run:
            print(json.dumps({'status':'STATIC_DRY_RUN_PASS','candidate_commit':SOURCE,
                              'runtime_mutations':'NONE'}))
            return 0
        lock = STATE / '.goal02-install.lock'
        with lock.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            status, report = apply(args.script_sha256)
        print(json.dumps({'status':status,'private_report':str(report)}))
        return 0 if status == 'LIVE_TECHNICAL_PASS' else 1
    except Exception as error:
        reason = str(error) if isinstance(error, Stop) else type(error).__name__
        print(json.dumps({'status':'BLOCKED','reason':reason,'runtime_mutations':'NONE'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
