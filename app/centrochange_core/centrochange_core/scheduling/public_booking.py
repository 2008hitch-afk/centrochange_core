"""Narrow first-meeting ingress; caller cannot select existing patient or practitioner IDs."""
from datetime import datetime, timedelta
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import getdate,get_time
from frappe.rate_limiter import rate_limit
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import enabled
from centrochange_core.security.lifecycle import lock,reconcile_patient
from centrochange_core.scheduling.booking import book

SERVICE_USER='cc-public-booking-service@example.invalid'

from centrochange_core.scheduling.public_offer import configured_type, validate_free_offer, PublicOfferError


def _public_offer(configuration, mode, for_update=False):
	"""Bind a mode to an explicitly configured canonical, free Appointment Type.

	The route selects ONLY director/center; mode selects the native service.
	No schema/DocPerm changes and no public caller-supplied appointment IDs.
	"""
	try:
		appointment_type = configured_type(frappe.conf.get('cc_public_first_meeting_types'), mode)
	except PublicOfferError:
		frappe.throw('La modalità scelta non è ancora prenotabile. Contatta la segreteria.', frappe.PermissionError)
	if not frappe.db.get_value('Appointment Type', appointment_type, 'cc_first_meeting', for_update=for_update):
		frappe.throw('La modalità scelta non è disponibile.', frappe.PermissionError)
	from centrochange_core.scheduling.booking import snapshot
	profile = snapshot(appointment_type, configuration.center)
	try:
		validate_free_offer(profile, mode)
	except PublicOfferError:
		frappe.throw('Il colloquio gratuito non è disponibile. Contatta la segreteria.', frappe.PermissionError)
	return appointment_type, profile



