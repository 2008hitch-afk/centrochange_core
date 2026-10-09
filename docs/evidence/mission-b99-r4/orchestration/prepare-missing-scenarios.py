import ops
code="""
from centrochange_core.uat import demo
from centrochange_core.finance import ts,incoming
from centrochange_core.finance.incoming_acceptance import xml
from centrochange_core.security.audit import serialize
x=demo.read();d=x.get('demo',x);f=x.get('fixture',d.get('fixture'));assert f
frappe.set_user(f['users']['m']['name'])
source=d['sources']['Beta parzialmente incassata'];inv=d['invoices']['Beta parzialmente incassata'];previous=d['fiscal']['TS pending']
r=ts.review_inputs(source,inv,'No Opposition','SYNTHETIC_ELIGIBLE','R4-BETA-REVIEW','SYNTHETIC R4 missing browser scenario',expense_amount=100,expense_code='SYNTHETIC_EXPENSE')['name']
ready=ts.prepare(source,inv,'R4-BETA-CORRECTION','SYNTHETIC R4 missing browser scenario',input_review=r,corrects=previous)['name']
print('TS_SCENARIO='+json.dumps({'previous_retained':frappe.db.get_value('CC Fiscal Transaction',previous,'status'),'current':frappe.db.get_value('CC Fiscal Transaction',ready,'status'),'corrects':previous,'attempts':frappe.db.get_value('CC Fiscal Transaction',ready,'attempt_count')}))
frappe.db.commit()
original=frappe.get_doc('Purchase Invoice',d['incoming']['payable']);supplier=original.supplier;issuer=frappe.db.get_value('Supplier',supplier,'tax_id')
source=incoming.intake(f['centers'][0],xml(issuer,'SYNTHETIC-R4-CANCELLED'),'SYNTHETIC R4 missing accounting scenario')['name']
incoming.bind_supplier(source,supplier,'SYNTHETIC R4 missing accounting scenario')
new=incoming.draft(source,[original.items[0].item_code],original.items[0].expense_account,'2026-10-05','2026-10-31','R4-CANCELLED-PI','SYNTHETIC R4 missing accounting scenario')['name']
incoming.submit(new,'SYNTHETIC R4 missing accounting scenario');incoming.cancel(new,'SYNTHETIC R4 missing accounting scenario')
frappe.db.commit();print('CANCELLED_PI_SCENARIO='+json.dumps({'name':new,'docstatus':frappe.db.get_value('Purchase Invoice',new,'docstatus'),'original_retained':frappe.db.get_value('Purchase Invoice',original.name,'docstatus')}));frappe.destroy()
"""
print(ops.execute(code,'missing-browser-fixtures'))
