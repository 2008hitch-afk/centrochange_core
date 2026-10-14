"""Offline contract tests for the operational-center boundary.

The shared Site is intentionally untouched: these tests use a fake Frappe DB.
"""

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2] / "app/centrochange_core/centrochange_core"


class Denied(Exception):
    pass


class FakeBranch:
    def __init__(self, name="Centro B", active=0):
        self.name = name
        self.doctype = "Branch"
        self.cc_operational = active
        self.saved = False

    def save(self, **_kwargs):
        self.saved = True

    def get(self, key):
        return getattr(self, key)


class CenterStateTests(unittest.TestCase):
    def setUp(self):
        self.branch = FakeBranch()
        self.audit = []
        self.manager = True
        self.conf = {}
        self.other = "Centro A"

        frappe = types.ModuleType("frappe")
        frappe.PermissionError = Denied
        frappe.conf = self.conf
        frappe.flags = {}
        frappe.whitelist = lambda **_kw: lambda fn: fn
        frappe.throw = lambda message, *_args: (_ for _ in ()).throw(Denied(message))
        frappe.get_doc = lambda *_args, **_kw: self.branch
        frappe.get_list = lambda *_args, **_kw: [{"name": "Centro A", "cc_operational": 1}]
        frappe.db = types.SimpleNamespace(get_value=lambda *_args, **_kw: self.other)

        audit = types.ModuleType("centrochange_core.security.audit")
        audit.append = lambda *args: self.audit.append(args)
        audit.atomic = lambda fn: fn
        @contextmanager
        def internal_write(_flag):
            yield
        audit.internal_write = internal_write

        guards = types.ModuleType("centrochange_core.security.guards")
        guards.is_manager = lambda: self.manager
        lifecycle = types.ModuleType("centrochange_core.security.lifecycle")
        lifecycle.lock = lambda: None

        modules = {"frappe": frappe, "centrochange_core": types.ModuleType("centrochange_core"),
                   "centrochange_core.security": types.ModuleType("centrochange_core.security"),
                   audit.__name__: audit, guards.__name__: guards, lifecycle.__name__: lifecycle}
        self.patch = patch.dict(sys.modules, modules)
        self.patch.start()
        spec = importlib.util.spec_from_file_location("cc_center_state_test", ROOT / "security/center_state.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        self.patch.stop()

    def test_manager_can_deactivate_second_center_with_audit(self):
        self.branch.cc_operational = 1
        result = self.module.set_operational("Centro B", "0", "Sede futura")
        self.assertEqual(result, {"center": "Centro B", "active": 0, "replay": False})
        self.assertTrue(self.branch.saved)
        self.assertEqual(self.audit[0][0], "CENTER_OPERATIONAL_STATE")
        self.assertEqual(self.audit[0][-1], "Sede futura")

    def test_activation_requires_explicit_site_gate(self):
        with self.assertRaisesRegex(Denied, "decisione"):
            self.module.set_operational("Centro B", "1", "Preparo la sede")
        self.assertFalse(self.branch.saved)
        self.assertEqual(self.audit, [])

    def test_replay_is_idempotent(self):
        result = self.module.set_operational("Centro B", "0", "Già inattiva")
        self.assertTrue(result["replay"])
        self.assertFalse(self.branch.saved)
        self.assertEqual(self.audit, [])

    def test_cannot_deactivate_last_operational_center(self):
        self.branch.cc_operational = 1
        self.other = None
        with self.assertRaisesRegex(Denied, "almeno una"):
            self.module.set_operational("Centro B", "0", "Richiesta")
        self.assertFalse(self.branch.saved)

    def test_non_manager_cannot_list_or_change_state(self):
        self.manager = False
        with self.assertRaises(Denied):
            self.module.list_centers()
        with self.assertRaises(Denied):
            self.module.set_operational("Centro B", "0", "Richiesta")

    def test_direct_branch_change_is_denied(self):
        previous = FakeBranch(active=1)
        with self.assertRaisesRegex(Denied, "tracciata"):
            self.module.protect_operational_state(self.branch, previous)

    def test_invalid_or_missing_reason_is_denied(self):
        for active, reason in (("2", "test"), ("0", "")):
            with self.assertRaises(Denied):
                self.module.set_operational("Centro B", active, reason)
        self.assertEqual(self.audit, [])


class OperationalGuardTests(unittest.TestCase):
    def setUp(self):
        self.fr = types.ModuleType("frappe")
        self.fr.PermissionError = Denied
        self.fr.flags = {}
        self.fr.session = types.SimpleNamespace(user="manager@example.invalid")
        self.fr.db = types.SimpleNamespace(get_value=lambda _dt, center, _field, **_kw: int(center == "Centro A"))
        self.fr.throw = lambda message, *_args: (_ for _ in ()).throw(Denied(message))
        self.patch = patch.dict(sys.modules, {"frappe": self.fr})
        self.patch.start()
        spec = importlib.util.spec_from_file_location("cc_guard_test", ROOT / "security/guards.py")
        self.guards = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.guards)

    def tearDown(self):
        self.patch.stop()

    def test_inactive_center_denied_even_to_manager(self):
        self.guards.require_operational_center("Centro A")
        with self.assertRaisesRegex(Denied, "non è operativa"):
            self.guards.require_operational_center("Centro B")

    def test_write_guard_checks_operational_state_but_read_scope_is_separate(self):
        with patch.object(self.guards, "require_center"), \
             patch.object(self.guards, "is_manager", return_value=True):
            self.guards.require_center("Centro B")
            with self.assertRaises(Denied):
                self.guards.require_operations("Centro B")

    def test_selector_filters_branch_and_membership(self):
        self.guards.enabled = lambda *_args: True
        self.guards.is_manager = lambda *_args: False
        self.guards.centers = lambda *_args: ["Centro A", "Centro B"]
        with patch.object(self.guards, "current_rows", return_value=[{"name": "Centro A"}]) as rows:
            self.guards.operational_centers()
        self.assertEqual(rows.call_args.kwargs["filters"],
                         {"cc_operational": 1, "name": ["in", ["Centro A", "Centro B"]]})


if __name__ == "__main__":
    unittest.main()
