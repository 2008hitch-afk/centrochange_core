"""Offline boundaries for direct and legacy practitioner center scopes."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/security/guards.py'


class PractitionerCenterGuardTest(unittest.TestCase):
    def setUp(self):
        self.fake = types.ModuleType('frappe')
        self.modules = patch.dict(sys.modules, {'frappe': self.fake})
        self.modules.start()
        spec = importlib.util.spec_from_file_location('cc_practitioner_center_guards', SOURCE)
        self.guards = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.guards)

    def tearDown(self):
        self.modules.stop()

    def test_no_memberships_cannot_match_empty_user_of_other_center(self):
        calls = []
        def rows(doctype, filters=None, fields=None, pluck=None):
            calls.append((doctype, filters))
            if doctype == 'CC Center Membership':
                return []
            if filters == {'cc_profile_center': 'B'}:
                return []
            raise AssertionError('Must not query legacy users with an empty sentinel')
        self.guards.current_rows = rows
        self.assertEqual(self.guards.practitioner_names_for_center('B'), [])
        self.assertEqual(len(calls), 2)

    def test_accountless_direct_scope_does_not_grant_other_center(self):
        doc = types.SimpleNamespace(user_id=None, get=lambda key: 'A' if key == 'cc_profile_center' else None)
        self.assertTrue(self.guards.practitioner_in_center(doc, 'A'))
        self.assertFalse(self.guards.practitioner_in_center(doc, 'B'))

    def test_disabled_linked_user_does_not_bypass_guard(self):
        doc = types.SimpleNamespace(user_id='u', get=lambda key: 'A' if key == 'cc_profile_center' else None)
        self.guards.enabled = lambda user: False
        self.assertFalse(self.guards.practitioner_in_center(doc, 'A'))

if __name__ == '__main__':
    unittest.main()
