"""Canonical session closure, cancellation facts and audited operational settlement."""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import frappe
from frappe.utils import getdate,get_time,cint
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import require_operations
from centrochange_core.security.lifecycle import lock
from centrochange_core.scheduling.booking import require_booking
from centrochange_core.operations import packages

ROME=ZoneInfo('Europe/Rome')


def now_utc():
	if frappe.in_test and frappe.conf.get('cc_synthetic_dev')==1 and frappe.flags.get('cc_test_clock'):
		return frappe.flags.cc_test_clock
	return datetime.now(timezone.utc)


def start_utc(doc):
	local=datetime.combine(getdate(doc.appointment_date),get_time(doc.appointment_time))
	first=local.replace(tzinfo=ROME,fold=0)
	second=local.replace(tzinfo=ROME,fold=1)
	if first.utcoffset()!=second.utcoffset() or first.astimezone(timezone.utc).astimezone(ROME).replace(tzinfo=None)!=local:
		frappe.throw('Ambiguous or nonexistent Europe/Rome session time must be corrected explicitly')
	return first.astimezone(timezone.utc)


def cancellation_fact(start,at):
	if start.tzinfo is None or at.tzinfo is None:
		frappe.throw('Cancellation calculation requires timezone-aware instants')
	delta=start.astimezone(timezone.utc)-at.astimezone(timezone.utc)
	microseconds=(delta.days*86400+delta.seconds)*1000000+delta.microseconds
	return {'notice_seconds':microseconds/1000000,'late':microseconds<48*3600*1000000}


def _doc(name):
	doc=frappe.get_doc('Patient Appointment',name,for_update=True)
	doc.check_permission('read')
	from centrochange_core.operations.notes import require_context
	require_context(doc.patient,doc.cc_center)
	return doc


def require_mutable(doc):
	if doc.cc_closure_state in ('Closed','Auto Locked'):
		frappe.throw('Session is locked; authorized reopen/correction is required',frappe.PermissionError)
	cutoff=datetime.combine(getdate(doc.appointment_date)+timedelta(days=1),get_time('07:00:00')).replace(tzinfo=ROME)
	if doc.cc_closure_state!='Reopened' and now_utc()>=cutoff.astimezone(timezone.utc):
		frappe.throw('Session passed the automatic lock cutoff',frappe.PermissionError)


def _patch(doc,values):
	allowed={'status','cc_closure_state','cc_economic_state','cc_performed','cc_paid','cc_cancelled_at',
		'cc_cancel_notice_seconds','cc_late_cancellation','cc_revision','cc_settlement_revision','cc_locked_at'}
	if not frappe.flags.get('cc_operation_write') or set(values)-allowed:
		frappe.throw('Invalid operation patch',frappe.PermissionError)
	frappe.db.set_value('Patient Appointment',doc.name,values)
	for key,value in values.items():
		doc.set(key,value)


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(appointment,reason):
	lock()
	doc=_doc(appointment)
	if doc.status=='Cancelled':
		return {'name':doc.name,'late':bool(doc.cc_late_cancellation),'replay':True}
	require_mutable(doc)
	if doc.cc_performed:
		frappe.throw('Performed sessions require correction, not ordinary cancellation')
	at=now_utc()
	fact=cancellation_fact(start_utc(doc),at)
	revision=cint(doc.cc_revision)+1
	packages.disposition(doc,fact['late'],reason,revision)
	economic='Package Covered' if fact['late'] and doc.cc_package else ('Due' if fact['late'] else 'Non Due')
	with internal_write('cc_operation_write'):
		_patch(doc,{'status':'Cancelled','cc_closure_state':'Closed','cc_economic_state':economic,
			'cc_cancelled_at':at.replace(tzinfo=None),'cc_cancel_notice_seconds':fact['notice_seconds'],
			'cc_late_cancellation':int(fact['late']),'cc_revision':revision})
	append('SESSION_CANCELLED',doc.doctype,doc.name,None,{**fact,'economic':economic},reason)
	return {'name':doc.name,'late':fact['late'],'replay':False}


