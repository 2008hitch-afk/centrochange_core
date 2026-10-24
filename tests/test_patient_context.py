"""Offline check that Manager reads still require a current patient/center link."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/operations/notes.py'


class PatientContextTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType('frappe')
        frappe.PermissionError = PermissionError
        frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        frappe.whitelist = lambda **kwargs: lambda fn: fn
        audit = types.ModuleType('centrochange_core.security.audit')
        audit.append = lambda *args: None
        audit.atomic = lambda fn: fn
        audit.internal_write = lambda *args: None
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.centers = guards.enabled = guards.names_condition = guards.patient_names = guards.patient_contexts = guards.practitioner_for = guards.roles = lambda *args: []
        guards.is_manager = lambda: True
        guards.require_center = guards.require_patient = lambda *args: None
        guards.current_rows = lambda *args, **kwargs: []
        self.modules = patch.dict(sys.modules, {
            'frappe': frappe,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.audit': audit,
            'centrochange_core.security.guards': guards,
            'centrochange_core.operations': types.ModuleType('centrochange_core.operations'),
        })
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.notes', SOURCE)
        self.notes = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.notes
        spec.loader.exec_module(self.notes)

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.operations.notes', None)

    def test_manager_cannot_read_patient_history_in_unassigned_center(self):
        with self.assertRaises(PermissionError):
            self.notes.require_context('PAT-B', 'CENTER-A')

    def test_manager_can_read_currently_assigned_patient(self):
        with patch.object(self.notes, 'current_rows', return_value=['ASSIGN-A']) as rows:
            self.notes.require_context('PAT-A', 'CENTER-A')
        self.assertEqual(rows.call_args.args, ('CC Patient Assignment',))
        self.assertEqual(rows.call_args.kwargs['filters'], {'patient': 'PAT-A', 'center': 'CENTER-A', 'active': 1})


if __name__ == '__main__':
    unittest.main()
