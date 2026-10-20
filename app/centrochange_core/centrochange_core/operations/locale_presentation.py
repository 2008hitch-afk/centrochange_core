"""Read-only Italian presentation of native invoice amounts in words.

The ERPNext accounting value remains canonical; native Form fields display a
localized companion only after the normal document read permission succeeds.
"""
from decimal import Decimal, ROUND_HALF_UP

import frappe
from num2words import num2words


@frappe.whitelist(methods=["GET"])
def invoice_words(doctype: str, name: str) -> str:
    if doctype not in ("Sales Invoice", "Purchase Invoice"):
        frappe.throw("Tipo di documento non consentito.", frappe.PermissionError)
    if not frappe.has_permission(doctype, "read"):
        frappe.throw("Permesso di lettura insufficiente.", frappe.PermissionError)
    invoice = frappe.get_doc(doctype, name)
    invoice.check_permission("read")
    if invoice.currency != "EUR":
        return ""
    amount = Decimal(str(invoice.grand_total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    words = num2words(f"{amount:.2f}", lang="it", to="currency", currency="EUR")
    return words[0].upper() + words[1:] + "."
