import frappe
from centrochange_core.security.guards import enabled,is_manager,roles,centers,current_rows


def require_finance_manager():
    if not is_manager():
        frappe.throw('La configurazione Finance è riservata alla Direzione.',frappe.PermissionError)


def allowed(user=None,write=False):
    if is_manager(user):
        return True
    assigned=set(roles(user))
    if not enabled(user) or 'CC Professional' in assigned:
        return False
    return bool(assigned & ({'CC Finance','CC Secretariat'} if write else {'CC Finance','CC Secretariat','CC Accountant'}))


def require_finance(center,write=False):
    if not allowed(write=write) or not is_manager() and center not in centers():
        frappe.throw('Non hai accesso alla Finanza di questa sede.',frappe.PermissionError)
    if write:
        from centrochange_core.security.guards import require_operational_center
        require_operational_center(center)


def patient_context(patient,center,write=False):
    require_finance(center,write)
    if not is_manager() and not current_rows('CC Patient Assignment',{'patient':patient,'center':center,'active':1},pluck='name'):
        frappe.throw('Non hai accesso al contesto contabile del paziente.',frappe.PermissionError)


def require_synthetic():
    from centrochange_core.dev_bootstrap import COMPANY
    if frappe.conf.get('cc_synthetic_dev')!=1 or not frappe.db.exists('Company',COMPANY):
        frappe.throw('La contabilità DEV richiede un ambiente esplicitamente sintetico.',frappe.PermissionError)
    return COMPANY


def source_names(user=None):
    if is_manager(user):
        return current_rows('CC Economic Source Link',pluck='name')
    if not allowed(user):
        return []
    return current_rows('CC Economic Source Link',{'center':['in',centers(user) or ['']]},pluck='name')


def source_query(user=None):
    from centrochange_core.security.guards import names_condition
    return '' if is_manager(user) else names_condition('CC Economic Source Link',source_names(user))


def source_permission(doc,user=None,ptype=None):
    return True if is_manager(user) else bool(ptype in ('read','select') and doc.name in source_names(user))
