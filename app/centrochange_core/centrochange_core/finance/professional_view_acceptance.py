"""Private synthetic verification; comparison writes are rolled back."""
import frappe
from centrochange_core.finance.reporting import professional_view


def run():
    from centrochange_core.uat.demo import credentials,inspect
    fixture=credentials();demo=inspect();center=fixture['centers'][0];practitioner=fixture['practitioners'][0]
    original=frappe.session.user;checks=[]
    args=dict(center=center,start='2026-09-28',end='2026-10-04',practitioner=practitioner)
    try:
        raw=frappe.get_all('Patient Appointment',filters={'cc_center':center,'practitioner':practitioner,'appointment_date':['between',[args['start'],args['end']]]},fields=['name','status','cc_performed','cc_paid','cc_price_snapshot','cc_currency_snapshot'])
        projections=[]
        for role in ('s','f','m','t'):
            frappe.set_user(fixture['users'][role]['name']);data=professional_view(**args)
            assert data['counts']['sessions']==len(raw)==len(data['sessions'])
            assert {r['name'] for r in data['sessions']}=={r.name for r in raw}
            assert data['counts']['cancelled']==sum(r.status=='Cancelled' for r in raw)
            assert data['counts']['performed']==sum(bool(r.cc_performed) and r.status!='Cancelled' for r in raw)
            assert data['counts']['operational_paid']==sum(bool(r.cc_paid) for r in raw)
            assert sum(data['snapshot_values'].values())==sum(float(r.cc_price_snapshot or 0) for r in raw)
            assert all(r['practitioner']==practitioner and args['start']<=str(r['appointment_date'])<=args['end'] for r in data['sessions'])
            assert 'PRIVATE BODY' not in frappe.as_json(data) and 'content' not in {k for r in data['sessions'] for k in r}
            assert data['counts']['performed']+data['counts']['cancelled']+data['counts']['future']+data['counts']['pending']+data['counts']['closed_not_performed']==len(raw)
            e=data['economics'];assert e['known_expected']==sum(r['amount'] for r in e['expectations'] if r['state']=='OK')
            assert e['expected']==(None if e['suspended'] or e['review'] else e['known_expected'])
            assert e['suspended']==sum(r['state']=='SUSPENDED' for r in e['expectations'])
            checks.append(role+' count/drill-down/classification/snapshot/expected/null/privacy reconciliation')
            projections.append({'counts':data['counts'],'snapshot_values':data['snapshot_values'],'economics':e})
        assert projections.count(projections[0])==len(projections);checks.append('authorized roles reconcile identical economic projection; operational detail privilege remains distinct')
        for role in ('a','b','c'):
            frappe.set_user(fixture['users'][role]['name'])
            try:professional_view(**args)
            except frappe.PermissionError:pass
            else:raise AssertionError('Professional financial report escalation')
        checks.append('A/B/C reporting denied before privileged queries')
        frappe.set_user(fixture['users']['f']['name'])
        try:professional_view(**{**args,'center':fixture['centers'][1]})
        except frappe.PermissionError:pass
        else:raise AssertionError('Foreign center exposed')
        checks.append('foreign-center financial report denied')
        data=professional_view(**{**args,'start':'2026-10-12','end':'2026-10-18'})
        assert data['counts']['sessions']==1 and data['counts']['future']==1 and len(data['sessions'])==1
        checks.append('future period deterministic native session projection')
        from centrochange_core.finance.professional_economics import compare
        frappe.set_user(fixture['users']['f']['name'])
        before=frappe.db.count('CC Professional Comparison')
        frappe.db.savepoint('professional_acceptance')
        try:
            baseline=professional_view(**args)
            chosen=next(r for r in baseline['economics']['expectations'] if r['state']=='OK')
            supplier=frappe.db.get_value('Healthcare Practitioner',practitioner,'supplier')
            current_invoice=frappe.db.get_value('Purchase Invoice',{'cc_center':center,'supplier':supplier,'docstatus':1,'is_return':0},'name')
            assert current_invoice
            result=compare(current_invoice,[chosen['name']],'Synthetic projection acceptance, rolled back')
            projected=professional_view(**args)
            comparison=next(r for r in projected['economics']['comparisons'] if r['name']==result['name'])
            invoice=frappe.get_doc('Purchase Invoice',current_invoice)
            assert comparison['received_amount']==invoice.net_total
            assert comparison['expected_amount']==chosen['amount']
            assert comparison['difference']==chosen['amount']-invoice.net_total
            assert [r['name'] for r in comparison['expectations']]==[chosen['name']]
            outside=professional_view(**{**args,'start':'2026-10-12','end':'2026-10-18'})
            assert result['name'] not in {r['name'] for r in outside['economics']['comparisons']}
            checks.append('canonical comparison exact references/expected/native net/difference; excluded outside composing session period')
            full=professional_view(**{**args,'start':'2026-09-28','end':'2026-10-31'})
            native=next(r for r in full['economics']['supplier_invoices'] if r['name']==invoice.name)
            assert native['net_total']==invoice.net_total and native['outstanding_amount']==invoice.outstanding_amount and native['status']==invoice.status
            checks.append('received invoice net/outstanding/status reconcile native supplier document without allocation')
        finally:
            frappe.db.rollback(save_point='professional_acceptance')
        assert frappe.db.count('CC Professional Comparison')==before
        checks.append('comparison and audit transaction rolled back; persistent demo preserved')
        return {'status':'PASS' ,'checks':checks,'canonical_sessions':len(raw),'persistent_changes':False}
    finally:frappe.set_user(original)
