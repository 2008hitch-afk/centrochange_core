"""Cross-domain financial totals and allowlisted projection regression."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import professional_acceptance,receivables_acceptance,reporting


def checks(fixture):
    result=professional_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    center=fixture['center'];frappe.set_user('Administrator')
    data=reporting.summary(center,'2026-01-01','2026-12-31');t=data['totals']
    assert t['revenue_net']==sum(r.net_total for r in data['sales_invoices'])
    assert t['receivable_outstanding']==sum(r.outstanding_amount for r in data['sales_invoices'])
    assert t['purchase_net']==sum(r.net_total for r in data['purchase_invoices'])
    assert t['payable_outstanding']==sum(r.outstanding_amount for r in data['purchase_invoices'])
    assert t['collected']==sum((r.received_amount if r.payment_type=='Receive' else -r.paid_amount if r.payment_type=='Pay' else 0) for r in data['payments'] if r.party_type=='Customer')
    assert t['indicative_margin'] is None
    assert not any(k in str(data) for k in ('SYNTHETIC PRIVATE','medical_history','allergies'))
    result.append('center native revenue costs cash outstanding totals reconcile with document drill-down and exclude cancelled postings and private bodies')
    future=reporting.summary(center,'2099-01-01','2099-12-31')
    assert future['totals']['expected_compensation'] is None and future['totals']['unresolved_expectations']>0
    customer=frappe.db.get_value('Patient',fixture['patient'],'customer')
    assert all(r.customer==customer for r in reporting.summary(center,'2026-01-01','2026-12-31',customer=customer)['sales_invoices'])
    professional=reporting.summary(center,'2026-01-01','2026-12-31',practitioner=fixture['prac1'])
    assert not professional['sales_invoices']
    assert 'no inferred allocation' in professional['scope_note']
    result.append('session-date and posting-date periods explicit; missing expectations unknown; shared fiscal subjects are not silently allocated')
    reject(lambda:reporting.summary(center,'2026-01-01','2028-01-01'))
    reject(lambda:reporting.records(center,'CC Private Note'))
    boot=reporting.bootstrap(center);assert boot['can_write'] and boot['unpaid_policy']=='UNSET' and boot['simulation_only']
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid',fixture['secretary']):
        frappe.set_user(actor)
        if actor in (fixture['pro1'],fixture['pro2']):
            reject(lambda:reporting.bootstrap(center));reject(lambda:reporting.summary(center,'2026-01-01','2026-12-31'));reject(lambda:reporting.records(center,'Sales Invoice'))
        else:
            assert reporting.summary(center,'2026-01-01','2026-12-31')['center']==center
            assert reporting.bootstrap(center)['can_write']==(actor==fixture['secretary'])
            reject(lambda:reporting.summary(fixture['other'],'2026-01-01','2026-12-31'))
    frappe.set_user('Administrator');result.append('financial bootstrap records reports respect actor center bounds and readonly accountant without clinical content')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:return security.run(extra_checks=checks)
    finally:frappe.flags.cc_test_clock=previous
