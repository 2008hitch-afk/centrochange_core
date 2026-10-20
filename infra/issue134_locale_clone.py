#!/usr/bin/env python3
"""One temporary, isolated rendering rehearsal for issue #134.

No command targets a DEV container, volume or network for mutation. The only
DEV reads are the already verified encrypted Site backup and a fingerprint.
Run as root with Python -I; artifacts remain private outside Git.
"""
import hashlib
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
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
PROJECT = 'cc134-locale-isolated'
SITE = 'centrochange.local'
BASE = 'sha256:d7315cb85d3d51ed6510b9d0f6f1b9b2be639cb2d637f67a57790136f5e55257'
BASE_TAG = 'centrochange-single:issue134-final-1b7ffc4'
BACKUP = Path('/home/empv26/.local/state/centrochange-single/issue134-final-install-runs/20261020T133631Z-63248')
STATE_ROOT = Path('/home/empv26/.local/state/centrochange-single/issue134-locale-clone')
APP_PREFIX = 'app/centrochange_core/centrochange_core/'
CHANGED = ('hooks.py', 'operations/website_brand.py', 'operations/locale_presentation.py',
           'translations/it.csv', 'public/js/cc_catalog_finance_list.js',
           'public/js/cc_finance_form.js', 'public/js/audit_view.js',
           'public/js/workspace.js',
           'public/js/ui_labels.js')
SERVICES = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')
ERROR_LOG = None


def run(args, *, input_bytes=None, check=True):
    """Never echo command arguments: they can contain the clone DB password."""
    result = subprocess.run(args, input=input_bytes, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if check and result.returncode:
        if ERROR_LOG:
            ERROR_LOG.write_bytes(result.stderr)
            ERROR_LOG.chmod(0o600)
        raise RuntimeError(f'{args[0]} failed ({result.returncode}); private stderr retained')
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compose(state):
    return ['docker', 'compose', '--env-file', str(state / 'runtime.env'),
            '-p', PROJECT, '-f', str(state / 'compose.yaml'), '-f', str(state / 'overlay.yaml')]


def verify_isolation(state):
    config = json.loads(run(compose(state) + ['config', '--format', 'json']).stdout)
    if config['name'] != PROJECT or set(config['networks']) != {PROJECT + '-net'}:
        raise RuntimeError('clone project/network isolation failed')
    if any(not name.startswith(PROJECT + '-') for name in config['volumes']):
        raise RuntimeError('clone volume isolation failed')
    frontend = config['services']['frontend']
    if frontend['ports'] != [{'mode': 'ingress', 'target': 8080, 'published': '8082',
                              'protocol': 'tcp', 'host_ip': '127.0.0.2'}]:
        raise RuntimeError('clone frontend listener isolation failed')
    if any('centrochange-dev' in json.dumps(service) for service in config['services'].values()):
        raise RuntimeError('DEV reference in resolved clone services')
    return config


def preflight():
    if os.geteuid() != 0 or sys.flags.isolated != 1:
        raise RuntimeError('requires sudo python3 -I')
    if run(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={PROJECT}', '-q']).stdout.strip():
        raise RuntimeError('existing isolated clone containers')
    for kind in ('volume', 'network'):
        if run(['docker', kind, 'ls', '--filter', f'name=^{PROJECT}', '-q']).stdout.strip():
            raise RuntimeError('existing isolated clone resource')
    info = json.loads(run(['docker', 'image', 'inspect', BASE]).stdout)[0]
    if info['Config']['Labels'].get('centrochange.source') != '1b7ffc465ff699de163f9536ab04d4dde4da54e3':
        raise RuntimeError('baseline image source differs')
    if run(['docker', 'image', 'inspect', '--format', '{{.Id}}', BASE_TAG]).stdout.strip().decode() != BASE:
        raise RuntimeError('local baseline image tag differs')
    if shutil.disk_usage('/var/lib/docker').free < 8 * 1024**3:
        raise RuntimeError('Docker free disk below 8 GiB')
    mem_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))
    if mem_kib < 3 * 1024**2:
        raise RuntimeError('available memory below 3 GiB')
    if not BACKUP.is_dir() or not (BACKUP / 'backup.key').is_file():
        raise RuntimeError('verified private backup unavailable')


