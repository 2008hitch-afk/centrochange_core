import frappe
from frappe.model.document import Document


class CCBookingConfirmation(Document):
    def validate(self):
        if not frappe.flags.get('cc_confirmation_write'):
            frappe.throw('Booking confirmations are service-controlled',frappe.PermissionError)
        old=self.get_doc_before_save()
        if old and any(self.get(k)!=old.get(k) for k in ['appointment','center','recipient','message']):
            frappe.throw('Confirmation snapshot is immutable',frappe.PermissionError)
    def on_trash(self):
        frappe.throw('Confirmation history cannot be deleted',frappe.PermissionError)
