"""Financial payload attachments retain private source identity server-side."""
import frappe


def managed(doc):
    return doc.attached_to_doctype in ('CC Incoming Invoice','CC Fiscal Transaction') or doc.attached_to_doctype in ('Sales Invoice','Purchase Invoice') and bool(frappe.db.get_value(doc.attached_to_doctype,doc.attached_to_name,'cc_center'))


def protected(doc,method=None):
    old=doc.get_doc_before_save()
    if not (managed(doc) or old and managed(old)):
        return
    if method=='on_trash':
        if frappe.flags.get('cc_fixture_file_cleanup') or doc.attached_to_doctype in ('Sales Invoice','Purchase Invoice') and frappe.flags.get('cc_accounting_write'):
            return
        frappe.throw('I documenti finanziari conservati non possono essere cancellati manualmente.',frappe.PermissionError)
    if not frappe.utils.cint(doc.is_private):
        frappe.throw('Gli allegati finanziari devono restare privati.',frappe.PermissionError)
    if old and doc.get('content') is not None:
        frappe.throw('Il contenuto del documento finanziario non può essere sostituito.',frappe.PermissionError)
    if old and any(doc.get(field)!=old.get(field) for field in ('attached_to_doctype','attached_to_name','file_url','file_name','content_hash')):
        frappe.throw('Identità e riferimento del documento finanziario non possono cambiare.',frappe.PermissionError)
    if doc.is_new() and not (frappe.flags.get('cc_incoming_write') or frappe.flags.get('cc_accounting_write') or frappe.flags.get('cc_fiscal_write')):
        frappe.throw('I documenti finanziari richiedono il servizio di gestione della fonte.',frappe.PermissionError)


def accounting_attachment_context(doc, deleting=False):
    """Delegated native Italy XML work, only inside the guarded invoice service.

    This does not grant File/Sales Invoice write/delete to a role or HTTP caller.
    Retained CC Fiscal Transaction payloads never enter this native XML path.
    """
    if not frappe.flags.get('cc_accounting_write') or doc.attached_to_doctype != 'Sales Invoice':
        return False
    if not doc.attached_to_name or not isinstance(doc.attached_to_name, (str, int)):
        frappe.throw('Indica il riferimento canonico dell’allegato fattura.')
    from centrochange_core.finance.guards import require_finance, require_synthetic
    invoice = frappe.get_doc('Sales Invoice', doc.attached_to_name)
    require_finance(invoice.cc_center, True)
    invoice.check_permission('read')
    if not invoice.cc_center or invoice.company != require_synthetic() or invoice.cc_fiscal_profile != 'SYNTHETIC_UNVERIFIED':
        frappe.throw('Seleziona un allegato fattura demo gestito.', frappe.PermissionError)
    if not frappe.utils.cint(doc.is_private) or doc.is_remote_file or not str(doc.file_name).endswith('.xml'):
        frappe.throw('L’allegato contabile nativo deve essere un XML locale e privato.', frappe.PermissionError)
    from frappe.database.schema import SPECIAL_CHAR_PATTERN
    if doc.attached_to_field and SPECIAL_CHAR_PATTERN.search(doc.attached_to_field):
        frappe.throw('Il riferimento dell’allegato non è valido.')
    if deleting:
        from erpnext.regional.italy.utils import get_e_invoice_attachments
        if invoice.docstatus != 2 or doc.name not in {row.name for row in get_e_invoice_attachments(invoice)}:
            frappe.throw('Puoi rimuovere solo l’XML nativo della fattura annullata.', frappe.PermissionError)
    elif invoice.docstatus != 1:
        frappe.throw('L’XML nativo richiede una fattura contabilizzata.', frappe.PermissionError)
    return True


class FinancialFileMixin:
    def validate_attachment_references(self):
        # Frappe 16.50 requires generic parent write; the existing service-only
        # accounting flow delegates this precise private XML operation instead.
        if accounting_attachment_context(self):
            return
        return super().validate_attachment_references()

    def check_permission(self, permtype='read', permlevel=None):
        # ERPNext Italy cancellation now deletes its generated XML under the
        # actual actor. Existing protected() already permits this service action.
        if permtype == 'delete' and accounting_attachment_context(self, deleting=True):
            return self
        return super().check_permission(permtype, permlevel)

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
                        frappe.throw('Il contenuto finanziario non può essere copiato in un allegato non protetto.',frappe.PermissionError)
        protected(self)
        if managed(self) and self.file_url and self.is_remote_file:
            frappe.throw('I documenti finanziari devono restare file locali conservati, mai URL remoti.',frappe.PermissionError)
        return super().before_insert()

    def validate(self):
        # Native File.validate can move the physical file before doc-event hooks run.
        protected(self)
        return super().validate()

    def on_trash(self):
        # Guard before the native controller unlinks bytes or adds comments.
        protected(self,method='on_trash')
        return super().on_trash()
