"""WP-00 synthetic DEV setup, invoked through bench; never a public API."""

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete


COMPANY = "Centro Change SYNTHETIC DEV"


def setup():
	if frappe.session.user != "Administrator" or frappe.conf.get("cc_synthetic_dev") != 1:
		frappe.throw("Synthetic bootstrap requires an explicitly marked DEV site and Administrator")
	company_count = frappe.db.count("Company")
	if company_count > 1 or (company_count and not frappe.db.exists("Company", COMPANY)):
		frappe.throw("Refusing synthetic setup on a site containing another company")
	if not frappe.is_setup_complete():
		result = setup_complete(
			{
				"language": "English",
				"country": "Italy",
				"currency": "EUR",
				"timezone": "Europe/Rome",
				"company_name": COMPANY,
				"company_abbr": "CCDEV",
				"chart_of_accounts": "Standard",
				"domain": "Services",
				"fy_start_date": "2026-01-01",
				"fy_end_date": "2026-12-31",
				"setup_demo": 0,
				"enable_telemetry": 0,
			}
		)
		if result != {"status": "ok"}:
			frappe.throw("Native setup wizard did not complete successfully")
	if not frappe.is_setup_complete() or not frappe.db.exists("Company", COMPANY):
		frappe.throw("Synthetic ERPNext setup postconditions failed")
	company = frappe.get_doc("Company", COMPANY)
	if company.default_currency != "EUR" or company.country != "Italy":
		frappe.throw("Synthetic company configuration differs from the DEV baseline")
	if not frappe.db.exists("Account", {"company": COMPANY, "is_group": 0}):
		frappe.throw("Synthetic company chart of accounts is missing")
	frappe.db.commit()
	return {"synthetic_dev": True, "company": COMPANY, "setup_complete": True}


def smoke():
	"""Exercise native Healthcare documents in a rolled-back synthetic transaction."""
	setup()
	frappe.db.savepoint("wp00_smoke")
	previous_smoke = frappe.flags.get("cc_runtime_smoke")
	previous_test = frappe.in_test
	frappe.in_test = True
	frappe.flags.cc_runtime_smoke = True
	try:
		patient = frappe.get_doc({
			"doctype": "Patient", "first_name": "WP00 SYNTHETIC Patient",
			"sex": "Female", "email": "patient.wp00@example.invalid", "invite_user": 0,
		}).insert()
		practitioner = frappe.get_doc({
			"doctype": "Healthcare Practitioner", "first_name": "WP00 SYNTHETIC Practitioner",
			"status": "Active",
		}).insert()
		appointment_type = frappe.get_doc({
			"doctype": "Appointment Type", "appointment_type": "WP00 SYNTHETIC Smoke",
			"allow_booking_for": "Practitioner", "default_duration": 30,
		}).insert()
		appointment = frappe.get_doc({
			"doctype": "Patient Appointment", "patient": patient.name,
			"practitioner": practitioner.name, "company": COMPANY,
			"appointment_type": appointment_type.name, "appointment_for": "Practitioner",
			"appointment_date": "2099-01-05", "appointment_time": "10:00:00",
			"duration": 30, "paid_amount": 0,
		}).insert()
		appointment.reload()
		assert appointment.patient == patient.name
		assert appointment.practitioner == practitioner.name
		assert appointment.duration == 30
		assert not appointment.invoiced and not appointment.ref_sales_invoice
		return {"patient": True, "practitioner": True, "appointment": True, "cleanup": "rollback"}
	finally:
		frappe.db.rollback(save_point="wp00_smoke")
		frappe.flags.cc_runtime_smoke = previous_smoke
		frappe.in_test = previous_test
