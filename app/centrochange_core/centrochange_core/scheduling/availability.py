"""Dedicated native recurring schedules and guarded absence management."""
import frappe
from frappe.utils import get_time
from centrochange_core.security.audit import append, atomic, internal_write
from centrochange_core.security.guards import enabled, is_manager, centers, require_operations, roles
from centrochange_core.security.lifecycle import lock


def require_practitioner(practitioner, center):
	doc=frappe.get_doc('Healthcare Practitioner',practitioner)
	if not enabled() or doc.status != 'Active':
		frappe.throw('Active authorized practitioner required',frappe.PermissionError)
	if not is_manager():
		if center not in centers():
			frappe.throw('Center access denied',frappe.PermissionError)
		if 'CC Professional' in roles():
			if doc.user_id != frappe.session.user:
				frappe.throw('Cross-practitioner schedule access denied',frappe.PermissionError)
		else:
			require_operations(center)
	if not doc.user_id or center not in centers(doc.user_id):
		frappe.throw('Practitioner must have active center membership')
	return doc


@frappe.whitelist(methods=['POST'])
@atomic
def set_schedule(practitioner,center,time_slots,reason):
	lock()
	identity=require_practitioner(practitioner,center)
	if isinstance(time_slots,str):
		time_slots=frappe.parse_json(time_slots)
	if not isinstance(time_slots,list) or len(time_slots)>100:
		frappe.throw('Invalid recurring schedule')
	slots=[]
	for row in time_slots:
		if row.get('day') not in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'):
			frappe.throw('Invalid weekday')
		start,end=get_time(row.get('from_time')),get_time(row.get('to_time'))
		if start>=end:
			frappe.throw('Schedule must start before it ends')
		if any(old['day']==row['day'] and start<get_time(old['to_time']) and end>get_time(old['from_time']) for old in slots):
			frappe.throw('Recurring schedule intervals overlap')
		slots.append({'day':row['day'],'from_time':str(start),'to_time':str(end)})
	name=frappe.db.get_value('Practitioner Schedule',{'cc_practitioner':practitioner,'cc_center':center},for_update=True)
	doc=frappe.get_doc('Practitioner Schedule',name) if name else frappe.get_doc({'doctype':'Practitioner Schedule',
		'schedule_name':'CC-'+frappe.generate_hash(length=16),'cc_practitioner':practitioner,'cc_center':center})
	before=[{'day':row.day,'from_time':str(get_time(row.from_time)),'to_time':str(get_time(row.to_time))} for row in doc.time_slots]
	if name and before==slots and not doc.disabled:
		return {'name':name}
	with internal_write('cc_schedule_write'):
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
		frappe.throw('Schedules and absences must use the guarded service',frappe.PermissionError)
