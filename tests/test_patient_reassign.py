"""Offline guard regression; real Frappe authorization is exercised separately."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/security/lifecycle.py'


class ReassignmentGuardTests(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = PermissionError
        self.frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.db = types.SimpleNamespace(get_value=self.get_value)
        self.frappe.share = types.ModuleType('frappe.share')
        permissions = types.ModuleType('frappe.permissions')
        permissions.add_user_permission = lambda *args, **kwargs: None
        permissions.remove_user_permission = lambda *args, **kwargs: None
        audit = types.ModuleType('centrochange_core.security.audit')
        audit.append = lambda *args: None
        audit.atomic = lambda fn: fn
        audit.internal_write = lambda *args: None
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.centers = guards.enabled = guards.is_manager = guards.patient_names = guards.require_center = lambda *args: None
        guards.require_manager = lambda: None
        guards.require_operations = lambda center: None
        guards.current_rows = guards.roles = lambda *args, **kwargs: []
        modules = {
            'frappe': self.frappe, 'frappe.share': self.frappe.share, 'frappe.permissions': permissions,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.audit': audit, 'centrochange_core.security.guards': guards,
        }
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.security.lifecycle', SOURCE)
        self.lifecycle = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.lifecycle
        spec.loader.exec_module(self.lifecycle)
        self.lifecycle.lock = lambda: None
        self.calls = []
        self.lifecycle.set_assignment = lambda *args: self.calls.append(args)
        self.old_active = 0

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.security.lifecycle', None)

    def get_value(self, doctype, filters, fieldname=None, **kwargs):
        if doctype == 'CC Patient Assignment':
            return 'ASSIGN-OLD' if self.old_active == 1 and filters.get('active') == 1 else None
        return None

    def test_stale_old_practitioner_does_not_grant_new_access(self):
        with self.assertRaises((ValueError, PermissionError)):
            self.lifecycle.reassign('PAT-1', 'CENTER-A', 'P-OLD', 'P-NEW', 'Synthetic test')
        self.assertEqual(self.calls, [])

    def test_current_old_practitioner_can_be_reassigned(self):
        self.old_active = 1
        self.lifecycle.reassign('PAT-1', 'CENTER-A', 'P-OLD', 'P-NEW', 'Synthetic test')
        self.assertEqual([row[2:4] for row in self.calls], [('P-OLD', 0), ('P-NEW', 1)])


if __name__ == '__main__':
    unittest.main()
