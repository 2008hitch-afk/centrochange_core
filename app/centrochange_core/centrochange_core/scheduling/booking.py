"""Canonical native appointments with guarded, serialized and idempotent booking."""
from datetime import datetime,timedelta
from hashlib import sha256
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
	if frappe.flags.get('cc_public_ingress'):
		from centrochange_core.scheduling.public_booking import SERVICE_USER
		context=frappe.flags.get('cc_public_booking_context') or {}
		if frappe.session.user!=SERVICE_USER or not enabled() or context.get('patient')!=patient or context.get('practitioner')!=practitioner or context.get('center')!=center:
			frappe.throw('Invalid public booking service scope',frappe.PermissionError)
		return
	require_center(center)
	require_patient(patient)
	if not is_manager() and not any(role in roles() for role in ('CC Professional','CC Secretariat')):
		frappe.throw('Operational booking permission required',frappe.PermissionError)
	if not frappe.db.get_value('CC Patient Assignment',{'patient':patient,'practitioner':practitioner,'center':center,'active':1},for_update=True):
		frappe.throw('Patient must be assigned to this practitioner in this center')
	# Scheduling self-management and booking share the same professional boundary.
	require_practitioner(practitioner,center)


def snapshot(appointment_type,center,patient=None):
	profile=frappe.get_doc('Appointment Type',appointment_type,for_update=True)
	if not frappe.db.get_value('CC Center Service',{'center':center,'appointment_type':appointment_type},'enabled',for_update=True):
		frappe.throw('Service is not enabled in this center')
	item=frappe.get_doc('Item',profile.cc_service_item,for_update=True)
	if item.disabled or item.is_stock_item or not item.is_sales_item:
		frappe.throw('Active non-stock sales service required')
	price_list=frappe.db.get_value('Branch',center,'cc_price_list',for_update=True)
	list_doc=frappe.get_doc('Price List',price_list,for_update=True)
	if not list_doc.enabled or not list_doc.selling:
		frappe.throw('Active selling price list required')
	date=datetime.now(ZoneInfo('Europe/Rome')).date()
	prices=current_rows('Item Price',{'item_code':item.name,'price_list':price_list},
		fields=['name','price_list_rate','currency','valid_from','valid_upto','customer','supplier','batch_no','uom'])
	prices=[row for row in prices if not row.customer and not row.supplier and not row.batch_no
		and (not row.uom or row.uom==item.stock_uom)
		and (not row.valid_from or getdate(row.valid_from)<=date) and (not row.valid_upto or getdate(row.valid_upto)>=date)]
	prices.sort(key=lambda row:getdate(row.valid_from) if row.valid_from else getdate('1900-01-01'),reverse=True)
	if not prices or len(prices)>1 and prices[0].valid_from==prices[1].valid_from:
		frappe.throw('Missing or ambiguous effective price')
	price=prices[0]
	if price.currency!=list_doc.currency or flt(price.price_list_rate)<0 or flt(profile.default_duration)<=0:
		frappe.throw('Invalid service price/currency/duration')
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
		frappe.throw('L’orario attraversa un cambio d’ora legale: scegli un intervallo non ambiguo.')
	if end.date()!=start.date():
		frappe.throw('La seduta deve iniziare e terminare nello stesso giorno.')
	if start<=datetime.now(ZoneInfo('Europe/Rome')).replace(tzinfo=None):
		previous=doc.get_doc_before_save() if doc.flags.get('cc_historical_slot_correction') else None
		if not (frappe.flags.get('cc_appointment_write') and previous
			and previous.cc_closure_state=='Reopened' and doc.cc_closure_state=='Reopened'
			and doc.status=='Closed' and getdate(previous.appointment_date)==getdate(doc.appointment_date)):
			frappe.throw('Una prenotazione o uno spostamento ordinario richiede un orario futuro. La correzione storica richiede una seduta riaperta e la stessa data.')
		require_historical_correction_without_effects(doc)
	schedules=current_rows('Practitioner Schedule',{'cc_practitioner':doc.practitioner,'cc_center':doc.cc_center,'disabled':0},pluck='name')
	rows=current_rows('Healthcare Schedule Time Slot',{'parent':['in',schedules or ['']], 'parenttype':'Practitioner Schedule',
		'day':start.strftime('%A')},fields=['from_time','to_time'])
	if not any(get_time(row.from_time)<=start.time() and get_time(row.to_time)>=end.time() for row in rows):
		frappe.throw('L’orario è fuori dalla disponibilità abituale del professionista nel Centro.')
	absences=current_rows('Practitioner Availability',{'scope_type':'Healthcare Practitioner','scope':doc.practitioner,
		'type':'Unavailable','docstatus':1},fields=['start_date','end_date','start_time','end_time','repeat'])
	for absence in absences:
		if absence.repeat!='Never':
			frappe.throw('L’assenza ricorrente richiede una regola esplicita prima di spostare la seduta.')
		absent_start=datetime.combine(getdate(absence.start_date),get_time(absence.start_time))
		absent_end=datetime.combine(getdate(absence.end_date or absence.start_date),get_time(absence.end_time))
		if start<absent_end and end>absent_start:
			frappe.throw('Il professionista non è disponibile in questo intervallo.')
	# Current row reads avoid the native non-locking overlap snapshot under REPEATABLE READ.
	rows=current_rows('Patient Appointment',{'appointment_date':doc.appointment_date,'name':['!=',doc.name or ''],
		'status':['!=','Cancelled']},fields=['name','patient','practitioner','appointment_time','duration'])
	for row in rows:
		if row.patient!=doc.patient and row.practitioner!=doc.practitioner:
			continue
		other=datetime.combine(start.date(),get_time(row.appointment_time))
		if start<other+timedelta(minutes=flt(row.duration)) and end>other:
			frappe.throw('Paziente o professionista hanno già una seduta in questo intervallo.')


