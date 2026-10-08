"""Narrow first-meeting ingress; caller cannot select existing patient or practitioner IDs."""
from hashlib import sha256
import json
import re

import frappe
from frappe.utils import getdate,get_time
from frappe.rate_limiter import rate_limit
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import enabled
from centrochange_core.security.lifecycle import lock,reconcile_patient
from centrochange_core.scheduling.booking import book

SERVICE_USER='cc-public-booking-service@example.invalid'


@frappe.whitelist(allow_guest=True,methods=['POST'])
@rate_limit(limit=10,seconds=60)
@atomic
def first_meeting(route,first_name,last_name,email,sex,appointment_date,appointment_time,request_key):
	if route not in ('Marco','Francesca') or not request_key or len(request_key)>140:
		frappe.throw('Invalid first-meeting request')
	for value in (first_name,last_name):
		if not isinstance(value,str) or not value.strip() or len(value)>80 or re.search(r'[<>\r\n]',value):
			frappe.throw('Invalid patient identity')
	if not isinstance(email,str) or len(email)>140:
		frappe.throw('Invalid email')
	frappe.utils.validate_email_address(email,throw=True)
	if frappe.conf.get('cc_synthetic_dev')==1 and not email.endswith('@example.invalid'):
		frappe.throw('Synthetic DEV ingress accepts example.invalid identities only')
	if not frappe.db.exists('Gender',sex):
		frappe.throw('Invalid demographic value')
	caller=frappe.session.user
	payload={'route':route,'first_name':first_name.strip(),'last_name':last_name.strip(),'email':email.lower(),
		'sex':sex,'appointment_date':str(getdate(appointment_date)),'appointment_time':str(get_time(appointment_time))}
	fingerprint=sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
	key=sha256((SERVICE_USER+'\0public-'+request_key).encode()).hexdigest()
	try:
		frappe.set_user(SERVICE_USER)
		lock()
		if not enabled(SERVICE_USER):
			frappe.throw('Public booking service unavailable',frappe.PermissionError)
		name=frappe.db.get_value('Patient Appointment',{'cc_booking_key':key},for_update=True)
		if name:
			if frappe.db.get_value('Patient Appointment',name,'cc_public_payload_hash',for_update=True)!=fingerprint:
				frappe.throw('Request key has a different first-meeting payload')
			return {'name':name,'replay':True}
		configuration=frappe.get_doc('CC Public Booking Route',route,for_update=True)
		if not configuration.enabled or not frappe.db.get_value('Appointment Type',configuration.appointment_type,'cc_first_meeting',for_update=True):
			frappe.throw('First-meeting route unavailable',frappe.PermissionError)
		practitioner=frappe.get_doc('Healthcare Practitioner',configuration.practitioner,for_update=True)
		from centrochange_core.security.guards import centers
		if practitioner.status!='Active' or configuration.center not in centers(practitioner.user_id):
			frappe.throw('First-meeting practitioner unavailable')
		# Existing identities require authorized human matching; never let public input link them.
		if frappe.db.get_value('Patient',{'email':payload['email']},for_update=True):
			frappe.throw('Existing identity requires administrative booking')
		context={'practitioner':configuration.practitioner,'center':configuration.center,
			'appointment_type':configuration.appointment_type}
		with internal_write('cc_public_ingress'):
			patient=frappe.get_doc({'doctype':'Patient','first_name':payload['first_name'],
				'last_name':payload['last_name'],'email':payload['email'],'sex':sex,'invite_user':0}).insert(ignore_permissions=True)
			previous=getattr(frappe.flags,'cc_public_booking_context',None)
			frappe.flags.cc_public_booking_context={**context,'patient':patient.name}
			try:
				with internal_write('cc_permission_write'):
					assignment=frappe.get_doc({'doctype':'CC Patient Assignment','patient':patient.name,
						'center':configuration.center,'practitioner':configuration.practitioner,'active':1}).insert(ignore_permissions=True)
					reconcile_patient(patient.name)
				append('PUBLIC_FIRST_MEETING_ASSIGNMENT',assignment.doctype,assignment.name,None,
					{**context,'caller':caller},'First-meeting ingress')
				result=book(patient.name,configuration.practitioner,configuration.center,configuration.appointment_type,
					appointment_date,appointment_time,'public-'+request_key,'First-meeting ingress')
				frappe.db.set_value('Patient Appointment',result['name'],'cc_public_payload_hash',fingerprint)
				return result
			finally:
				frappe.flags.cc_public_booking_context=previous
	finally:
		frappe.set_user(caller)
