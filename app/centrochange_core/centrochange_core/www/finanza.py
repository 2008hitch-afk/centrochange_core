import frappe
from centrochange_core.finance.guards import allowed
no_cache=True

def get_context(context):
    if frappe.session.user=='Guest':
        frappe.local.flags.redirect_location='/login?redirect-to=/finanza'
        raise frappe.Redirect
    if not allowed():frappe.throw('Finance workspace access denied',frappe.PermissionError)
    from frappe.sessions import get_csrf_token
    context.uat_demo=frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
    context.csrf_token=get_csrf_token()
    from centrochange_core.security.guards import is_manager
    context.application_manager=is_manager()
    context.title='Centro Change — Finanza'
