import frappe

from centrochange_core.security.guards import (
	centers, enabled, is_manager, names_condition, patient_names, practitioner_for,
)


def patient_query(user=None):
	return "" if is_manager(user) else names_condition("Patient", patient_names(user))


def patient_permission(doc, user=None, ptype=None):
	if is_manager(user):
		return True
	user = user or frappe.session.user
	if doc.is_new() and ptype == "create":
		roles = frappe.get_roles(user)
		return True if enabled(user) and centers(user) and "CC Secretariat" in roles and "CC Professional" not in roles else False
	if not enabled(user) or doc.name not in patient_names(user):
		return False
	if ptype in ("delete", "share", "export", "import", "create"):
		return False
	return True


def practitioner_query(user=None):
	if is_manager(user):
		return ""
	name = _active_practitioner(user)
	return names_condition("Healthcare Practitioner", [name] if name else [])


def _active_practitioner(user=None):
	user = user or frappe.session.user
	if not enabled(user) or "CC Professional" not in frappe.get_roles(user):
		return None
	name = practitioner_for(user)
	if not name:
		return None
	return name if any(frappe.db.get_value("Branch", center, "cc_operational") for center in centers(user)) else None


def practitioner_permission(doc, user=None, ptype=None):
	if is_manager(user):
		return True
	if doc.name != _active_practitioner(user) or ptype not in ("read", "select"):
		return False
	return True


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


def membership_permission(doc, user=None, ptype=None):
	if is_manager(user):
		return True
	if not enabled(user) or doc.user != (user or frappe.session.user) or ptype not in ("read", "select"):
		return False
	return True


def assignment_permission(doc, user=None, ptype=None):
	if is_manager(user):
		return True
	if ptype not in ("read", "select") or not enabled(user) or not doc.active or doc.center not in centers(user) or doc.patient not in patient_names(user):
		return False
	if "CC Professional" in frappe.get_roles(user or frappe.session.user) and doc.practitioner != practitioner_for(user):
		return False
	return True


def branch_permission(doc, user=None, ptype=None):
	if is_manager(user):
		return True
	return True if doc.name in centers(user) and ptype in ("read", "select") else False
