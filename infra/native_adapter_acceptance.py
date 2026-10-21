"""Actual-principal positive/negative regression for service-owned native factories.

Explicit isolated Compose backend/site required; disposable synthetic records only.
"""
import argparse,json,subprocess

CODE = r'''
import frappe,json
frappe.init(site=SITE,sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
assert frappe.conf.get('cc_synthetic_dev')==1
from centrochange_core.security import dev_acceptance as fixtures
from centrochange_core.security.lifecycle import set_membership
from centrochange_core.finance import receivables,receivables_acceptance,native_adapter
from centrochange_core.finance.guards import require_synthetic
checks=[];f=None

def denied(fn):
    try:fn()
    except (frappe.PermissionError,frappe.ValidationError):return
    raise AssertionError('Unauthorized or invalid adapter call accepted')

try:
    f=fixtures.create_http(scheduling=True,operations=True,finance=True,public_route=False)
    prepared=receivables_acceptance.prepare_http(f)
    principal=f['users']['f']['name'];frappe.set_user(principal)
    inv=receivables.draft([prepared['source']],'2026-10-05','2026-10-31',f['tag']+'-adapter-invoice',f['tag'])['name']
    receivables.submit(inv,f['tag']);invoice=frappe.get_doc('Sales Invoice',inv)
    company=require_synthetic();bank=frappe.db.get_single_value('CC Finance Settings','bank_account') or frappe.db.get_value('Company',company,'default_cash_account')
    principal=f['users']['f']['name'];frappe.set_user(principal)
    roles=sorted(frappe.get_roles());assert 'CC Finance' in roles and 'CC Manager' not in roles
    assert not frappe.has_permission('Payment Entry','create')
    assert not frappe.has_permission('Sales Taxes and Charges Template','select')
    native_adapter.sales_taxes(f['centers'][0],company)
    from centrochange_core.security.audit import internal_write
    xml=frappe.get_doc({'doctype':'File','file_name':'synthetic-service.xml','attached_to_doctype':'Sales Invoice','attached_to_name':inv,'is_private':1,'content':'<synthetic/>'})
    denied(lambda:xml.validate_attachment_references())
    with internal_write('cc_accounting_write'):
        xml.validate_attachment_references()
        denied(lambda:xml.check_permission('delete'))
        xml.is_private=0;denied(lambda:xml.validate_attachment_references());xml.is_private=1
    checks.append('native Italy XML submitted under Finance; direct generic write and premature/public XML rejected')
    doc=native_adapter.payment_document(invoice,40,bank)
    assert doc.owner==principal and doc.party==invoice.customer and doc.paid_amount==doc.received_amount==40
    assert doc.references[0].allocated_amount==40 and doc.is_new()
    assert frappe.session.user==principal and sorted(frappe.get_roles())==roles
    checks.append('Finance own scoped factories work without native create/select or actor switch')
    forged=frappe.copy_doc(invoice);forged.name=invoice.name;forged.customer='UNAUTHORIZED';forged.cc_center=f['centers'][1]
    projected=native_adapter.payment_document(forged,40,bank)
    assert projected.party==invoice.customer and projected.cost_center==doc.cost_center
    checks.append('in-memory forged ownership/center ignored in favor of canonical locked invoice')
    for value in (0,-1,float('nan'),float('inf'),101):
        denied(lambda:native_adapter.payment_document(invoice,value,bank))
    checks.append('non-positive non-finite and over-balance payments rejected')
    denied(lambda:native_adapter.sales_taxes(f['centers'][1],company))
    denied(lambda:native_adapter.sales_taxes(f['centers'][0],'UNAUTHORIZED-COMPANY'))
    denied(lambda:native_adapter.payment_document(frappe.get_doc('Patient',f['patients'][0]),40,bank))
    checks.append('foreign center/company and non-invoice contexts rejected')
    for role in ('a','b','c','t'):
        frappe.set_user(f['users'][role]['name'])
        denied(lambda:native_adapter.sales_taxes(f['centers'][0],company))
        denied(lambda:native_adapter.payment_document(invoice,40,bank))
        with internal_write('cc_accounting_write'):
            denied(lambda:xml.validate_attachment_references())
        checks.append(role+' actual-principal native adapters denied')
    frappe.set_user(principal)
    result=receivables.pay(inv,40,'2026-10-05',f['tag']+'-adapter-pay',f['tag'])
    assert result['invoice']['outstanding']==60
    event=frappe.get_doc('CC Audit Event',{'event_type':'RECEIPT_POSTED','reference_name':result['payment']})
    assert event.actor==principal and float(json.loads(event.before_state)['outstanding'])==100
    assert float(json.loads(event.after_state)['outstanding'])==60 and json.loads(event.after_state)['allocated']==40
    assert frappe.db.get_value('Payment Entry',result['payment'],'owner')==principal
    assert receivables.pay(inv,40,'2026-10-05',f['tag']+'-adapter-pay',f['tag'])['invoice']['replay']
    assert frappe.session.user==principal and sorted(frappe.get_roles())==roles
    assert not frappe.has_permission('Payment Entry','create')
    checks.append('native posted partial payment/idempotence retain real owner and before/after audit actor')
    frappe.set_user('Administrator');set_membership(principal,f['centers'][0],0,f['tag']);set_membership(principal,f['centers'][1],1,f['tag'])
    frappe.set_user(principal)
    denied(lambda:native_adapter.payment_document(invoice,10,bank))
    denied(lambda:native_adapter.sales_taxes(f['centers'][0],company))
    with internal_write('cc_accounting_write'):
        denied(lambda:xml.validate_attachment_references())
    checks.append('revoked-center canonical invoice and tax adapters denied')
    print(json.dumps({'status':'PASS','checks':checks,'permission_grants_added':False,'principal_elevation':False}))
finally:
    frappe.set_user('Administrator')
    if f:fixtures.recover_http(f['tag'])
    frappe.destroy()
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--backend',required=True);p.add_argument('--site',required=True);a=p.parse_args()
    assert a.project!='centrochange-dev' and a.backend.startswith(a.project+'-')
    labels=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .Config.Labels}}',a.backend],text=True))
    assert labels['com.docker.compose.project']==a.project
    r=subprocess.run(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',a.backend,'env/bin/python'],input='SITE='+repr(a.site)+'\n'+CODE,text=True,capture_output=True)
    print(r.stdout+r.stderr);raise SystemExit(r.returncode)

if __name__=='__main__':main()
