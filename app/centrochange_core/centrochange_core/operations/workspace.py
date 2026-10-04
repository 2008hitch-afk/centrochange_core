"""Bounded, explicitly scoped operational projections for the primary workspace."""
from datetime import timedelta
import frappe
from frappe.utils import getdate
from centrochange_core.security.guards import enabled,is_manager,roles,require_center
from centrochange_core.operations.notes import require_context

APPOINTMENT_FIELDS=['name','patient','patient_name','practitioner','practitioner_name','cc_center',
    'appointment_date','appointment_time','duration','status','cc_closure_state','cc_economic_state',
    'cc_performed','cc_paid','cc_service_label','cc_price_snapshot','cc_currency_snapshot','cc_package','cc_package_state']


def require_actor():
    if not enabled() or not (is_manager() or {'CC Professional','CC Secretariat'} & set(roles())):
        frappe.throw('Operational workspace access denied',frappe.PermissionError)


@frappe.whitelist()
def agenda(center,start,end):
    require_actor()
    require_center(center)
    start,end=getdate(start),getdate(end)
    if end<start or end-start>timedelta(days=92):
        frappe.throw('Select an agenda interval of at most 93 days')
    rows=frappe.get_list('Patient Appointment',filters={'cc_center':center,'appointment_date':['between',[start,end]]},
        fields=APPOINTMENT_FIELDS,order_by='appointment_date,appointment_time,name',page_length=201)
    return {'appointments':rows[:200],'truncated':len(rows)>200}


@frappe.whitelist()
def patient_history(patient,center):
    require_actor()
    require_context(patient,center)
    appointments=frappe.get_list('Patient Appointment',filters={'patient':patient,'cc_center':center},
        fields=APPOINTMENT_FIELDS,order_by='appointment_date desc,appointment_time desc,name',page_length=101)
    identifiers=[row.name for row in appointments[:100]]
    settlements=frappe.get_list('CC Settlement',filters={'appointment':['in',identifiers or ['']]},
        fields=['name','appointment','paid','mode_of_payment','sequence','actor','event_time','reason'],
        order_by='creation desc',page_length=200)
    organizational=frappe.get_list('CC Organizational Note',filters={'patient':patient,'center':center},
        fields=['name','practitioner','content','authored_by','creation','corrects'],order_by='creation desc',page_length=100)
    # A non-clinical principal never asks native list APIs for a private table.
    private=[]
    if 'CC Professional' in roles():
        private=frappe.get_list('CC Private Note',filters={'patient':patient,'center':center},
            fields=['name','content','authored_by','creation','corrects'],order_by='creation desc',page_length=100)
    return {'appointments':appointments[:100],'truncated':len(appointments)>100,
        'settlements':settlements,'organizational_notes':organizational,'private_notes':private}
