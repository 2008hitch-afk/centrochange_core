"""Offline service contract for the contextual payment hold; not live Frappe evidence."""
from copy import deepcopy
from datetime import date, datetime, time, timezone
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/scheduling/booking.py'


class PaymentOverrideContractTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.admin = True
        self.fail_move = False
        self.doc = types.SimpleNamespace(name='APP-NEW', patient='PAT-1', practitioner='PRO-1',
            cc_center='CENTER-A', appointment_date=date(2026, 11, 1), appointment_time=time(9),
            check_permission=lambda permission: None)
        self.debts = [
            {'doctype': 'Sales Invoice', 'name': 'INV-1', 'center': 'CENTER-A',
             'amount': 80, 'currency': 'EUR', 'due_date': date(2026, 10, 1),
             'original_due_date': date(2026, 10, 1), 'deadline': datetime(2026, 10, 1, tzinfo=timezone.utc)},
            {'doctype': 'Patient Appointment', 'name': 'APP-OLD', 'center': 'CENTER-B',
             'amount': 40, 'currency': 'EUR', 'due_date': date(2026, 10, 2),
             'original_due_date': date(2026, 10, 2), 'deadline': datetime(2026, 10, 2, tzinfo=timezone.utc)},
        ]
        frappe = types.ModuleType('frappe')
        frappe.PermissionError = PermissionError
        frappe.whitelist = lambda **kwargs: lambda fn: fn
        frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        frappe.get_doc = lambda *args, **kwargs: self.doc
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(str(value))
        utils.get_time = lambda value: value if isinstance(value, time) else time.fromisoformat(str(value))
        utils.flt = float
        audit = types.ModuleType('centrochange_core.security.audit')

        def atomic(fn):
            def wrapped(*args, **kwargs):
                before = deepcopy(self.events)
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    self.events[:] = before
                    raise
            return wrapped

        audit.atomic = atomic
        audit.append = lambda *args: None
        audit.internal_write = lambda *args: None
        guards = types.ModuleType('centrochange_core.security.guards')
        for name in ('enabled', 'is_manager', 'roles', 'require_patient', 'require_center', 'current_rows'):
            setattr(guards, name, lambda *args, **kwargs: None)
        lifecycle = types.ModuleType('centrochange_core.security.lifecycle')
        lifecycle.lock = lambda: None
        operations = types.ModuleType('centrochange_core.operations.lifecycle')
        operations.ROME = timezone.utc
        operations.now_utc = lambda: datetime(2026, 10, 23, tzinfo=timezone.utc)
        operations.start_utc = lambda doc: datetime.combine(utils.getdate(doc.appointment_date),
            utils.get_time(doc.appointment_time), tzinfo=timezone.utc)
        availability = types.ModuleType('centrochange_core.scheduling.availability')
        availability.require_practitioner = lambda *args: None
        collections = types.ModuleType('centrochange_core.finance.collections')
        collections._booking_debts = lambda patient: self.debts
        collections.override = lambda patient, center, doctype, name, due, key, reason: self.events.append((center, doctype, name, due))
        finance = types.ModuleType('centrochange_core.finance.guards')
        finance.allowed = lambda **kwargs: self.admin
        finance.patient_context = lambda *args, **kwargs: None if self.admin else (_ for _ in ()).throw(PermissionError())
        modules = {'frappe': frappe, 'frappe.utils': utils,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.audit': audit,
            'centrochange_core.security.guards': guards,
            'centrochange_core.security.lifecycle': lifecycle,
            'centrochange_core.operations': types.ModuleType('centrochange_core.operations'),
            'centrochange_core.operations.lifecycle': operations,
            'centrochange_core.scheduling': types.ModuleType('centrochange_core.scheduling'),
            'centrochange_core.scheduling.availability': availability,
            'centrochange_core.finance': types.ModuleType('centrochange_core.finance'),
            'centrochange_core.finance.collections': collections,
            'centrochange_core.finance.guards': finance}
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.scheduling.booking', SOURCE)
        self.booking = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.booking
        spec.loader.exec_module(self.booking)
        self.booking.require_booking = lambda *args: None
        self.booking.reschedule = self._move

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.scheduling.booking', None)

    def _move(self, *args):
        if self.fail_move:
            raise ValueError('Slot non disponibile')
        if self.doc.appointment_date == date.fromisoformat(args[1]) and self.doc.appointment_time == time.fromisoformat(args[2]):
            return {'name': args[0], 'replay': True}
        self.doc.appointment_date = date.fromisoformat(args[1])
        self.doc.appointment_time = time.fromisoformat(args[2])
        self.events.append(('move', args[0]))
        return {'name': args[0], 'replay': False}

    @staticmethod
    def references():
        return [{'reference_doctype': 'Patient Appointment', 'reference_name': 'APP-OLD'},
                {'reference_doctype': 'Sales Invoice', 'reference_name': 'INV-1'}]

    def submit(self, refs=None):
        return self.booking.reschedule_with_payment_override('APP-NEW', '2026-11-10', '10:00',
            'Spostamento', 'Motivo amministrativo', '2026-11-10', 'request-1',
            self.references() if refs is None else refs)

    def test_unpaid_positions_do_not_block_reschedule_preview(self):
        preview = self.booking.reschedule_payment_blockers('APP-NEW', '2026-11-10', '10:00')
        self.assertEqual(preview, {'blocked': False, 'can_override': False, 'debts': []})
        self.assertEqual(self.events, [])

    def test_obsolete_override_cannot_be_used_to_bypass_guards(self):
        with self.assertRaises(PermissionError):
            self.submit()
        self.assertEqual(self.events, [])

    def test_unpaid_positions_do_not_reveal_details_to_professional(self):
        self.admin = False
        self.assertEqual(self.booking.reschedule_payment_blockers('APP-NEW', '2026-11-10', '10:00'),
                         {'blocked': False, 'can_override': False, 'debts': []})


if __name__ == '__main__':
    unittest.main()
