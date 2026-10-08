import frappe
from centrochange_core.operations.workspace import require_actor
no_cache=True

def get_context(context):
    if frappe.session.user=='Guest':
        frappe.local.flags.redirect_location='/login?redirect-to=/centrochange'
        raise frappe.Redirect
    require_actor()
    from frappe.sessions import get_csrf_token
    context.uat_demo=frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
    context.csrf_token=get_csrf_token()
    from centrochange_core.security.guards import is_manager
    context.application_manager=is_manager()
    context.title='Centro Change — Agenda'
    return context
