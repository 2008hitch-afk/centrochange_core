"""Private synthetic reconciliation; additional mapping/deferral tests roll back."""
import frappe
from centrochange_core.finance.patient_reporting import patient_view


def reconcile(data):
    t=data['totals']
    assert t['invoiced']==sum(r['grand_total'] for r in data['invoices'])
    assert t['collected']==sum(r['collected_amount'] for r in data['payments'])
    assert t['outstanding']==sum(r['outstanding_amount'] for r in data['open_invoices'])
    assert t['overdue']==sum(r['outstanding_amount'] for r in data['overdue_invoices'])
    assert t['open_invoices']==len(data['open_invoices'])
    assert data['counts']['sessions']==len(data['sessions'])
    assert len({r['name'] for r in data['sessions']})==len(data['sessions'])
    assert all(data['start']<=frappe.utils.getdate(r['appointment_date'])<=data['end'] for r in data['sessions'])
    assert 'PRIVATE BODY' not in frappe.as_json(data)
    if data['customer']:
        native=frappe.get_all('Sales Invoice',filters={'cc_center':data['center'],'customer':data['customer'],'docstatus':1,'outstanding_amount':['>',0]},fields=['name','outstanding_amount'])
        assert t['outstanding']==sum(r.outstanding_amount for r in native)
        assert {r['name'] for r in data['open_invoices']}=={r.name for r in native}
        invoices=frappe.get_all('Sales Invoice',filters={'cc_center':data['center'],'customer':data['customer'],'docstatus':1,'posting_date':['between',[data['start'],data['end']]]},fields=['name','grand_total'])
        assert t['invoiced']==sum(r.grand_total for r in invoices)
        payments=frappe.get_all('Payment Entry',filters={'cc_center':data['center'],'party_type':'Customer','party':data['customer'],'docstatus':1,'posting_date':['between',[data['start'],data['end']]]},fields=['name','payment_type','received_amount','paid_amount'])
        assert t['collected']==sum(r.received_amount if r.payment_type=='Receive' else -r.paid_amount if r.payment_type=='Pay' else 0 for r in payments)


def run():
    from centrochange_core.uat.demo import credentials,inspect
    from centrochange_core.finance import collections
    from centrochange_core.security.audit import internal_write
    fixture=credentials();demo=inspect();center=fixture['centers'][0];original=frappe.session.user;checks=[];cases={}
    args=dict(center=center,start='2026-09-28',end='2026-10-31')
    try:
        for role in ('s','f','m','t'):
            frappe.set_user(fixture['users'][role]['name']);listing=patient_view(**args)
            assert len({r['key'] for r in listing['rows']})==len(listing['rows'])
            for name in ('Beta','Gamma','Theta'):
                data=patient_view(**args,patient=demo['patients'][name]);reconcile(data)
                row=next(r for r in listing['rows'] if r['key']==data['key']);assert row['totals']==data['totals']
                cases[name]={'totals':data['totals'],'state':data['state'],'next_due_date':data['next_due_date'],'deferred':data['deferred'],'blocked':data['blocked']}
            checks.append(role+' authorized list/detail native invoice/payment/outstanding/overdue reconciliation')
        frappe.set_user(fixture['users']['s']['name'])
        gamma=patient_view(**args,patient=demo['patients']['Gamma']);assert gamma['totals']['outstanding']==0
        theta=patient_view(**args,patient=demo['patients']['Theta']);assert theta['totals']['outstanding']>0
        position=collections.position(demo['patients']['Theta'],center)
        assert theta['blocked']==position['blocked']
        for row in theta['open_invoices']:
            assert row['original_due_date']==frappe.db.get_value('Sales Invoice',row['name'],'due_date')
            override=collections._deferred('Sales Invoice',row['name'])
            assert row['effective_due_date']==(override.due_date if override else row['original_due_date'])
        checks.append('current regular/open/Theta cases; original/effective due date and block match canonical collections')
        for role in ('a','b','c'):
            frappe.set_user(fixture['users'][role]['name'])
            try:patient_view(**args)
            except frappe.PermissionError:pass
            else:raise AssertionError('Professional accounting escalation')
        frappe.set_user(fixture['users']['f']['name'])
        for extra in ({'center':fixture['centers'][1]},{'patient':demo['patients']['Altro centro']},{'key':'SYNTHETIC-UNAUTHORIZED'}):
            try:patient_view(**{**args,**extra})
            except frappe.PermissionError:pass
            else:raise AssertionError('Foreign context exposed')
        checks.append('A/B/C and foreign center/Patient/Customer denied')
        # Supported internal test context: mapping and approved override service only;
        # both remain inside savepoint and do not persist Owner UAT data changes.
        frappe.set_user(fixture['users']['m']['name']);beta=demo['patients']['Beta'];old_customer=frappe.db.get_value('Patient',beta,'customer')
        frappe.db.savepoint('patient_report_acceptance')
        try:
            customer=gamma['customer']
            with internal_write('cc_identity_write'):
                frappe.db.set_value('Patient',beta,'customer',customer,update_modified=False)
            shared=patient_view(**args,key=customer);reconcile(shared)
            assert shared['shared'] and {beta,demo['patients']['Gamma']}<={p['name'] for p in shared['patients']}
            assert all(link['patient'] is None or link['patient'] in {p['name'] for p in shared['patients']} for invoice in shared['invoices']+shared['open_invoices'] for link in invoice['session_links'])
            listing=patient_view(**args);assert sum(r['key']==customer for r in listing['rows'])==1
            assert next(r for r in listing['rows'] if r['key']==customer)['totals']==shared['totals']
            checks.append('shared Customer appears once, two Patient identities, native fiscal totals unallocated')
            frappe.db.set_value('Patient',beta,'customer',None,update_modified=False)
            unmapped=patient_view(**args,patient=beta)
            assert unmapped['customer'] is None and unmapped['totals']['outstanding'] is None and unmapped['totals']['invoiced'] is None
            assert not unmapped['invoices'] and not unmapped['payments']
            checks.append('unmapped Patient has unknown accounting position, never invented zero or center totals')
            native=theta['open_invoices'][0];date=frappe.utils.add_days(frappe.utils.today(),40)
            collections.override(demo['patients']['Theta'],center,'Sales Invoice',native['name'],date,'patient-report-savepoint','Synthetic deferred reporting acceptance')
            changed=patient_view(**args,patient=demo['patients']['Theta']);reconcile(changed)
            row=next(r for r in changed['open_invoices'] if r['name']==native['name'])
            assert str(row['effective_due_date'])==date and row['original_due_date']==native['original_due_date']
            assert changed['totals']['outstanding']==theta['totals']['outstanding'] and changed['deferred']
            assert row['name'] not in {r['name'] for r in changed['overdue_invoices']}
            checks.append('approved deferral preserves debt/original date and removes deferred native invoice from overdue')
        finally:frappe.db.rollback(save_point='patient_report_acceptance')
        assert frappe.db.get_value('Patient',beta,'customer')==old_customer
        restored=patient_view(**args,patient=demo['patients']['Theta']);assert restored['totals']==theta['totals']
        checks.append('mapping/deferral/audit rolled back; demo preserved')
        return {'status':'PASS','checks':checks,'cases':cases,'persistent_changes':False}
    finally:frappe.set_user(original)
