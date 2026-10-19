#!/usr/bin/env python3
"""One nonfinancial, exact-cleanup role save check on the current DEV image."""
import importlib.util
import json
import os
from pathlib import Path
import pwd
import secrets
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'infra'))
from fixture_command import execute_fixture

spec=importlib.util.spec_from_file_location('gate',ROOT/'infra/issue139_install_gate.py')
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
IMAGE='sha256:47d753955c81033b11317381b5fdc63aa5e438cec304e57e93a0b6c0215b6758'
RUN=gate.STATE/'browser-evidence/mvp-devfirst-role-saves'


def main():
    assert os.geteuid()==0 and sys.flags.isolated
    module=gate.old_probe()
    services=module.snapshot()
    assert len(services)==9 and all(services[name]['image']==IMAGE for name in gate.APP)
    assert module.hooks()==module.GUARDS
    before=module.runtime_fingerprint()
    permissions=gate.permission_fingerprint(module)
    directory=RUN/('run-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+secrets.token_hex(2))
    directory.mkdir(mode=0o700,parents=True,exist_ok=False)
    account=pwd.getpwnam('empv26')
    os.chown(directory,account.pw_uid,account.pw_gid)
    fixture=None
    result=None
    cleanup=None
    failure=None
    try:
        fixture=execute_fixture('centrochange_core.security.dev_acceptance.create_http',
            {'scheduling':True,'operations':False,'finance':False,'finance_users':False,'public_route':False},
            diagnostic_dir=directory)
        fixture_path=directory/'fixture.json'
        gate.private_write(fixture_path,json.dumps(fixture).encode())
        os.chown(fixture_path,account.pw_uid,account.pw_gid)
        environment=['PATH=/usr/sbin:/usr/bin:/sbin:/bin','HOME=/home/empv26',
            'NODE_PATH=/tmp/cc-browser-qa/node_modules',
            'LD_LIBRARY_PATH=/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
            'CC_BASE_URL=http://centrochange.local:8082',
            f'CC_ROLE_FIXTURE={fixture_path}',f'CC_ROLE_OUTPUT={directory}']
        browser=subprocess.run(['runuser','-u','empv26','--','/usr/bin/env',*environment,
            'node',str(ROOT/'infra/browser/mvp_devfirst_role_saves.cjs')],
            cwd=ROOT,capture_output=True,text=True,timeout=180)
        gate.private_write(directory/'browser.log',(browser.stdout+'\n'+browser.stderr).encode())
        result=json.loads((directory/'role-saves.json').read_text()) if (directory/'role-saves.json').exists() else None
        if browser.returncode or result is None or result['status']!='PASS':
            failure='browser_save_failed'
    except (OSError,ValueError,subprocess.TimeoutExpired,Exception) as error:
        failure=type(error).__name__
    finally:
        if fixture:
            users=[row['name'] for row in fixture['users'].values()]
            for _ in range(30):
                pending=execute_fixture('centrochange_core.security.dev_acceptance.pending_contacts',
                    {'users':users},diagnostic_dir=directory)
                if pending['pending']==0:
                    break
                time.sleep(1)
            if pending['pending']:
                failure='pending_contact_jobs'
            else:
                try:
                    cleanup=execute_fixture('centrochange_core.security.dev_acceptance.recover_http',
                        {'tag':fixture['tag']},diagnostic_dir=directory)
                except Exception as error:
                    cleanup={'cleanup':'FAIL','type':type(error).__name__}
                    failure=failure or 'exact_cleanup_failed'
            (directory/'fixture.json').unlink(missing_ok=True)
    after=module.runtime_fingerprint()
    unchanged=after==before and gate.permission_fingerprint(module)==permissions and module.hooks()==module.GUARDS and module.snapshot()==services
    status='PASS' if not failure and cleanup=={'cleanup':'PASS'} and unchanged else 'FAIL'
    report={'status':status,'checks':result['checks'] if result else [],'failure':failure,
            'cleanup':cleanup,'baseline_restored':unchanged,'candidate_image':IMAGE}
    gate.private_write(directory/'report.json',json.dumps(report,indent=2).encode())
    print(json.dumps({'status':status,'checks':len(report['checks']),'cleanup':cleanup,
        'baseline_restored':unchanged,'failure':failure,'evidence':str(directory)}))
    return 0 if status=='PASS' else 2


if __name__=='__main__':
    raise SystemExit(main())
