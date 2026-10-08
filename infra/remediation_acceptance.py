#!/usr/bin/env python3
"""Composed GOAL-02 rollback-only backend review. No dataset reset/seed."""
import json
import os
from pathlib import Path
import subprocess

MODULES = (
    'operations.integration_acceptance', 'security.audit_view_acceptance',
    'scheduling.reopen_acceptance', 'finance.expectation_ui_acceptance',
    'finance.bank_trace_acceptance', 'operations.confirmation_acceptance',
    'operations.search_acceptance', 'finance.professional_view_acceptance',
    'finance.patient_report_acceptance', 'security.final_review_acceptance', 'uat.acceptance',
)


def main():
    os.umask(0o077)
    code = '''import importlib,json,hashlib,frappe
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
frappe.set_user('Administrator')
tracked=['Patient','Patient Appointment','Sales Invoice','Purchase Invoice','Payment Entry','GL Entry','Payment Ledger Entry','CC Audit Event','CC Booking Confirmation','Communication']
tracked+=['CC Center Membership','CC Patient Assignment','CC Professional Expectation','CC Unpaid Threshold','CC TS Input Review','CC Fiscal Transaction','CC Economic Source Link','Sales Invoice Item','Purchase Invoice Item','Payment Entry Reference','Bank Transaction','Bank Transaction Payments','Has Role']
before={dt:frappe.db.count(dt) for dt in tracked}
def digest():
 data={dt:frappe.get_all(dt,fields=['*'],order_by='name',limit_page_length=0) for dt in tracked}
 return hashlib.sha256(json.dumps(data,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
initial_digest=digest()
results={}
try:
 for module in MODULES:
  frappe.set_user('Administrator')
  try:
   results[module]=importlib.import_module('centrochange_core.'+module).run()
   assert results[module]['status']=='PASS'
  finally:frappe.db.rollback()
  assert before=={dt:frappe.db.count(dt) for dt in tracked}, 'Persistent synthetic data changed'
  assert initial_digest==digest(), 'Canonical persisted rows changed'
 print('CC_REVIEW_JSON='+json.dumps({'status':'PASS','results':results,'persistent_counts_unchanged':True,'canonical_rows_sha256_unchanged':True,'canonical_rows_sha256':initial_digest},default=str))
finally:frappe.db.rollback();frappe.destroy()
'''.replace('MODULES', repr(MODULES))
    result = subprocess.run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', 'centrochange-dev-backend-1', 'env/bin/python'], input=code, capture_output=True, text=True)
    log = Path('/tmp/cc-remediation-backend.log')
    log.write_text(result.stdout + result.stderr)
    os.chmod(log, 0o600)
    if result.returncode:
        raise RuntimeError('Backend regression failed; inspect private external diagnostic ' + str(log))
    line = next(line for line in reversed(result.stdout.splitlines()) if line.startswith('CC_REVIEW_JSON='))
    print(json.dumps(json.loads(line.split('=', 1)[1])))


if __name__ == '__main__':
    main()
