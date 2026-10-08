"""Role-scoped synthetic UAT guide; operational permissions remain server-side."""
import frappe
from centrochange_core.security.guards import enabled, is_manager, roles
from centrochange_core.finance.guards import allowed
no_cache = True


def get_context(context):
    if frappe.conf.get('cc_synthetic_dev') != 1 or frappe.conf.get('cc_uat_demo') != 1:
        raise frappe.DoesNotExistError
    if frappe.session.user == 'Guest':
        frappe.local.flags.redirect_location = '/login?redirect-to=/validazione'
        raise frappe.Redirect
    assigned = set(roles())
    operational = is_manager() or bool(assigned & {'CC Professional', 'CC Secretariat'})
    if not enabled() or not (operational or allowed()):
        frappe.throw('Validation guide access denied', frappe.PermissionError)
    context.operational = operational
    context.finance = allowed()
    context.manager = is_manager()
    context.administrative = is_manager() or 'CC Secretariat' in assigned
    context.professional = 'CC Professional' in assigned
    context.readonly = 'CC Accountant' in assigned and not is_manager()
    context.title = 'Centro Change — Guida alla validazione'
