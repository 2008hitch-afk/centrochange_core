"""Supported Frappe v16 extensions; upstream controllers remain untouched."""

import frappe
from frappe.sessions import clear_sessions

from centrochange_core.security.guards import enabled, is_manager, require_manager
from centrochange_core.security.install import CLINICAL_FIELDS


class PatientMixin:
	def onload(self):
		from frappe.contacts.address_and_contact import load_address_and_contact
		load_address_and_contact(self)
		# Native Patient dashboard joins accounting without an explicit financial guard.
		if is_manager() or "CC Finance" in frappe.get_roles():
			self.load_dashboard_info()

	def validate(self):
		super().validate()
		previous = self.get_doc_before_save()
		for field in CLINICAL_FIELDS:
			if self.get(field) and (not previous or self.get(field) != previous.get(field)):
				frappe.throw("Clinical content belongs in contextual guarded records, not the shared patient identity")

	def on_trash(self):
		frappe.throw("Patient deletion requires a separately governed retention process", frappe.PermissionError)


class PractitionerMixin:
	def validate(self):
		self.user_id = self.user_id or None
		previous = self.get_doc_before_save()
		if not previous:
			require_manager()
		elif (previous.user_id != self.user_id or previous.status != self.status) and not frappe.flags.get("cc_permission_write"):
			frappe.throw("Practitioner lifecycle changes must use the controlled service", frappe.PermissionError)
		if self.user_id and (not enabled(self.user_id) and self.status == "Active"):
			frappe.throw("Active practitioner requires an enabled principal")
		super().validate()

	def on_update(self):
		# Native on_update only adds a User Permission even when Disabled. The supported
		# extension replaces that grant with the reconciler registered as a doc event.
		pass


class ManagedShareMixin:
	def after_insert(self):
		if self.share_doctype == "Patient" and frappe.flags.get("cc_permission_write"):
			return  # Native shared comments would expose assignment audit on the Patient.
		return super().after_insert()

	def on_trash(self):
		if self.share_doctype == "Patient" and frappe.flags.get("cc_permission_write"):
			return
		return super().on_trash()


class UserMixin:
	def _is_cc_user(self):
		return bool(frappe.db.exists("Healthcare Practitioner", {"user_id": self.name})
			or frappe.db.exists("CC Center Membership", {"user": self.name})
			or any(role.role.startswith("CC ") for role in self.roles))

	def check_enable_disable(self):
		if not self._is_cc_user():
			return super().check_enable_disable()
		# Native logout commits immediately. Defer session deletion until the permission
		# transaction succeeds, while preserving native notification/field validation.
		manager = getattr(frappe.local, "login_manager", None)
		frappe.local.login_manager = None
		try:
			return super().check_enable_disable()
		finally:
			frappe.local.login_manager = manager

	def has_value_changed(self, fieldname):
		if fieldname == "user_type" and getattr(self, "_cc_defer_user_type_logout", False):
			return False
		return super().has_value_changed(fieldname)

	def on_update(self):
		if not self._is_cc_user():
			return super().on_update()
		invalidate = not self.enabled or super().has_value_changed("user_type")
		self._cc_defer_user_type_logout = True
		try:
			super().on_update()
		finally:
			self._cc_defer_user_type_logout = False
		if invalidate:
			user = self.name
			previous = self.get_doc_before_save()
			old_type = previous.user_type if previous else self.user_type
			def invalidate_committed_state():
				state = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
				if state and (not state.enabled or state.user_type != old_type):
					clear_sessions(user=user, force=True)
			frappe.db.after_commit.add(invalidate_committed_state)
