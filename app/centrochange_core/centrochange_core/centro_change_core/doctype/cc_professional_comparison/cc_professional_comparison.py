from frappe.model.document import Document
from centrochange_core.finance.professional_economics import protected

class CCProfessionalComparison(Document):
    def validate(self):
        protected(self)
    def on_trash(self):
        protected(self,"on_trash")
