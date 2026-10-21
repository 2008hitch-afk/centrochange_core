#!/usr/bin/env python3
"""Temporary isolated Frappe clone for #75 Form CSS; never mutates DEV.

Reuses the proven #134 clone restore path with a distinct Docker namespace.
The only image delta is the candidate versioned CSS. The clone and volumes
are removed in finally; private screenshots remain outside Git.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
CLONE_SOURCE = REPO / 'infra/issue134_locale_clone.py'
spec = importlib.util.spec_from_file_location('verified_locale_clone', CLONE_SOURCE)
clone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clone)
clone.PROJECT = 'cc75-form-isolated'
clone.BASE = 'sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e'
clone.BASE_TAG = 'centrochange-single:issue134-cumulative'
clone.BACKUP = Path('/home/empv26/.local/state/centrochange-single/issue134-cumulative-install-runs/20261020T194425Z-454399')
clone.STATE_ROOT = Path('/home/empv26/.local/state/centrochange-single/issue75-form-isolated')
clone.CHANGED = ('public/css/cc_premium_nexus.css',)


def guard():
    if os.geteuid() or not sys.flags.isolated:
        raise RuntimeError('requires sudo python3 -I')
    for kind in ('container', 'volume', 'network'):
        args = ['docker', kind, 'ls', '-q', '--filter', f'name=^{clone.PROJECT}']
        if kind == 'container':
            args.insert(3, '-a')
        if clone.run(args).stdout.strip():
            raise RuntimeError(f'existing {clone.PROJECT} {kind} resource')
    image = json.loads(clone.run(['docker', 'image', 'inspect', clone.BASE]).stdout)[0]
    if image['Config']['Labels'].get('centrochange.source') != 'e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec':
        raise RuntimeError('DEV baseline image source drift')
    if clone.run(['docker', 'image', 'inspect', '--format', '{{.Id}}', clone.BASE_TAG]).stdout.decode().strip() != clone.BASE:
        raise RuntimeError('DEV baseline image tag drift')
    if shutil.disk_usage('/var/lib/docker').free < 8 * 1024**3:
        raise RuntimeError('Docker disk below 8 GiB')
    memory = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                  if line.startswith('MemAvailable:'))
    if memory < 3 * 1024**2:
        raise RuntimeError('available memory below 3 GiB')
    if not (clone.BACKUP / 'backup-manifest.json').is_file() or not (clone.BACKUP / 'backup.key').is_file():
        raise RuntimeError('verified encrypted backup unavailable')


def main():
    guard()
    clone.STATE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    state = clone.STATE_ROOT / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}')
    state.mkdir(mode=0o700)
    clone.ERROR_LOG = state / 'error.stderr'
    account = pwd.getpwnam('empv26')
    browser_root = Path('/home/empv26/.local/state/centrochange-single/browser-evidence')
    if browser_root.stat().st_uid != account.pw_uid or browser_root.stat().st_mode & 0o077:
        raise RuntimeError('private browser evidence directory has unsafe ownership or permissions')
    output = browser_root / 'issue75-form-isolated' / state.name
    output.mkdir(mode=0o700, parents=True)
    os.chown(output.parent, account.pw_uid, account.pw_gid)
    os.chmod(output.parent, 0o700)
    os.chown(output, account.pw_uid, account.pw_gid)
    report = {'status':'BLOCKED','clone_project':clone.PROJECT,'dev_mutated':False}
    image = None
    try:
        clone.setup(state)
        report['restore'] = 'PASS'
        image = clone.build_candidate(state)
        overlay = (state / 'overlay.yaml').read_text().replace(clone.BASE, image)
        (state / 'overlay.yaml').write_text(overlay)
        clone.verify_isolation(state)
        clone.run(clone.compose(state) + ['up','-d','--no-deps','--force-recreate',*clone.SERVICES])
        expected = hashlib.sha256((REPO / clone.APP_PREFIX / clone.CHANGED[0]).read_bytes()).hexdigest()
        observed = clone.run(['docker','exec',f'{clone.PROJECT}-backend-1','sha256sum',
            '/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/' + clone.CHANGED[0]])
        if observed.stdout.decode().split()[0] != expected:
            raise RuntimeError('candidate CSS not installed on clone')
        report['candidate_css'] = 'PASS'
        # The restored synthetic Site may have an outdated Manager password.
        # Rotate it only inside this isolated clone; never target a DEV container.
        if clone.PROJECT != 'cc75-form-isolated':
            raise RuntimeError('clone project identity drift')
        source_fixture = json.loads(Path('/home/empv26/.local/state/centrochange-single/demo-owner.json').read_text())
        private_fixture = json.loads(json.dumps(source_fixture))
        manager = (private_fixture.get('fixture') or private_fixture)['users']['m']
        manager_password = secrets.token_urlsafe(24)
        reset_code = '''import frappe,json,sys
from frappe.utils.password import update_password
payload=json.load(sys.stdin)
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
assert frappe.db.exists("User",payload["user"])
update_password(payload["user"],payload["password"])
frappe.db.commit()
frappe.destroy()
'''
        clone.run(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1',
                   '-w','/home/frappe/frappe-bench/sites',
                   f'{clone.PROJECT}-backend-1',
                   '/home/frappe/frappe-bench/env/bin/python','-c',reset_code],
                  input_bytes=json.dumps({'user':manager['name'],'password':manager_password}).encode())
        manager['password'] = manager_password
        fixture_path = output / 'clone-fixture.json'
        fixture_path.write_text(json.dumps(private_fixture))
        os.chown(fixture_path, account.pw_uid, account.pw_gid)
        fixture_path.chmod(0o600)
        env = [
            'NODE_PATH=/tmp/cc-browser-qa/node_modules',
            f'CC_DEMO_FIXTURE={fixture_path}',
            f'CC_CANDIDATE_CSS={REPO / clone.APP_PREFIX / clone.CHANGED[0]}',
            f'CC_OUTPUT_DIR={output}',
            'CC_BROWSER_IP=127.0.0.2',
            'CC_FORM_MANAGER=1',
        ]
        result = clone.run(['runuser','-u','empv26','--','env',*env,'node',
            str(REPO / 'infra/browser/issue75_native_form_affordance.cjs')], check=False)
        report['browser_exit_code'] = result.returncode
        if (output / 'results.json').is_file():
            rows = json.loads((output / 'results.json').read_text())
            report['browser'] = {status:sum(row['status']==status for row in rows)
                                 for status in ('PASS','FAIL','BLOCKED')}
        else:
            (state / 'browser.stderr').write_bytes(result.stderr)
        report['status'] = ('PASS' if report.get('browser',{}).get('PASS') == 22
                            else 'PARTIAL' if report.get('browser') else 'BLOCKED')
    except Exception as error:
        report['failure'] = f'{type(error).__name__}: {str(error)[:180]}'
    finally:
        if (state / 'runtime.env').exists():
            clone.run(clone.compose(state) + ['down','-v','--remove-orphans'],check=False)
        if image:
            clone.run(['docker','image','rm',image],check=False)
        for name in ('database.sql.gz','files.tgz','private-files.tgz',
                     'site_config.json','common_site_config.json','runtime.env'):
            (state / name).unlink(missing_ok=True)
        (output / 'clone-fixture.json').unlink(missing_ok=True)
        leftover = clone.run(['docker','ps','-a','-q','--filter',
                              f'label=com.docker.compose.project={clone.PROJECT}']).stdout.strip()
        report['cleanup'] = 'PASS' if not leftover else 'FAIL'
        if leftover:
            report['status'] = 'CLEANUP_FAILED'
        (state / 'summary.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({'status':report['status'],'restore':report.get('restore'),
                          'candidate_css':report.get('candidate_css'),
                          'browser':report.get('browser'),'cleanup':report['cleanup'],
                          'state':str(state),'failure':report.get('failure')}),flush=True)
    return 0 if report['status']=='PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
