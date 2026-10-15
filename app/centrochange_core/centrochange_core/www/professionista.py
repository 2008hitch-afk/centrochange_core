import frappe
from centrochange_core.finance.guards import allowed
no_cache=True

def get_context(context):
    if frappe.session.user=='Guest':
        frappe.local.flags.redirect_location='/login?redirect-to=/professionista'
        raise frappe.Redirect
    if not allowed():frappe.throw('Non hai accesso al report professionista.',frappe.PermissionError)
    return context
