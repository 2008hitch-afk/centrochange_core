"""Read-only native reconciliation trace regression."""
import frappe
from centrochange_core.finance.banking import candidates


def run():
    user=frappe.session.user
    try:
        frappe.set_user('cc-http-uat0000001-f@example.invalid')
        movements=frappe.get_list('Bank Transaction',filters={'cc_center':'CC-HTTP-UAT0000001 A','docstatus':1,'unallocated_amount':0},pluck='name')
        matched=[]
        for name in movements:
            d=candidates(name)
            assert d['state']=='Reconciled'
            for r in d['reconciled_documents']:
                if r['name']=='ACC-SINV-2026-00081':
                    assert r['allocated_amount']==60 and r['subject']=='CC-HTTP-UAT0000001 Beta'
                    matched.append(name)
        assert matched
        for suffix in ['a','b','c']:
            frappe.set_user('cc-http-uat0000001-'+suffix+'@example.invalid')
            try:candidates(matched[0])
            except frappe.PermissionError:pass
            else:raise AssertionError('Bank trace leak')
        return {'status':'PASS','checks':['settled Beta invoice retained in native trace','60 EUR allocation','fiscal subject','A/B/C denied']}
    finally:frappe.set_user(user)
