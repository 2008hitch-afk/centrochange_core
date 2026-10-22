"""SQL reports cannot bypass row scope through native report role permissions."""
import frappe
from centrochange_core.security.guards import is_manager


def before_request():
    if is_manager():
        return
    from urllib.parse import unquote
    path=unquote(getattr(getattr(frappe.local,'request',None),'path',''))
    commands=[frappe.form_dict.get('cmd') or '',path.rsplit('/method/',1)[-1]]
    if any(command.startswith(('frappe.desk.query_report.','erpnext.accounts.','erpnext.regional.italy.')) for command in commands):
        frappe.throw(frappe._('Use scoped Centro Change accounting reports'),frappe.PermissionError)
