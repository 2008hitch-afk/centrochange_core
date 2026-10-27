"""Bounded, explicitly scoped operational projections for the primary workspace."""
from datetime import timedelta
import json
import frappe
from frappe.utils import getdate,get_time
from centrochange_core.security.guards import enabled,is_manager,roles,require_center,current_rows
from centrochange_core.operations.notes import require_context

APPOINTMENT_FIELDS=['name','patient','patient_name','practitioner','practitioner_name','cc_center',
    'appointment_date','appointment_time','duration','status','cc_closure_state','cc_economic_state',
    'cc_performed','cc_paid','cc_late_cancellation','cc_service_label','cc_price_snapshot','cc_currency_snapshot','cc_package','cc_package_state']


def require_actor():
    if not enabled() or not (is_manager() or {'CC Professional','CC Secretariat'} & set(roles())):
        frappe.throw('Non hai accesso alla schermata operativa.',frappe.PermissionError)


def center_patient_names(center, include_historical=False):
    """Patient IDs in a center; historical records are Manager search only."""
    if is_manager():
        filters={'center':center}
        if not include_historical:
            filters['active']=1
        return current_rows('CC Patient Assignment', filters, pluck='patient')
    from centrochange_core.security.guards import patient_contexts
    return [patient for patient, assigned_center in patient_contexts() if assigned_center == center]


def require_history_context(patient, center):
    """Read historical center records only for a Manager still authorized there."""
    require_center(center)
    if is_manager() and current_rows('CC Patient Assignment',
            {'patient':patient,'center':center},pluck='name'):
        return bool(current_rows('CC Patient Assignment',
            {'patient':patient,'center':center,'active':1},pluck='name'))
    require_context(patient,center)
    return True


@frappe.whitelist()
def agenda(center, start, end, practitioner=None):
    require_actor()
    require_center(center)
    start, end = getdate(start), getdate(end)
    if end < start or end - start > timedelta(days=92):
        frappe.throw('Seleziona un intervallo Agenda di massimo 93 giorni.')
    filters = {'cc_center': center, 'appointment_date': ['between', [start, end]]}
    from centrochange_core.security.guards import roles, is_manager, practitioner_for
    user_roles = roles()
    if 'CC Professional' in user_roles and not is_manager():
        my_practitioner = practitioner_for()
        filters['practitioner'] = my_practitioner
    elif practitioner:
        if isinstance(practitioner, str) and ',' in practitioner:
            filters['practitioner'] = ['in', [p.strip() for p in practitioner.split(',') if p.strip()]]
        elif isinstance(practitioner, list):
            filters['practitioner'] = ['in', practitioner]
        elif practitioner not in ('all', '', None):
            filters['practitioner'] = practitioner

    # Query full period (up to bounded MAX_AGENDA_LIMIT = 5000) without premature 500 truncation
    MAX_AGENDA_LIMIT = 5000
    rows = frappe.get_list('Patient Appointment', filters=filters,
        fields=APPOINTMENT_FIELDS, order_by='appointment_date,appointment_time,name', page_length=MAX_AGENDA_LIMIT + 1)
    truncated = len(rows) > MAX_AGENDA_LIMIT
    if truncated:
        rows = rows[:MAX_AGENDA_LIMIT]

    # Resolve patient identities in bounded batches of 200
    patient_ids = list({row.patient for row in rows if getattr(row, 'patient', None)})
    patient_query = frappe.get_list if is_manager() else frappe.get_all
    names = {}
    CHUNK_SIZE = 200
    if patient_ids:
        for i in range(0, len(patient_ids), CHUNK_SIZE):
            chunk = patient_ids[i:i + CHUNK_SIZE]
            p_rows = patient_query('Patient',
                filters={'name': ['in', chunk]},
                fields=['name', 'first_name', 'last_name'], page_length=len(chunk))
            for p in p_rows:
                p_name = getattr(p, 'name', None) or (p.get('name') if isinstance(p, dict) else None)
                names[p_name] = p

    for row in rows:
        row.appointment_time = str(get_time(row.appointment_time))
        identity = names.get(row.patient)
        if identity:
            row.patient_first_name = getattr(identity, 'first_name', None) or (identity.get('first_name') if isinstance(identity, dict) else None)
            row.patient_last_name = getattr(identity, 'last_name', None) or (identity.get('last_name') if isinstance(identity, dict) else None)
        else:
            row.patient_first_name = None
            row.patient_last_name = None

    return {'appointments': rows, 'total': len(rows), 'truncated': truncated}


