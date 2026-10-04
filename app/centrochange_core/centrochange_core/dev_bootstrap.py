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
