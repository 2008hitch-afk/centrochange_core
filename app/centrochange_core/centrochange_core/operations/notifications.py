"""Idempotent internal delivery via native Notification Log; no external mail provider."""
import frappe
from centrochange_core.security.audit import atomic,internal_write,append
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,require_manager
from centrochange_core.operations.install import AUTOMATION_USER


@atomic
def deliver(name):
    previous=frappe.session.user
    try:
        frappe.set_user(AUTOMATION_USER)
        lock()
        doc=frappe.get_doc('CC Notification',name,for_update=True)
        if doc.state=='Sent':
            return {'state':'Sent','replay':True}
        existing=frappe.db.get_value('Notification Log',{'cc_notification':name},for_update=True)
        attempts=doc.attempts+1
        if doc.recipient=='Guest' or not frappe.db.get_value('User',doc.recipient,'enabled',for_update=True):
            with internal_write('cc_notification_write'):
                doc.update({'state':'Failed','attempts':attempts,'last_error':'Recipient disabled'}).save(ignore_permissions=True)
            return {'state':'Failed','replay':False}
        # Native insertion is rolled back if delivery fails; no half-delivered outbox row.
        if not existing:
            frappe.get_doc({'doctype':'Notification Log','for_user':doc.recipient,'type':'Alert',
                'subject':doc.message,'email_content':doc.message,'cc_notification':name}).insert(ignore_permissions=True)
        with internal_write('cc_notification_write'):
            doc.update({'state':'Sent','attempts':attempts,'last_error':None}).save(ignore_permissions=True)
        return {'state':'Sent','replay':bool(existing)}
    finally:
        frappe.set_user(previous)


def dispatch_pending():
    names=[row.name for row in current_rows('CC Notification',{'state':['in',['Pending','Failed']]},fields=['name','attempts','retry_limit']) if row.attempts<(row.retry_limit or 5)][:100]
    results=[]
    for name in names:
        try:
            results.append(deliver(name))
        except Exception:
            # Bound and sanitize operational diagnostics; native transaction rollback preserves retry.
            previous=frappe.session.user
            try:
                frappe.set_user(AUTOMATION_USER)
                lock()
                doc=frappe.get_doc('CC Notification',name,for_update=True)
                with internal_write('cc_notification_write'):
                    doc.update({'state':'Failed','attempts':doc.attempts+1,'last_error':'Internal delivery failed; inspect protected server diagnostics'}).save(ignore_permissions=True)
                results.append({'state':'Failed'})
            finally:
                frappe.set_user(previous)
    return {'sent':sum(row['state']=='Sent' for row in results),'failed':sum(row['state']=='Failed' for row in results)}


@frappe.whitelist(methods=['POST'])
@atomic
def retry(name,reason):
    lock()
    require_manager()
    if not reason or not reason.strip():
        frappe.throw('Indica il motivo del nuovo tentativo.')
    doc=frappe.get_doc('CC Notification',name,for_update=True)
    if doc.state=='Sent':
        return {'name':name,'replay':True}
    with internal_write('cc_notification_write'):
        doc.update({'state':'Pending','retry_limit':doc.attempts+5,'last_error':None}).save(ignore_permissions=True)
    append('NOTIFICATION_RETRY',doc.doctype,name,None,{'state':'Pending'},reason)
    return {'name':name,'replay':False}

@frappe.whitelist(methods=['GET'])
def target(name):
    """Resolve historical payment notices only after checking both records' scope."""
    doc = frappe.get_doc('CC Notification', name)
    doc.check_permission('read')
    if doc.kind == 'CLOSURE_REMINDER':
        parts = (doc.event_key or '').split(':')
        if len(parts) >= 3 and parts[0] == 'closure-reminder':
            return {'day_closure':parts[1]}
        return None
    if doc.reference_doctype != 'CC Payment Notice' or not doc.reference_name:
        return None
    notice = frappe.get_doc('CC Payment Notice', doc.reference_name)
    notice.check_permission('read')
    from centrochange_core.finance.guards import patient_context
    patient_context(notice.patient, notice.center)
    return {'patient':notice.patient, 'center':notice.center}
