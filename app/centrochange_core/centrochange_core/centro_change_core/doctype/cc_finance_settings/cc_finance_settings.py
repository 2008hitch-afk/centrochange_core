from frappe.model.document import Document

class CCFinanceSettings(Document):
	def validate(self):
		from centrochange_core.finance.guards import require_finance_manager
		require_finance_manager()
		import frappe
		if self.unpaid_compensation_policy != "HC-0005 DECISION-054":
			frappe.throw("Professional unpaid compensation follows HC-0005 DECISION-054")
		if not frappe.utils.cint(self.simulation_only):
			frappe.throw('L’attivazione di servizi fiscali reali non è autorizzata nel DEV.',frappe.PermissionError)
