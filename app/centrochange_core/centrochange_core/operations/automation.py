"""Deterministic catch-up; local calendar cutoffs, no external delivery."""
from datetime import datetime,timedelta,timezone
import frappe
from frappe.utils import getdate,get_time
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import current_rows
from centrochange_core.security.lifecycle import lock
from centrochange_core.operations.install import AUTOMATION_USER
from centrochange_core.operations.lifecycle import ROME,now_utc,_patch


def enqueue_notice(key,user,kind,doctype,name,message):
	existing=frappe.db.get_value('CC Notification',{'event_key':key},for_update=True)
	if existing:
		return existing
	with internal_write('cc_notification_write'):
		return frappe.get_doc({'doctype':'CC Notification','event_key':key,'recipient':user,'kind':kind,
			'reference_doctype':doctype,'reference_name':name,'message':message,'state':'Pending'}).insert(ignore_permissions=True).name


@atomic
def catch_up():
	# Private scheduled job: no API decorator, no caller-controlled authority.
	previous=frappe.session.user
	try:
		frappe.set_user(AUTOMATION_USER)
		lock()
		at=now_utc()
		local=at.astimezone(ROME)
		rows=current_rows('Patient Appointment',{'appointment_date':['<=',local.date()],
			'cc_closure_state':'Pending'},fields=['name','appointment_date','practitioner'])
		locked=reminded=0
		for row in rows:
			doc=frappe.get_doc('Patient Appointment',row.name,for_update=True)
			date=getdate(doc.appointment_date)
			cutoff=datetime.combine(date+timedelta(days=1),get_time('07:00:00')).replace(tzinfo=ROME)
			if at>=cutoff.astimezone(timezone.utc):
				with internal_write('cc_operation_write'):
					_patch(doc,{'cc_closure_state':'Auto Locked','cc_locked_at':at.replace(tzinfo=None)})
				append('SESSION_AUTO_LOCKED',doc.doctype,doc.name,{'closure':'Pending'},{'closure':'Auto Locked'},'07:00 local cutoff catch-up')
				locked+=1
			elif local>=datetime.combine(date,get_time('21:00:00')).replace(tzinfo=ROME):
				user=frappe.db.get_value('Healthcare Practitioner',doc.practitioner,'user_id',for_update=True)
				if user and frappe.db.get_value('User',user,'enabled',for_update=True):
					key=f'closure-reminder:{date}:{doc.practitioner}'
					existed=frappe.db.get_value('CC Notification',{'event_key':key},for_update=True)
					enqueue_notice(key,user,'CLOSURE_REMINDER','Healthcare Practitioner',doc.practitioner,
						'Hai sedute da chiudere oggi. Apri la tua Agenda per completarle.')
					reminded+=int(not bool(existed))
		return {'locked':locked,'reminders':reminded}
	finally:
		frappe.set_user(previous)
