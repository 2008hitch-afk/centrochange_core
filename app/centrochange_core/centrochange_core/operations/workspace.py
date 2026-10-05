"""Bounded, explicitly scoped operational projections for the primary workspace."""
from datetime import timedelta
import frappe
from frappe.utils import getdate,get_time
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
    for row in rows:
        row.appointment_time=str(get_time(row.appointment_time))
    return {'appointments':rows[:200],'truncated':len(rows)>200}


@frappe.whitelist()
def patient_history(patient,center):
    require_actor()
    require_context(patient,center)
    appointments=frappe.get_list('Patient Appointment',filters={'patient':patient,'cc_center':center},
        fields=APPOINTMENT_FIELDS,order_by='appointment_date desc,appointment_time desc,name',page_length=101)
    for row in appointments:
        row.appointment_time=str(get_time(row.appointment_time))
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


@frappe.whitelist()
def bootstrap(center=None):
    from centrochange_core.security.guards import centers,practitioner_for,current_rows
    require_actor()
    available=current_rows('Branch',fields=['name','branch']) if is_manager() else current_rows('Branch',{'name':['in',centers() or ['']]},fields=['name','branch'])
    if not available:
        return {'centers':[],'patients':[],'practitioners':[],'services':[],'payment_methods':[],'roles':roles()}
    center=center or available[0].name
    require_center(center)
    if center not in [row.name for row in available]:
        frappe.throw('Unknown center',frappe.PermissionError)
    try:
        patients=frappe.get_list('Patient',fields=['name','patient_name'],page_length=500,order_by='patient_name')
    except frappe.PermissionError:
        patients=[]
    from centrochange_core.security.guards import patient_contexts
    if not is_manager():
        contexts=patient_contexts()
        patients=[row for row in patients if (row.name,center) in contexts]
    memberships=current_rows('CC Center Membership',{'center':center,'active':1},pluck='user')
    filters={'status':'Active','user_id':['in',memberships or ['']]}
    if 'CC Professional' in roles() and not is_manager():
        filters['name']=practitioner_for() or ''
    practitioners=current_rows('Healthcare Practitioner',filters,fields=['name','practitioner_name'])
    profiles=current_rows('CC Center Service',{'center':center,'enabled':1},pluck='appointment_type')
    from centrochange_core.scheduling.booking import snapshot
    services=[]
    for profile in profiles:
        try:
            services.append({'name':profile,**snapshot(profile,center)})
        except frappe.ValidationError:
            # Incomplete catalog is unavailable, never silently priced at zero.
            pass
    from centrochange_core.operations.packages import _balance
    packages=[]
    for row in frappe.get_list('CC Patient Package',fields=['name','patient','template','service_item','practitioner'],page_length=200):
        doc=frappe.get_doc('CC Patient Package',row.name)
        if center in [eligible.center for eligible in doc.centers]:
            packages.append({**row,'label':frappe.db.get_value('CC Package Template',row.template,'title'),**_balance(row.name)})
    return {'center':center,'centers':available,'patients':patients,'practitioners':practitioners,'services':services,
        'packages':packages,'payment_methods':current_rows('Mode of Payment',{'enabled':1},pluck='name'),'roles':roles()}


@frappe.whitelist()
def schedules(center):
    require_actor()
    require_center(center)
    names=frappe.get_list('Practitioner Schedule',filters={'cc_center':center},pluck='name',page_length=100)
    result=[]
    for name in names:
        doc=frappe.get_doc('Practitioner Schedule',name)
        doc.check_permission('read')
        result.append({'name':name,'practitioner':doc.cc_practitioner,'time_slots':[{'day':row.day,'from_time':str(get_time(row.from_time)),'to_time':str(get_time(row.to_time))} for row in doc.time_slots]})
    return result
