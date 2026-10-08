"""Append-only business events; access controlled by the audit DocType."""

from contextlib import contextmanager
import json

import frappe


@contextmanager
def internal_write(flag):
	previous = frappe.flags.get(flag)
	frappe.flags[flag] = True
	try:
		yield
	finally:
		frappe.flags[flag] = previous


def serialize(value):
	return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def atomic(function):
	"""Roll back a failed service even when its internal caller catches the error."""
	from functools import wraps

	@wraps(function)
	def wrapped(*args, **kwargs):
		point = "cc_" + frappe.generate_hash(length=12)
		frappe.db.savepoint(point)
		try:
			return function(*args, **kwargs)
		except Exception:
			frappe.db.rollback(save_point=point)
			raise
	return wrapped


def append(event, doctype, name, before, after, reason):
	if not reason or not reason.strip():
		frappe.throw("A business reason is required")
	with internal_write("cc_audit_write"):
		return frappe.get_doc({
			"doctype": "CC Audit Event", "event_type": event,
			"actor": frappe.session.user, "event_time": frappe.utils.now_datetime(),
			"reference_doctype": doctype, "reference_name": name,
			"before_state": serialize(before), "after_state": serialize(after),
			"reason": reason,
		}).insert(ignore_permissions=True).name


def immutable(doc, method=None):
	if method == "on_trash" or not doc.is_new() or not frappe.flags.get("cc_audit_write"):
		frappe.throw("Business audit events are append-only and service-controlled", frappe.PermissionError)
