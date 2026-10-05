"""Supported model/logging extensions keep confidential request bodies out of diagnostics."""
import json
import logging
import frappe


def sensitive_request():
    if frappe.flags.get('cc_confidential_request'):
        return True
    request=getattr(frappe.local,'request',None)
    path=getattr(request,'path','')
    if 'centrochange_core.operations.notes.add_note' in path or any('centrochange_core.finance.'+name in path for name in ('incoming','sdi','ts','fiscal')):
        return True
    # API payloads can encode native documents as JSON. Do not retain clinical request bodies.
    return 'CC Private Note' in json.dumps(getattr(frappe.local,'form_dict',{}) or {},default=str) or 'CC%20Private%20Note' in path or 'CC Private Note' in path


class ConfidentialLogFilter(logging.Filter):
    def filter(self,record):
        if sensitive_request():
            record.msg='Confidential request diagnostic redacted; inspect sanitized Error Log fingerprint.'
            record.args=()
            record.exc_info=None
            record.exc_text=None
            record.stack_info=None
        return True


def before_request():
    frappe.flags.cc_confidential_request=sensitive_request()
    logger=frappe.logger(with_more_info=True)
    for handler in logger.handlers:
        if not any(isinstance(item,ConfidentialLogFilter) for item in handler.filters):
            # Runs after the native SiteContextFilter which adds Form Dict.
            handler.addFilter(ConfidentialLogFilter())


def redact(doc):
    if sensitive_request():
        doc.error='Confidential operation failed. Request, body and local variables redacted.'
        doc.method='Confidential operation'
        doc.metadata=frappe.as_json({'redacted':True,'fingerprint':doc.fingerprint})
        doc.reference_doctype=None
        doc.reference_name=None


class ErrorLogMixin:
    def deferred_insert(self):
        redact(self)
        return super().deferred_insert()

    def before_insert(self):
        redact(self)
        parent=getattr(super(),'before_insert',None)
        if parent:
            return parent()
