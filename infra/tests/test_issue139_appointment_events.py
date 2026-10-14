"""Verify the appointment timeline cannot expose another patient or clinical note."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2] / "app/centrochange_core/centrochange_core"


class Denied(Exception):
    pass


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.checked = []
        self.reads = []
        frappe = types.ModuleType("frappe")
        frappe.PermissionError = Denied
        frappe.whitelist = lambda **_kw: lambda fn: fn
        frappe.throw = lambda message, *_args: (_ for _ in ()).throw(Denied(message))
        doc = types.SimpleNamespace(name="APP-001", patient="PAT-001", cc_center="Centro A",
                                    check_permission=lambda action: self.checked.append(action))
        frappe.get_doc = lambda *_args: doc
        util = types.ModuleType("frappe.utils")
        util.getdate = lambda value: value
        util.get_time = lambda value: value
        frappe.utils = util
        guards = types.ModuleType("centrochange_core.security.guards")
        guards.enabled = lambda: True
        guards.is_manager = lambda: False
        guards.roles = lambda: ["CC Professional"]
        guards.require_center = lambda *_args: None
        guards.current_rows = lambda *args, **kwargs: self.reads.append((args, kwargs)) or [
            types.SimpleNamespace(event_type="APPOINTMENT_RESCHEDULED", actor="operator",
                event_time="2026-10-14 10:00:00", reason="Correzione", before_state='{"appointment_time":"09:00:00","patient":"SECRET"}',
                after_state='{"appointment_time":"10:00:00","patient":"SECRET"}')]
        notes = types.ModuleType("centrochange_core.operations.notes")
        notes.require_context = lambda *_args: None
        modules = {"frappe": frappe, "frappe.utils": util,
                   "centrochange_core": types.ModuleType("centrochange_core"),
                   "centrochange_core.security": types.ModuleType("centrochange_core.security"),
                   "centrochange_core.operations": types.ModuleType("centrochange_core.operations"),
                   guards.__name__: guards, notes.__name__: notes}
        self.patch = patch.dict(sys.modules, modules)
        self.patch.start()
        spec = importlib.util.spec_from_file_location("cc_workspace_test", ROOT / "operations/workspace.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.notes = notes

    def tearDown(self):
        self.patch.stop()

    def test_scoped_timeline_strips_unapproved_fields(self):
        events = self.module.appointment_events("APP-001")
        self.assertEqual(self.checked, ["read"])
        self.assertEqual(self.reads[0][0][1]["reference_name"], "APP-001")
        self.assertEqual(events[0]["before"], {"appointment_time": "09:00:00"})
        self.assertEqual(events[0]["after"], {"appointment_time": "10:00:00"})

    def test_scope_denial_happens_before_audit_query(self):
        self.module.require_context = lambda *_args: (_ for _ in ()).throw(Denied("other center"))
        with self.assertRaises(Denied):
            self.module.appointment_events("APP-001")
        self.assertEqual(self.reads, [])


if __name__ == "__main__":
    unittest.main()
