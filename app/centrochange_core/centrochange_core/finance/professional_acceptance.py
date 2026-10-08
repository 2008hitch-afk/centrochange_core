"""Synthetic parametric economics and deterministic queue runtime regression."""
from datetime import timedelta
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import incoming_acceptance,receivables_acceptance,professional_economics as economics,admin_queue as queue
from centrochange_core.operations.lifecycle import now_utc


def checks(fixture):
    result=incoming_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    frappe.set_user('Administrator');center=fixture['center'];prac=fixture['prac1']
    sources=frappe.get_all('CC Economic Source Link',filters={'center':center,'performed':1,'economic_state':'Due'},fields=['name','appointment','operational_paid'])
    paid=next(s for s in sources if economics.patient_paid(frappe.get_doc('CC Economic Source Link',s.name)))
    unpaid=next(s for s in sources if not economics.patient_paid(frappe.get_doc('CC Economic Source Link',s.name)))
    assert frappe.db.get_single_value('CC Finance Settings','unpaid_compensation_policy')=='UNSET'
    args=dict(center=center,practitioner=prac,service_item='CC SYNTHETIC SESSION',valid_from='2099-01-01',basis='Fixed Amount',value=100,currency='EUR',request_key='synthetic-compensation-100',reason='Synthetic explicitly configured test rate')
    rule=economics.configure_rule(**args)['name']
    assert economics.configure_rule(**args)['replay']
    reject(lambda:economics.configure_rule(**{**args,'value':101}))
    expected=economics.capture(paid.name,'Synthetic paid compensation snapshot',rule)
    assert expected['state']=='OK' and expected['amount']==100
    assert economics.capture(paid.name,'Synthetic expected replay',rule)['replay']
    unresolved=economics.capture(unpaid.name,'Synthetic unpaid unresolved compensation',rule)
    assert unresolved['state']=='REVIEW' and unresolved['amount'] is None
    assert frappe.db.get_value('CC Professional Expectation',unresolved['name'],'problem')=='Unpaid Compensation Policy Unset'
    missing=economics.capture(paid.name,'Synthetic missing rule')
    assert missing['state']=='REVIEW' and missing['amount'] is None
    economics.capture(paid.name,'Synthetic restore explicit snapshot',rule)
    result.append('explicit immutable compensation rule replay and paid source calculation; unpaid policy UNSET stays REVIEW with unknown amount')
    doc=frappe.get_doc('CC Compensation Rule',rule);doc.value=999;reject(lambda:doc.save(ignore_permissions=True))
    reject(lambda:frappe.delete_doc('CC Professional Expectation',expected['name'],ignore_permissions=True))
    result.append('rule and historical professional expectation cannot be rewritten or deleted through generic APIs')
    native=frappe.get_all('Purchase Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0},pluck='name')[0]
    comparison=economics.compare(native,[expected['name']],'Synthetic explicit received invoice comparison')
    assert comparison['state']=='OK' and economics.compare(native,[expected['name']],'Synthetic comparison retry')['replay']
    assert economics.compare(native,[unresolved['name']],'Synthetic unknown comparison')['state']=='REVIEW'
    reject(lambda:economics.compare(native,[expected['name'],missing['name']],'Synthetic double session rejection'))
    position=economics.position(center,prac)
    assert position['expected_amount'] is None and position['unresolved_count']>0
    result.append('native received net amount comparison retains source drill-down and distinguishes OK REVIEW and unknown aggregate')
    first=queue.refresh(center,'Synthetic condition detection');assert first['conditions']>0
    assert not queue.refresh(center,'Synthetic condition replay')['changed']
    items=queue.list_items(center);assert any(i.exception_type=='Incoming Invoice Review' for i in items)
    name=next(i.name for i in items if i.exception_type=='Unresolved Bank Movement')
    due=now_utc().replace(tzinfo=None)+timedelta(days=2)
    managed=queue.manage(name,1,'Synthetic work assignment',assignee=fixture['secretary'],due_at=due,defer_until=due)
    assert managed['state']=='Deferred' and queue.manage(name,1,'Synthetic management replay',assignee=fixture['secretary'],due_at=due,defer_until=due)['replay']
    assert not queue.refresh(center,'Synthetic deferred condition remains')['changed']
    prior=frappe.flags.get('cc_test_clock');frappe.flags.cc_test_clock=now_utc()+timedelta(days=3)
    queue.refresh(center,'Synthetic defer expiry');assert frappe.db.get_value('CC Admin Exception',name,'state')=='Assigned'
    frappe.flags.cc_test_clock=prior
    from centrochange_core.finance.banking import cancel
    ref=frappe.db.get_value('CC Admin Exception',name,'reference_name');cancel(ref,'Synthetic underlying unresolved movement cancellation')
    queue.refresh(center,'Synthetic resolved condition catchup');assert frappe.db.get_value('CC Admin Exception',name,'state')=='Closed'
    reject(lambda:queue.manage(name,1,'Synthetic manual resurrection'))
    reject(lambda:queue.manage(items[0].name,1,'Synthetic unauthorized assignee',assignee=fixture['pro1']))
    reject(lambda:frappe.get_doc('CC Admin Exception',items[0].name).save(ignore_permissions=True))
    queue.catch_up()
    assert frappe.session.user=='Administrator'
    result.append('administrative conditions dedupe; audited assign priority due defer expiry and auto-close retain source truth; scheduler restores principal')
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid'):
        frappe.set_user(actor)
        reject(lambda:economics.capture(paid.name,'Unauthorized economics mutation',rule))
        reject(lambda:queue.refresh(center,'Unauthorized queue mutation'))
        if actor.startswith('accountant'):
            assert queue.list_items(center)
            frappe.get_doc('CC Professional Expectation',expected['name']).check_permission('read')
        else:
            reject(lambda:queue.list_items(center));reject(lambda:economics.position(center,prac))
            for dt,n in [('CC Compensation Rule',rule),('CC Professional Expectation',expected['name']),('CC Professional Comparison',comparison['name']),('CC Admin Exception',items[0].name)]:
                reject(lambda:frappe.get_doc(dt,n).check_permission('read'))
        result.append('professional and read-only accountant professional economics and admin work mutation boundaries')
    frappe.set_user('Administrator');return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:return security.run(extra_checks=checks)
    finally:frappe.flags.cc_test_clock=previous
