#!/usr/bin/env python3
"""One approved synthetic POS proof on the installed DEV, with retained native history."""
import importlib.util
import json
import os
from pathlib import Path
import pwd
import secrets
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('gate', ROOT / 'infra/issue139_install_gate.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
IMAGE = 'sha256:e2df539cc99fee6965102f539c0969dbec98d2ad59bf7c0d9631d4e03774acdb'
SCRIPT = ROOT / 'infra/mvp_pos_retained_runtime.py'
DEMO = gate.STATE / 'demo-owner.json'
BACKUP = gate.STATE / 'issue139-install-runs/20261019T201455Z-3466982'


def runtime(stage, tag, invoice='', payment='', evidence=None):
    env = ['-e', 'FRAPPE_STREAM_LOGGING=1', '-e', f'CC_POS_TEST_TAG={tag}']
    if invoice:
        env += ['-e', f'CC_POS_INVOICE={invoice}']
    if payment:
        env += ['-e', f'CC_POS_PAYMENT={payment}']
    command = ['docker', 'exec', '-i', *env, '-w', '/home/frappe/frappe-bench/sites',
        'centrochange-dev-backend-1', '/home/frappe/frappe-bench/env/bin/python', '-', stage]
    result = subprocess.run(command, input=SCRIPT.read_text(), text=True,
        capture_output=True, timeout=150)
    if evidence:
        gate.private_write(evidence / f'{stage}.log', (result.stdout + '\n' + result.stderr).encode())
    lines = [line.split('=', 1)[1] for line in result.stdout.splitlines() if line.startswith('CC_POS_STAGE=')]
    value = json.loads(lines[-1]) if lines else {'status': 'NO_RESULT'}
    if result.returncode:
        raise RuntimeError(f'{stage} failed: {value.get("error_type", "unknown")}; see private log')
    return value


def backup_ok():
    manifest = json.loads((BACKUP / 'backup-manifest.json').read_text())
    import hashlib
    for kind, part in manifest.items():
        encrypted = BACKUP / part['file']
        command = ['gpg', '--batch', '--quiet', '--pinentry-mode', 'loopback',
            '--passphrase-file', str(BACKUP / 'backup.key'), '--decrypt', str(encrypted)]
        result = subprocess.run(command, capture_output=True, timeout=120)
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != part['sha256']:
            raise RuntimeError(f'backup part {kind} is not recoverable')
    return len(manifest)


def preexisting_records(module):
    code = '''import json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
spec={"Patient":["name","modified"],"Patient Appointment":["name","modified"],
"Customer":["name","modified"],"Sales Invoice":["name","modified","docstatus","outstanding_amount"],
"Payment Entry":["name","modified","docstatus"],"GL Entry":["name","modified","debit","credit","is_cancelled"],
"Payment Ledger Entry":["name","modified","amount","delinked"],"Branch":["name","modified","cc_operational"],
"Mode of Payment":["name","modified"]}
data={kind:{row.name:[str(row.get(field)) for field in fields[1:]] for row in
frappe.get_all(kind,fields=fields,limit_page_length=0)} for kind,fields in spec.items()}
print("CC_PRIOR="+json.dumps(data,sort_keys=True));frappe.db.rollback();frappe.destroy()
'''
    output = module.backend_python(code)
    return json.loads(next(row.split('=', 1)[1] for row in output.splitlines()
                           if row.startswith('CC_PRIOR=')))


def main():
    assert os.geteuid() == 0 and sys.flags.isolated
    module = gate.old_probe()
    services = module.snapshot()
    assert len(services) == 9 and all(services[name]['image'] == IMAGE for name in gate.APP)
    assert module.hooks() == module.GUARDS
    before = module.runtime_fingerprint()
    assert before['sha256'] == 'f5cea384c350dc8780818ccec752a314885085b8f14afb49a9c34115fa68b517'
    permissions = gate.permission_fingerprint(module)
    prior = preexisting_records(module)
    assert DEMO.is_file() and DEMO.stat().st_mode & 0o077 == 0
    assert backup_ok() == 4
    tag = 'CC-MVP-POS-' + secrets.token_hex(6)
    assert runtime('preflight', tag)['status'] == 'PASS'
    evidence = gate.STATE / 'browser-evidence' / ('mvp-pos-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    evidence.mkdir(mode=0o700)
    account = pwd.getpwnam('empv26')
    os.chown(evidence, account.pw_uid, account.pw_gid)
    result_path = evidence / 'browser-result.json'
    gate.private_write(evidence / 'authorization.json', json.dumps({
        'owner_authorization': '2026-10-19 last-two-capabilities, one synthetic POS proof',
        'tag': tag, 'image': IMAGE, 'before': before, 'backup': str(BACKUP),
        'script_sha256': __import__('hashlib').sha256(SCRIPT.read_bytes()).hexdigest(),
    }, indent=2).encode())
    invoice = ''
    payment = ''
    prepared = None
    browser_status = 'NOT_RUN'
    cleanup = 'NOT_RUN'
    failure = None
    try:
        prepared = runtime('prepare', tag, evidence=evidence)
        invoice = prepared['invoice']
        browser_env = {'PATH': '/usr/bin:/bin', 'HOME': '/home/empv26',
            'LD_LIBRARY_PATH': '/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
            'CC_CHROMIUM': '/home/empv26/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell',
            'CC_DEMO_CREDENTIALS': str(DEMO), 'CC_POS_TEST_TAG': tag,
            'CC_POS_INVOICE': invoice, 'CC_POS_MODE': prepared['mode'],
            'CC_POS_EVIDENCE': str(evidence),
            'CC_POS_RESULT': str(result_path)}
        run = subprocess.run(['runuser', '-u', 'empv26', '--', '/usr/bin/env',
            *(f'{key}={value}' for key, value in browser_env.items()),
            'node', str(ROOT / 'infra/browser/mvp_pos_retained_live.cjs')],
            capture_output=True, text=True, timeout=180)
        gate.private_write(evidence / 'browser.log', (run.stdout + '\n' + run.stderr).encode())
        browser_status = 'PASS' if run.returncode == 0 else 'FAIL'
        if result_path.exists():
            payment = json.loads(result_path.read_text())['payment']
        if browser_status != 'PASS':
            failure = 'browser_flow_failed'
    except Exception as error:
        failure = failure or type(error).__name__
    finally:
        if invoice:
            try:
                observed = runtime('inspect', tag, invoice=invoice, evidence=evidence)
                matches = observed['matching_payments']
                if not payment and len(matches) == 1:
                    payment = matches[0]
                if len(matches) > 1 or (matches and matches != [payment]):
                    raise RuntimeError('ambiguous synthetic payment dependencies')
                final = runtime('finalize', tag, invoice=invoice, payment=payment, evidence=evidence)
                cleanup = 'PASS' if final['retained_native_history'] else 'FAIL'
            except Exception as error:
                cleanup = 'FAIL'
                failure = failure or type(error).__name__
        after = module.runtime_fingerprint()
        current = preexisting_records(module)
        prior_unchanged = all(current[kind].get(name) == values
            for kind, rows in prior.items() for name, values in rows.items())
        controls = {'services': module.snapshot() == services,
            'hooks': module.hooks() == module.GUARDS,
            'permissions': gate.permission_fingerprint(module) == permissions,
            'same_database': after['db_sha256'] == before['db_sha256'],
            'preexisting_records': prior_unchanged,
            'communications': after['communication_sha256'] == before['communication_sha256']}
        status = 'PASS' if not failure and browser_status == 'PASS' and cleanup == 'PASS' and all(controls.values()) else 'FAIL'
        report = {'status': status, 'browser': browser_status, 'native_reversal': cleanup,
            'failure': failure, 'controls': controls, 'before': before,
            'after': after, 'invoice': invoice, 'payment': payment,
            'retained_history_expected': bool(invoice)}
        gate.private_write(evidence / 'report.json', json.dumps(report, indent=2).encode())
        print(json.dumps({'status': status, 'browser': browser_status, 'native_reversal': cleanup,
            'failure': failure, 'controls': controls, 'evidence': str(evidence)}))
    return 0 if status == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
