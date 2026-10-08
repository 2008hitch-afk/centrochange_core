from frappe.model.document import Document
from centrochange_core.finance.fiscal import protected

class CCFiscalTransaction(Document):
    def validate(self):
        protected(self)
    def on_trash(self):
        protected(self,"on_trash")
