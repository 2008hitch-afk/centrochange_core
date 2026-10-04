"""Versioned, idempotent security configuration; no permission state from testlab."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CLINICAL_FIELDS = (
	"blood_group", "inpatient_status", "inpatient_record", "emergency_record", "allergies",
	"medication", "medical_history", "surgical_history", "tobacco_past_use", "tobacco_current_use",
	"alcohol_past_use", "alcohol_current_use", "surrounding_factors", "other_risk_factors",
	"patient_details", "patient_relation",
)


def ensure_roles():
	for role in ("CC Manager", "CC Professional", "CC Secretariat", "CC Finance"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def configure():
	ensure_roles()
	create_custom_fields({"Patient Appointment": [{
		"fieldname": "cc_center", "label": "Centro Change Center", "fieldtype": "Link", "options": "Branch",
		"insert_after": "company",
	}], "Practitioner Schedule": [
		{"fieldname":"cc_practitioner", "label":"Centro Change Practitioner", "fieldtype":"Link", "options":"Healthcare Practitioner"},
		{"fieldname":"cc_center", "label":"Centro Change Center", "fieldtype":"Link", "options":"Branch"},
	], "Practitioner Availability": [
		{"fieldname":"cc_center", "label":"Centro Change Center", "fieldtype":"Link", "options":"Branch"},
	]})
	# Override the complete Patient permission set, preserving deny-by-default for professionals.
	permissions = {
		"Patient": [
			("CC Manager", {"read": 1, "write": 1, "create": 1, "report": 1}),
			("CC Professional", {}), ("CC Secretariat", {"create": 1}),
		],
		"Healthcare Practitioner": [
			("CC Manager", {"read": 1, "create": 1, "write": 1, "report": 1}),
			("CC Professional", {"read": 1}),
		],
		"Branch": [
			("CC Manager", {"read": 1, "write": 1, "create": 1}),
			("CC Professional", {"read": 1}), ("CC Secretariat", {"read": 1}),
		],
	}
	for doctype, rows in permissions.items():
		# Deliberately controlled product policy: replace only these three master permission sets.
		frappe.db.delete("Custom DocPerm", {"parent": doctype})
		for role, rights in rows:
			frappe.get_doc({"doctype": "Custom DocPerm", "parent": doctype, "parenttype": "DocType",
				"parentfield": "permissions", "role": role, "permlevel": 0,
				**{right: 0 for right in ("read", "write", "create", "delete", "submit", "cancel",
					"amend", "report", "export", "import", "share", "print", "email", "select")}, **rights}).insert(ignore_permissions=True)
		frappe.clear_cache(doctype=doctype)
	# A shared patient identity must never serve as cross-center clinical/private storage.
	# Contextual notes/history remain distinct guarded records in subsequent waves.
	for field in CLINICAL_FIELDS:
		make_property_setter("Patient", field, "permlevel", 2, "Int", validate_fields_for_doctype=False)
	# Native uniqueness semantics require a database boundary, not a pre-insert query.
	frappe.db.add_unique("Healthcare Practitioner", ["user_id"], constraint_name="cc_primary_practitioner_user")
	frappe.db.add_unique("CC Center Membership", ["user", "center"], constraint_name="cc_user_center_membership")
