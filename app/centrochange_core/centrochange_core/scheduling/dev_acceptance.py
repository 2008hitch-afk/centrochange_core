"""Synthetic schedule regressions reuse isolated security fixtures."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.scheduling.availability import set_schedule,create_absence


def checks(fixture):
	pro1,pro2,center,other,prac1,prac2=(fixture[key] for key in ('pro1','pro2','center','other','prac1','prac2'))
	result=[]
	slots=[{'day':'Monday','from_time':'09:00:00','to_time':'12:00:00'}]
	frappe.set_user(pro1)
	name=set_schedule(prac1,center,slots,'Synthetic self schedule')['name']
	assert frappe.db.get_value('Practitioner Schedule',name,'cc_practitioner')==prac1
	result.append('self recurring schedule persisted')
	try:
		set_schedule(prac2,center,slots,'Unauthorized cross schedule')
	except frappe.PermissionError:
		result.append('cross-practitioner recurring mutation denied')
	else:
		raise AssertionError('Cross recurring mutation accepted')
	try:
		set_schedule(prac1,other,slots,'Unauthorized center')
	except frappe.PermissionError:
		result.append('cross-center recurring mutation denied')
	else:
		raise AssertionError('Cross center mutation accepted')
	absence=create_absence(prac1,center,'2099-01-05','2099-01-05','09:00:00','10:00:00','Synthetic absence')['name']
	assert frappe.db.get_value('Practitioner Availability',absence,'docstatus')==1
	result.append('self native absence submitted')
	before=frappe.db.count('CC Audit Event')
	assert create_absence(prac1,center,'2099-01-05','2099-01-05','09:00:00','10:00:00','Synthetic retry')['name']==absence
	assert set_schedule(prac1,center,slots,'Synthetic retry')['name']==name
	assert before==frappe.db.count('CC Audit Event')
	result.append('schedule and absence retry idempotent')
	frappe.set_user('Administrator')
	set_schedule(prac2,center,slots,'Synthetic central schedule')
	assert len(frappe.get_all('Practitioner Schedule',filters={'cc_center':center}))==2
	result.append('central management uses distinct dedicated schedules')
	frappe.set_user('Administrator')
	return result


def run():
	return security.run(extra_checks=checks)
