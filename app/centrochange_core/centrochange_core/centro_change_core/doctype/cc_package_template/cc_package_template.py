from frappe.model.document import Document

class CCPackageTemplate(Document):
	def validate(self):
		import frappe
		from centrochange_core.security.guards import require_manager
		require_manager()
		if not self.units or self.units<1 or self.units>9999:
			frappe.throw("Le unità del pacchetto devono essere tra 1 e 9999.")
