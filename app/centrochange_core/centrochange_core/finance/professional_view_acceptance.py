"""Private synthetic read-only verification against canonical runtime sources."""
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
        return {'status':'PASS','checks':checks,'canonical_sessions':len(raw),'read_only':True}
    finally:frappe.set_user(original)
