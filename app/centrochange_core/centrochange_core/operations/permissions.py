"""Operation projections scope native/internal queries explicitly."""
import frappe
from centrochange_core.security.guards import centers,current_rows,enabled,is_manager,names_condition,patient_names,patient_contexts,practitioner_for,roles


def appointment_names(user=None):
	if is_manager(user):
		return current_rows('Patient Appointment',pluck='name')
	filters={'patient':['in',patient_names(user) or ['']],'cc_center':['in',centers(user) or ['']]}
	if 'CC Professional' in roles(user):
		filters['practitioner']=practitioner_for(user) or ''
	elif 'CC Secretariat' not in roles(user):
		return []
	contexts=patient_contexts(user)
	return [row.name for row in current_rows('Patient Appointment',filters,fields=['name','patient','cc_center']) if (row.patient,row.cc_center) in contexts]


def package_names(user=None):
	if is_manager(user):
		return current_rows('CC Patient Package',pluck='name')
	if not enabled(user):
		return []
	rows=current_rows('CC Patient Package',{'patient':['in',patient_names(user) or ['']]},fields=['name','patient','practitioner'])
	rows=[row for row in rows if not row.practitioner or 'CC Professional' not in roles(user) or row.practitioner==practitioner_for(user)]
	allowed=current_rows('CC Package Center',{'parent':['in',[row.name for row in rows] or ['']],
		'parenttype':'CC Patient Package','center':['in',centers(user) or ['']]},fields=['parent','center'])
	contexts=patient_contexts(user)
	patients={row.name:row.patient for row in rows}
	return list({row.parent for row in allowed if (patients[row.parent],row.center) in contexts})


def package_query(user=None):
	return '' if is_manager(user) else names_condition('CC Patient Package',package_names(user))


def package_permission(doc,user=None,ptype=None):
	if is_manager(user):
		return True
	return bool(ptype in ('read','select') and doc.name in package_names(user))


def ledger_names(user=None):
	if is_manager(user):
		return current_rows('CC Package Ledger',pluck='name')
	rows=current_rows('CC Package Ledger',{'package':['in',package_names(user) or ['']]},fields=['name','appointment','center'])
	appointments=set(appointment_names(user))
	return [row.name for row in rows if (not row.center or row.center in centers(user)) and (not row.appointment or row.appointment in appointments)]


def ledger_query(user=None):
	return '' if is_manager(user) else names_condition('CC Package Ledger',ledger_names(user))


def ledger_permission(doc,user=None,ptype=None):
	if is_manager(user):
		return True
	return bool(ptype in ('read','select') and doc.name in ledger_names(user))


def settlement_query(user=None):
	if is_manager(user):
		return ''
	return names_condition('CC Settlement',current_rows('CC Settlement',{'appointment':['in',appointment_names(user) or ['']]},pluck='name'))


def settlement_permission(doc,user=None,ptype=None):
	if is_manager(user):
		return True
	return bool(ptype in ('read','select') and doc.appointment in appointment_names(user))


def notification_query(user=None):
	if is_manager(user):
		return ''
	return names_condition('CC Notification',current_rows('CC Notification',{'recipient':user or frappe.session.user},pluck='name')) if enabled(user) else '1=0'


def notification_permission(doc,user=None,ptype=None):
	if is_manager(user):
		return True
	return bool(enabled(user) and ptype in ('read','select') and doc.recipient==(user or frappe.session.user))
