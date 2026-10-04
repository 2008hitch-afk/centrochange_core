import frappe

from centrochange_core.security.guards import (
	centers, enabled, is_manager, names_condition, patient_names, practitioner_for,
)


def patient_query(user=None):
	return "" if is_manager(user) else names_condition("Patient", patient_names(user))


def patient_permission(doc, user=None, permission_type=None):
	if is_manager(user):
		return None
	user = user or frappe.session.user
	if doc.is_new() and permission_type == "create":
		roles = frappe.get_roles(user)
		return None if enabled(user) and centers(user) and "CC Secretariat" in roles and "CC Professional" not in roles else False
	if not enabled(user) or doc.name not in patient_names(user):
		return False
	if permission_type in ("delete", "share", "export", "import", "create"):
		return False
	return None


def practitioner_query(user=None):
	if is_manager(user):
		return ""
	return names_condition("Healthcare Practitioner", [practitioner_for(user)] if practitioner_for(user) else [])


def practitioner_permission(doc, user=None, permission_type=None):
	if is_manager(user):
		return None
	if doc.name != practitioner_for(user) or permission_type not in ("read", "select"):
		return False
	return None


def membership_query(user=None):
	if is_manager(user):
		return ""
	return "`tabCC Center Membership`.`user` = " + frappe.db.escape(user or frappe.session.user)


def assignment_query(user=None):
	if is_manager(user):
		return ""
	filters = {"patient": ["in", patient_names(user) or [""]], "center": ["in", centers(user) or [""]], "active": 1}
	if "CC Professional" in frappe.get_roles(user or frappe.session.user):
		filters["practitioner"] = practitioner_for(user) or ""
	return names_condition("CC Patient Assignment", frappe.get_all("CC Patient Assignment", filters=filters, pluck="name"))


def branch_query(user=None):
	return "" if is_manager(user) else names_condition("Branch", centers(user))


def membership_permission(doc, user=None, permission_type=None):
	if is_manager(user):
		return None
	if not enabled(user) or doc.user != (user or frappe.session.user) or permission_type not in ("read", "select"):
		return False
	return None


def assignment_permission(doc, user=None, permission_type=None):
	if is_manager(user):
		return None
	if permission_type not in ("read", "select") or not enabled(user) or not doc.active or doc.center not in centers(user) or doc.patient not in patient_names(user):
		return False
	if "CC Professional" in frappe.get_roles(user or frappe.session.user) and doc.practitioner != practitioner_for(user):
		return False
	return None


def branch_permission(doc, user=None, permission_type=None):
	if is_manager(user):
		return None
	return None if doc.name in centers(user) and permission_type in ("read", "select") else False
