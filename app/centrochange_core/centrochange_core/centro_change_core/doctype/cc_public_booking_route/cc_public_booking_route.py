import frappe
from frappe.model.document import Document


class CCPublicBookingRoute(Document):
	def validate(self):
		from centrochange_core.security.guards import require_manager
		require_manager()
		if self.route not in ('Marco','Francesca'):
			frappe.throw('Sono consentiti solo i percorsi primo incontro approvati.')
