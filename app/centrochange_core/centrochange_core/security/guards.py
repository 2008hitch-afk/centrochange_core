"""Explicit authorization for application services and privileged query primitives."""

import frappe


def enabled(user=None):
	user = user or frappe.session.user
	return user != "Guest" and bool(frappe.db.get_value("User", user, "enabled", for_update=bool(frappe.flags.get("cc_permission_current_read"))))


def is_manager(user=None):
	user = user or frappe.session.user
	return enabled(user) and (user == "Administrator" or "CC Manager" in roles(user))


def require_manager():
	if not is_manager():
		frappe.throw("Centro Change management permission required", frappe.PermissionError)


def centers(user=None):
	user = user or frappe.session.user
	if not enabled(user):
		return []
	# Internal primitive: caller scope is fixed to the authenticated user.
	return current_rows("CC Center Membership", filters={"user": user, "active": 1}, pluck="center")


def require_center(center):
	if not is_manager() and center not in centers():
		frappe.throw("Centro Change center access denied", frappe.PermissionError)


def require_operations(center):
	require_center(center)
	if not is_manager() and "CC Secretariat" not in roles():
		frappe.throw("Centro Change administrative permission required", frappe.PermissionError)


def practitioner_for(user=None):
	user = user or frappe.session.user
	if not enabled(user):
		return None
	return frappe.db.get_value("Healthcare Practitioner", {"user_id": user, "status": "Active"}, "name",
		for_update=bool(frappe.flags.get("cc_permission_current_read")))


def patient_names(user=None):
	user = user or frappe.session.user
	allowed_centers = centers(user)
	if not allowed_centers:
		return []
	filters = {"active": 1, "center": ["in", allowed_centers]}
	user_roles = roles(user)
	if "CC Professional" in user_roles:
		practitioner = practitioner_for(user)
		if not practitioner:
			return []
		filters["practitioner"] = practitioner
	elif "CC Secretariat" not in user_roles:
		return []
	return current_rows("CC Patient Assignment", filters=filters, pluck="patient")


def require_patient(patient, permission="read"):
	if not enabled() or (not is_manager() and patient not in patient_names()):
		frappe.throw("Centro Change patient access denied", frappe.PermissionError)
	frappe.get_doc("Patient", patient).check_permission(permission)


def names_condition(doctype, names):
	if not names:
		return "1=0"
	values = ",".join(frappe.db.escape(name) for name in set(names))
	return f"`tab{doctype}`.`name` IN ({values})"


def current_rows(doctype, filters=None, fields=None, pluck=None):
	"""Permission transactions need current reads after waiting under REPEATABLE READ."""
	return frappe.db.get_values(doctype, filters=filters, fieldname=pluck or fields or "name",
		as_dict=not bool(pluck), pluck=bool(pluck),
		for_update=bool(frappe.flags.get("cc_permission_current_read")))


def roles(user=None):
	user=user or frappe.session.user
	if frappe.flags.get("cc_permission_current_read"):
		return current_rows("Has Role", {"parent":user}, pluck="role")
	return frappe.get_roles(user)
