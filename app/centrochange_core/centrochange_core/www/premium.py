"""Isolated React workspace shell; server remains the authorization authority."""
import frappe

no_cache = True


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/premium"
        raise frappe.Redirect
    from centrochange_core.operations.workspace import require_actor
    from centrochange_core.finance.guards import allowed as finance_allowed
    from frappe.sessions import get_csrf_token

    try:
        require_actor()
    except frappe.PermissionError:
        if not finance_allowed():
            raise
    context.csrf_token = get_csrf_token()
    context.title = "Centro Change — Workspace"
    return context
