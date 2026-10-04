"""Transactional services for center membership, patient assignment and principals."""

import frappe
import frappe.share
from frappe.permissions import add_user_permission, remove_user_permission

from centrochange_core.security.audit import append, atomic, internal_write
from centrochange_core.security.guards import (
	centers, enabled, is_manager, patient_names, require_center, require_manager, require_operations, current_rows, roles,
)


def lock():
	# This product-owned Role row serializes permission mutations until transaction commit.
	# No named lock released before commit, no implicit commit inside a service.
	frappe.db.sql("SELECT name FROM tabRole WHERE name='CC Manager' FOR UPDATE")
	frappe.flags.cc_permission_current_read = True
	# Current read after acquiring the serialization row, including waiting requests.
	if frappe.session.user == "Guest" or not frappe.db.get_value("User", frappe.session.user, "enabled", for_update=True):
		frappe.throw("Disabled or anonymous principal cannot mutate permissions", frappe.PermissionError)


def reconcile_user(user):
	"""Rebuild only managed Patient shares and Practitioner permissions for one principal."""
	lock()
	with internal_write("cc_permission_write"):
		for name in current_rows("DocShare", filters={"share_doctype": "Patient", "user": user}, pluck="name"):
			frappe.delete_doc("DocShare", name, ignore_permissions=True,
				flags={"ignore_share_permission": True})
		if enabled(user):
			for patient in set(patient_names(user)):
				write = int("CC Secretariat" in roles(user) and "CC Professional" not in roles(user))
				frappe.share.add_docshare("Patient", patient, user=user, read=1, write=write,
					flags={"ignore_share_permission": True})
		for permission in current_rows("User Permission", filters={"user": user, "allow": "Healthcare Practitioner"},
			fields=["for_value"]):
			remove_user_permission("Healthcare Practitioner", permission.for_value, user, ignore_permissions=True)
		if enabled(user):
			for name in current_rows("Healthcare Practitioner", filters={"user_id": user, "status": "Active"}, pluck="name"):
				add_user_permission("Healthcare Practitioner", name, user, ignore_permissions=True)
	frappe.clear_cache(user=user)
	frappe.db.after_commit.add(lambda: frappe.clear_cache(user=user))


def reconcile_patient(patient):
	users = set(current_rows("DocShare", filters={"share_doctype": "Patient", "share_name": patient}, pluck="user"))
	assignments = current_rows("CC Patient Assignment", filters={"patient": patient, "active": 1},
		fields=["practitioner", "center"])
	for assignment in assignments:
		if assignment.practitioner:
			users.add(frappe.db.get_value("Healthcare Practitioner", assignment.practitioner, "user_id"))
		users.update(current_rows("CC Center Membership", filters={"center": assignment.center, "active": 1}, pluck="user"))
	for user in sorted(user for user in users if user):
		reconcile_user(user)


@frappe.whitelist(methods=["POST"])
@atomic
def set_membership(user, center, active, reason):
	lock()
	require_manager()
	active = int(frappe.utils.cint(active))
	if active not in (0, 1) or user in ("Guest", "Administrator"):
		frappe.throw("Invalid operational center membership")
	name = frappe.db.get_value("CC Center Membership", {"user": user, "center": center}, for_update=True)
	doc = frappe.get_doc("CC Center Membership", name) if name else frappe.get_doc({
		"doctype": "CC Center Membership", "user": user, "center": center,
	})
	before = {"active": doc.active} if name else None
	if name and int(doc.active) == active:
		return {"name": name, "active": active}
	with internal_write("cc_permission_write"):
		doc.active = active
		doc.save(ignore_permissions=True)
		reconcile_user(user)
	append("CENTER_MEMBERSHIP", doc.doctype, doc.name, before, {"active": active}, reason)
	return {"name": doc.name, "active": active}


@frappe.whitelist(methods=["POST"])
@atomic
def set_assignment(patient, center, practitioner=None, active=1, reason=None):
	lock()
	require_operations(center)
	active = int(frappe.utils.cint(active))
	if active not in (0, 1):
		frappe.throw("Invalid assignment state")
	if practitioner and active:
		identity = frappe.get_doc("Healthcare Practitioner", practitioner)
		if identity.status != "Active" or not identity.user_id or not enabled(identity.user_id) or center not in centers(identity.user_id):
			frappe.throw("Practitioner must be active and assigned to this center")
	filters = {"patient": patient, "center": center, "practitioner": practitioner or ["is", "not set"]}
	name = frappe.db.get_value("CC Patient Assignment", filters, for_update=True)
	doc = frappe.get_doc("CC Patient Assignment", name) if name else frappe.get_doc({
		"doctype": "CC Patient Assignment", "patient": patient, "center": center, "practitioner": practitioner,
	})
	before = {"active": doc.active} if name else None
	if name and int(doc.active) == active:
		return {"name": name, "active": active}
	with internal_write("cc_permission_write"):
		doc.active = active
		doc.save(ignore_permissions=True)
		reconcile_patient(patient)
	append("PATIENT_ASSIGNMENT", doc.doctype, doc.name, before, {"active": active}, reason)
	return {"name": doc.name, "active": active}


