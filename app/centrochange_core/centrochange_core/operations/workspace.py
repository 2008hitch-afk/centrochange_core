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
        return {'centers':[],'patients':[],'practitioners':[],'services':[],'payment_methods':[],'roles':roles(),'is_manager':is_manager(),'demo_labels':{}}
    center=center or available[0].name
    require_center(center)
    if center not in [row.name for row in available]:
        frappe.throw('La sede selezionata non è disponibile.',frappe.PermissionError)
    try:
        patients=frappe.get_list('Patient',filters={'name':['in',center_patient_names(center) or ['']]},
            fields=['name','patient_name','first_name','last_name'],page_length=500,order_by='patient_name')
    except frappe.PermissionError:
        patients=[]
    from centrochange_core.security.guards import practitioner_names_for_center
    names=practitioner_names_for_center(center)
    filters={'status':'Active','name':['in',names or ['']]}
    if 'CC Professional' in roles() and not is_manager():
        own=practitioner_for()
        filters['name']=['in',[own] if own in names else ['']]
    practitioners=current_rows('Healthcare Practitioner',filters,fields=['name','practitioner_name'])
    profiles=current_rows('CC Center Service',{'center':center,'enabled':1},pluck='appointment_type')
    from centrochange_core.scheduling.booking import snapshot
    from centrochange_core.scheduling.public_offer import configured_type, validate_free_offer, PublicOfferError
    public_center=bool(frappe.db.exists('CC Public Booking Route',{'center':center,'enabled':1}))
    services=[]
    for profile in profiles:
        try:
            service={'name':profile,**snapshot(profile,center)}
            for mode in ('sede','online'):
                try:
                    if (profile == configured_type(frappe.conf.get('cc_public_first_meeting_types'), mode)
                            and frappe.db.get_value('Appointment Type',profile,'cc_first_meeting')):
                        validate_free_offer(service,mode)
                        service['configured_first_meeting_mode']=mode
                        if public_center:
                            service['public_first_meeting_mode']=mode
                except PublicOfferError:
                    pass
            services.append(service)
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
        'packages':packages,'payment_methods':current_rows('Mode of Payment',{'enabled':1},pluck='name'),'roles':roles(),'is_manager':is_manager(),
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



def _fiscal_customer_create(label, tax_id=None):
    """Create one synthetic Customer within the caller's locked transaction."""
    from centrochange_core.scoped_api import bounded
    label = bounded(label, 'Intestatario fiscale', 140)
    tax_id = bounded(tax_id, 'Identificativo fiscale', 50, required=False) or None
    if tax_id and frappe.db.exists('Customer', {'tax_id': tax_id}):
        frappe.throw('Esiste già un intestatario con questo identificativo. Selezionalo dall’elenco.')
    values = {
        'doctype': 'Customer', 'customer_name': label, 'customer_type': 'Individual',
        'customer_group': frappe.db.get_single_value('Selling Settings', 'customer_group'),
        'territory': frappe.db.get_single_value('Selling Settings', 'territory'),
    }
    if tax_id:
        values['tax_id'] = tax_id
    return frappe.get_doc(values).insert(ignore_permissions=True, ignore_mandatory=True).name


def _fiscal_existing_in_center(center, customer):
    """No Customer search outside the selected center, even for a manager."""
    allowed = frappe.get_all('CC Patient Assignment', filters={'center': center}, pluck='patient')
    links = frappe.get_all('Patient', filters={'name': ['in', allowed or ['']]}, pluck='customer')
    economic = frappe.get_all('CC Economic Source Link', filters={'center': center}, pluck='customer')
    if not customer or customer not in set(links + economic):
        frappe.throw('Intestatario non disponibile per questo centro.', frappe.PermissionError)
    if not frappe.db.exists('Customer', customer):
        frappe.throw('Intestatario fiscale inesistente.')
    return customer


@frappe.whitelist(methods=['POST'])
def create_patient(center,first_name,sex,uid,practitioner,request_key,reason,last_name=None,email=None,mobile=None,phone=None,ts_preference=None,
                   payer_mode='self',payer_customer=None,payer_first_name=None,payer_last_name=None,payer_tax_id=None):
    # Healthcare native Patient/Customer hooks are kept; the service controls
    # which Customer exists before Patient.insert() to avoid a duplicate.
    from centrochange_core.operations.profiles import _atomic_provision
    return _atomic_provision(_create_patient)(center,first_name,sex,uid,practitioner,request_key,reason,last_name,email,mobile,phone,ts_preference,
                                              payer_mode,payer_customer,payer_first_name,payer_last_name,payer_tax_id)


