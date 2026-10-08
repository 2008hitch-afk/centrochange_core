from frappe.model.document import Document
from centrochange_core.operations.integrity import immutable

class CCTSInputReview(Document):
    def validate(self):
        immutable(self)
    def on_trash(self):
        immutable(self,"on_trash")
