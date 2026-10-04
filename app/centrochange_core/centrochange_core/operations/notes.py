"""Contextual organizational notes and confidential professional revisions."""
import frappe
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import (
	centers,current_rows,enabled,is_manager,names_condition,patient_names,patient_contexts,practitioner_for,
	require_center,require_patient,roles,
)


def require_context(patient,center):
	require_center(center)
	require_patient(patient)
	if is_manager():
		return
	filters={'patient':patient,'center':center,'active':1}
	if 'CC Professional' in roles():
		filters['practitioner']=practitioner_for() or ''
	elif 'CC Secretariat' not in roles():
		frappe.throw('Operational note access denied',frappe.PermissionError)
	if not current_rows('CC Patient Assignment',filters,pluck='name'):
		frappe.throw('Patient is not assigned in this note context',frappe.PermissionError)


def require_private(doc,user=None):
	user=user or frappe.session.user
	if not enabled(user) or 'CC Professional' not in roles(user) or doc.practitioner!=practitioner_for(user) or doc.center not in centers(user):
		frappe.throw('Confidential professional note access denied',frappe.PermissionError)
	if not current_rows('CC Patient Assignment',{'patient':doc.patient,'center':doc.center,'practitioner':doc.practitioner,'active':1},pluck='name'):
		frappe.throw('Confidential note patient assignment denied',frappe.PermissionError)


def validate_note(doc):
	if not doc.is_new() or not frappe.flags.get('cc_notes_write'):
		frappe.throw('Notes are append-only; use the guarded revision service',frappe.PermissionError)
	if not doc.content or len(doc.content)>100000:
		frappe.throw('A bounded note is required')
	doc.authored_by=frappe.session.user
	if doc.doctype=='CC Private Note':
		require_private(doc)
	else:
		require_context(doc.patient,doc.center)
	if doc.corrects:
		previous=frappe.get_doc(doc.doctype,doc.corrects)
		if doc.doctype=='CC Private Note':
			require_private(previous)
		else:
			require_context(previous.patient,previous.center)
		if previous.patient!=doc.patient or previous.center!=doc.center or previous.practitioner!=doc.practitioner:
			frappe.throw('Revision cannot change note context')


@frappe.whitelist(methods=['POST'])
@atomic
def add_note(patient,center,content,private=0,corrects=None):
	from centrochange_core.security.lifecycle import lock
	lock()
	private=frappe.utils.cint(private)
	if private not in (0,1):
		frappe.throw('Invalid note class')
	doctype='CC Private Note' if private else 'CC Organizational Note'
	doc=frappe.get_doc({'doctype':doctype,'patient':patient,'center':center,'content':content,
		'practitioner':practitioner_for() if 'CC Professional' in roles() else None,
		'authored_by':frappe.session.user,'corrects':corrects})
	with internal_write('cc_notes_write'):
		doc.insert(ignore_permissions=True)
	# No clinical/private body or patient identity is copied into management audit.
	append('PRIVATE_NOTE_CREATED' if private else 'ORGANIZATIONAL_NOTE_CREATED',doctype,doc.name,None,
		{'corrects':corrects},'Protected note revision' if corrects else 'Protected note entry')
	return {'name':doc.name}


def note_query(doctype,user=None):
	if doctype=='CC Private Note':
		if not enabled(user) or 'CC Professional' not in roles(user):
			return '1=0'
		filters={'practitioner':practitioner_for(user) or '', 'center':['in',centers(user) or ['']],
			'patient':['in',patient_names(user) or ['']]}
	else:
		if is_manager(user):
			return ''
		filters={'center':['in',centers(user) or ['']],'patient':['in',patient_names(user) or ['']]}
	contexts=patient_contexts(user)
	return names_condition(doctype,[row.name for row in current_rows(doctype,filters,fields=['name','patient','center']) if (row.patient,row.center) in contexts])


def private_query(user=None):
	return note_query('CC Private Note',user)


def organizational_query(user=None):
	return note_query('CC Organizational Note',user)


def private_permission(doc,user=None,ptype=None):
	if ptype not in ('read','select'):
		return False
	try:
		require_private(doc,user)
		return True
	except frappe.PermissionError:
		return False


def organizational_permission(doc,user=None,ptype=None):
	if is_manager(user):
		return True
	return bool(enabled(user) and ptype in ('read','select') and (doc.patient,doc.center) in patient_contexts(user))


def request_guard():
	"""Administrative native privilege never substitutes for a clinical principal."""
	from urllib.parse import unquote
	import json
	if enabled() and 'CC Professional' in roles() and practitioner_for():
		return
	path=unquote(getattr(getattr(frappe.local,'request',None),'path',''))
	def targets(value):
		if isinstance(value,dict):
			return any(targets(key) or targets(item) for key,item in value.items())
		if isinstance(value,(list,tuple)):
			return any(targets(item) for item in value)
		if not isinstance(value,str):
			return False
		if value=='CC Private Note' or value.startswith('CC Private Note.') or value.startswith('`tabCC Private Note`'):
			return True
		if value.startswith(('{','[')):
			try:
				return targets(json.loads(value))
			except (ValueError,TypeError):
				return False
		return False
	if '/api/resource/CC Private Note' in path or '/api/v2/document/CC Private Note' in path or targets(frappe.form_dict):
		frappe.throw('Private notes require an authorized clinical principal',frappe.PermissionError)
