"""Supported operational fields and deterministic service configuration."""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

AUTOMATION_USER='cc-automation-service@example.invalid'


def configure():
	fields=[('cc_closure_state','Closure State','Select',{'options':'Pending\nClosed\nAuto Locked\nReopened','default':'Pending'}),
		('cc_economic_state','Economic Disposition','Select',{'options':'Pending\nDue\nWaived\nPackage Covered\nNon Due','default':'Pending'}),
		('cc_performed','Performed','Check',{'default':'0'}),('cc_paid','Operational Paid','Check',{'default':'0'}),
		('cc_cancelled_at','Cancellation Time UTC','Datetime',{}),('cc_cancel_notice_seconds','Cancellation Notice Seconds','Float',{}),
		('cc_late_cancellation','Late Cancellation Fact','Check',{'default':'0'}),
		('cc_package','Patient Package','Link',{'options':'CC Patient Package'}),
		('cc_package_state','Package State','Select',{'options':'\nReserved\nConsumed\nReleased'}),
		('cc_revision','Economic Revision','Int',{'default':'0'}),('cc_settlement_revision','Settlement Revision','Int',{'default':'0','hidden':1}),('cc_locked_at','Lock Time UTC','Datetime',{})]
	create_custom_fields({'Patient Appointment':[{'fieldname':name,'label':label,'fieldtype':kind,
		'read_only':1,**extra} for name,label,kind,extra in fields]})
	frappe.db.add_unique('CC Settlement',['appointment','sequence'],constraint_name='cc_settlement_sequence')
	frappe.db.add_unique('CC Notification',['event_key'],constraint_name='cc_notification_event_key')
	if not frappe.db.exists('Role','CC Automation Service'):
		frappe.get_doc({'doctype':'Role','role_name':'CC Automation Service','desk_access':0}).insert(ignore_permissions=True)
	if not frappe.db.exists('User',AUTOMATION_USER):
		frappe.get_doc({'doctype':'User','email':AUTOMATION_USER,'first_name':'Centro Change Automation Service',
			'enabled':1,'send_welcome_email':0,'roles':[{'role':'CC Automation Service'}]}).insert(ignore_permissions=True)
