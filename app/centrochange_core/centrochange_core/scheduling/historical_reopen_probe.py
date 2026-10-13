"""DECISION-058 UAT-11 regression: synthetic fixtures, full transaction rollback."""

from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import frappe

from centrochange_core.operations.lifecycle import close, reopen, record_settlement, start_utc
from centrochange_core.operations import packages
from centrochange_core.scheduling.availability import set_schedule, create_absence, cancel_absence
from centrochange_core.scheduling.booking import SNAPSHOTS, book, reschedule
from centrochange_core.security.audit import internal_write
from centrochange_core.security import dev_acceptance as security
from centrochange_core.security.lifecycle import set_assignment


class FixtureClock(datetime):
	@classmethod
	def now(cls, tz=None):
		at = cls(2026, 9, 1, 12, 0, tzinfo=ZoneInfo('Europe/Rome'))
		return at.astimezone(tz) if tz else at.replace(tzinfo=None)


def _rejected(action, expected):
	try:
		action()
	except frappe.ValidationError as error:
		assert expected in str(error), (expected, str(error))
	else:
		raise AssertionError('Expected validation rejection: ' + expected)


def checks(fixture):
	center, practitioner, patient = (fixture[key] for key in ('center', 'prac1', 'patient'))
	frappe.set_user('Administrator')
	set_schedule(practitioner, center, [{'day': 'Monday', 'from_time': '09:00:00', 'to_time': '12:00:00'}], 'UAT-11 synthetic schedule')
	item = frappe.get_doc({'doctype': 'Item', 'item_code': 'CC UAT11 SERVICE',
		'item_name': 'CC UAT11 Service', 'item_group': 'Services', 'stock_uom': 'Nos',
		'is_stock_item': 0, 'is_sales_item': 1}).insert()
	price_list = frappe.get_doc({'doctype': 'Price List', 'price_list_name': 'CC UAT11 PRICE',
		'enabled': 1, 'selling': 1, 'currency': 'EUR'}).insert()
	profile = frappe.get_doc({'doctype': 'Appointment Type', 'appointment_type': 'CC UAT11 SERVICE',
		'allow_booking_for': 'Practitioner', 'default_duration': 60,
		'cc_service_item': item.name}).insert()
	frappe.db.set_value('Branch', center, 'cc_price_list', price_list.name)
	frappe.get_doc({'doctype': 'CC Center Service', 'center': center,
		'appointment_type': profile.name, 'enabled': 1}).insert()
	frappe.get_doc({'doctype': 'Item Price', 'item_code': item.name,
		'price_list': price_list.name, 'price_list_rate': 100,
		'currency': 'EUR', 'valid_from': '2020-01-01'}).insert()
	set_assignment(patient, center, practitioner, 1, 'UAT-11 synthetic assignment')
	args = {'patient': patient, 'practitioner': practitioner, 'center': center,
		'appointment_type': profile.name, 'appointment_date': '2026-09-28',
		'appointment_time': '09:00:00', 'request_key': 'cc-uat11-historical',
		'reason': 'UAT-11 synthetic booking'}
	_rejected(lambda: book(**{**args, 'request_key': 'cc-uat11-ordinary-past',
		'appointment_time': '11:00:00'}), 'richiede un orario futuro')
	assert not book(**{**args, 'appointment_date': '2099-01-19',
		'request_key': 'cc-uat11-ordinary-future'})['replay']
	with patch('centrochange_core.scheduling.booking.datetime', FixtureClock):
		name = book(**args)['name']
		blocker = book(**{**args, 'appointment_time': '11:00:00',
			'request_key': 'cc-uat11-historical-collision'})['name']
	assert blocker != name
	doc = frappe.get_doc('Patient Appointment', name)
	snapshots = {key: doc.get(key) for key in SNAPSHOTS}
	old_clock = frappe.flags.get('cc_test_clock')
	try:
		frappe.flags.cc_test_clock = start_utc(doc) + timedelta(hours=2)
		assert not close(name, 0, 'UAT-11 synthetic close')['replay']
	finally:
		frappe.flags.cc_test_clock = old_clock
	_rejected(lambda: reschedule(name, '2099-01-19', '10:00:00',
		'UAT-11 closed move deny'), 'riapertura autorizzata')
	assert not reopen(name, 'UAT-11 synthetic authorized reopen')['replay']
	assert reopen(name, 'UAT-11 synthetic reopen replay')['replay']
	direct = frappe.get_doc('Patient Appointment', name)
	direct.appointment_time = '10:00:00'
	try:
		direct.save(ignore_permissions=True)
	except frappe.PermissionError:
		pass
	else:
		raise AssertionError('Direct mutation bypassed governed reschedule')
	frappe.set_user(fixture['pro2'])
	try:
		frappe.call('centrochange_core.scheduling.booking.reschedule',appointment=name,
			appointment_date='2026-09-28',appointment_time='10:00:00',
			reason='UAT-11 cross-practitioner API bypass')
	except frappe.PermissionError:
		pass
	else:
		raise AssertionError('Cross-practitioner correction accepted')
	finally:
		frappe.set_user('Administrator')
	before_events = frappe.db.count('CC Audit Event', {'reference_name': name})
	_rejected(lambda: reschedule(name, '2026-09-29', '10:00:00',
		'UAT-11 cross-date correction'), 'stessa data')
	_rejected(lambda: reschedule(name, '2026-09-28', '10:00:00', ''),
		'Indica il motivo')
	_rejected(lambda: reschedule(name, '2026-09-28', '11:00:00',
		'UAT-11 historical collision'), 'già una seduta')
	absence=create_absence(practitioner,center,'2026-09-28','2026-09-28',
		'10:00:00','11:00:00','UAT-11 synthetic absence')['name']
	_rejected(lambda: reschedule(name, '2026-09-28', '10:00:00',
		'UAT-11 historical absence'), 'non è disponibile')
	cancel_absence(absence,'UAT-11 synthetic absence release')
	doc.reload()
	assert str(doc.appointment_date) == '2026-09-28' and str(frappe.utils.get_time(doc.appointment_time)) == '09:00:00'
	assert frappe.db.count('CC Audit Event', {'reference_name': name}) == before_events
	assert not reschedule(name, '2026-09-28', '10:00:00',
		'UAT-11 same-day governed correction')['replay']
	assert reschedule(name, '2026-09-28', '10:00:00',
		'UAT-11 historical replay')['replay']
	_rejected(lambda: reschedule(name, '2026-09-28', '10:00:00', ''),
		'Indica il motivo')
	doc.reload()
	assert {key: doc.get(key) for key in SNAPSHOTS} == snapshots
	assert doc.cc_closure_state == 'Reopened'
	events = frappe.get_all('CC Audit Event', filters={'reference_name': name,
		'event_type': 'APPOINTMENT_RESCHEDULED'},fields=['before_state','after_state'])
	assert len(events) == 1
	assert frappe.parse_json(events[0].before_state)['appointment_time'] == '09:00:00'
	assert frappe.parse_json(events[0].after_state)['appointment_time'] == '10:00:00'
	assert frappe.db.count('CC Audit Event', {'reference_name': name}) == before_events+1
	# Each derived-fact fixture is isolated by a nested savepoint. The appointment
	# stays at 10:00 and every rejected 09:00 correction leaves audit unchanged.
	mode=frappe.db.get_value('Mode of Payment',{'enabled':1},'name')
	assert mode, 'Enabled synthetic payment method required'
	frappe.db.savepoint('cc_uat11_paid')
	record_settlement(name,1,'UAT-11 synthetic paid settlement',mode)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 paid correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_paid')
	frappe.db.savepoint('cc_uat11_package')
	frappe.db.set_value('Patient Appointment',name,'cc_package_state','Consumed')
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 consumed package correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_package')
	frappe.db.savepoint('cc_uat11_ledger')
	template=frappe.get_doc({'doctype':'CC Package Template','title':'CC UAT11 PACKAGE',
		'service_item':item.name,'units':1,'enabled':1}).insert()
	package=packages.issue(template.name,patient,[center],'cc-uat11-package',
		'UAT-11 synthetic package')['name']
	with internal_write('cc_operation_write'):
		frappe.get_doc({'doctype':'CC Package Ledger','package':package,'appointment':name,
			'center':center,'event_type':'CONSUME','remaining_delta':-1,
			'reserved_delta':-1,'event_key':'cc-uat11-synthetic-consume',
			'actor':'Administrator','event_time':frappe.utils.now_datetime(),
			'reason':'UAT-11 synthetic consumed package'}).insert(ignore_permissions=True)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 package ledger correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_ledger')
	frappe.db.savepoint('cc_uat11_override')
	with internal_write('cc_operation_write'):
		frappe.get_doc({'doctype':'CC Payment Override','patient':patient,'center':center,
			'reference_doctype':'Patient Appointment','reference_name':name,
			'due_date':'2099-02-01','reason':'UAT-11 synthetic debt decision',
			'recorded_by':'Administrator','request_key':'cc-uat11-override',
			'request_hash':'cc-uat11-override'}).insert(ignore_permissions=True)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 payment override correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_override')
	frappe.db.savepoint('cc_uat11_source')
	company=frappe.db.get_single_value('Global Defaults','default_company')
	cost_center=frappe.db.get_value('Cost Center',{'company':company,'is_group':0},'name')
	group=frappe.db.get_value('Customer Group',{'is_group':0},'name')
	territory=frappe.db.get_value('Territory',{'is_group':0},'name')
	customer=frappe.get_doc({'doctype':'Customer','customer_name':'CC UAT11 SYNTHETIC CUSTOMER',
		'customer_group':group,'territory':territory}).insert().name
	with internal_write('cc_operation_write'):
		source=frappe.get_doc({'doctype':'CC Economic Source Link','source_key':'cc-uat11-synthetic-source',
			'appointment':name,'patient':patient,'customer':customer,'practitioner':practitioner,
			'center':center,'company':company,'cost_center':cost_center,'service_item':item.name,
			'currency':'EUR','captured_by':'Administrator','snapshot_hash':'cc-uat11-synthetic-source'}).insert(ignore_permissions=True)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 economic source correction'), 'rettifica separata')
	with internal_write('cc_operation_write'):
		frappe.get_doc({'doctype':'CC Professional Expectation','center':center,
			'source':source.name,'appointment':name,'practitioner':practitioner,
			'state':'REVIEW','sequence':1,'snapshot_hash':'cc-uat11-synthetic-expectation',
			'recorded_by':'Administrator'}).insert(ignore_permissions=True)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 professional expectation correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_source')
	frappe.db.savepoint('cc_uat11_confirmation')
	with internal_write('cc_confirmation_write'):
		frappe.get_doc({'doctype':'CC Booking Confirmation','appointment':name,
			'center':center,'recipient':'uat11@example.invalid',
			'message':'Conferma sintetica 28/09 ore 10','state':'Simulated Sent'}).insert(ignore_permissions=True)
	_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
		'UAT-11 confirmation correction'), 'rettifica separata')
	frappe.db.rollback(save_point='cc_uat11_confirmation')
	frappe.db.savepoint('cc_uat11_unverified')
	get_value=frappe.db.get_value
	def unavailable(doctype,*a,**kw):
		if doctype=='CC Economic Source Link':
			raise RuntimeError('synthetic link verification unavailable')
		return get_value(doctype,*a,**kw)
	with patch.object(frappe.db,'get_value',side_effect=unavailable):
		_rejected(lambda: reschedule(name, '2026-09-28', '09:00:00',
			'UAT-11 unavailable-link correction'), 'Impossibile verificare')
	frappe.db.rollback(save_point='cc_uat11_unverified')
	assert frappe.db.count('CC Audit Event', {'reference_name': name}) == before_events+1
	assert not reschedule(name, '2099-01-26', '10:00:00',
		'UAT-11 governed future move')['replay']
	assert reschedule(name, '2099-01-26', '10:00:00',
		'UAT-11 future move replay')['replay']
	doc.reload()
	assert {key: doc.get(key) for key in SNAPSHOTS} == snapshots
	assert doc.cc_closure_state == 'Reopened'
	events = frappe.get_all('CC Audit Event', filters={'reference_name': name},
		fields=['event_type', 'before_state', 'after_state'])
	moves = [event for event in events if event.event_type == 'APPOINTMENT_RESCHEDULED']
	assert len(moves) == 2
	assert any(frappe.parse_json(event.before_state)['appointment_date']=='2026-09-28'
		and frappe.parse_json(event.after_state)['appointment_date']=='2099-01-26' for event in moves)
	try:
		frappe.flags.cc_test_clock=start_utc(doc)+timedelta(hours=2)
		assert not close(name,0,'UAT-11 governed reclosure')['replay']
	finally:
		frappe.flags.cc_test_clock=old_clock
	doc.reload()
	assert doc.cc_closure_state=='Closed'
	set_assignment(patient, center, practitioner, 0, 'UAT-11 synthetic fixture release')
	return ['ordinary past booking denied; future booking allowed', 'synthetic historical session closed',
		'closed move denied', 'authorized reopen and direct/cross-practitioner bypass denied',
		'cross-date, missing reason, collision and absence denied',
		'historical same-day correction and replay audited',
		'paid settlement, package state/ledger, economic source and expectation blocked',
		'payment override, confirmation and unverifiable links blocked',
		'governed future move and replay; reclosure allowed', 'snapshot and before/after audit retained']


def run():
	return security.run(extra_checks=checks)