def _settlement(doc,paid,mode,reason):
	paid=cint(paid)
	if paid not in (0,1):
		frappe.throw('Paid must be a boolean operational fact')
	if paid and (not mode or not frappe.db.get_value('Mode of Payment',mode,'enabled',for_update=True)):
		frappe.throw('An enabled informative payment method is required')
	rows=current_settlements(doc.name)
	if rows and rows[0].paid==paid and (rows[0].mode_of_payment or None)==(mode or None):
		return rows[0].name
	if not reason or not reason.strip():
		frappe.throw('A settlement business reason is required')
	sequence=cint(doc.cc_settlement_revision)+1
	with internal_write('cc_operation_write'):
		event=frappe.get_doc({'doctype':'CC Settlement','appointment':doc.name,'paid':paid,'sequence':sequence,
			'mode_of_payment':mode,'actor':frappe.session.user,'event_time':frappe.utils.now_datetime(),'reason':reason}).insert(ignore_permissions=True)
		_patch(doc,{'cc_paid':paid,'cc_settlement_revision':sequence})
	append('OPERATIONAL_SETTLEMENT',doc.doctype,doc.name,None,{'paid':paid,'method':mode,'settlement':event.name},reason)
	return event.name


def current_settlements(appointment):
	from centrochange_core.security.guards import current_rows
	rows=current_rows('CC Settlement',{'appointment':appointment},fields=['name','paid','mode_of_payment','sequence'])
	return sorted(rows,key=lambda row:row.sequence,reverse=True)


@frappe.whitelist(methods=['POST'])
@atomic
def close(appointment,paid,reason,mode_of_payment=None):
	lock()
	doc=_doc(appointment)
	if doc.cc_closure_state=='Closed' and doc.cc_performed:
		rows=current_settlements(doc.name)
		if cint(paid)!=doc.cc_paid or rows and (rows[0].mode_of_payment or None)!=(mode_of_payment or None):
			frappe.throw('Closed settlement changes require a correction service')
		return {'name':doc.name,'replay':True}
	require_mutable(doc)
	if doc.status=='Cancelled':
		frappe.throw('Cancelled sessions require authorized economic correction')
	if start_utc(doc)+timedelta(minutes=doc.duration)>now_utc():
		frappe.throw('Cannot mark a future or ongoing session performed')
	revision=cint(doc.cc_revision)+1
	due=doc.cc_economic_state!='Waived'
	packages.disposition(doc,due,reason,revision)
	with internal_write('cc_operation_write'):
		_patch(doc,{'status':'Closed','cc_closure_state':'Closed','cc_performed':1,
			'cc_economic_state':('Package Covered' if doc.cc_package else 'Due') if due else 'Waived','cc_revision':revision})
	_settlement(doc,paid,mode_of_payment,reason)
	append('SESSION_CLOSED',doc.doctype,doc.name,None,{'performed':True,'economic':doc.cc_economic_state},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def waive(appointment,reason):
	lock()
	doc=_doc(appointment)
	require_operations(doc.cc_center)
	if doc.cc_economic_state=='Waived':
		return {'name':doc.name,'replay':True}
	if doc.cc_economic_state not in ('Due','Package Covered'):
		frappe.throw('A due economic disposition is required')
	revision=cint(doc.cc_revision)+1
	packages.disposition(doc,False,reason,revision)
	with internal_write('cc_operation_write'):
		_patch(doc,{'cc_economic_state':'Waived','cc_revision':revision})
	append('ECONOMIC_WAIVER',doc.doctype,doc.name,{'late':bool(doc.cc_late_cancellation)},
		{'economic':'Waived','late':bool(doc.cc_late_cancellation)},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def reopen(appointment,reason):
	lock()
	doc=_doc(appointment)
	require_operations(doc.cc_center)
	if doc.cc_closure_state=='Reopened':
		return {'name':doc.name,'replay':True}
	if doc.cc_closure_state not in ('Closed','Auto Locked'):
		frappe.throw('A finalized session is required')
	before={'closure':doc.cc_closure_state}
	with internal_write('cc_operation_write'):
		_patch(doc,{'cc_closure_state':'Reopened','cc_revision':cint(doc.cc_revision)+1})
	append('SESSION_REOPENED',doc.doctype,doc.name,before,{'closure':'Reopened'},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def record_settlement(appointment,paid,reason,mode_of_payment=None):
	lock()
	doc=_doc(appointment)
	if doc.cc_closure_state in ('Closed','Auto Locked'):
		require_operations(doc.cc_center)
		if doc.cc_closure_state=='Auto Locked':
			frappe.throw('Auto-locked sessions must be reopened before correction',frappe.PermissionError)
	else:
		require_mutable(doc)
	return {'settlement':_settlement(doc,paid,mode_of_payment,reason),'paid':cint(paid)}
