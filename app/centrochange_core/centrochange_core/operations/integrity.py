"""Operation ledgers are append-only even through generic document APIs."""
import frappe


def immutable(doc,method=None):
	if method=='on_trash' or not doc.is_new() or not frappe.flags.get('cc_operation_write'):
		frappe.throw('I record operativi sono storici e modificabili solo dal servizio previsto.',frappe.PermissionError)
