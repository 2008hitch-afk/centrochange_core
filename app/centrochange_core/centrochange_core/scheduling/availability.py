"""Dedicated native recurring schedules and guarded absence management."""
import frappe
from frappe.utils import get_time
from centrochange_core.security.audit import append, atomic, internal_write
from centrochange_core.security.guards import enabled, is_manager, centers, require_operations, roles
from centrochange_core.security.lifecycle import lock


def require_practitioner(practitioner, center):
	from centrochange_core.security.guards import require_operational_center
	require_operational_center(center)
	doc=frappe.get_doc('Healthcare Practitioner',practitioner,for_update=True)
	if not enabled() or doc.status != 'Active':
		frappe.throw('Seleziona un professionista attivo e autorizzato.',frappe.PermissionError)
	if not is_manager():
		if center not in centers():
			frappe.throw('Non hai accesso a questa sede.',frappe.PermissionError)
		if 'CC Professional' in roles():
			if doc.user_id != frappe.session.user:
				frappe.throw('Non puoi consultare la disponibilità di un altro professionista.',frappe.PermissionError)
		else:
			require_operations(center)
	if not doc.user_id or center not in centers(doc.user_id):
		frappe.throw('Il professionista deve avere un’appartenenza attiva alla sede.')
	return doc


@frappe.whitelist(methods=['POST'])
@atomic
def set_schedule(practitioner,center,time_slots,reason,expected_modified=None):
	lock()
	identity=require_practitioner(practitioner,center)
	if isinstance(time_slots,str):
		time_slots=frappe.parse_json(time_slots)
	if not isinstance(time_slots,list) or len(time_slots)>100:
		frappe.throw('La disponibilità settimanale non è valida.')
	slots=[]
	for row in time_slots:
		if row.get('day') not in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'):
			frappe.throw('Il giorno della settimana non è valido.')
		start,end=get_time(row.get('from_time')),get_time(row.get('to_time'))
		if start>=end:
			frappe.throw('L’ora iniziale deve precedere quella finale.')
		if any(old['day']==row['day'] and start<get_time(old['to_time']) and end>get_time(old['from_time']) for old in slots):
			frappe.throw('Le fasce della disponibilità settimanale si sovrappongono.')
		slots.append({'day':row['day'],'from_time':str(start),'to_time':str(end)})
	name=frappe.db.get_value('Practitioner Schedule',{'cc_practitioner':practitioner,'cc_center':center},for_update=True)
	doc=frappe.get_doc('Practitioner Schedule',name,for_update=True) if name else frappe.get_doc({'doctype':'Practitioner Schedule',
		'schedule_name':'CC-'+frappe.generate_hash(length=16),'cc_practitioner':practitioner,'cc_center':center})
	if expected_modified is not None and ((name and str(doc.modified)!=str(expected_modified)) or (not name and expected_modified!='')):
		frappe.throw('L’orario è cambiato: ricarica la disponibilità prima di salvare.')
	before=[{'day':row.day,'from_time':str(get_time(row.from_time)),'to_time':str(get_time(row.to_time))} for row in doc.time_slots]
	if name and before==slots and not doc.disabled:
		return {'name':name}
	with internal_write('cc_schedule_write'):
		doc.disabled=0
		doc.set('time_slots',slots)
		doc.save(ignore_permissions=True)
		if not any(row.schedule==doc.name for row in identity.practitioner_schedules):
			identity.append('practitioner_schedules',{'schedule':doc.name})
			identity.save(ignore_permissions=True)
	append('SCHEDULE_CHANGED',doc.doctype,doc.name,before,slots,reason)
	return {'name':doc.name}


