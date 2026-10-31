"""Offline validation checks; real permission tests require isolated Frappe."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class InvalidState(Exception):
    pass


class AccessStateTest(unittest.TestCase):
    def test_malformed_state_never_becomes_revocation(self):
        frappe = types.ModuleType('frappe')
        frappe.throw = lambda message: (_ for _ in ()).throw(InvalidState(message))
        frappe.whitelist = lambda **kwargs: lambda fn: fn
        share = types.ModuleType('frappe.share')
        permissions = types.ModuleType('frappe.permissions')
        permissions.add_user_permission = permissions.remove_user_permission = lambda *args, **kwargs: None
        audit = types.ModuleType('centrochange_core.security.audit')
        audit.append = audit.internal_write = lambda *args, **kwargs: None
        audit.atomic = lambda fn: fn
        guards = types.ModuleType('centrochange_core.security.guards')
        for name in ('centers', 'enabled', 'is_manager', 'patient_names', 'require_center', 'require_manager', 'require_operations', 'require_operational_center', 'current_rows', 'roles'):
            setattr(guards, name, lambda *args, **kwargs: None)
        modules = {'frappe': frappe, 'frappe.share': share, 'frappe.permissions': permissions,
                   'centrochange_core.security.audit': audit, 'centrochange_core.security.guards': guards}
        path = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/security/lifecycle.py'
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('audit10_lifecycle', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for value, expected in ((0, 0), (1, 1), ('0', 0), ('1', 1), (' 1 ', 1)):
                self.assertEqual(module._active_value(value), expected)
            for value in ('invalid', '', None, '2', '-1', '0.0'):
                with self.subTest(value=value), self.assertRaises(InvalidState):
                    module._active_value(value)


if __name__ == '__main__':
    unittest.main()
