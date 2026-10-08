#!/usr/bin/env python3
"""Read-only DEV synthetic canonical-row fingerprint; never print source values."""
import json
import subprocess


def main():
    code='''import json,hashlib,frappe
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
try:
 assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
 frappe.set_user('Administrator')
 tracked=['Patient','Patient Appointment','Healthcare Practitioner','CC Center Membership','CC Patient Assignment','CC Private Note','CC Organizational Note','CC Patient Package','CC Package Ledger','CC Settlement','CC Economic Source Link','CC Professional Expectation','CC Unpaid Threshold','CC Professional Comparison','CC TS Input Review','CC Fiscal Transaction','CC Fiscal Attempt','CC Audit Event','CC Booking Confirmation','Sales Invoice','Sales Invoice Item','Purchase Invoice','Purchase Invoice Item','Payment Entry','Payment Entry Reference','Bank Transaction','Bank Transaction Payments','GL Entry','Payment Ledger Entry','Has Role','Custom DocPerm']
 rows={dt:frappe.get_all(dt,fields=['*'],order_by='name',limit_page_length=0) for dt in tracked}
 digest=hashlib.sha256(json.dumps(rows,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
 print('CC_FINGERPRINT='+json.dumps({'status':'PASS','canonical_rows_sha256':digest,'counts':{dt:len(data) for dt,data in rows.items()},'mutations':'NONE'}))
finally:frappe.db.rollback();frappe.destroy()
'''
    result=subprocess.run(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench','centrochange-dev-backend-1','env/bin/python'],input=code,text=True,capture_output=True)
    if result.returncode:raise RuntimeError('Read-only synthetic fingerprint failed')
    line=next(s for s in result.stdout.splitlines() if s.startswith('CC_FINGERPRINT='))
    print(json.dumps(json.loads(line.split('=',1)[1])))


if __name__=='__main__':main()
