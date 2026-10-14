"""Bounded, explicitly scoped operational projections for the primary workspace."""
from datetime import timedelta
import json
import frappe
from frappe.utils import getdate,get_time
from centrochange_core.security.guards import enabled,is_manager,roles,require_center,current_rows
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
    from centrochange_core.operations.packages import balance
    packages=[]
    for row in frappe.get_list('CC Patient Package',filters={'patient':patient},fields=['name','template'],page_length=100):
        doc=frappe.get_doc('CC Patient Package',row.name)
        if center in [eligible.center for eligible in doc.centers]:
            packages.append({'name':row.name,'label':frappe.db.get_value('CC Package Template',row.template,'title'),
                **balance(row.name,center)})
    return {'appointments':appointments[:100],'truncated':len(appointments)>100,
        'settlements':settlements,'organizational_notes':organizational,'private_notes':private,'packages':packages}


@frappe.whitelist(methods=['GET'])
def appointment_events(appointment):
    """Operational timeline scoped to one readable appointment, without audit-table access."""
    require_actor()
    doc=frappe.get_doc('Patient Appointment',appointment)
    require_context(doc.patient,doc.cc_center)
    doc.check_permission('read')
    allowed={'APPOINTMENT_BOOKED':('appointment_date','appointment_time'),
             'APPOINTMENT_RESCHEDULED':('appointment_date','appointment_time'),
             'SESSION_CANCELLED':('late','economic'),
             'SESSION_CLOSED':('performed','economic'),
             'SESSION_REOPENED':('closure',),
             'ECONOMIC_WAIVER':('economic','late'),
             'OPERATIONAL_SETTLEMENT':('paid','method')}
    rows=current_rows('CC Audit Event',{'reference_doctype':'Patient Appointment',
        'reference_name':doc.name,'event_type':['in',list(allowed)]},
        fields=['event_type','actor','event_time','reason','before_state','after_state'])
    if len(rows)>100:
        frappe.throw('Storico troppo esteso: restringere la consultazione.')
    result=[]
    for row in sorted(rows,key=lambda event:event.event_time):
        keys=allowed[row.event_type]
        before=json.loads(row.before_state or '{}') or {}
        after=json.loads(row.after_state or '{}') or {}
        result.append({'event_type':row.event_type,'actor':row.actor,'event_time':row.event_time,
                       'reason':row.reason,'before':{key:before[key] for key in keys if key in before},
                       'after':{key:after[key] for key in keys if key in after}})
    return result


@frappe.whitelist()
def bootstrap(center=None):
    from centrochange_core.security.guards import practitioner_for,current_rows,operational_centers
    require_actor()
    available=operational_centers()
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
    names=frappe.get_list('Practitioner Schedule',filters={'cc_center':center,'disabled':0},pluck='name',page_length=100)
    result=[]
    for name in names:
        doc=frappe.get_doc('Practitioner Schedule',name)
        doc.check_permission('read')
        absences=frappe.get_list('Practitioner Availability',filters={'cc_center':center,'scope_type':'Healthcare Practitioner','scope':doc.cc_practitioner,'type':'Unavailable','docstatus':1},fields=['start_date','end_date','start_time','end_time','repeat'],page_length=100)
        for absence in absences:
            absence.start_time=str(get_time(absence.start_time))
            absence.end_time=str(get_time(absence.end_time))
        result.append({'name':name,'practitioner':doc.cc_practitioner,'absences':absences,'time_slots':[{'day':row.day,'from_time':str(get_time(row.from_time)),'to_time':str(get_time(row.to_time))} for row in doc.time_slots]})
    return result


@frappe.whitelist(methods=['POST'])
def create_patient(center,first_name,sex,uid,practitioner,request_key,reason,last_name=None,email=None):
    # Reuse the central native Patient and assignment services; no clinical master is added.
    from centrochange_core.security.audit import atomic
    return atomic(_create_patient)(center,first_name,sex,uid,practitioner,request_key,reason,last_name,email)


