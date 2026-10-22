from frappe.model.document import Document

class CCOrganizationalNote(Document):
	def validate(self):
		from centrochange_core.operations.notes import validate_note
		validate_note(self)
	def on_trash(self):
		import frappe
		frappe.throw("Le note restano nello storico e non possono essere sovrascritte.",frappe.PermissionError)