def require_historical_correction_without_effects(doc):
	"""Fail closed on retained downstream facts before moving a reopened past slot.

	A zero-paid closure settlement is the mandatory operational closure record,
	not a receipt. A paid settlement or a derived source is an economic fact.
	"""
	blocked='La correzione storica richiede una rettifica separata: esistono effetti economici o amministrativi collegati.'
	unverified='Impossibile verificare i collegamenti economici della seduta: serve una rettifica separata.'
	if doc.cc_paid or doc.cc_package_state in ('Consumed','Released'):
		frappe.throw(blocked)
	checks=(
		('CC Professional Expectation',{'appointment':doc.name}),
		('CC Economic Source Link',{'appointment':doc.name}),
		('CC Settlement',{'appointment':doc.name,'paid':1}),
		('CC Payment Override',{'reference_doctype':'Patient Appointment','reference_name':doc.name}),
		('CC Admin Exception',{'reference_doctype':'Patient Appointment','reference_name':doc.name}),
		('CC Booking Confirmation',{'appointment':doc.name}),
		('Communication',{'reference_doctype':'Patient Appointment','reference_name':doc.name}),
	)
	try:
		linked=any(frappe.db.get_value(doctype,filters,'name',for_update=True) for doctype,filters in checks)
		ledger=any(row.event_type!='RESERVE' for row in current_rows('CC Package Ledger',
			{'appointment':doc.name},fields=['event_type']))
		# Other same-day expectations can include this session in their unpaid rank.
		peers=current_rows('Patient Appointment',{'patient':doc.patient,'practitioner':doc.practitioner,
			'appointment_date':doc.appointment_date},pluck='name')
		peer_expectation=frappe.db.get_value('CC Professional Expectation',
			{'appointment':['in',peers or ['']]},'name',for_update=True)
		# A notice records a patient/center debt, not a document ID: its exact
		# session link cannot be established, so any such notice blocks the move.
		notice=frappe.db.get_value('CC Payment Notice',{'patient':doc.patient,'center':doc.cc_center},'name',for_update=True)
	except Exception:
		frappe.throw(unverified)
	if linked or ledger or peer_expectation or notice:
		frappe.throw(blocked)


@frappe.whitelist(methods=['POST'])
@atomic
def book(patient,practitioner,center,appointment_type,appointment_date,appointment_time,request_key,reason,patient_package=None):
	lock()
	require_booking(patient,practitioner,center)
	if not request_key or len(request_key)>140:
		frappe.throw('A bounded idempotency key is required')
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
			frappe.throw('Idempotency key was already used with a different booking')
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
			frappe.throw('Appointments must use the guarded Centro Change service',frappe.PermissionError)
		previous=self.get_doc_before_save()
		if previous and any(previous.get(field)!=self.get(field) for field in SNAPSHOTS):
			frappe.throw('Historical appointment snapshots are immutable: '+', '.join(field for field in SNAPSHOTS if previous.get(field)!=self.get(field)))
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
		frappe.throw('Appointments require governed cancellation/correction',frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def blocked_native(**kwargs):
	frappe.throw('Use the guarded Centro Change operational service',frappe.PermissionError)


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
		frappe.throw('La seduta conclusa richiede una riapertura autorizzata prima della correzione.')
	from centrochange_core.operations.lifecycle import require_mutable
	require_mutable(doc)
	date,time=getdate(appointment_date),get_time(appointment_time)
	before={'appointment_date':str(getdate(doc.appointment_date)),'appointment_time':str(get_time(doc.appointment_time))}
	after={'appointment_date':str(date),'appointment_time':str(time)}
	if before==after:
		if datetime.combine(date,time)<=datetime.now(ZoneInfo('Europe/Rome')).replace(tzinfo=None) and (not reason or not reason.strip()):
			frappe.throw('Indica il motivo della correzione storica della seduta.')
		return {'name':doc.name,'replay':True}
	if not reason or not reason.strip():
		frappe.throw('Indica il motivo dello spostamento della seduta.')
	historical=datetime.combine(date,time)<=datetime.now(ZoneInfo('Europe/Rome')).replace(tzinfo=None)
	if historical:
		if doc.cc_closure_state!='Reopened' or doc.status!='Closed':
			frappe.throw('La correzione di un orario passato richiede una seduta formalmente riaperta.')
		if date!=getdate(doc.appointment_date):
			frappe.throw('La correzione storica può cambiare soltanto l’orario, nella stessa data della seduta.')
	with internal_write('cc_appointment_write'):
		doc.appointment_date=date
		doc.appointment_time=time
		doc.flags.cc_historical_slot_correction=historical
		try:
			doc.save(ignore_permissions=True)
		finally:
			doc.flags.cc_historical_slot_correction=False
	append('APPOINTMENT_RESCHEDULED',doc.doctype,doc.name,before,after,reason)
	return {'name':doc.name,'replay':False}
