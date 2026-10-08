from frappe.model.document import Document
from centrochange_core.finance.fiscal import protected_attempt

class CCFiscalAttempt(Document):
    def validate(self):
        protected_attempt(self)
    def on_trash(self):
        protected_attempt(self,"on_trash")
