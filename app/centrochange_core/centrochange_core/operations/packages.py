"""Patient-package balances are derived exclusively from append-only events."""
import frappe
from frappe.utils import getdate
from centrochange_core.security.audit import append,atomic,internal_write,retry_deadlock_once
from centrochange_core.security.guards import is_manager,require_operations,current_rows
from centrochange_core.security.lifecycle import lock
from centrochange_core.operations.notes import require_context


def _package(name):
	return frappe.get_doc('CC Patient Package',name,for_update=True)


def _balance(name):
	rows=current_rows('CC Package Ledger',{'package':name},fields=['remaining_delta','reserved_delta'])
	remaining=sum(row.remaining_delta for row in rows)
	reserved=sum(row.reserved_delta for row in rows)
	if remaining<0 or reserved<0 or reserved>remaining:
		frappe.throw('Le unità del pacchetto non sono coerenti: verifica lo storico.')
	return {'remaining':remaining,'reserved':reserved,'available':remaining-reserved}


def _append(package,kind,remaining,reserved,key,reason,appointment=None,center=None):
	if not reason or not reason.strip():
		frappe.throw('Indica il motivo dell’operazione sul pacchetto.')
	existing=frappe.db.get_value('CC Package Ledger',{'event_key':key},for_update=True)
	if existing:
		row=frappe.get_doc('CC Package Ledger',existing,for_update=True)
		if (row.package,row.event_type,row.remaining_delta,row.reserved_delta,row.appointment or None)!=(package,kind,remaining,reserved,appointment):
			frappe.throw('L’evento del pacchetto è già associato a un’operazione diversa.')
		return existing
	balance=_balance(package)
	if balance['remaining']+remaining<0 or balance['reserved']+reserved<0 or balance['reserved']+reserved>balance['remaining']+remaining:
		frappe.throw('Le unità del pacchetto sono insufficienti o incoerenti.')
	with internal_write('cc_operation_write'):
		return frappe.get_doc({'doctype':'CC Package Ledger','package':package,'event_type':kind,
			'remaining_delta':remaining,'reserved_delta':reserved,'event_key':key,'appointment':appointment,
			'center':center,'actor':frappe.session.user,'event_time':frappe.utils.now_datetime(),'reason':reason}).insert(ignore_permissions=True).name


@frappe.whitelist(methods=['POST'])
@retry_deadlock_once
@atomic
def issue(template,patient,centers,request_key,reason,valid_until=None,practitioner=None):
	lock()
	if isinstance(centers,str):
		centers=frappe.parse_json(centers)
	if not isinstance(centers,list) or not centers or len(centers)>100 or len(set(centers))!=len(centers):
		frappe.throw('Indica le sedi ammesse per il pacchetto.')
	for center in centers:
		require_operations(center)
		require_context(patient,center)
	if not request_key or len(request_key)>140:
		frappe.throw('Indica un identificativo valido per l’assegnazione del pacchetto.')
	from hashlib import sha256
	key=sha256((frappe.session.user+'\0'+request_key).encode()).hexdigest()
	existing=frappe.db.get_value('CC Patient Package',{'issue_key':key},for_update=True)
	if existing:
		doc=_package(existing)
		if doc.patient!=patient or doc.template!=template or sorted(row.center for row in doc.centers)!=sorted(centers) or (doc.practitioner or None)!=(practitioner or None) or (str(doc.valid_until) if doc.valid_until else None)!=(str(getdate(valid_until)) if valid_until else None):
			frappe.throw('L’assegnazione è già stata usata con dati del pacchetto diversi.')
		return {'name':doc.name,**_balance(doc.name)}
	profile=frappe.get_doc('CC Package Template',template,for_update=True)
	if not profile.enabled:
		frappe.throw('Il modello pacchetto non è attivo.')
	if valid_until and getdate(valid_until)<frappe.utils.getdate():
		frappe.throw('La scadenza del pacchetto è nel passato.')
	if practitioner:
		from centrochange_core.security.guards import centers as practitioner_centers, enabled
		identity=frappe.get_doc('Healthcare Practitioner',practitioner)
		if identity.status!='Active' or not identity.user_id or not enabled(identity.user_id) or not set(centers).issubset(set(practitioner_centers(identity.user_id))):
			frappe.throw('Il professionista del pacchetto deve essere attivo e assegnato alle sedi selezionate.')
	with internal_write('cc_operation_write'):
		doc=frappe.get_doc({'doctype':'CC Patient Package','template':template,'patient':patient,
			'service_item':profile.service_item,'issue_key':key,'centers':[{'center':center} for center in centers],
			'practitioner':practitioner,'valid_until':valid_until,'issued_by':frappe.session.user}).insert(ignore_permissions=True)
		_append(doc.name,'GRANT',profile.units,0,'grant:'+doc.name,reason)
	append('PACKAGE_ISSUED',doc.doctype,doc.name,None,{'units':profile.units,'centers':centers},reason)
	return {'name':doc.name,**_balance(doc.name)}


@frappe.whitelist()
def balance(package,center):
	doc=frappe.get_doc('CC Patient Package',package)
	doc.check_permission('read')
	require_context(doc.patient,center)
	if center not in [row.center for row in doc.centers]:
		frappe.throw('Non hai accesso al pacchetto in questa sede.',frappe.PermissionError)
	return _balance(package)


def reserve(doc,reason):
	if not doc.cc_package:
		return
	package=_package(doc.cc_package)
	if package.patient!=doc.patient or package.service_item!=doc.cc_service_item or doc.cc_center not in [row.center for row in package.centers] or package.practitioner and package.practitioner!=doc.practitioner:
		frappe.throw('Il pacchetto non copre paziente, servizio o contesto selezionati.')
	if package.valid_until and getdate(doc.appointment_date)>getdate(package.valid_until):
		frappe.throw('Il pacchetto scade prima della seduta.')
	_append(package.name,'RESERVE',0,1,'reserve:'+doc.name,reason,doc.name,doc.cc_center)
	frappe.db.set_value('Patient Appointment',doc.name,'cc_package_state','Reserved')
	doc.cc_package_state='Reserved'


def disposition(doc,due,reason,revision):
	if not doc.cc_package:
		return
	_package(doc.cc_package)
	state=doc.cc_package_state
	if due and state=='Reserved':
		kind,remaining,reserved='CONSUME',-1,-1
	elif not due and state=='Reserved':
		kind,remaining,reserved='RELEASE',0,-1
	elif not due and state=='Consumed':
		kind,remaining,reserved='CORRECT',1,0
	elif due and state=='Released':
		kind,remaining,reserved='CORRECT',-1,0
	else:
		return
	_append(doc.cc_package,kind,remaining,reserved,f'disposition:{doc.name}:{revision}',reason,doc.name,doc.cc_center)
	doc.cc_package_state='Consumed' if due else 'Released'
	frappe.db.set_value('Patient Appointment',doc.name,'cc_package_state',doc.cc_package_state)


@frappe.whitelist(methods=['POST'])
@atomic
def adjust(package,units,request_key,reason):
	lock()
	doc=_package(package)
	doc.check_permission('read')
	for row in doc.centers:
		require_operations(row.center)
		require_context(doc.patient,row.center)
	units=frappe.utils.cint(units)
	if not units or abs(units)>9999 or not request_key or len(request_key)>140:
		frappe.throw('La rettifica del pacchetto non è valida.')
	from hashlib import sha256
	key=sha256((package+'\0'+request_key).encode()).hexdigest()
	name=_append(package,'ADJUST',units,0,'adjust:'+key,reason)
	return {'event':name,**_balance(package)}
