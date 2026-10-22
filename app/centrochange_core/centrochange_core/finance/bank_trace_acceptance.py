"""Read-only native reconciliation trace regression."""
import frappe
from centrochange_core.finance.banking import candidates


def _principal(role):
    for row in frappe.get_all('Has Role',filters={'role':role,'parenttype':'User'},pluck='parent',limit_page_length=0):
        if frappe.db.get_value('User',row,'enabled'):
            return row
    return None


def run():
    user=frappe.session.user
    try:
        finance_user=_principal('CC Finance')
        assert finance_user,'An enabled Finance principal is required for bank trace acceptance.'
        frappe.set_user(finance_user)
        from centrochange_core.security.guards import centers
        movements=[]
        for center in centers(finance_user):
            movements.extend(frappe.get_list('Bank Transaction',filters={'cc_center':center,'docstatus':1,'unallocated_amount':0},pluck='name'))
        matched=[]
        for name in movements:
            d=candidates(name)
            assert d['state']=='Reconciled'
            for r in d['reconciled_documents']:
                assert r['allocated_amount']>0 and r['subject']
                matched.append((name,r))
        assert matched
        movement,document=matched[0]
        assert document['allocated_amount']>0 and document['subject']
        for role in ['CC Professional']:
            principals=[row for row in frappe.get_all('Has Role',filters={'role':role,'parenttype':'User'},pluck='parent',limit_page_length=0) if frappe.db.get_value('User',row,'enabled')]
            assert principals,'An enabled professional principal is required for cross-role trace denial.'
            for principal in principals[:3]:
                frappe.set_user(principal)
                try:candidates(movement)
                except frappe.PermissionError:pass
                else:raise AssertionError('Bank trace leak')
        return {'status':'PASS','checks':['a currently reconciled native document is shown with subject and positive allocation','A/B/C denied']}
    finally:frappe.set_user(user)