def _create_patient(center,first_name,sex,uid,practitioner,request_key,reason,last_name,email,mobile=None,phone=None,ts_preference=None,
                    payer_mode='self',payer_customer=None,payer_first_name=None,payer_last_name=None,payer_tax_id=None):
    from hashlib import sha256
    from centrochange_core.security.audit import append,internal_write,serialize
    from centrochange_core.security.lifecycle import lock,set_assignment
    from centrochange_core.security.guards import require_operations,require_manager,require_center
    from centrochange_core.finance.guards import require_synthetic
    from centrochange_core.scoped_api import bounded
    lock();require_operations(center);require_center(center);require_manager();require_synthetic()
    if frappe.db.get_single_value('Healthcare Settings', 'send_registration_msg'):
        frappe.throw('Creazione sospesa: la notifica SMS di registrazione è attiva.')
    if ts_preference is not None and ts_preference not in ('', 'No Opposition', 'Opposed'):
        frappe.throw('Preferenza Tessera Sanitaria non valida.')
    supplied_mobile = mobile is not None
    supplied_phone = phone is not None
    first_name=str(first_name or '').strip();last_name=str(last_name or '').strip();uid=str(uid or '').strip();email=str(email or '').strip().lower() or None
    mobile=str(mobile or '').strip();phone=str(phone or '').strip()
    if not first_name.startswith(('SYNTHETIC','CC-HTTP-')) or not uid.startswith(('SYNTHETIC-','CC-HTTP-')):
        frappe.throw('Nel DEV sono ammesse solo identità esplicitamente sintetiche.')
    if len(first_name)>140 or len(last_name)>140 or len(uid)>140 or len(mobile)>140 or len(phone)>140 or not frappe.db.exists('Gender',sex):
        frappe.throw('Compila i dati identificativi nei limiti previsti e seleziona un sesso valido.')
    if email and (not email.endswith('@example.invalid') or len(email)>140 or not frappe.utils.validate_email_address(email)):
        frappe.throw('È consentita solo una email sintetica del dominio example.invalid.')
    if not request_key or len(request_key)>160:frappe.throw('Indica una chiave valida per la creazione del paziente.')
    payer_mode=bounded(payer_mode,'Modalità intestatario',20)
    if payer_mode not in ('self','existing','new'):
        frappe.throw('Seleziona un intestatario fiscale valido.')
    payer_customer=bounded(payer_customer,'Intestatario',140,required=False)
    payer_first_name=bounded(payer_first_name,'Nome intestatario',140,required=False)
    payer_last_name=bounded(payer_last_name,'Cognome intestatario',140,required=False)
    payer_tax_id=bounded(payer_tax_id,'Identificativo fiscale',50,required=False)
    if payer_mode=='existing' and not payer_customer:
        frappe.throw('Seleziona un intestatario già registrato.')
    if payer_mode=='new' and (not payer_first_name or not payer_last_name or not payer_tax_id):
        frappe.throw('Compila nome, cognome e identificativo fiscale del nuovo intestatario.')
    if payer_mode=='self' and (payer_customer or payer_first_name or payer_last_name or payer_tax_id):
        frappe.throw('Non sono necessari dati di un secondo intestatario.')
    if payer_mode=='existing' and (payer_first_name or payer_last_name or payer_tax_id):
        frappe.throw('Per un intestatario esistente seleziona soltanto la persona.')
    if payer_mode=='new' and payer_customer:
        frappe.throw('Non selezionare un intestatario esistente per crearne uno nuovo.')
    key=sha256(serialize([frappe.session.user,center,request_key]).encode()).hexdigest()
    payload={'center':center,'first_name':first_name,'last_name':last_name,'sex':sex,'uid':uid,'email':email,'practitioner':practitioner,
             'payer_mode':payer_mode,'payer_customer':payer_customer,'payer_first_name':payer_first_name,
             'payer_last_name':payer_last_name,'payer_tax_id':payer_tax_id,
             **({'mobile': mobile} if supplied_mobile else {}), **({'phone': phone} if supplied_phone else {}),
             **({'ts_preference': ts_preference} if ts_preference is not None else {})}
    digest=sha256(serialize(payload).encode()).hexdigest()
    old=frappe.db.get_value('Patient',{'cc_intake_key':key},['name','cc_intake_hash'],as_dict=True,for_update=True)
    if old:
        if old.cc_intake_hash!=digest:frappe.throw('La creazione del paziente è già stata usata con dati diversi.')
        from centrochange_core.security.guards import require_patient
        require_patient(old.name)
        return {'name':old.name,'replay':True}
    if frappe.db.exists('Patient',{'uid':uid}):
        frappe.throw('L’identità esiste già: cerca l’UID esatto e assegna esplicitamente il paziente.')
    payer=None
    if payer_mode=='existing':
        payer=_fiscal_existing_in_center(center,payer_customer)
    if payer_mode=='new':
        payer=_fiscal_customer_create(' '.join([payer_first_name,payer_last_name]),payer_tax_id)
    # When Healthcare's automatic Customer creation is disabled, self mode
    # must still produce one unambiguous mapping in this same transaction.
    if payer_mode=='self' and not frappe.db.get_single_value('Healthcare Settings','link_customer_to_patient'):
        payer=_fiscal_customer_create(' '.join([first_name,last_name]))
    doc_values={'doctype':'Patient','first_name':first_name,'last_name':last_name,'sex':sex,'uid':uid,
                'email':email,'mobile':mobile,'phone':phone,'invite_user':0,
                'cc_intake_key':key,'cc_intake_hash':digest,'cc_external_payer':1 if payer_mode!='self' else 0,
                **({'customer':payer} if payer else {}),
                **({'cc_ts_preference':ts_preference} if ts_preference is not None else {})}
    with internal_write('cc_patient_intake_write'), internal_write('cc_ts_preference_write'), internal_write('cc_finance_mapping_write'):
        doc=frappe.get_doc(doc_values).insert(ignore_permissions=True)
    # Healthcare's after_insert / on_update may have filled the Customer link
    # using db.set_value; reload to inspect the actual persisted relationship.
    doc.reload()
    if not doc.customer or (payer and doc.customer != payer):
        frappe.throw('Collegamento fiscale incoerente: la creazione è stata annullata.')
    if ts_preference is not None:
        append('PATIENT_TS_PREFERENCE_CHANGED','Patient',doc.name,{'preference':''},{'preference':ts_preference},reason)
    set_assignment(doc.name,center,practitioner,1,reason)
    append('PATIENT_FISCAL_PAYER_LINKED','Patient',doc.name,None,
           {'center':center,'payer_kind':payer_mode,'customer_hash':sha256(doc.customer.encode()).hexdigest()},reason)
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
