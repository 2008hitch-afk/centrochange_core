from frappe.model.document import Document

class CCPrivateNote(Document):
	def validate(self):
		from centrochange_core.operations.notes import validate_note
		validate_note(self)
	def on_trash(self):
		import frappe
		frappe.throw("Le note riservate restano nello storico e non possono essere sovrascritte.",frappe.PermissionError)
	def check_permission(self,permtype="read",permlevel=None):
		from centrochange_core.operations.notes import require_private
		require_private(self)
		return super().check_permission(permtype,permlevel)
	def as_dict(self,*args,**kwargs):
		from centrochange_core.operations.notes import require_private
		require_private(self)
		return super().as_dict(*args,**kwargs)
