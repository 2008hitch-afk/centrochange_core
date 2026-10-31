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
		frappe.throw("Un account anonimo o disattivato non può modificare gli accessi.", frappe.PermissionError)


def _active_value(value):
	"""Reject malformed states instead of coercing them into a revocation."""
	if isinstance(value, bool):
		return int(value)
	if str(value).strip() not in ("0", "1"):
		frappe.throw("Lo stato richiesto non è valido.")
	return int(str(value).strip())


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
	active = _active_value(active)
	if active not in (0, 1) or user in ("Guest", "Administrator"):
		frappe.throw("L’appartenenza operativa alla sede non è valida.")
	name = frappe.db.get_value("CC Center Membership", {"user": user, "center": center}, for_update=True)
	doc = frappe.get_doc("CC Center Membership", name, for_update=True) if name else frappe.get_doc({
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
		frappe.throw("Lo stato dell’assegnazione non è valido.")
	if practitioner and active:
		identity = frappe.get_doc("Healthcare Practitioner", practitioner, for_update=True)
		if identity.status != "Active" or not identity.user_id or not enabled(identity.user_id) or center not in centers(identity.user_id):
			frappe.throw("Il professionista deve essere attivo e assegnato a questa sede.")
	filters = {"patient": patient, "center": center, "practitioner": practitioner or ["is", "not set"]}
	name = frappe.db.get_value("CC Patient Assignment", filters, for_update=True)
	doc = frappe.get_doc("CC Patient Assignment", name, for_update=True) if name else frappe.get_doc({
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
		frappe.throw("La riassegnazione richiede due professionisti diversi.")
	# A stale selection must never grant the new professional access while the
	# actual previous assignment remains active. Lock the current row first.
	if not frappe.db.get_value('CC Patient Assignment', {
		'patient': patient, 'center': center, 'practitioner': old_practitioner, 'active': 1,
	}, 'name', for_update=True):
		frappe.throw('Il professionista precedente non è più assegnato: aggiorna la scheda.')
	# Both operations remain in the same request transaction: deny before granting.
	set_assignment(patient, center, old_practitioner, 0, reason)
	return set_assignment(patient, center, new_practitioner, 1, reason)


@frappe.whitelist(methods=["POST"])
@atomic
def set_practitioner_state(practitioner, active, reason):
	lock()
	require_manager()
	doc = frappe.get_doc("Healthcare Practitioner", practitioner, for_update=True)
	active = _active_value(active)
	if active not in (0, 1) or doc.user_id in (None, "", "Guest", "Administrator"):
		frappe.throw("Serve un account operativo valido e collegato.")
	user = frappe.get_doc("User", doc.user_id, for_update=True)
	if "CC Professional" not in roles(user.name):
		frappe.throw("L’account non appartiene a un professionista Centro Change.")
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
	doc = frappe.get_doc("Healthcare Practitioner", practitioner, for_update=True)
	if new_user in ("Administrator", "Guest") or not enabled(new_user) or "CC Professional" not in roles(new_user):
		frappe.throw("Il sostituto deve essere un professionista Centro Change attivo.")
	old_user = doc.user_id
	if old_user == new_user:
		return {"user": new_user}
	if old_user in ("Administrator", "Guest"):
		frappe.throw("Un account tecnico integrato non può essere sostituito.")
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
		frappe.throw("Le relazioni di accesso richiedono il servizio autorizzato Centro Change.", frappe.PermissionError)


def protect_share(doc, method=None):
	if doc.share_doctype=='File':
		from centrochange_core.finance.files import managed
		if managed(frappe.get_doc('File',doc.share_name)):
			frappe.throw('I documenti finanziari non possono essere condivisi manualmente.',frappe.PermissionError)
	if doc.share_doctype=='Communication' and frappe.db.get_value('Communication',doc.share_name,'reference_doctype')=='CC Payment Notice':
		frappe.throw('La comunicazione di pagamento non può essere condivisa fuori dal suo ambito.',frappe.PermissionError)
	if doc.share_doctype in ('CC Economic Source Link','Customer','Supplier','Cost Center','Account','Sales Invoice','Purchase Invoice','Payment Entry','GL Entry','Payment Ledger Entry','Bank Transaction','Bank Account','CC Payment Agreement','CC Payment Override','CC Payment Notice','CC Incoming Invoice','CC Compensation Rule','CC Professional Expectation','CC Professional Comparison','CC Admin Exception','CC Fiscal Transaction','CC Fiscal Attempt','CC TS Input Review'):
		frappe.throw('La condivisione contabile non può ampliare l’accesso Finance.',frappe.PermissionError)
	if doc.share_doctype == "CC Private Note":
		frappe.throw("Le note riservate non possono essere condivise.", frappe.PermissionError)
	if doc.share_doctype in ("Patient", "Healthcare Practitioner") and not frappe.flags.get("cc_permission_write"):
		frappe.throw("La condivisione dei dati clinici è gestita dal servizio autorizzato.", frappe.PermissionError)


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
		frappe.throw("I permessi del professionista sono gestiti dal servizio autorizzato.", frappe.PermissionError)


def protect_user_lifecycle(doc, method=None):
	previous = doc.get_doc_before_save()
	if previous and previous.enabled != doc.enabled and frappe.db.exists("Healthcare Practitioner", {"user_id": doc.name}) and not frappe.flags.get("cc_permission_write"):
		frappe.throw("L’attivazione del professionista richiede il servizio di gestione autorizzato.", frappe.PermissionError)