@frappe.whitelist(allow_guest=True,methods=['POST'])
@rate_limit(limit=10,seconds=60)
@atomic
def first_meeting(route,first_name,last_name,email,sex,appointment_date,appointment_time,request_key,mode):
	if route not in ('Marco','Francesca') or mode not in ('sede','online') or not isinstance(request_key,str) or not request_key or len(request_key)>140:
		frappe.throw('Controlla i dati del primo incontro.')
	for value in (first_name,last_name):
		if not isinstance(value,str) or not value.strip() or len(value)>80 or re.search(r'[<>\r\n]',value):
			frappe.throw('Controlla i dati identificativi del paziente.')
	if not isinstance(email,str) or len(email)>140:
		frappe.throw('Inserisci un indirizzo email valido.')
	frappe.utils.validate_email_address(email,throw=True)
	if frappe.conf.get('cc_synthetic_dev')==1 and not email.endswith('@example.invalid'):
		frappe.throw('Nel DEV sono consentite solo identità demo example.invalid.')
	if not frappe.db.exists('Gender',sex):
		frappe.throw('Controlla il valore anagrafico selezionato.')
	booking_date=getdate(appointment_date)
	today=datetime.now(ZoneInfo('Europe/Rome')).date()
	if booking_date<today or booking_date>today+timedelta(days=120):
		frappe.throw('Scegli una data futura entro 120 giorni.')
	caller=frappe.session.user
	payload={'route':route,'mode':mode,'first_name':first_name.strip(),'last_name':last_name.strip(),'email':email.lower(),
		'sex':sex,'appointment_date':str(booking_date),'appointment_time':str(get_time(appointment_time))}
	fingerprint=sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
	key=sha256((SERVICE_USER+'\0public-'+request_key).encode()).hexdigest()
	try:
		frappe.set_user(SERVICE_USER)
		lock()
		if not enabled(SERVICE_USER):
			frappe.throw('La prenotazione pubblica non è disponibile.',frappe.PermissionError)
		name=frappe.db.get_value('Patient Appointment',{'cc_booking_key':key},for_update=True)
		if name:
			if frappe.db.get_value('Patient Appointment',name,'cc_public_payload_hash',for_update=True)!=fingerprint:
				frappe.throw('La richiesta è già stata usata con dati diversi.')
			from centrochange_core.operations.booking_confirmation import confirm
			return {'name':name,'replay':True,'confirmation':confirm(name,route,payload['email'],mode)}
		configuration=frappe.get_doc('CC Public Booking Route',route,for_update=True)
		if not frappe.db.get_value('Branch',configuration.center,'cc_operational',for_update=True):
			frappe.throw('Percorso primo incontro non disponibile.',frappe.PermissionError)
		if not configuration.enabled:
			frappe.throw('Percorso primo incontro non disponibile.',frappe.PermissionError)
		appointment_type, _profile = _public_offer(configuration,mode,for_update=True)
		practitioner=frappe.get_doc('Healthcare Practitioner',configuration.practitioner,for_update=True)
		from centrochange_core.security.guards import centers
		if practitioner.status!='Active' or configuration.center not in centers(practitioner.user_id):
			frappe.throw('Il professionista del primo incontro non è disponibile.')
		# Existing identities require authorized human matching; never let public input link or mutate them.
		# If an email is already present, isolate the ingress record and emit a triage event for front-office deduplication.
		existing_patient=frappe.db.get_value('Patient',{'email':payload['email']},'name',for_update=True)
		context={'practitioner':configuration.practitioner,'center':configuration.center,
			'appointment_type':appointment_type}
		with internal_write('cc_public_ingress'):
			patient=frappe.get_doc({'doctype':'Patient','first_name':payload['first_name'],
				'last_name':payload['last_name'],'email':payload['email'],'sex':sex,'invite_user':0}).insert(ignore_permissions=True)
			if existing_patient:
				append('PUBLIC_FIRST_MEETING_POTENTIAL_DUPLICATE','Patient',patient.name,None,
					{'existing_patient':existing_patient,'email':payload['email'],'mode':mode,'director':route},
					'Segreteria triage required: public first meeting with existing email identity')
			previous=getattr(frappe.flags,'cc_public_booking_context',None)
			frappe.flags.cc_public_booking_context={**context,'patient':patient.name}
			try:
				with internal_write('cc_permission_write'):
					assignment=frappe.get_doc({'doctype':'CC Patient Assignment','patient':patient.name,
						'center':configuration.center,'practitioner':configuration.practitioner,'active':1}).insert(ignore_permissions=True)
					reconcile_patient(patient.name)
				append('PUBLIC_FIRST_MEETING_ASSIGNMENT',assignment.doctype,assignment.name,None,
					{**context,'caller':caller},'First-meeting ingress')
				result=book(patient.name,configuration.practitioner,configuration.center,appointment_type,
					appointment_date,appointment_time,'public-'+request_key,'First-meeting ingress')
				append('PUBLIC_FIRST_MEETING_MODE','Patient Appointment',result['name'],None,
					{'mode':mode,'director':route,'duration':20,'price':0},'Colloquio conoscitivo gratuito')
				frappe.db.set_value('Patient Appointment',result['name'],'cc_public_payload_hash',fingerprint)
				from centrochange_core.operations.booking_confirmation import confirm
				return {**result,'confirmation':confirm(result['name'],route,payload['email'],mode)}
			finally:
				frappe.flags.cc_public_booking_context=previous
	finally:
		frappe.set_user(caller)


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30,seconds=60)
def available_slots(route,start_date,mode):
	"""Public seven-day projection exposes slots only, never patient or practitioner IDs."""
	from types import SimpleNamespace
	from centrochange_core.security.guards import current_rows,centers
	from centrochange_core.scheduling.booking import snapshot,validate_slot
	if route not in ('Marco','Francesca') or mode not in ('sede','online'):
		frappe.throw('Percorso primo incontro non supportato.',frappe.PermissionError)
	date=getdate(start_date)
	today=datetime.now(ZoneInfo('Europe/Rome')).date()
	horizon=today+timedelta(days=120)
	if date<today or date>horizon:
		frappe.throw('Scegli una data futura entro 120 giorni.')
	configuration=frappe.get_doc('CC Public Booking Route',route)
	if not frappe.db.get_value('Branch',configuration.center,'cc_operational'):
		frappe.throw('Percorso primo incontro non disponibile.',frappe.PermissionError)
	if not configuration.enabled:
		frappe.throw('Percorso primo incontro non disponibile.',frappe.PermissionError)
	_, profile = _public_offer(configuration,mode)
	practitioner=frappe.get_doc('Healthcare Practitioner',configuration.practitioner)
	if not enabled(SERVICE_USER) or practitioner.status!='Active' or configuration.center not in centers(practitioner.user_id):
		frappe.throw('Percorso primo incontro non disponibile.',frappe.PermissionError)
	duration=float(profile['duration'])
	schedules=current_rows('Practitioner Schedule',{'cc_practitioner':configuration.practitioner,'cc_center':configuration.center,'disabled':0},pluck='name')
	rows=current_rows('Healthcare Schedule Time Slot',{'parent':['in',schedules or ['']],'parenttype':'Practitioner Schedule'},fields=['day','from_time','to_time'])
	slots=[]
	for offset in range(7):
		day=date+timedelta(days=offset)
		if day>horizon:
			break
		for row in rows:
			if row.day!=day.strftime('%A'):
				continue
			at=datetime.combine(day,get_time(row.from_time));end=datetime.combine(day,get_time(row.to_time))
			while at+timedelta(minutes=duration)<=end and len(slots)<100:
				candidate=SimpleNamespace(appointment_date=day,appointment_time=at.time(),duration=duration,
					practitioner=configuration.practitioner,cc_center=configuration.center,patient=None,name=None)
				try:
					validate_slot(candidate)
					slots.append({'date':str(day),'time':str(at.time())})
				except frappe.ValidationError:
					pass
				at+=timedelta(minutes=duration)
	return {'route':route,'mode':mode,'service':'Colloquio conoscitivo gratuito',
		'duration':20,'price':0,'currency':'EUR','slots':slots}
