import ops
code="""
import traceback
from centrochange_core.security import dev_acceptance as fixtures
from centrochange_core.finance import receivables_acceptance as tests,receivables
f=None
try:
 f=fixtures.create_http(scheduling=True,operations=True,finance=True,public_route=False)
 prepared=tests.prepare_http(f)
 frappe.set_user(f['users']['f']['name'])
 print('FINANCE_PRINCIPAL='+json.dumps({'roles':frappe.get_roles(),'permissions':{dt:frappe.has_permission(dt,'read') for dt in ['Sales Invoice','Payment Entry','Sales Taxes and Charges Template','Company','Customer','Account']}}))
 try: print('DRAFT_RESULT='+json.dumps(receivables.draft([prepared['source']],'2026-10-05','2026-10-31',f['tag']+'-diagnostic',f['tag']),default=str))
 except Exception:traceback.print_exc()
finally:
 frappe.set_user('Administrator')
 if f:fixtures.recover_http(f['tag'])
 frappe.destroy()
"""
print(ops.execute(code,'finance-root-cause'))
