"""UAT-11 decision probe: synthetic fixtures, always rolled back by security.run.

This records the current boundary; it does not authorize past-slot corrections.
"""

from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import frappe

from centrochange_core.operations.lifecycle import close, reopen, start_utc
from centrochange_core.scheduling.availability import set_schedule
from centrochange_core.scheduling.booking import SNAPSHOTS, book, reschedule
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
		'appointment_time': '11:00:00'}), 'Appointment requires a future same-day interval')
	with patch('centrochange_core.scheduling.booking.datetime', FixtureClock):
		name = book(**args)['name']
	doc = frappe.get_doc('Patient Appointment', name)
	snapshots = {key: doc.get(key) for key in SNAPSHOTS}
	old_clock = frappe.flags.get('cc_test_clock')
	try:
		frappe.flags.cc_test_clock = start_utc(doc) + timedelta(hours=2)
		assert not close(name, 0, 'UAT-11 synthetic close')['replay']
	finally:
		frappe.flags.cc_test_clock = old_clock
	_rejected(lambda: reschedule(name, '2099-01-19', '10:00:00',
		'UAT-11 closed move deny'), 'Finalized appointments require a governed correction')
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
	before_events = frappe.db.count('CC Audit Event', {'reference_name': name})
	_rejected(lambda: reschedule(name, '2026-09-28', '10:00:00',
		'UAT-11 historical correction probe'), 'Appointment requires a future same-day interval')
	doc.reload()
	assert str(doc.appointment_date) == '2026-09-28' and str(frappe.utils.get_time(doc.appointment_time)) == '09:00:00'
	assert frappe.db.count('CC Audit Event', {'reference_name': name}) == before_events
	blocker = book(**{**args, 'appointment_date': '2099-01-19',
		'appointment_time': '10:00:00', 'request_key': 'cc-uat11-future-collision'})['name']
	assert blocker != name
	_rejected(lambda: reschedule(name, '2099-01-19', '10:00:00',
		'UAT-11 collision probe'), 'Patient or practitioner interval is already booked')
	_rejected(lambda: reschedule(name, '2099-01-26', '10:00:00', ''),
		'A business reason is required')
	assert frappe.db.count('CC Audit Event', {'reference_name': name}) == before_events
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
	assert len(moves) == 1
	assert frappe.parse_json(moves[0].before_state)['appointment_date'] == '2026-09-28'
	assert frappe.parse_json(moves[0].after_state)['appointment_date'] == '2099-01-26'
	set_assignment(patient, center, practitioner, 0, 'UAT-11 synthetic fixture release')
	return ['ordinary past booking denied', 'synthetic historical session closed',
		'closed move denied', 'authorized reopen and direct bypass denied',
		'historical same-day move denied by future-slot rule without mutation',
		'collision and missing reason denied', 'governed future move and replay',
		'snapshot and before/after audit retained']


def run():
	return security.run(extra_checks=checks)
