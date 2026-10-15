#!/usr/bin/env python3
"""Read-only final fingerprint/permission/hook check in the isolated W5 clone."""
import json, subprocess
from pathlib import Path
BASE_DATA='e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3'
BASE_COMM='b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2'
BASE_PERMS='97af394ec1d9b4fe18b551282c2ecec40b5b70558e0d4968dfadf341ec66b52c'
GUARDS=['centrochange_core.finance.request_guard.before_request',
        'centrochange_core.security.diagnostics.before_request',
        'centrochange_core.security.api.before_request',
        'centrochange_core.operations.notes.request_guard',
        'centrochange_core.operations.website_brand.client_language',
        'centrochange_core.operations.website_brand.login_language']
source='''import hashlib,json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
types=["Patient","Healthcare Practitioner","Patient Appointment","Sales Invoice","Purchase Invoice","Payment Entry","Bank Transaction","CC Audit Event","CC Booking Confirmation","CC Fiscal Transaction","CC Professional Comparison"]
rows={dt:frappe.get_all(dt,fields=["name","modified"],order_by="name",limit_page_length=0) for dt in types}
audit=frappe.get_all("CC Audit Event",filters={"event_type":"CENTER_OPERATIONAL_STATE","reference_doctype":"Branch","reference_name":"CC-HTTP-UAT0000001 A"},fields=["name","reason"],limit_page_length=0)
assert len(audit)==1 and audit[0].reason=="#139 isolated W5 rehearsal"
rows["CC Audit Event"]=[r for r in rows["CC Audit Event"] if r.name!=audit[0].name]
data=json.dumps(rows,sort_keys=True,default=str,separators=(",",":"))
communication=frappe.get_all("Communication",fields=["name","modified"],order_by="name",limit_page_length=0)
comm=json.dumps(communication,sort_keys=True,default=str,separators=(",",":"))
rights=("read","write","create","delete","submit","cancel","amend","report","export","import","share","print","email","select")
spec={"Custom DocPerm":["parent","role","permlevel",*rights],"Has Role":["parent","role"],"User Permission":["user","allow","for_value","apply_to_all_doctypes"],"DocShare":["user","share_doctype","share_name","read","write","share","submit"]}
permissions={}
for doctype,fields in spec.items():
 values=frappe.get_all(doctype,fields=fields,limit_page_length=0)
 permissions[doctype]=sorted([tuple(str(row.get(field) or "") for field in fields) for row in values])
perm=json.dumps(permissions,sort_keys=True,separators=(",",":"))
hooks=frappe.get_hooks("before_request",app_name="centrochange_core")
effective=frappe.get_hooks("before_request")
centers=[frappe.db.get_value("Branch",name,"cc_operational") for name in ("CC-HTTP-UAT0000001 A","CC-HTTP-UAT0000001 B")]
print("CC_ISOLATED_INTEGRITY="+json.dumps({"data_sha256":hashlib.sha256(data.encode()).hexdigest(),"communication_sha256":hashlib.sha256(comm.encode()).hexdigest(),"permission_sha256":hashlib.sha256(perm.encode()).hexdigest(),"hooks":hooks,"hook_counts":[effective.count(x) for x in hooks],"centers":centers,"counts":{dt:len(rows[dt]) for dt in types}}))
frappe.db.rollback();frappe.destroy()
'''
cmd=['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench/sites',
     'cc139-w5-isolated-backend-1','/home/frappe/frappe-bench/env/bin/python']
result=subprocess.run(cmd,input=source,text=True,capture_output=True,check=True)
row=json.loads(next(line.split('=',1)[1] for line in result.stdout.splitlines() if line.startswith('CC_ISOLATED_INTEGRITY=')))
assert row['data_sha256']==BASE_DATA and row['communication_sha256']==BASE_COMM
assert row['permission_sha256']==BASE_PERMS
assert row['hooks']==GUARDS and row['hook_counts']==[1]*6
assert row['centers']==[1,0]
print(json.dumps({'status':'PASS','data_baseline_except_one_audit':True,'permissions_unchanged':True,
                  'six_hooks':True,'center_a_active':True,'center_b_inactive':True,'counts':row['counts']}))
