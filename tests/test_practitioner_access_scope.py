"""Offline guard regression; live Frappe/DB checks remain a separate gate."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/security/permissions.py'


class PractitionerAccessScopeTest(unittest.TestCase):
    def setUp(self):
        self.memberships = ['CENTRO-A']
        self.operational = True
        self.frappe = types.ModuleType('frappe')
        self.frappe.session = types.SimpleNamespace(user='pro@example.invalid')
        self.frappe.get_roles = lambda user: ['CC Professional']
        self.frappe.db = types.SimpleNamespace(get_value=lambda dt, name, field: int(self.operational) if dt == 'Branch' and field == 'cc_operational' else None)
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.centers = lambda user=None: self.memberships
        guards.enabled = lambda user=None: True
        guards.is_manager = lambda user=None: False
        guards.names_condition = lambda dt, names: 'own' if names else '1=0'
        guards.patient_names = lambda user=None: []
        guards.practitioner_for = lambda user=None: 'PRO-A'
        self.modules = patch.dict(sys.modules, {'frappe': self.frappe, 'centrochange_core': types.ModuleType('centrochange_core'), 'centrochange_core.security': types.ModuleType('centrochange_core.security'), 'centrochange_core.security.guards': guards})
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.security.permissions', SOURCE)
        self.permissions = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.permissions)

    def tearDown(self):
        self.modules.stop()

    def test_direct_doctype_read_revoked_with_membership(self):
        own = types.SimpleNamespace(name='PRO-A')
        self.assertEqual(self.permissions.practitioner_query(), 'own')
        self.assertTrue(self.permissions.practitioner_permission(own, ptype='read'))
        self.memberships = []
        self.assertEqual(self.permissions.practitioner_query(), '1=0')
        self.assertFalse(self.permissions.practitioner_permission(own, ptype='read'))

    def test_inactive_center_denies_direct_doctype_read(self):
        own = types.SimpleNamespace(name='PRO-A')
        self.operational = False
        self.assertEqual(self.permissions.practitioner_query(), '1=0')
        self.assertFalse(self.permissions.practitioner_permission(own, ptype='read'))


if __name__ == '__main__':
    unittest.main()