@frappe.whitelist(methods=['POST'])
@atomic
def create_absence(practitioner,center,start_date,end_date,start_time,end_time,reason):
	lock()
	require_practitioner(practitioner,center)
	existing=frappe.db.get_value('Practitioner Availability',{'type':'Unavailable','scope_type':'Healthcare Practitioner',
		'scope':practitioner,'cc_center':center,'start_date':start_date,'end_date':end_date,
		'start_time':start_time,'end_time':end_time,'docstatus':1},for_update=True)
	if existing:
		return {'name':existing}
	with internal_write('cc_schedule_write'):
		doc=frappe.get_doc({'doctype':'Practitioner Availability','type':'Unavailable',
			'scope_type':'Healthcare Practitioner','scope':practitioner,'cc_center':center,
			'start_date':start_date,'end_date':end_date,'start_time':start_time,'end_time':end_time,
			'reason':'Time Off','repeat':'Never','status':'Active'}).insert(ignore_permissions=True)
		doc.submit()
	append('ABSENCE_CREATED',doc.doctype,doc.name,None,{'practitioner':practitioner,'center':center,
		'start_date':start_date,'end_date':end_date,'start_time':start_time,'end_time':end_time},reason)
	return {'name':doc.name}


def protected_schedule(doc,method=None):
	if not frappe.flags.get('cc_schedule_write'):
		frappe.throw('Usa il servizio autorizzato per disponibilità e assenze.',frappe.PermissionError)


def schedule_query(user=None):
	from centrochange_core.security.guards import current_rows,roles,practitioner_for,names_condition
	if is_manager(user):
		return ''
	filters={'cc_center':['in',centers(user) or ['']]}
	if 'CC Professional' in roles(user):
		filters['cc_practitioner']=practitioner_for(user) or ''
	elif 'CC Secretariat' not in roles(user):
		return '1=0'
	return names_condition('Practitioner Schedule',current_rows('Practitioner Schedule',filters,pluck='name'))


def availability_query(user=None):
	from centrochange_core.security.guards import current_rows,roles,practitioner_for,names_condition
	if is_manager(user):
		return ''
	filters={'cc_center':['in',centers(user) or ['']],'scope_type':'Healthcare Practitioner'}
	if 'CC Professional' in roles(user):
		filters['scope']=practitioner_for(user) or ''
	elif 'CC Secretariat' not in roles(user):
		return '1=0'
	return names_condition('Practitioner Availability',current_rows('Practitioner Availability',filters,pluck='name'))


def schedule_permission(doc,user=None,ptype=None):
	from centrochange_core.security.guards import roles,practitioner_for
	if is_manager(user):
		return True
	if not enabled(user) or ptype not in ('read','select') or doc.cc_center not in centers(user):
		return False
	if 'CC Professional' in roles(user):
		return doc.cc_practitioner==practitioner_for(user)
	return 'CC Secretariat' in roles(user)


def availability_permission(doc,user=None,ptype=None):
	from centrochange_core.security.guards import roles,practitioner_for
	if is_manager(user):
		return True
	if not enabled(user) or ptype not in ('read','select') or doc.cc_center not in centers(user) or doc.scope_type!='Healthcare Practitioner':
		return False
	if 'CC Professional' in roles(user):
		return doc.scope==practitioner_for(user)
	return 'CC Secretariat' in roles(user)


@frappe.whitelist(methods=['POST'])
@atomic
def cancel_absence(availability,reason):
	lock()
	doc=frappe.get_doc('Practitioner Availability',availability,for_update=True)
	if doc.scope_type!='Healthcare Practitioner' or doc.type!='Unavailable':
		frappe.throw('Puoi annullare solo le assenze gestite da Centro Change.')
	require_practitioner(doc.scope,doc.cc_center)
	if doc.docstatus==2:
		return {'name':doc.name,'replay':True}
	if doc.docstatus!=1:
		frappe.throw('Seleziona un’assenza confermata.')
	with internal_write('cc_schedule_write'):
		doc.flags.ignore_permissions=True
		doc.cancel()
	append('ABSENCE_CANCELLED',doc.doctype,doc.name,{'docstatus':1},{'docstatus':2},reason)
	return {'name':doc.name,'replay':False}