def setup(state):
    source = (REPO / 'infra/compose.yaml').read_text()
    if source.count('centrochange-dev') < 10:
        raise RuntimeError('pinned Compose topology drift')
    source = source.replace('centrochange-dev', PROJECT)
    source = source.replace('127.0.0.1:${HTTP_PORT', '127.0.0.2:${HTTP_PORT')
    if 'centrochange-dev' in source or '127.0.0.2:${HTTP_PORT' not in source:
        raise RuntimeError('clone Compose transform failed')
    (state / 'compose.yaml').write_text(source)
    overlay = ['services:']
    for service in (*SERVICES, 'configurator'):
        overlay += [f'  {service}:', f'    image: {BASE}', '    pull_policy: never',
                    '    volumes:', f'      - {PROJECT}-{service}-logs:/home/frappe/frappe-bench/logs']
        if service == 'frontend':
            overlay += ['    networks:', f'      {PROJECT}-net:', '        aliases:', f'          - {SITE}']
    overlay += ['volumes:']
    for service in (*SERVICES, 'configurator'):
        overlay += [f'  {PROJECT}-{service}-logs:', f'    name: {PROJECT}-{service}-logs']
    (state / 'overlay.yaml').write_text('\n'.join(overlay) + '\n')
    existing = dict(line.split('=', 1) for line in
                    Path('/home/empv26/.local/state/centrochange-single/runtime.env').read_text().splitlines()
                    if '=' in line and not line.startswith('#'))
    if existing.get('SITE_NAME') != SITE or existing.get('HTTP_PORT') != '8082':
        raise RuntimeError('DEV source env Site/port drift')
    clone_password = secrets.token_urlsafe(30)
    (state / 'runtime.env').write_text(
        f'SITE_NAME={SITE}\nHTTP_PORT=8082\nDB_PASSWORD={clone_password}\n'
        f'ADMIN_PASSWORD={existing["ADMIN_PASSWORD"]}\nCC_UAT_IMAGE={BASE}\n')
    (state / 'runtime.env').chmod(0o600)
    verify_isolation(state)
    run(compose(state) + ['up', '-d', '--no-deps', 'db', 'redis-cache', 'redis-queue'])
    for _ in range(60):
        rows = run(compose(state) + ['ps', '--format', 'json']).stdout.decode()
        if rows.count('healthy') >= 3:
            break
        time.sleep(2)
    else:
        raise RuntimeError('isolated database/Redis unhealthy')
    volume = PROJECT + '-sites'
    run(['docker', 'run', '--rm', '--network', 'none', '-u', '0', '-v', volume + ':/target',
         '--entrypoint', 'sh', BASE, '-c',
         'cp -a /home/frappe/frappe-bench/sites/. /target/ && '
         'mkdir -p /target/centrochange.local/private/backups && chown -R 1000:0 /target'])
    manifest = json.loads((BACKUP / 'backup-manifest.json').read_text())
    names = {'db':'database.sql.gz', 'public':'files.tgz',
             'private':'private-files.tgz', 'config':'site_config.json'}
    for kind, name in names.items():
        item = manifest[kind]
        payload = run(['gpg', '--batch', '--quiet', '--pinentry-mode', 'loopback',
                       '--passphrase-file', str(BACKUP / 'backup.key'), '--decrypt',
                       str(BACKUP / item['file'])]).stdout
        if sha(payload) != item['sha256'] or len(payload) != item['bytes']:
            raise RuntimeError(f'backup {kind} integrity failed')
        target = state / name
        target.write_bytes(payload)
        target.chmod(0o600)
    run(['docker', 'cp', 'centrochange-dev-backend-1:/home/frappe/frappe-bench/sites/common_site_config.json',
         str(state / 'common_site_config.json')])
    run(['docker', 'run', '--rm', '--network', 'none', '-u', '0', '-v', volume + ':/target',
         '-v', str(state) + ':/source:ro', '--entrypoint', 'sh', BASE, '-c',
         'cp /source/site_config.json /target/centrochange.local/site_config.json && '
         'cp /source/database.sql.gz /source/files.tgz /source/private-files.tgz '
         '/target/centrochange.local/private/backups/ && '
         'cp /source/common_site_config.json /target/common_site_config.json && '
         'chown -R 1000:0 /target/centrochange.local /target/common_site_config.json'])
    bench = '/home/frappe/frappe-bench'
    run(compose(state) + ['run', '--rm', '--no-deps', 'backend', 'bench', '--site', SITE,
         'restore', f'{bench}/sites/{SITE}/private/backups/database.sql.gz',
         '--db-root-password', clone_password,
         '--with-public-files', f'{bench}/sites/{SITE}/private/backups/files.tgz',
         '--with-private-files', f'{bench}/sites/{SITE}/private/backups/private-files.tgz', '--force'])
    site_config = json.loads((state / 'site_config.json').read_text())
    db_name, password = site_config['db_name'], site_config['db_password']
    if not re.fullmatch(r'_[a-z0-9]+', db_name) or "'" in password:
        raise RuntimeError('restored Site DB credentials unsafe')
    sql = (f"CREATE USER IF NOT EXISTS '{db_name}'@'%' IDENTIFIED BY '{password}'; "
           f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_name}'@'%'; FLUSH PRIVILEGES;")
    run(['docker', 'exec', '-i', f'{PROJECT}-db-1', 'sh', '-c',
         'mariadb -uroot -p"$MYSQL_ROOT_PASSWORD"'], input_bytes=sql.encode())
    run(compose(state) + ['up', '-d', '--no-deps', *SERVICES])
    for _ in range(60):
        result = run(['curl', '--silent', '--output', '/dev/null', '--write-out', '%{http_code}',
                      '--resolve', f'{SITE}:8082:127.0.0.2', f'http://{SITE}:8082/login'], check=False)
        if result.stdout == b'200':
            return
        time.sleep(2)
    raise RuntimeError('isolated Frappe login unavailable')


