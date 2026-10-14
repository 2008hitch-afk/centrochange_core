#!/usr/bin/env python3
"""Rollback-only GOAL-02 checks on the persistent synthetic single stack."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


PRIVATE_RUNS = Path('/home/empv26/.local/state/centrochange-single/goal02-install-runs')


def private_failure_log(stdout, stderr, directory=PRIVATE_RUNS):
    """Create a new root-owned diagnostic; never reuse a shared /tmp path."""
    directory = Path(directory)
    if not directory.is_dir() or directory.is_symlink():
        raise RuntimeError('Private GOAL-02 evidence directory unavailable')
    fd, name = tempfile.mkstemp(prefix='targeted-regression-', suffix='.log', dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as log:
            log.write(stdout)
            log.write(stderr)
        return Path(name)
    except Exception:
        Path(name).unlink(missing_ok=True)
        raise


MODULES = (
    'operations.integration_acceptance',
    'operations.confirmation_acceptance',
    'operations.search_acceptance',
    'security.final_review_acceptance',
)


def main():
    os.umask(0o077)
    code = '''import hashlib,importlib,json,frappe
from frappe.utils import getdate
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
frappe.set_user('Administrator')
tracked=['Patient','Patient Appointment','Sales Invoice','Purchase Invoice','Payment Entry','GL Entry','Payment Ledger Entry','CC Audit Event','CC Booking Confirmation','Communication','CC Center Membership','CC Patient Assignment','CC Professional Expectation','CC Unpaid Threshold','CC TS Input Review','CC Fiscal Transaction','CC Economic Source Link','Bank Transaction']
def digest():
 data={dt:frappe.get_all(dt,fields=['*'],order_by='name',limit_page_length=0) for dt in tracked}
 return hashlib.sha256(json.dumps(data,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
initial=digest();results={}
try:
 for module in MODULES:
  frappe.set_user('Administrator')
  try:
   result=importlib.import_module('centrochange_core.'+module).run()
   assert result['status']=='PASS',module
   results[module]=len(result.get('checks',[]))
  finally:frappe.db.rollback()
  assert digest()==initial,'Persistent rows changed after '+module
 from centrochange_core.security.audit_view import events
 tag='CC-HTTP-UAT0000001'
 for kind in ('PROFESSIONAL_UNPAID_THRESHOLD_CONFIGURED','TS_SYNTHETIC_INPUT_REVIEWED'):
  source=frappe.get_all('CC Audit Event',filters={'reason':tag,'event_type':kind},fields=['name','event_time'],limit_page_length=2)
  assert len(source)==1,(kind,len(source))
  date=str(getdate(source[0].event_time))
  frappe.set_user(tag.lower()+'-m@example.invalid')
  assert any(row.name==source[0].name and row.reason==tag for row in events(date,date,event_type=kind)['events']),kind
  frappe.set_user('Administrator')
 for suffix in ('a','b','c','s','f','t'):
  frappe.set_user(tag.lower()+'-'+suffix+'@example.invalid')
  try:events(date,date)
  except frappe.PermissionError:pass
  else:raise AssertionError('Audit access allowed for '+suffix)
 frappe.set_user('Guest')
 try:events(date,date)
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest audit access allowed')
 frappe.db.rollback();assert digest()==initial,'Persistent rows changed after audit read'
 print('CC_GOAL02_JSON='+json.dumps({'status':'PASS','module_checks':results,'audit_seed_events':2,'audit_denied_principals':7,'persistent_rows_sha256_unchanged':True,'persistent_rows_sha256':initial}))
finally:frappe.db.rollback();frappe.destroy()
'''.replace('MODULES', repr(MODULES))
    result = subprocess.run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w',
        '/home/frappe/frappe-bench/sites', 'centrochange-dev-backend-1',
        '/home/frappe/frappe-bench/env/bin/python'],
        input=code, capture_output=True, text=True)
    if result.returncode:
        log = private_failure_log(result.stdout, result.stderr)
        raise RuntimeError('Targeted regression failed; private diagnostic: ' + str(log))
    line = next(line for line in reversed(result.stdout.splitlines()) if line.startswith('CC_GOAL02_JSON='))
    print(json.dumps(json.loads(line.split('=', 1)[1])))


if __name__ == '__main__':
    main()
