from frappe.model.document import Document
from centrochange_core.finance.incoming import protected_source

class CCIncomingInvoice(Document):
	def validate(self):
		protected_source(self)

	def on_trash(self):
		protected_source(self,method="on_trash")