def _create_patient(center,first_name,sex,uid,practitioner,request_key,reason,last_name,email):
    from hashlib import sha256
    from centrochange_core.security.audit import append,internal_write,serialize
    from centrochange_core.security.lifecycle import lock,set_assignment
    from centrochange_core.security.guards import require_operations
    from centrochange_core.finance.guards import require_synthetic
    lock();require_operations(center);require_synthetic()
    first_name=str(first_name or '').strip();last_name=str(last_name or '').strip();uid=str(uid or '').strip();email=str(email or '').strip().lower() or None
    if not first_name.startswith(('SYNTHETIC','CC-HTTP-')) or not uid.startswith(('SYNTHETIC-','CC-HTTP-')):
        frappe.throw('This DEV intake accepts explicitly synthetic identity inputs only')
    if len(first_name)>140 or len(last_name)>140 or len(uid)>140 or not frappe.db.exists('Gender',sex):
        frappe.throw('Bounded identity fields and an existing native gender are required')
    if email and (not email.endswith('@example.invalid') or len(email)>140 or not frappe.utils.validate_email_address(email)):
        frappe.throw('Only a valid fictional example.invalid email is permitted')
    if not request_key or len(request_key)>160:frappe.throw('A bounded patient intake key is required')
    key=sha256(serialize([frappe.session.user,center,request_key]).encode()).hexdigest()
    payload={'center':center,'first_name':first_name,'last_name':last_name,'sex':sex,'uid':uid,'email':email,'practitioner':practitioner}
    digest=sha256(serialize(payload).encode()).hexdigest()
    old=frappe.db.get_value('Patient',{'cc_intake_key':key},['name','cc_intake_hash'],as_dict=True,for_update=True)
    if old:
        if old.cc_intake_hash!=digest:frappe.throw('Patient intake retry differs from the recorded request')
        from centrochange_core.security.guards import require_patient
        require_patient(old.name)
        return {'name':old.name,'replay':True}
    if frappe.db.exists('Patient',{'uid':uid}):
        frappe.throw('Identity already exists; use exact UID discovery and an explicit assignment')
    with internal_write('cc_patient_intake_write'):
        doc=frappe.get_doc({'doctype':'Patient','first_name':first_name,'last_name':last_name,'sex':sex,'uid':uid,'email':email,
            'invite_user':0,'cc_intake_key':key,'cc_intake_hash':digest}).insert(ignore_permissions=True)
    set_assignment(doc.name,center,practitioner,1,reason)
    append('PATIENT_INTAKE_CREATED','Patient',doc.name,None,{'center':center,'payload_hash':digest},reason)
    return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['GET'])
def management_context(center):
    from centrochange_core.security.guards import require_manager,current_rows
    require_manager()
    users=current_rows('Has Role',{'role':['in',['CC Professional','CC Secretariat','CC Finance','CC Accountant','CC Manager']]},pluck='parent')
    return {'users':current_rows('User',{'name':['in',users or ['']]},fields=['name','full_name','enabled']),
        'memberships':current_rows('CC Center Membership',{'center':center},fields=['name','user','active']),
        'practitioners':current_rows('Healthcare Practitioner',fields=['name','practitioner_name','user_id','status'])}


@frappe.whitelist(methods=['GET'])
def patient_search(center, query=''):
    """Permission-aware bounded operational identity search; never clinical content."""
    require_actor(); require_center(center)
    query=str(query or '').strip()
    if len(query)>140:frappe.throw('Search text is too long')
    filters={}
    if not is_manager():
        from centrochange_core.security.guards import patient_contexts
        filters['name']=['in',[p for p,c in patient_contexts() if c==center] or ['']]
    text='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    # Non-manager roles use document-scoped Patient permissions, not generic list rights.
    # The narrow internal query is confined to exact current authorized patient/center pairs.
    lookup=frappe.get_list if is_manager() else frappe.get_all
    rows=lookup('Patient',filters=filters,
        or_filters={k:['like',text] for k in ['patient_name','first_name','last_name','name','uid']},
        fields=['name','patient_name','uid'],order_by='patient_name,name',page_length=51)
    return {'patients':rows[:50],'truncated':len(rows)>50}
