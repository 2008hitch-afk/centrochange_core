from frappe.model.document import Document

class CCEconomicSourceLink(Document):
	def validate(self):
		from centrochange_core.operations.integrity import immutable
		immutable(self)
	def on_trash(self):
		from centrochange_core.operations.integrity import immutable
		immutable(self,"on_trash")
