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
	}, *[{"fieldname":name,"label":label,"fieldtype":kind,**extra,"read_only":1,"no_copy":1}
		for name,label,kind,extra in [
			("cc_booking_key","Booking Key","Data",{"unique":1}),
			("cc_public_payload_hash","Public Payload Hash","Data",{}),
			("cc_booking_date","Booking Date","Date",{}),
			("cc_service_item","Service Item Snapshot","Link",{"options":"Item"}),
			("cc_service_label","Service Label Snapshot","Data",{}),
			("cc_price_snapshot","Price Snapshot","Currency",{}),
			("cc_currency_snapshot","Currency Snapshot","Link",{"options":"Currency"}),
			("cc_price_list_snapshot","Price List Snapshot","Link",{"options":"Price List"}),
			("cc_item_price_source","Item Price Source","Link",{"options":"Item Price"}),
		]],], "Branch": [
			{"fieldname":"cc_price_list","label":"Centro Change Selling Price List","fieldtype":"Link","options":"Price List"},
			{"fieldname":"cc_operational","label":"Sede operativa","fieldtype":"Check","default":"1",
			 "description":"Una sede non operativa resta consultabile nello storico, ma non accetta nuove operazioni."},
		],
	"Appointment Type": [{"fieldname":"cc_service_item","label":"Centro Change Service Item","fieldtype":"Link","options":"Item"}, {"fieldname":"cc_first_meeting","label":"Centro Change First Meeting","fieldtype":"Check","default":"0"}],
	"Practitioner Schedule": [
		{"fieldname":"cc_practitioner", "label":"Centro Change Practitioner", "fieldtype":"Link", "options":"Healthcare Practitioner"},
		{"fieldname":"cc_center", "label":"Centro Change Center", "fieldtype":"Link", "options":"Branch"},
	], "Practitioner Availability": [
		{"fieldname":"cc_center", "label":"Centro Change Center", "fieldtype":"Link", "options":"Branch"},
	]})
	create_custom_fields({'Patient':[{'fieldname':name,'label':label,'fieldtype':'Data','read_only':1,'hidden':1,**extra} for name,label,extra in [('cc_intake_key','Controlled Intake Key',{'unique':1}),('cc_intake_hash','Controlled Intake Payload Hash',{})]]})
	# Override the complete Patient permission set, preserving deny-by-default for professionals.
	permissions = {
		**{doctype:[("CC Manager",{"read":1}), ("CC Professional",{"read":1}), ("CC Secretariat",{"read":1})] for doctype in ("Practitioner Schedule","Practitioner Availability")},
		**{doctype:[("CC Manager",{"read":1,"write":1,"create":1,"report":1})] for doctype in ("Item","Item Price","Price List","Appointment Type")},
		"Patient Appointment": [("CC Manager", {"read":1,"write":1,"create":1,"report":1}),
			("CC Professional", {"read":1}), ("CC Secretariat", {"read":1})],
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
	# Capture duration once in the booking service; native fetch otherwise refreshes it on moves.
	make_property_setter("Patient Appointment", "duration", "fetch_from", "", "Data", validate_fields_for_doctype=False)
	# A shared patient identity must never serve as cross-center clinical/private storage.
	# Contextual notes/history remain distinct guarded records in subsequent waves.
	for field in CLINICAL_FIELDS:
		make_property_setter("Patient", field, "permlevel", 2, "Int", validate_fields_for_doctype=False)
	# Native uniqueness semantics require a database boundary, not a pre-insert query.
	frappe.db.add_unique("Healthcare Practitioner", ["user_id"], constraint_name="cc_primary_practitioner_user")
	frappe.db.add_unique("CC Center Membership", ["user", "center"], constraint_name="cc_user_center_membership")
	frappe.db.add_unique("CC Center Service", ["center", "appointment_type"], constraint_name="cc_center_service")
	frappe.db.add_unique("Practitioner Schedule", ["cc_practitioner", "cc_center"], constraint_name="cc_practitioner_center_schedule")


	# Dedicated noninteractive ingress identity; no broad manager/clinical role.
	from centrochange_core.scheduling.public_booking import SERVICE_USER
	if not frappe.db.exists('Role','CC Public Booking Service'):
		frappe.get_doc({'doctype':'Role','role_name':'CC Public Booking Service','desk_access':0}).insert(ignore_permissions=True)
	if not frappe.db.exists('User',SERVICE_USER):
		frappe.get_doc({'doctype':'User','email':SERVICE_USER,'first_name':'Centro Change Public Booking Service',
			'enabled':1,'send_welcome_email':0,'roles':[{'role':'CC Public Booking Service'}]}).insert(ignore_permissions=True)
