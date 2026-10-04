"""Narrow guarded replacements for non-permission-aware Marley identity methods."""

import frappe

from centrochange_core.security.guards import require_manager, require_operations, require_patient


IDENTITY_FIELDS = (
	"name", "patient_name", "first_name", "middle_name", "last_name", "dob", "sex", "status",
	"uid", "email", "mobile", "phone", "customer", "default_currency", "default_price_list",
	"customer_group", "territory", "language", "country",
)


@frappe.whitelist()
def get_patient_detail(patient):
	require_patient(patient)
	doc = frappe.get_doc("Patient", patient)
	return {key: doc.get(key) for key in IDENTITY_FIELDS}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_practitioner_list(doctype, txt, searchfield, start, page_len, filters=None):
	if doctype != "Healthcare Practitioner":
		frappe.throw("Invalid practitioner lookup", frappe.PermissionError)
	return frappe.get_list("Healthcare Practitioner", fields=["name", "practitioner_name"],
		filters={"status": "Active"}, or_filters={"name": ["like", "%" + txt + "%"],
			"practitioner_name": ["like", "%" + txt + "%"]}, start=start, page_length=min(int(page_len), 50), as_list=True)


@frappe.whitelist()
def get_supplier_and_user(user_id=None, supplier=None):
	require_manager()
	from healthcare.healthcare.doctype.healthcare_practitioner.healthcare_practitioner import get_supplier_and_user as native
	return native(user_id=user_id, supplier=supplier)


@frappe.whitelist()
def discover_patient(center, uid):
	"""Exact identifier lookup for authorized cross-center identity reuse; never clinical."""
	require_operations(center)
	if not uid or len(uid) > 140:
		frappe.throw("An exact patient identifier is required")
	return frappe.get_all("Patient", filters={"uid": uid}, fields=list(IDENTITY_FIELDS), limit_page_length=1)


def before_request():
	# Defense for retained sessions if a post-commit invalidation callback fails.
	from centrochange_core.security.guards import enabled
	from centrochange_core.scheduling.public_booking import SERVICE_USER
	from centrochange_core.operations.install import AUTOMATION_USER
	if frappe.session.user in (SERVICE_USER, AUTOMATION_USER):
		frappe.throw("Ingress service cannot authenticate interactively", frappe.PermissionError)
	if frappe.session.user != "Guest" and not enabled():
		frappe.throw("Disabled principal cannot access Centro Change", frappe.PermissionError)