@frappe.whitelist(methods=["POST"])
@atomic
def reassign(patient, center, old_practitioner, new_practitioner, reason):
	lock()
	require_operations(center)
	if old_practitioner == new_practitioner:
		frappe.throw("Reassignment requires distinct practitioners")
	# Both operations remain in the same request transaction: deny before granting.
	set_assignment(patient, center, old_practitioner, 0, reason)
	return set_assignment(patient, center, new_practitioner, 1, reason)


@frappe.whitelist(methods=["POST"])
@atomic
def set_practitioner_state(practitioner, active, reason):
	lock()
	require_manager()
	doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	active = int(frappe.utils.cint(active))
	if active not in (0, 1) or doc.user_id in (None, "", "Guest", "Administrator"):
		frappe.throw("A valid linked operational principal is required")
	user = frappe.get_doc("User", doc.user_id)
	if "CC Professional" not in roles(user.name):
		frappe.throw("Principal is not a Centro Change professional")
	before = {"status": doc.status, "enabled": user.enabled}
	after = {"status": "Active" if active else "Disabled", "enabled": active}
	if before == after:
		return after
	with internal_write("cc_permission_write"):
		user.enabled = active
		user.save(ignore_permissions=True)
		doc.status = after["status"]
		doc.save(ignore_permissions=True)
		reconcile_user(user.name)
	append("PRACTITIONER_STATE", doc.doctype, doc.name, before, after, reason)
	return after


@frappe.whitelist(methods=["POST"])
@atomic
def replace_principal(practitioner, new_user, reason):
	lock()
	require_manager()
	doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	if new_user in ("Administrator", "Guest") or not enabled(new_user) or "CC Professional" not in roles(new_user):
		frappe.throw("Replacement must be an enabled Centro Change professional")
	old_user = doc.user_id
	if old_user == new_user:
		return {"user": new_user}
	if old_user in ("Administrator", "Guest"):
		frappe.throw("Cannot replace a built-in principal")
	# Reconciliation revokes the old principal and grants the new one in one transaction.
	with internal_write("cc_permission_write"):
		doc.user_id = new_user
		doc.save(ignore_permissions=True)
		if old_user:
			reconcile_user(old_user)
		reconcile_user(new_user)
	append("PRINCIPAL_REPLACED", doc.doctype, doc.name, {"user": old_user}, {"user": new_user}, reason)
	return {"user": new_user}


def protected_relationship(doc, method=None):
	if not frappe.flags.get("cc_permission_write"):
		frappe.throw("Permission relationships must use the Centro Change service", frappe.PermissionError)


def protect_share(doc, method=None):
	if doc.share_doctype in ("Patient", "Healthcare Practitioner") and not frappe.flags.get("cc_permission_write"):
		frappe.throw("Clinical identity shares are service-controlled", frappe.PermissionError)


def practitioner_updated(doc, method=None):
	previous = doc.get_doc_before_save()
	users = {doc.user_id, previous.user_id if previous else None}
	for user in sorted(user for user in users if user):
		reconcile_user(user)


def user_updated(doc, method=None):
	if doc.name not in ("Administrator", "Guest") and (
		frappe.db.exists("Healthcare Practitioner", {"user_id": doc.name})
		or frappe.db.exists("CC Center Membership", {"user": doc.name})
	):
		reconcile_user(doc.name)


def protect_user_permission(doc, method=None):
	if doc.allow == "Healthcare Practitioner" and not frappe.flags.get("cc_permission_write"):
		frappe.throw("Practitioner user permissions are service-controlled", frappe.PermissionError)


def protect_user_lifecycle(doc, method=None):
	previous = doc.get_doc_before_save()
	if previous and previous.enabled != doc.enabled and frappe.db.exists("Healthcare Practitioner", {"user_id": doc.name}) and not frappe.flags.get("cc_permission_write"):
		frappe.throw("Professional enable/disable must use the atomic lifecycle service", frappe.PermissionError)
