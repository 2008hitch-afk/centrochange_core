"""Readable comparison uses canonical references; all test writes rolled back."""
import frappe
from centrochange_core.finance import reporting, professional_economics as economics
from centrochange_core.finance.guards import require_synthetic


def run():
    require_synthetic();user=frappe.session.user
    frappe.db.savepoint('cc_expectation_ui')
    try:
        frappe.set_user('cc-http-uat0000001-f@example.invalid')
        center='CC-HTTP-UAT0000001 A'
        rows=reporting.records(center,'CC Professional Expectation')
        selected=next(r for r in rows if r['appointment']=='HLC-APP-2026-00132')
        assert selected['appointment_label'] and selected['state']=='OK' and selected['amount']==40
        supplier=frappe.db.get_value('Healthcare Practitioner',selected['practitioner'],'supplier')
        invoice=frappe.db.get_value('Purchase Invoice',{'cc_center':center,'supplier':supplier,'docstatus':1,'is_return':0},'name')
        assert invoice
        before={dt:frappe.db.count(dt) for dt in ['Purchase Invoice','GL Entry','Payment Ledger Entry']}
        result=economics.compare(invoice,[selected['name']],'SYNTHETIC readable comparison regression')
        doc=frappe.get_doc('CC Professional Comparison',result['name'])
        assert doc.state=='REVIEW' and doc.problem=='Amount Difference' and doc.expected_amount==40
        assert frappe.parse_json(doc.expectations_json)==[selected['name']]
        assert economics.compare(invoice,[selected['name']],'SYNTHETIC comparison replay')['replay']
        assert before=={dt:frappe.db.count(dt) for dt in before}
        for suffix in ['a','b','c']:
            frappe.set_user('cc-http-uat0000001-'+suffix+'@example.invalid')
            try:reporting.records(center,'CC Professional Expectation')
            except frappe.PermissionError:pass
            else:raise AssertionError('Professional economics leak')
        return {'status':'PASS','checks':['readable canonical projection','exact selected snapshot reference','explicit Amount Difference','idempotent comparison','no native debt/ledger created','A/B/C denied']}
    finally:
        frappe.db.rollback(save_point='cc_expectation_ui');frappe.set_user(user)
