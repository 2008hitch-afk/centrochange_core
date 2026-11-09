"""Regression for manager/practitioner User Permission reconciliation."""
import contextlib
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class DirectorReconcileTest(unittest.TestCase):
    def test_manager_has_no_practitioner_restriction_and_professional_keeps_it(self):
        f = types.ModuleType('frappe')
        f.share = types.ModuleType('frappe.share')
        f.share.add_docshare = lambda *a, **k: None
        f.whitelist = lambda **k: lambda fn: fn
        f.clear_cache = lambda **k: None
        f.db = types.SimpleNamespace(after_commit=types.SimpleNamespace(add=lambda cb: None))
        permissions = types.ModuleType('frappe.permissions')
        added, removed = [], []
        permissions.add_user_permission = lambda *a, **k: added.append(a)
        permissions.remove_user_permission = lambda *a, **k: removed.append(a)
        audit = types.ModuleType('centrochange_core.security.audit')
        audit.append = lambda *a, **k: None
        audit.atomic = lambda fn: fn
        audit.internal_write = lambda _: contextlib.nullcontext()
        guards = types.ModuleType('centrochange_core.security.guards')
        for name in ('centers', 'require_center', 'require_manager', 'require_operations', 'require_operational_center'):
            setattr(guards, name, lambda *a, **k: None)
        guards.enabled = lambda user: True
        guards.is_manager = lambda user=None: user == 'director'
        guards.roles = lambda user: ['CC Manager'] if user == 'director' else ['CC Professional']
        guards.patient_names = lambda user: []
        def rows(doctype, filters=None, **kwargs):
            if doctype == 'User Permission': return [types.SimpleNamespace(for_value='old')]
            if doctype == 'Healthcare Practitioner': return ['own']
            return []
        guards.current_rows = rows
        modules = {'frappe': f, 'frappe.share': f.share, 'frappe.permissions': permissions,
                   'centrochange_core.security.audit': audit, 'centrochange_core.security.guards': guards}
        path = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/security/lifecycle.py'
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('director_lifecycle', path)
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            mod.lock = lambda: None
            mod.reconcile_user('director')
            self.assertEqual(added, [])
            self.assertEqual(len(removed), 1)
            mod.reconcile_user('professional')
            self.assertEqual(added, [('Healthcare Practitioner', 'own', 'professional')])

if __name__ == '__main__':
    unittest.main()
