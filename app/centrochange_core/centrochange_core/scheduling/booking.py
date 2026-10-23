"""Canonical native appointments with guarded, serialized and idempotent booking."""
from datetime import datetime,timedelta
from hashlib import sha256
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_time,getdate,flt
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import enabled,is_manager,roles,require_patient,require_center,current_rows
from centrochange_core.security.lifecycle import lock
from centrochange_core.scheduling.availability import require_practitioner

SNAPSHOTS=('cc_booking_key','cc_booking_date','cc_service_item','cc_service_label','cc_price_snapshot',
	'cc_currency_snapshot','cc_price_list_snapshot','cc_item_price_source','cc_payment_terms_mode','cc_payment_agreed_date','duration','appointment_type','cc_package')


def require_booking(patient,practitioner,center):
	from centrochange_core.security.guards import require_operational_center
	require_operational_center(center)
	if frappe.flags.get('cc_public_ingress'):
		from centrochange_core.scheduling.public_booking import SERVICE_USER
		context=frappe.flags.get('cc_public_booking_context') or {}
		if frappe.session.user!=SERVICE_USER or not enabled() or context.get('patient')!=patient or context.get('practitioner')!=practitioner or context.get('center')!=center:
			frappe.throw('Servizio non disponibile per la prenotazione pubblica.',frappe.PermissionError)
		return
	require_center(center)
	require_patient(patient)
	if not is_manager() and not any(role in roles() for role in ('CC Professional','CC Secretariat')):
		frappe.throw('Non hai il permesso di prenotare questa seduta.',frappe.PermissionError)
	if not frappe.db.get_value('CC Patient Assignment',{'patient':patient,'practitioner':practitioner,'center':center,'active':1},for_update=True):
		frappe.throw('Il paziente deve essere assegnato al professionista in questa sede.')
	# Scheduling self-management and booking share the same professional boundary.
	require_practitioner(practitioner,center)


def snapshot(appointment_type,center,patient=None):
	profile=frappe.get_doc('Appointment Type',appointment_type,for_update=True)
	if not frappe.db.get_value('CC Center Service',{'center':center,'appointment_type':appointment_type},'enabled',for_update=True):
		frappe.throw('Il servizio non è disponibile in questa sede.')
	item=frappe.get_doc('Item',profile.cc_service_item,for_update=True)
	if item.disabled or item.is_stock_item or not item.is_sales_item:
		frappe.throw('Seleziona un servizio attivo del centro.')
	price_list=frappe.db.get_value('Branch',center,'cc_price_list',for_update=True)
	list_doc=frappe.get_doc('Price List',price_list,for_update=True)
	if not list_doc.enabled or not list_doc.selling:
		frappe.throw('Manca un listino prezzi attivo per il servizio.')
	date=datetime.now(ZoneInfo('Europe/Rome')).date()
	prices=current_rows('Item Price',{'item_code':item.name,'price_list':price_list},
		fields=['name','price_list_rate','currency','valid_from','valid_upto','customer','supplier','batch_no','uom'])
	prices=[row for row in prices if not row.customer and not row.supplier and not row.batch_no
		and (not row.uom or row.uom==item.stock_uom)
		and (not row.valid_from or getdate(row.valid_from)<=date) and (not row.valid_upto or getdate(row.valid_upto)>=date)]
	prices.sort(key=lambda row:getdate(row.valid_from) if row.valid_from else getdate('1900-01-01'),reverse=True)
	if not prices or len(prices)>1 and prices[0].valid_from==prices[1].valid_from:
		frappe.throw('La tariffa del servizio manca o non è univoca.')
	price=prices[0]
	if price.currency!=list_doc.currency or flt(price.price_list_rate)<0 or flt(profile.default_duration)<=0:
		frappe.throw('Controlla prezzo, valuta e durata del servizio.')
	from centrochange_core.finance.collections import _agreement
	agreement=_agreement(patient,center) if patient else None
	return {'cc_payment_terms_mode':agreement.mode if agreement else 'Immediate',
		'cc_payment_agreed_date':agreement.due_date if agreement else None,'cc_booking_date':date,'cc_service_item':item.name,'cc_service_label':item.item_name,
		'cc_price_snapshot':price.price_list_rate,'cc_currency_snapshot':price.currency,
		'cc_price_list_snapshot':price_list,'cc_item_price_source':price.name,'duration':profile.default_duration}


