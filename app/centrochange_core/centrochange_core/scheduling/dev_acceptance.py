"""Synthetic schedule regressions reuse isolated security fixtures."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.scheduling.availability import set_schedule,create_absence,cancel_absence


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
	assert not cancel_absence(absence,'Synthetic cancel absence')['replay']
	assert cancel_absence(absence,'Synthetic cancel retry')['replay']
	assert frappe.db.get_value('Practitioner Availability',absence,'docstatus')==2
	result.append('absence cancellation uses native correction and idempotent retry')
	frappe.set_user('Administrator')
	set_schedule(prac2,center,slots,'Synthetic central schedule')
	assert len(frappe.get_all('Practitioner Schedule',filters={'cc_center':center}))==2
	result.append('central management uses distinct dedicated schedules')
	frappe.set_user(pro1)
	assert frappe.get_list('Practitioner Schedule',pluck='name')==[name]
	frappe.get_doc('Practitioner Schedule',name).check_permission('read')
	result.append('own schedule list and direct read scoped')
	other_schedule=frappe.db.get_value('Practitioner Schedule',{'cc_practitioner':prac2,'cc_center':center})
	try:
		frappe.get_doc('Practitioner Schedule',other_schedule).check_permission('read')
	except frappe.PermissionError:
		result.append('cross practitioner direct schedule read denied')
	else:
		raise AssertionError('Cross schedule read accepted')
	try:
		frappe.get_doc({'doctype':'Practitioner Schedule','schedule_name':'CC SYNTHETIC BYPASS','cc_practitioner':prac1,'cc_center':center,'time_slots':slots}).insert(ignore_permissions=True)
	except frappe.PermissionError:
		result.append('generic recurring schedule bypass denied')
	else:
		raise AssertionError('Generic schedule mutation accepted')
	frappe.set_user('Administrator')
	result.extend(booking_checks(fixture))
	return result


def run():
	return security.run(extra_checks=checks)


def booking_checks(fixture):
	from centrochange_core.scheduling.booking import book,reschedule
	from centrochange_core.security.audit import internal_write
	from frappe.utils import add_days,nowdate
	center,prac,patient=(fixture[key] for key in ('center','prac1','patient'))
	item=frappe.get_doc({'doctype':'Item','item_code':'CC SYNTHETIC SESSION','item_name':'CC SYNTHETIC Session',
		'item_group':'Services','stock_uom':'Nos','is_stock_item':0,'is_sales_item':1}).insert()
	price_list=frappe.get_doc({'doctype':'Price List','price_list_name':'CC SYNTHETIC CENTER PRICE',
		'enabled':1,'selling':1,'currency':'EUR'}).insert()
	profile=frappe.get_doc({'doctype':'Appointment Type','appointment_type':'CC SYNTHETIC SESSION',
		'allow_booking_for':'Practitioner','default_duration':60,'cc_service_item':item.name}).insert()
	frappe.db.set_value('Branch',center,'cc_price_list',price_list.name)
	frappe.get_doc({'doctype':'CC Center Service','center':center,'appointment_type':profile.name,'enabled':1}).insert()
	price=frappe.get_doc({'doctype':'Item Price','item_code':item.name,'price_list':price_list.name,
		'price_list_rate':100,'currency':'EUR','valid_from':'2020-01-01'}).insert()
	frappe.get_doc({'doctype':'Item Price','item_code':item.name,'price_list':price_list.name,
		'price_list_rate':999,'currency':'EUR','valid_from':'2090-01-01'}).insert()
	payload={'patient':patient,'practitioner':prac,'center':center,'appointment_type':profile.name,
		'appointment_date':'2099-01-12','appointment_time':'09:00:00','request_key':'cc-synthetic-booking','reason':'Synthetic booking'}
	from centrochange_core.security.lifecycle import set_assignment
	set_assignment(patient,center,prac,1,'Synthetic booking assignment')
	booking=book(**payload)
	doc=frappe.get_doc('Patient Appointment',booking['name'])
	assert doc.duration==60 and doc.cc_price_snapshot==100 and doc.cc_item_price_source==price.name
	result=['booking-date price chosen over future session tariff']
	assert book(**payload)=={'name':doc.name,'replay':True}
	result.append('booking retry replays canonical appointment')
	profile.default_duration=30
	profile.save()
	price.price_list_rate=130
	price.save()
	doc.reload()
	assert doc.duration==60 and doc.cc_price_snapshot==100
	result.append('catalog changes preserve historical duration and price')
	doc.cc_price_snapshot=0
	try:
		with internal_write('cc_appointment_write'):
			doc.save()
	except frappe.ValidationError:
		result.append('snapshot tampering rejected server-side')
	else:
		raise AssertionError('Snapshot tampering accepted')
	try:
		book(**{**payload,'request_key':'cc-synthetic-collision'})
	except frappe.ValidationError:
		result.append('same practitioner and patient interval collision denied')
	else:
		raise AssertionError('Collision accepted')
	try:
		book(**{**payload,'request_key':'cc-synthetic-outside','appointment_time':'18:00:00'})
	except frappe.ValidationError:
		result.append('outside recurring schedule booking denied')
	else:
		raise AssertionError('Outside schedule accepted')
	doc.reload()
	moved=reschedule(doc.name,'2099-01-19','09:00:00','Synthetic move')
	doc.reload()
	assert moved['name']==doc.name and doc.duration==60 and doc.cc_price_snapshot==100
	result.append('reschedule preserves canonical identity and historical snapshot')
	before=frappe.db.count('CC Audit Event')
	assert reschedule(doc.name,'2099-01-19','09:00:00','Synthetic move retry')['replay']
	assert before==frappe.db.count('CC Audit Event')
	result.append('reschedule retry idempotent')
	item.disabled=1
	item.save()
	try:
		book(**{**payload,'request_key':'cc-synthetic-disabled','appointment_date':'2099-01-19'})
	except frappe.ValidationError:
		result.append('disabled service booking denied')
	else:
		raise AssertionError('Disabled service accepted')
	set_assignment(patient,center,prac,0,'Synthetic booking fixture release')
	return result