def build_candidate(state):
    context = state / 'build'; context.mkdir(mode=0o700)
    dockerfile = [f'FROM {BASE_TAG}', 'USER root']
    for index, relative in enumerate(CHANGED):
        source = REPO / APP_PREFIX / relative
        destination = context / str(index)
        shutil.copy2(source, destination)
        destination.chmod(0o644)
        dockerfile.append(f'COPY --chown=1000:0 {index} '
                          f'/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/{relative}')
    dockerfile += ['USER 1000', 'LABEL centrochange.locale_rehearsal="134"']
    (context / 'Dockerfile').write_text('\n'.join(dockerfile) + '\n')
    image = f'centrochange-single:issue134-locale-rehearsal-{state.name}'
    run(['docker', 'build', '--network', 'none', '-t', image, str(context)])
    return image


def main():
    global ERROR_LOG
    preflight()
    import importlib.util
    spec = importlib.util.spec_from_file_location('cc_dev_readonly', REPO / 'infra/goal02_install_one_command.py')
    dev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev)
    before = {'services':dev.snapshot(), 'data':dev.runtime_fingerprint(), 'hooks':dev.hooks()}
    STATE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    state = STATE_ROOT / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}')
    state.mkdir(mode=0o700)
    ERROR_LOG = state / 'error.stderr'
    result = {'status':'BLOCKED', 'clone_project':PROJECT, 'dev_mutated':False}
    try:
        setup(state)
        result['baseline_clone'] = 'PASS'
        image = build_candidate(state)
        result['candidate_image'] = image
        # Candidate changes remain scoped to the clone. The six services all
        # use one image; no DEV Compose file, tag or volume is touched.
        overlay = (state / 'overlay.yaml').read_text().replace(BASE, image)
        (state / 'overlay.yaml').write_text(overlay)
        verify_isolation(state)
        run(compose(state) + ['up', '-d', '--no-deps', '--force-recreate', *SERVICES])
        result['candidate_clone'] = 'PASS'
        for index, relative in enumerate(CHANGED):
            expected = sha((state / 'build' / str(index)).read_bytes())
            actual = run(['docker', 'exec', f'{PROJECT}-backend-1', 'sha256sum',
                          '/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/' + relative])
            if actual.stdout.decode().split()[0] != expected:
                raise RuntimeError(f'clone app source mismatch: {relative}')
        result['candidate_source'] = 'PASS'
        print(json.dumps({'phase':'ISOLATED_CANDIDATE_RUNNING','state':str(state)}), flush=True)
        # Same invalidation planned for the gated DEV executor, only on clone.
        refresh = '''import frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.client_cache.delete_value("app_hooks")
from frappe.translate import clear_cache
clear_cache()
assert "centrochange_core.operations.website_brand.client_time_format" in frappe.get_hooks("boot_session")
frappe.db.rollback()
frappe.destroy()
print("CC_LOCALE_HOOK=PASS")
'''
        output = run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1',
                      '-w', '/home/frappe/frappe-bench/sites',
                      f'{PROJECT}-backend-1', '/home/frappe/frappe-bench/env/bin/python', '-'],
                     input_bytes=refresh.encode()).stdout
        if b'CC_LOCALE_HOOK=PASS' not in output:
            raise RuntimeError('isolated locale hook/cache invalidation failed')
        result['hook_cache'] = 'PASS'
        browser = Path('/home/empv26/.local/state/centrochange-single/issue134-cumulative-locale') / state.name
        browser.mkdir(mode=0o700, parents=True, exist_ok=False)
        account = pwd.getpwnam('empv26')
        os.chown(browser, account.pw_uid, account.pw_gid)
        browser.chmod(0o700)
        shots = browser / 'screenshots'; shots.mkdir(mode=0o700)
        os.chown(shots, account.pw_uid, account.pw_gid)
        environment = [f'CC_DEMO_FIXTURE=/home/empv26/.local/state/centrochange-single/demo-owner.json',
                       f'CC_BROWSER_IP=127.0.0.2',
                       'NODE_PATH=/tmp/cc-browser-qa/node_modules',
                       'LD_LIBRARY_PATH=/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu']
        sweeps = [] if os.environ.get('CC_LOCALE_CLONE_PRINT_ONLY') == '1' else [
            ('routes', ['CC_INVENTORY_FORMS=0']),
            ('forms', ['CC_INVENTORY_ROUTES=0', 'CC_INVENTORY_ROLES=m,f'])]
        if os.environ.get('CC_LOCALE_CLONE_TARGETED') == '1':
            sweeps = [('routes', ['CC_INVENTORY_FORMS=0', 'CC_INVENTORY_ROLES=m,f',
                                  'CC_INVENTORY_ROUTE_FILTER=@agenda,cc_view=agenda&cc_ops_view=Notifiche,/app/item,/app/appointment-type']),
                      ('forms', ['CC_INVENTORY_ROUTES=0', 'CC_INVENTORY_ROLES=m,f',
                                  'CC_INVENTORY_FORM_FILTER=sales-invoice,purchase-invoice'])]
        for name, extra in sweeps:
            args = ['runuser', '-u', 'empv26', '--', 'env', *environment,
                    f'CC_INVENTORY_OUTPUT={browser / (name + ".json")}', *extra,
                    f'CC_INVENTORY_SCREENSHOTS={shots}',
                    'node', str(REPO / 'infra/browser/issue134_visible_text_inventory.cjs')]
            outcome = run(args, check=False)
            if outcome.returncode:
                raise RuntimeError(f'isolated {name} browser inventory failed; private output retained')
            result[name] = json.loads(outcome.stdout.decode().splitlines()[-1])
        args = ['runuser', '-u', 'empv26', '--', 'env', *environment,
                f'CC_INVENTORY_OUTPUT={browser}', 'node',
                str(REPO / 'infra/browser/issue134_print_inventory.cjs')]
        outcome = run(args, check=False)
        if outcome.returncode:
            (state / 'print.stderr').write_bytes(outcome.stderr)
            (state / 'print.stdout').write_bytes(outcome.stdout)
            raise RuntimeError('isolated HTML/PDF browser probe failed; private output retained')
        result['print'] = json.loads(outcome.stdout.decode().splitlines()[-1])
        pdf_text = run(['docker', 'run', '--rm', '--network', 'none', '-v', str(browser)+':/probe:ro',
                        '--entrypoint', '/home/frappe/frappe-bench/env/bin/python', image,
                        '-c', 'from pypdf import PdfReader; import json; '
                        'r=PdfReader("/probe/invoice.pdf"); '
                        'print(json.dumps({"pages":len(r.pages),"text":" ".join(p.extract_text() or "" for p in r.pages)}))']).stdout
        (browser / 'pdf-text.json').write_bytes(pdf_text)
        (browser / 'pdf-text.json').chmod(0o600)
        parsed = json.loads(pdf_text)
        result['pdf_pages'] = parsed['pages']
        if parsed['pages'] < 1 or not parsed['text'].strip():
            raise RuntimeError('isolated PDF text extraction failed')
        printed = json.loads((browser / 'print-inventory.json').read_text())
        if not printed['html']['title'].startswith('Fattura paziente: '):
            raise RuntimeError('native browser print title remains English')
        for source in (printed['html']['text'], parsed['text']):
            if re.search(r'\b(?:Sales Invoice|Billed To|Italy|Nos)\b', source):
                raise RuntimeError('invoice HTML/PDF retains an English operator label')
        result['status'] = 'PASS'
    except Exception as error:
        result['failure'] = f'{type(error).__name__}: {str(error)[:200]}'
    finally:
        if (state / 'runtime.env').is_file() and (state / 'compose.yaml').is_file():
            run(compose(state) + ['down', '-v', '--remove-orphans'], check=False)
        remaining = run(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={PROJECT}', '-q']).stdout.strip()
        if remaining:
            result['status'] = 'CLEANUP_FAILED'
        else:
            result['clone_cleanup'] = 'PASS'
            image = result.get('candidate_image')
            if image and image.startswith('centrochange-single:issue134-locale-rehearsal-'):
                run(['docker', 'image', 'rm', image], check=False)
        for name in ('database.sql.gz', 'files.tgz', 'private-files.tgz',
                     'site_config.json', 'common_site_config.json', 'runtime.env'):
            (state / name).unlink(missing_ok=True)
        if any((state / name).exists() for name in ('database.sql.gz', 'files.tgz',
                                                   'private-files.tgz', 'site_config.json')):
            result['status'] = 'CLEANUP_FAILED'
        after = {'services':dev.snapshot(), 'data':dev.runtime_fingerprint(), 'hooks':dev.hooks()}
        result['dev_unchanged'] = before == after
        if not result['dev_unchanged']:
            result['status'] = 'SECURITY_STOP'
        (state / 'summary.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
