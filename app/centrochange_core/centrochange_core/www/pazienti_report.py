import frappe
from centrochange_core.finance.guards import allowed
no_cache=True


def get_context(context):
    if frappe.session.user=='Guest':
        frappe.local.flags.redirect_location='/login?redirect-to=/pazienti_report'
        raise frappe.Redirect
    if not allowed():frappe.throw('Patient financial report access denied',frappe.PermissionError)
    return context
