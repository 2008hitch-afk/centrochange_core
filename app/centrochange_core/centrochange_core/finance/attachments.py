"""Manual private administrative attachments on existing native documents."""
import base64
import binascii
from pathlib import PurePath

import frappe
from frappe.utils.file_manager import save_file

from centrochange_core.finance.guards import require_finance
from centrochange_core.security.audit import append, internal_write


MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {
    '.pdf': (b'%PDF-',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
}
PARENTS = {'Sales Invoice', 'Purchase Invoice', 'Bank Transaction', 'CC Incoming Invoice'}


def _parent(doctype, name, write=False):
    if doctype not in PARENTS or not name:
        frappe.throw('Documento amministrativo non supportato.', frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    center = doc.get('center') if doctype == 'CC Incoming Invoice' else doc.get('cc_center')
    if not center:
        frappe.throw('Il documento non è associato a una sede Centro Change.', frappe.PermissionError)
    require_finance(center, write)
    doc.check_permission('read')
    if write and doc.get('docstatus') == 2:
        frappe.throw('Non puoi allegare file a un documento annullato.')
    return doc, center


@frappe.whitelist(methods=['GET'])
def list_for_document(doctype, name):
    doc, _center = _parent(doctype, name)
    files = frappe.get_all('File', filters={
        'attached_to_doctype': doc.doctype, 'attached_to_name': doc.name,
        'is_private': 1, 'is_remote_file': 0,
    }, fields=['name', 'file_name', 'file_url', 'creation'], order_by='creation asc')
    return [{'name': row.name, 'file_name': row.file_name, 'file_url': row.file_url,
             'creation': row.creation} for row in files]


@frappe.whitelist(methods=['POST'])
def attach(doctype, name, file_name, content_base64, reason):
    parent, center = _parent(doctype, name, write=True)
    if not reason or not reason.strip():
        frappe.throw('Indica il motivo dell’allegato.')
    safe_name = PurePath(str(file_name or '').replace('\\', '/')).name
    suffix = PurePath(safe_name).suffix.lower()
    if not safe_name or len(safe_name) > 180 or suffix not in ALLOWED:
        frappe.throw('Carica un PDF, JPG o PNG con un nome file valido.')
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError, TypeError):
        frappe.throw('Il contenuto del file non è valido.')
    if not raw or len(raw) > MAX_BYTES:
        frappe.throw('Il file deve avere dimensione massima di 5 MB.')
    if not any(raw.startswith(signature) for signature in ALLOWED[suffix]):
        frappe.throw('Il contenuto non corrisponde al formato dichiarato del file.')
    with internal_write('cc_finance_attachment_write'):
        file_doc = save_file(safe_name, raw, parent.doctype, parent.name, is_private=1)
    if not file_doc.is_private or file_doc.is_remote_file:
        frappe.throw('Il file non è stato conservato come allegato privato locale.', frappe.PermissionError)
    append('FINANCIAL_DOCUMENT_ATTACHED', parent.doctype, parent.name,
           {}, {'file': file_doc.name, 'file_name': safe_name, 'center': center}, reason.strip())
    return {'file': file_doc.name, 'file_name': safe_name, 'file_url': file_doc.file_url,
            'private': True, 'center': center}
