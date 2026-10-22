"""Offline regression for stale Agenda availability submissions; no Frappe runtime."""
from datetime import time
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/scheduling/availability.py'


class ScheduleConcurrencyTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType('frappe')
        frappe.whitelist = lambda **kwargs: lambda fn: fn
        frappe.PermissionError = PermissionError
        frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        frappe.db = types.SimpleNamespace(get_value=lambda *args, **kwargs: 'SCHED-1')
        frappe.get_doc = lambda *args, **kwargs: types.SimpleNamespace(modified='2026-10-22 11:00:00')
        utils = types.ModuleType('frappe.utils')
        utils.get_time = lambda value: time.fromisoformat(str(value))
        audit = types.ModuleType('centrochange_core.security.audit')
        audit.atomic = lambda fn: fn
        audit.append = lambda *args: None
        audit.internal_write = lambda *args: None
        guards = types.ModuleType('centrochange_core.security.guards')
        for name in ('enabled', 'is_manager', 'centers', 'require_operations', 'roles'):
            setattr(guards, name, lambda *args: None)
        lifecycle = types.ModuleType('centrochange_core.security.lifecycle')
        lifecycle.lock = lambda: None
        modules = {'frappe': frappe, 'frappe.utils': utils,
                   'centrochange_core': types.ModuleType('centrochange_core'),
                   'centrochange_core.security': types.ModuleType('centrochange_core.security'),
                   'centrochange_core.security.audit': audit,
                   'centrochange_core.security.guards': guards,
                   'centrochange_core.security.lifecycle': lifecycle,
                   'centrochange_core.scheduling': types.ModuleType('centrochange_core.scheduling')}
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.scheduling.availability', SOURCE)
        self.availability = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.availability
        spec.loader.exec_module(self.availability)
        self.availability.require_practitioner = lambda *args: types.SimpleNamespace()

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.scheduling.availability', None)

    def test_stale_snapshot_rejected_before_schedule_mutation(self):
        slots = [{'day': 'Monday', 'from_time': '09:00', 'to_time': '12:00'}]
        with self.assertRaisesRegex(ValueError, 'L’orario è cambiato'):
            self.availability.set_schedule('PRO-A', 'CENTRO-A', slots, 'Prova sintetica',
                                           expected_modified='2026-10-22 10:00:00')

    def test_new_schedule_race_rejected_before_schedule_mutation(self):
        slots = [{'day': 'Monday', 'from_time': '09:00', 'to_time': '12:00'}]
        with self.assertRaisesRegex(ValueError, 'L’orario è cambiato'):
            self.availability.set_schedule('PRO-A', 'CENTRO-A', slots, 'Prova sintetica', expected_modified='')


if __name__ == '__main__':
    unittest.main()