def validate_slot(doc):
	from centrochange_core.finance.collections import require_booking as require_payment_clearance
	require_payment_clearance(doc)
	start=datetime.combine(getdate(doc.appointment_date),get_time(doc.appointment_time))
	end=start+timedelta(minutes=flt(doc.duration))
	# Native local-time collision arithmetic cannot safely represent DST folds/gaps.
	# Refuse these intervals rather than create an appointment that cannot be closed.
	from centrochange_core.operations.lifecycle import start_utc
	from types import SimpleNamespace
	start_instant=start_utc(doc)
	end_instant=start_utc(SimpleNamespace(appointment_date=end.date(),appointment_time=end.time()))
	if end_instant-start_instant!=timedelta(minutes=flt(doc.duration)):
		frappe.throw('L’orario attraversa un cambio di ora legale: scegli un intervallo non ambiguo.')
	if start<=datetime.now(ZoneInfo('Europe/Rome')).replace(tzinfo=None) or end.date()!=start.date():
		frappe.throw('La prenotazione richiede un intervallo futuro nello stesso giorno.')
	schedules=current_rows('Practitioner Schedule',{'cc_practitioner':doc.practitioner,'cc_center':doc.cc_center,'disabled':0},pluck='name')
	rows=current_rows('Healthcare Schedule Time Slot',{'parent':['in',schedules or ['']], 'parenttype':'Practitioner Schedule',
		'day':start.strftime('%A')},fields=['from_time','to_time'])
	if not any(get_time(row.from_time)<=start.time() and get_time(row.to_time)>=end.time() for row in rows):
		frappe.throw('L’orario è fuori dalla disponibilità abituale della sede.')
	absences=current_rows('Practitioner Availability',{'scope_type':'Healthcare Practitioner','scope':doc.practitioner,
		'type':'Unavailable','docstatus':1},fields=['start_date','end_date','start_time','end_time','repeat'])
	for absence in absences:
		if absence.repeat!='Never':
			frappe.throw('Una fascia di assenza ricorrente richiede una regola supportata.')
		absent_start=datetime.combine(getdate(absence.start_date),get_time(absence.start_time))
		absent_end=datetime.combine(getdate(absence.end_date or absence.start_date),get_time(absence.end_time))
		if start<absent_end and end>absent_start:
			frappe.throw('Il professionista non è disponibile nell’intervallo scelto.')
	# Current row reads avoid the native non-locking overlap snapshot under REPEATABLE READ.
	rows=current_rows('Patient Appointment',{'appointment_date':doc.appointment_date,'name':['!=',doc.name or ''],
		'status':['!=','Cancelled']},fields=['name','patient','practitioner','appointment_time','duration'])
	for row in rows:
		if row.patient!=doc.patient and row.practitioner!=doc.practitioner:
			continue
		other=datetime.combine(start.date(),get_time(row.appointment_time))
		if start<other+timedelta(minutes=flt(row.duration)) and end>other:
			frappe.throw('L’intervallo è già occupato per il paziente o il professionista.')


@frappe.whitelist(methods=['POST'])
@atomic
def book(patient,practitioner,center,appointment_type,appointment_date,appointment_time,request_key,reason,patient_package=None):
	lock()
	require_booking(patient,practitioner,center)
	if not request_key or len(request_key)>140:
		frappe.throw('La richiesta di prenotazione richiede un identificativo valido.')
	key=sha256((frappe.session.user+'\0'+request_key).encode()).hexdigest()
	name=frappe.db.get_value('Patient Appointment',{'cc_booking_key':key},for_update=True)
	payload={'patient':patient,'practitioner':practitioner,'cc_center':center,'appointment_type':appointment_type,
		'appointment_date':getdate(appointment_date),'appointment_time':get_time(appointment_time),'cc_package':patient_package or None}
	if name:
		existing=frappe.get_doc('Patient Appointment',name,for_update=True)
		existing_values={field:existing.get(field) for field in payload}
		existing_values['appointment_date']=getdate(existing.appointment_date)
		existing_values['appointment_time']=get_time(existing.appointment_time)
		existing_values['cc_package']=existing.cc_package or None
		if existing_values!=payload:
			frappe.throw('Questo identificativo è già stato usato per una prenotazione diversa.')
		return {'name':name,'replay':True}
	company=frappe.db.get_single_value('Global Defaults','default_company')
	doc=frappe.get_doc({'doctype':'Patient Appointment',**payload,**snapshot(appointment_type,center,patient),
		'cc_booking_key':key,'company':company,'appointment_for':'Practitioner','paid_amount':0})
	with internal_write('cc_appointment_write'):
		doc.insert(ignore_permissions=True)
		from centrochange_core.operations.packages import reserve
		reserve(doc,reason)
	append('APPOINTMENT_BOOKED',doc.doctype,doc.name,None,{**payload,**{field:doc.get(field) for field in SNAPSHOTS}},reason)
	return {'name':doc.name,'replay':False}