@frappe.whitelist()
def patient_history(patient, center, page=None, page_length=50):
    require_actor()
    active_context = require_history_context(patient, center)

    total_appointments = 0
    if hasattr(frappe, 'db') and hasattr(frappe.db, 'count'):
        try:
            total_appointments = frappe.db.count('Patient Appointment', filters={'patient': patient, 'cc_center': center})
        except Exception:
            total_appointments = 0

    def _cint(v, default=0):
        try:
            return int(v)
        except (ValueError, TypeError):
            return default

    p = _cint(page) if page is not None else None
    pl = _cint(page_length, 50) if page_length else 50
    if pl <= 0:
        pl = 50

    if p is not None:
        p = max(1, p)
        offset = (p - 1) * pl
        appointments = frappe.get_list('Patient Appointment', filters={'patient': patient, 'cc_center': center},
            fields=APPOINTMENT_FIELDS, order_by='appointment_date desc,appointment_time desc,name',
            limit_start=offset, page_length=pl)
        truncated = False
        if not total_appointments:
            total_appointments = len(appointments)
        total_pages = max(1, (total_appointments + pl - 1) // pl)
    else:
        appointments = frappe.get_list('Patient Appointment', filters={'patient': patient, 'cc_center': center},
            fields=APPOINTMENT_FIELDS, order_by='appointment_date desc,appointment_time desc,name', page_length=101)
        truncated = len(appointments) > 100
        appointments = appointments[:100]
        if not total_appointments:
            total_appointments = len(appointments)
        total_pages = 1
        p = 1

    for row in appointments:
        row.appointment_time = str(get_time(row.appointment_time))
    identifiers = [row.name for row in appointments]
    settlements = frappe.get_list('CC Settlement', filters={'appointment': ['in', identifiers or ['']]},
        fields=['name', 'appointment', 'paid', 'mode_of_payment', 'sequence', 'actor', 'event_time', 'reason'],
        order_by='creation desc', page_length=max(200, len(identifiers) * 2))
    organizational = frappe.get_list('CC Organizational Note', filters={'patient': patient, 'center': center},
        fields=['name', 'practitioner', 'content', 'authored_by', 'creation', 'corrects'], order_by='creation desc', page_length=100)
    # A non-clinical principal never asks native list APIs for a private table.
    private = []
    if 'CC Professional' in roles():
        private = frappe.get_list('CC Private Note', filters={'patient': patient, 'center': center},
            fields=['name', 'content', 'authored_by', 'creation', 'corrects'], order_by='creation desc', page_length=100)
    from centrochange_core.operations.packages import balance, _balance
    packages = []
    for row in frappe.get_list('CC Patient Package', filters={'patient': patient}, fields=['name', 'template'], page_length=100):
        doc = frappe.get_doc('CC Patient Package', row.name)
        if center in [eligible.center for eligible in doc.centers]:
            packages.append({'name': row.name, 'label': frappe.db.get_value('CC Package Template', row.template, 'title'),
                'valid_until': str(doc.valid_until) if doc.valid_until else None,
                'practitioner': doc.practitioner, **(balance(row.name, center) if active_context else _balance(row.name))})
    assignment_rows = current_rows('CC Patient Assignment', {'patient': patient, 'center': center},
        fields=['name', 'practitioner'])
    names = [(row.name if hasattr(row, 'name') else (row.get('name') if isinstance(row, dict) else row)) for row in assignment_rows]
    practitioners = {
        (row.name if hasattr(row, 'name') else (row.get('name') if isinstance(row, dict) else row)):
        (row.practitioner if hasattr(row, 'practitioner') else (row.get('practitioner') if isinstance(row, dict) else None))
        for row in assignment_rows
    }
    assignment_events = []
    if names:
        events = current_rows('CC Audit Event', {'reference_doctype': 'CC Patient Assignment',
            'reference_name': ['in', names], 'event_type': 'PATIENT_ASSIGNMENT'},
            fields=['reference_name', 'actor', 'event_time', 'reason', 'after_state'])
        if len(events) > 200:
            frappe.throw('Storico assegnazioni troppo esteso: contatta la Direzione.')
        for event in sorted(events, key=lambda item: item.event_time, reverse=True):
            after = json.loads(event.after_state or '{}')
            assignment_events.append({'practitioner': practitioners[event.reference_name],
                'active': int(after.get('active', 0)), 'actor': event.actor,
                'event_time': event.event_time, 'reason': event.reason})
    return {
        'appointments': appointments,
        'total_appointments': total_appointments,
        'page': p,
        'page_length': pl,
        'total_pages': total_pages,
        'truncated': truncated,
        'settlements': settlements,
        'organizational_notes': organizational,
        'private_notes': private,
        'packages': packages,
        'assignment_events': assignment_events
    }


@frappe.whitelist(methods=['GET'])
def appointment_events(appointment):
    """Operational timeline scoped to one readable appointment, without audit-table access."""
    require_actor()
    doc=frappe.get_doc('Patient Appointment',appointment)
    require_history_context(doc.patient,doc.cc_center)
    doc.check_permission('read')
    allowed={'APPOINTMENT_BOOKED':('appointment_date','appointment_time'),
             'APPOINTMENT_RESCHEDULED':('appointment_date','appointment_time'),
             'SESSION_CANCELLED':('late','economic'),
             'SESSION_CLOSED':('performed','economic','paid','method','note'),
             'SESSION_LATE_COMPLETED':('performed','economic','paid','method','note'),
             'SESSION_AUTO_LOCKED':('closure',),
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
        return {'centers':[],'patients':[],'practitioners':[],'services':[],'payment_methods':[],'roles':roles(),'demo_labels':{}}
    center=center or available[0].name
    require_center(center)
    if center not in [row.name for row in available]:
        frappe.throw('La sede selezionata non è disponibile.',frappe.PermissionError)
    try:
        patients=frappe.get_list('Patient',filters={'name':['in',center_patient_names(center) or ['']]},
            fields=['name','patient_name','first_name','last_name'],page_length=500,order_by='patient_name')
    except frappe.PermissionError:
        patients=[]
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
    from centrochange_core.uat.display import operational_aliases
    return {'center':center,'centers':available,'patients':patients,'practitioners':practitioners,'services':services,
        'packages':packages,'payment_methods':current_rows('Mode of Payment',{'enabled':1},pluck='name'),'roles':roles(),
        'demo_labels':operational_aliases(center,patients,practitioners,services,packages,available,is_manager())}


@frappe.whitelist()
def schedules(center):
    require_actor()
    require_center(center)
    names=frappe.get_list('Practitioner Schedule',filters={'cc_center':center,'disabled':0},pluck='name',page_length=100)
    result=[]
    for name in names:
        doc=frappe.get_doc('Practitioner Schedule',name)
        doc.check_permission('read')
        absences=frappe.get_list('Practitioner Availability',filters={'cc_center':center,'scope_type':'Healthcare Practitioner','scope':doc.cc_practitioner,'type':'Unavailable','docstatus':1},fields=['name','start_date','end_date','start_time','end_time','repeat'],page_length=100)
        for absence in absences:
            absence.start_time=str(get_time(absence.start_time))
            absence.end_time=str(get_time(absence.end_time))
        result.append({'name':name,'modified':str(doc.modified),'practitioner':doc.cc_practitioner,'absences':absences,'time_slots':[{'day':row.day,'from_time':str(get_time(row.from_time)),'to_time':str(get_time(row.to_time))} for row in doc.time_slots]})
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
        frappe.throw('Nel DEV sono ammesse solo identità esplicitamente sintetiche.')
    if len(first_name)>140 or len(last_name)>140 or len(uid)>140 or not frappe.db.exists('Gender',sex):
        frappe.throw('Compila i dati identificativi nei limiti previsti e seleziona un sesso valido.')
    if email and (not email.endswith('@example.invalid') or len(email)>140 or not frappe.utils.validate_email_address(email)):
        frappe.throw('È consentita solo una email demo valida del dominio example.invalid.')
    if not request_key or len(request_key)>160:frappe.throw('Indica un identificativo valido per la creazione del paziente.')
    key=sha256(serialize([frappe.session.user,center,request_key]).encode()).hexdigest()
    payload={'center':center,'first_name':first_name,'last_name':last_name,'sex':sex,'uid':uid,'email':email,'practitioner':practitioner}
    digest=sha256(serialize(payload).encode()).hexdigest()
    old=frappe.db.get_value('Patient',{'cc_intake_key':key},['name','cc_intake_hash'],as_dict=True,for_update=True)
    if old:
        if old.cc_intake_hash!=digest:frappe.throw('La creazione del paziente è già stata usata con dati diversi.')
        from centrochange_core.security.guards import require_patient
        require_patient(old.name)
        return {'name':old.name,'replay':True}
    if frappe.db.exists('Patient',{'uid':uid}):
        frappe.throw('L’identità esiste già: cerca l’UID esatto e assegna esplicitamente il paziente.')
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
    permitted_roles = ['CC Professional', 'CC Secretariat', 'CC Finance', 'CC Accountant', 'CC Manager']
    role_records = current_rows('Has Role', {'role': ['in', permitted_roles]}, fields=['parent', 'role'])
    user_ids = sorted({row.parent for row in role_records})
    role_names = {}
    for row in role_records:
        role_names.setdefault(row.parent, []).append(row.role)
    visible_users = current_rows('User', {'name': ['in', user_ids or ['']]},
                                 fields=['name', 'full_name', 'enabled'])
    return {'users': [{**dict(row), 'roles': sorted(role_names.get(row.name, []))}
                      for row in visible_users],
        'memberships': current_rows('CC Center Membership', {'center': center},
                                    fields=['name', 'user', 'active', 'modified']),
        'practitioners': current_rows('Healthcare Practitioner',
                                     fields=['name', 'practitioner_name', 'user_id', 'status', 'modified'])}


@frappe.whitelist(methods=['GET'])
def patient_search(center, query=''):
    """Permission-aware bounded operational identity search; never clinical content."""
    require_actor(); require_center(center)
    from centrochange_core.security.guards import operational_centers
    if center not in [row.name for row in operational_centers()]:
        frappe.throw('La sede selezionata non è disponibile.', frappe.PermissionError)
    query=str(query or '').strip()
    if len(query)>140:frappe.throw('Il testo di ricerca è troppo lungo.')
    all_names=set(center_patient_names(center,include_historical=True))
    active_names=set(center_patient_names(center))
    filters={'name':['in',list(all_names) or ['']]}
    text='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    # Non-manager roles use document-scoped Patient permissions, not generic list rights.
    # The narrow internal query is confined to exact current authorized patient/center pairs.
    lookup=frappe.get_list if is_manager() else frappe.get_all
    rows=lookup('Patient',filters=filters,
        or_filters={k:['like',text] for k in ['patient_name','first_name','last_name','name','uid']},
        fields=['name','patient_name','first_name','last_name','uid'],order_by='patient_name,name',page_length=51)
    return {'patients':[{**row,'active_assignment':row.name in active_names} for row in rows[:50]],
        'truncated':len(rows)>50}
