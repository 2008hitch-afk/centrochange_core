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


def operational_centers(user=None):
	"""Selectable centers only; historical read scopes still use ``centers``."""
	if not enabled(user):
		return []
	filters = {"cc_operational": 1}
	if not is_manager(user):
		filters["name"] = ["in", centers(user) or [""]]
	return current_rows("Branch", filters=filters, fields=["name", "branch"])


def require_operational_center(center):
	if not center or not frappe.db.get_value("Branch", center, "cc_operational",
			for_update=bool(frappe.flags.get("cc_permission_current_read"))):
		frappe.throw("La sede non è operativa: nuove operazioni non consentite.", frappe.PermissionError)


def require_center(center):
	if not is_manager() and center not in centers():
		frappe.throw("Centro Change center access denied", frappe.PermissionError)


def require_operations(center):
	require_center(center)
	require_operational_center(center)
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
	return frappe.db.get_values(doctype, filters={} if filters is None else filters, fieldname=pluck or fields or "name",
		as_dict=not bool(pluck), pluck=bool(pluck),
		for_update=bool(frappe.flags.get("cc_permission_current_read")))


def roles(user=None):
	user=user or frappe.session.user
	if frappe.flags.get("cc_permission_current_read"):
		names=current_rows("Has Role", {"parent":user,"parenttype":"User"}, pluck="role")
		return [name for name in names if not frappe.db.get_value("Role",name,"disabled",for_update=True)]
	return frappe.get_roles(user)


def patient_contexts(user=None):
	"""Exact patient/center pairs, never a Cartesian product of independent scopes."""
	user=user or frappe.session.user
	if not enabled(user):
		return set()
	filters={'active':1,'center':['in',centers(user) or ['']]}
	if 'CC Professional' in roles(user):
		filters['practitioner']=practitioner_for(user) or ''
	elif 'CC Secretariat' not in roles(user):
		return set()
	return {(row.patient,row.center) for row in current_rows('CC Patient Assignment',filters,fields=['patient','center'])}
