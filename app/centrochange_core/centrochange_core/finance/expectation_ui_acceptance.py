"""Readable comparison uses canonical references; all test writes rolled back."""
import frappe
from centrochange_core.finance import reporting, professional_economics as economics
from centrochange_core.finance.guards import require_synthetic


def _principals(role):
    rows=frappe.get_all('Has Role',filters={'role':role,'parenttype':'User'},pluck='parent',limit_page_length=0)
    return [name for name in rows if frappe.db.get_value('User',name,'enabled')]


def run():
    require_synthetic();user=frappe.session.user
    frappe.db.savepoint('cc_expectation_ui')
    try:
        finance_users=_principals('CC Finance');assert finance_users,'An enabled Finance principal is required for this regression.'
        frappe.set_user(finance_users[0])
        from centrochange_core.security.guards import centers
        center=None;selected=None;invoice=None
        for candidate_center in centers(finance_users[0]):
            rows=reporting.records(candidate_center,'CC Professional Expectation')
            for row in rows:
                if row['state']!='OK' or not row['amount_known'] or not row['appointment_label']:
                    continue
                supplier=frappe.db.get_value('Healthcare Practitioner',row['practitioner'],'supplier')
                candidates=frappe.get_list('Purchase Invoice',filters={'cc_center':candidate_center,'supplier':supplier,'docstatus':1,'is_return':0},fields=['name','net_total'],limit_page_length=0)
                native=next((doc for doc in candidates if abs(float(doc.net_total or 0)-float(row['amount']))>0.0001),None)
                if native:
                    center=candidate_center;selected=row;invoice=native.name;break
            if selected:break
        assert selected and invoice, 'Current synthetic expectation and submitted supplier invoice fixture required.'
        assert selected['appointment_label'] and selected['state']=='OK' and selected['amount']>0
        before={dt:frappe.db.count(dt) for dt in ['Purchase Invoice','GL Entry','Payment Ledger Entry']}
        result=economics.compare(invoice,[selected['name']],'SYNTHETIC readable comparison regression')
        doc=frappe.get_doc('CC Professional Comparison',result['name'])
        assert doc.state=='REVIEW' and doc.problem=='Amount Difference' and doc.expected_amount==selected['amount']
        assert frappe.parse_json(doc.expectations_json)==[selected['name']]
        assert economics.compare(invoice,[selected['name']],'SYNTHETIC comparison replay')['replay']
        assert before=={dt:frappe.db.count(dt) for dt in before}
        professionals=_principals('CC Professional');assert professionals,'An enabled professional principal is required for cross-role denial.'
        for principal in professionals[:3]:
            frappe.set_user(principal)
            try:reporting.records(center,'CC Professional Expectation')
            except frappe.PermissionError:pass
            else:raise AssertionError('Professional economics leak')
        return {'status':'PASS','checks':['readable canonical projection selected dynamically from current native records','exact selected snapshot reference','explicit amount difference computed from current invoice and expectation','idempotent comparison','no native debt/ledger created','A/B/C denied']}
    finally:
        frappe.db.rollback(save_point='cc_expectation_ui');frappe.set_user(user)
