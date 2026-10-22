"""Print only an existing native format of a permitted center finance document."""
import frappe
from centrochange_core.finance.guards import require_finance
from centrochange_core.scoped_api import bounded

PRINTABLE = ('Sales Invoice', 'Purchase Invoice', 'Payment Entry')


@frappe.whitelist(methods=['GET'])
def preview(center, doctype, name, print_format='Standard'):
    require_finance(center)
    if doctype not in PRINTABLE:
        frappe.throw('Tipo documento non stampabile', frappe.PermissionError)
    name = bounded(name, 'Documento')
    print_format = bounded(print_format, 'Formato di stampa')
    if print_format != 'Standard' and not frappe.db.exists('Print Format', {'name': print_format, 'doc_type': doctype, 'disabled': 0}):
        frappe.throw('Formato di stampa non autorizzato', frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    if doc.cc_center != center:
        frappe.throw('Documento non disponibile per questo centro', frappe.PermissionError)
    doc.check_permission('read')
    doc.check_permission('print')
    return {'doctype': doctype, 'name': name, 'format': print_format,
            'html': frappe.get_print(doctype, name, print_format=print_format, as_pdf=False)}