class AppointmentMixin:
	def validate(self):
		if frappe.flags.get('cc_runtime_smoke') and frappe.conf.get('cc_synthetic_dev')==1 and frappe.session.user=='Administrator':
			return super().validate()
		if not frappe.flags.get('cc_appointment_write'):
			frappe.throw('Usa il servizio di prenotazione autorizzato Centro Change.',frappe.PermissionError)
		previous=self.get_doc_before_save()
		if previous and any(previous.get(field)!=self.get(field) for field in SNAPSHOTS):
			frappe.throw('I dati storici della seduta non possono essere modificati: '+', '.join(field for field in SNAPSHOTS if previous.get(field)!=self.get(field)))
		require_booking(self.patient,self.practitioner,self.cc_center)
		if previous:
			from centrochange_core.operations.lifecycle import require_mutable
			require_mutable(self)
		validate_slot(self)
		super().validate()

	def after_insert(self):
		# Native portal billing and SMS/calendar publication do not define product ingress.
		if frappe.flags.get('cc_runtime_smoke'):
			return super().after_insert()

	def on_update(self):
		if frappe.flags.get('cc_runtime_smoke'):
			return super().on_update()

	def on_trash(self):
		frappe.throw('La seduta richiede una cancellazione o correzione autorizzata.',frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def blocked_native(**kwargs):
	frappe.throw('Usa il servizio operativo autorizzato Centro Change.',frappe.PermissionError)


def appointment_query(user=None):
	from centrochange_core.operations.permissions import appointment_names
	from centrochange_core.security.guards import names_condition
	return '' if is_manager(user) else names_condition('Patient Appointment',appointment_names(user))


def appointment_permission(doc,user=None,ptype=None):
	from centrochange_core.security.guards import patient_contexts,practitioner_for
	if is_manager(user):
		return True
	if not enabled(user) or ptype not in ('read','select') or (doc.patient,doc.cc_center) not in patient_contexts(user):
		return False
	return 'CC Professional' not in roles(user) or doc.practitioner==practitioner_for(user)


@frappe.whitelist(methods=['POST'])
@atomic
def reschedule(appointment,appointment_date,appointment_time,reason):
	lock()
	doc=frappe.get_doc('Patient Appointment',appointment,for_update=True)
	doc.check_permission('read')
	require_booking(doc.patient,doc.practitioner,doc.cc_center)
	if doc.status in ('Cancelled','No Show') or (doc.status=='Closed' and doc.cc_closure_state!='Reopened'):
		frappe.throw('Una seduta definitiva richiede una correzione autorizzata.')
	from centrochange_core.operations.lifecycle import require_mutable
	require_mutable(doc)
	date,time=getdate(appointment_date),get_time(appointment_time)
	before={'appointment_date':str(getdate(doc.appointment_date)),'appointment_time':str(get_time(doc.appointment_time))}
	after={'appointment_date':str(date),'appointment_time':str(time)}
	if before==after:
		return {'name':doc.name,'replay':True}
	with internal_write('cc_appointment_write'):
		doc.appointment_date=date
		doc.appointment_time=time
		doc.save(ignore_permissions=True)
	append('APPOINTMENT_RESCHEDULED',doc.doctype,doc.name,before,after,reason)
	return {'name':doc.name,'replay':False}


def _payment_blockers(doc,appointment_date,appointment_time):
	"""Recompute the payment hold for the proposed slot, across patient centers."""
	from centrochange_core.finance.collections import _booking_debts
	from centrochange_core.operations.lifecycle import ROME,start_utc
	at=start_utc(SimpleNamespace(appointment_date=getdate(appointment_date),
		appointment_time=get_time(appointment_time))).astimezone(ROME)
	return sorted((debt for debt in _booking_debts(doc.patient)
		if debt['name']!=doc.name and debt['deadline']<at),
		key=lambda debt:(debt['doctype'],debt['name']))


def _payment_override_allowed(patient,debts):
	from centrochange_core.finance.guards import allowed,patient_context
	if not allowed(write=True):
		return False
	try:
		for center in sorted({debt['center'] for debt in debts}):
			patient_context(patient,center,True)
	except frappe.PermissionError:
		return False
	return True


@frappe.whitelist(methods=['GET'])
def reschedule_payment_blockers(appointment,appointment_date,appointment_time):
	"""Show debt details only if the actor could authorize every blocking position."""
	doc=frappe.get_doc('Patient Appointment',appointment)
	doc.check_permission('read')
	require_booking(doc.patient,doc.practitioner,doc.cc_center)
	debts=_payment_blockers(doc,appointment_date,appointment_time)
	if not debts:
		return {'blocked':False,'can_override':False,'debts':[]}
	if not _payment_override_allowed(doc.patient,debts):
		return {'blocked':True,'can_override':False,'debts':[]}
	return {'blocked':True,'can_override':True,'debts':[
		{'center':debt['center'],'reference_doctype':debt['doctype'],
		 'reference_name':debt['name'],'amount':debt['amount'],
		 'currency':debt['currency'],'due_date':str(debt['due_date']),
		 'original_due_date':str(debt['original_due_date'])}
		for debt in debts]}


@frappe.whitelist(methods=['POST'])
@atomic
def reschedule_with_payment_override(appointment,appointment_date,appointment_time,reason,
		override_reason,due_date,request_key,expected_references):
	"""Defer every blocking debt and move in one transaction or roll all of it back."""
	lock()
	doc=frappe.get_doc('Patient Appointment',appointment,for_update=True)
	doc.check_permission('read')
	require_booking(doc.patient,doc.practitioner,doc.cc_center)
	if not request_key or len(str(request_key))>120:
		frappe.throw('Indica un identificativo valido per la richiesta.')
	if not override_reason or not override_reason.strip():
		frappe.throw('Indica il motivo della deroga.')
	if not due_date:
		frappe.throw('Indica la nuova scadenza.')
	from centrochange_core.finance.collections import override
	from centrochange_core.finance.guards import patient_context
	from centrochange_core.operations.lifecycle import ROME,now_utc
	due=getdate(due_date)
	if due<now_utc().astimezone(ROME).date() or due<getdate(appointment_date):
		frappe.throw('La nuova scadenza deve coprire la data dello spostamento.')
	debts=_payment_blockers(doc,appointment_date,appointment_time)
	if not debts and getdate(doc.appointment_date)==getdate(appointment_date) and get_time(doc.appointment_time)==get_time(appointment_time):
		# A network retry after a committed move is a normal reschedule replay.
		return reschedule(appointment,appointment_date,appointment_time,reason)
	if not debts or not _payment_override_allowed(doc.patient,debts):
		frappe.throw('La deroga richiede una posizione bloccante e un accesso amministrativo autorizzato.',frappe.PermissionError)
	import json
	try:
		refs=json.loads(expected_references) if isinstance(expected_references,str) else expected_references
	except (TypeError,ValueError):
		refs=None
	current=[{'reference_doctype':debt['doctype'],'reference_name':debt['name']} for debt in debts]
	if not isinstance(refs,list) or not all(isinstance(ref,dict) and set(ref)=={'reference_doctype','reference_name'} for ref in refs) or sorted(refs,key=lambda ref:(ref['reference_doctype'],ref['reference_name']))!=current:
		frappe.throw('La posizione dei pagamenti è cambiata. Riprova lo spostamento.')
	for debt in debts:
		patient_context(doc.patient,debt['center'],True)
		if due<=getdate(debt['due_date']):
			frappe.throw('La nuova scadenza deve essere successiva a tutte le scadenze attuali.')
		override(doc.patient,debt['center'],debt['doctype'],debt['name'],due,
			f"{request_key}:{sha256((debt['doctype']+':'+debt['name']).encode()).hexdigest()[:20]}",override_reason)
	# reschedule runs its normal authorization, slot, closure and debt guards again.
	return reschedule(appointment,appointment_date,appointment_time,reason)
