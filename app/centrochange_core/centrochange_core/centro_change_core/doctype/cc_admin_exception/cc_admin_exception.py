from frappe.model.document import Document
from centrochange_core.finance.admin_queue import protected

class CCAdminException(Document):
    def validate(self):
        protected(self)
    def on_trash(self):
        protected(self,"on_trash")
