from frappe.model.document import Document

class CCNotification(Document):
	def validate(self):
		import frappe
		if not frappe.flags.get("cc_notification_write"):
			frappe.throw("Notifications are service-controlled",frappe.PermissionError)
	def on_trash(self):
		import frappe
		frappe.throw("La cronologia delle notifiche non può essere cancellata.",frappe.PermissionError)
