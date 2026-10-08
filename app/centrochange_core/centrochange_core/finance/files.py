"""Financial payload attachments retain private source identity server-side."""
import frappe


def managed(doc):
    return doc.attached_to_doctype=='CC Incoming Invoice' or doc.attached_to_doctype in ('Sales Invoice','Purchase Invoice') and bool(frappe.db.get_value(doc.attached_to_doctype,doc.attached_to_name,'cc_center'))


def protected(doc,method=None):
    old=doc.get_doc_before_save()
    if not (managed(doc) or old and managed(old)):
        return
    if method=='on_trash':
        if frappe.flags.get('cc_fixture_file_cleanup') or doc.attached_to_doctype!='CC Incoming Invoice' and frappe.flags.get('cc_accounting_write'):
            return
        frappe.throw('Retained financial payloads cannot be deleted manually',frappe.PermissionError)
    if not frappe.utils.cint(doc.is_private):
        frappe.throw('Financial payload attachments must remain private',frappe.PermissionError)
    if old and doc.get('content') is not None:
        frappe.throw('Financial payload bytes cannot be replaced',frappe.PermissionError)
    if old and any(doc.get(field)!=old.get(field) for field in ('attached_to_doctype','attached_to_name','file_url','file_name','content_hash')):
        frappe.throw('Financial payload identity/reference cannot be changed',frappe.PermissionError)
    if doc.is_new() and not (frappe.flags.get('cc_incoming_write') or frappe.flags.get('cc_accounting_write')):
        frappe.throw('Financial payloads require the source-controlled service',frappe.PermissionError)


class FinancialFileMixin:
    def before_insert(self):
        # A new unprotected alias must not expose bytes retained by a financial parent.
        if not managed(self):
            filters=[]
            if self.file_url:
                filters.append({'file_url':self.file_url})
            if self.content:
                from frappe.utils.file_manager import get_content_hash
                filters.append({'content_hash':get_content_hash(self.content)})
            for match in filters:
                for origin in frappe.get_all('File',filters=match,fields=['attached_to_doctype','attached_to_name']):
                    if managed(origin):
                        frappe.throw('Financial payload bytes cannot be copied to an unprotected attachment',frappe.PermissionError)
        protected(self)
        if managed(self) and self.file_url and self.is_remote_file:
            frappe.throw('Financial payloads must be local retained bytes, never remote URLs',frappe.PermissionError)
        return super().before_insert()

    def validate(self):
        # Native File.validate can move the physical file before doc-event hooks run.
        protected(self)
        return super().validate()

    def on_trash(self):
        # Guard before the native controller unlinks bytes or adds comments.
        protected(self,method='on_trash')
        return super().on_trash()
