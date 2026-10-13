#!/usr/bin/env python3
"""Run the versioned UAT-11 probe in the existing DEV process, without deployment.

The probe source is sent through stdin and executed in memory. Its synthetic
fixtures and audit rows are rolled back; no container source file is changed.
"""

import base64
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'app/centrochange_core/centrochange_core/scheduling/historical_reopen_probe.py'
TRACKED = ('Patient', 'Patient Appointment', 'CC Audit Event', 'Version',
	'CC Center Membership', 'CC Patient Assignment', 'Practitioner Schedule',
	'Healthcare Schedule Time Slot', 'CC Settlement', 'Healthcare Practitioner',
	'Item', 'Item Price', 'Price List', 'Appointment Type', 'CC Center Service',
	'Branch', 'Event', 'Sales Invoice', 'Payment Entry', 'GL Entry',
	'Payment Ledger Entry')


def main():
	source = base64.b64encode(PROBE.read_bytes()).decode()
	code = '''import base64,hashlib,json,frappe
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
frappe.set_user('Administrator')
tracked=TRACKED
def digest():
 data={dt:frappe.get_all(dt,fields=['*'],order_by='name',limit_page_length=0) for dt in tracked}
 return hashlib.sha256(json.dumps(data,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
initial=digest()
try:
 namespace={'__name__':'cc_issue78_probe'}
 exec(compile(base64.b64decode(SOURCE), 'historical_reopen_probe.py', 'exec'), namespace)
 result=namespace['run']()
 assert result['status']=='PASS' and result['cleanup']=='rollback'
 assert digest()==initial, 'Persistent rows changed after rollback'
 print('CC_ISSUE78_JSON='+json.dumps({'status':'PASS','checks':result['checks'][:8],
  'cleanup':'rollback','persistent_rows_sha256_unchanged':True,'persistent_rows_sha256':initial}))
finally:frappe.db.rollback();frappe.destroy()
'''.replace('TRACKED', repr(TRACKED)).replace('SOURCE', repr(source))
	result = subprocess.run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1',
		'-w', '/home/frappe/frappe-bench', 'centrochange-dev-backend-1',
		'env/bin/python'], input=code, text=True, capture_output=True)
	if result.returncode:
		log = Path('/tmp/cc-issue78-probe-private.log')
		log.write_text(result.stdout + result.stderr)
		log.chmod(0o600)
		raise RuntimeError('UAT-11 probe failed; private diagnostic: ' + str(log))
	line = next(line for line in reversed(result.stdout.splitlines())
		if line.startswith('CC_ISSUE78_JSON='))
	print(line.removeprefix('CC_ISSUE78_JSON='))


if __name__ == '__main__':
	main()
