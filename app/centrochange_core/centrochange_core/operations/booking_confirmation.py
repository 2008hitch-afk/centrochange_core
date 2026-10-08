"""Immediate DEV-only confirmation via native Communication and simulated sink."""
from html import escape
import re
import frappe
from centrochange_core.security.audit import atomic, append, internal_write
from centrochange_core.security.guards import require_manager
from centrochange_core.security.lifecycle import lock
from centrochange_core.finance.guards import require_synthetic


def _simulate(doc):
    # No sendmail/SMTP/provider/Email Queue invocation. Only an example.invalid sink.
    if not doc.recipient.endswith('@example.invalid'):
        frappe.throw('Synthetic confirmation recipient required')
    return frappe.get_doc({'doctype':'Communication','communication_type':'Communication',
        'communication_medium':'Email','sent_or_received':'Sent','subject':'Centro Change — Conferma primo incontro',
        'content':doc.message,'recipients':doc.recipient,'sender':'cc-public-booking-service@example.invalid',
        'reference_doctype':'Patient Appointment','reference_name':doc.appointment}).insert(ignore_permissions=True).name


def deliver(name):
    require_synthetic();lock()
    doc=frappe.get_doc('CC Booking Confirmation',name,for_update=True)
    if doc.state=='Simulated Sent':return {'state':doc.state,'replay':True}
    frappe.db.savepoint('cc_confirmation_delivery')
    try:
        communication=_simulate(doc)
    except Exception:
        frappe.db.rollback(save_point='cc_confirmation_delivery')
        with internal_write('cc_confirmation_write'):
            doc.update({'state':'Failed','attempts':doc.attempts+1,'last_error':'Simulated confirmation failed; management retry required'}).save(ignore_permissions=True)
        append('BOOKING_CONFIRMATION_FAILED',doc.doctype,doc.name,None,{'appointment':doc.appointment,'state':'Failed'},'First-meeting confirmation')
        return {'state':'Failed','replay':False}
    with internal_write('cc_confirmation_write'):
        doc.update({'state':'Simulated Sent','attempts':doc.attempts+1,'communication':communication,'last_error':None}).save(ignore_permissions=True)
    append('BOOKING_CONFIRMATION_SIMULATED',doc.doctype,doc.name,None,{'appointment':doc.appointment,'state':doc.state},'First-meeting confirmation')
    return {'state':doc.state,'replay':False}


def confirm(appointment,route,email):
    require_synthetic();lock()
    from centrochange_core.scheduling.public_booking import SERVICE_USER
    if frappe.session.user!=SERVICE_USER:
        frappe.throw('Public confirmation service scope required',frappe.PermissionError)
    doc=frappe.get_doc('Patient Appointment',appointment)
    old=frappe.db.get_value('CC Booking Confirmation',{'appointment':appointment},'name',for_update=True)
    if old:return {'state':frappe.db.get_value('CC Booking Confirmation',old,'state'),'replay':True}
    if route not in ('Marco','Francesca') or not email.endswith('@example.invalid'):
        frappe.throw('Synthetic first-meeting confirmation required')
    date=frappe.utils.getdate(doc.appointment_date).strftime('%d/%m/%Y')
    time=str(frappe.utils.get_time(doc.appointment_time))[:5]
    message='<p>Primo incontro confermato per il '+date+' alle '+time+' con '+escape(route)+'.</p><p>Servizio: '+escape(re.sub(r'^CC-HTTP-[A-Za-z0-9]+\s+','',doc.cc_service_label))+' · '+str(int(doc.duration))+' minuti.</p><p>Conferma registrata in simulazione: nessuna email reale inviata.</p>'
    with internal_write('cc_confirmation_write'):
        outbox=frappe.get_doc({'doctype':'CC Booking Confirmation','appointment':doc.name,'center':doc.cc_center,'recipient':email,'message':message,'state':'Pending'}).insert(ignore_permissions=True)
    return deliver(outbox.name)


@frappe.whitelist(methods=['GET'])
def records(center):
    require_manager()
    return frappe.get_list('CC Booking Confirmation',filters={'center':center},fields=['name','appointment','recipient','state','attempts','last_error','message'],page_length=100,order_by='creation desc')


@frappe.whitelist(methods=['POST'])
@atomic
def retry(name,reason):
    require_manager();require_synthetic();lock()
    if not reason or not reason.strip():frappe.throw('A retry reason is required')
    doc=frappe.get_doc('CC Booking Confirmation',name)
    result=deliver(name)
    append('BOOKING_CONFIRMATION_RETRIED',doc.doctype,name,None,{'state':result['state']},reason)
    return result
