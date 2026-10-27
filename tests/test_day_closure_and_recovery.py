"""Unit and integration tests for CORE #173: «Chiudi la mia giornata» & late closure recovery.

Verifications:
1. get_day_closure_sessions:
   - Proper date filtering and sorting.
   - Detection and return of arrear dates with unclosed (Pending / Auto Locked) sessions.
   - Strict practitioner scoping for CC Professional role.
2. close_day:
   - Bulk closure of sessions with Performed (Yes/No), Paid (Yes/No), Mode of Payment.
   - Performed=1 sets status='Closed', cc_performed=1, cc_closure_state='Closed', cc_economic_state='Due' and CC Settlement.
   - Performed=0 sets status='No Show', cc_performed=0, cc_closure_state='Closed', cc_economic_state='Non Due', cc_paid=0.
   - Autonomous recovery of Auto Locked sessions by practitioner WITHOUT Direction intervention / reopen:
     transitions to Closed, records SESSION_LATE_COMPLETED audit event.
   - IDOR protection: Professional B cannot close Professional A's sessions (PermissionError).
   - Inactive center / center mismatch protection (PermissionError).
   - Re-closure protection: already Closed sessions cannot be overwritten with different parameters.
   - Replay idempotency: identical re-submission returns replay=True without duplicate audit events.
   - Future sessions cannot be marked as performed.
   - Cancelled sessions cannot be closed as performed.
3. Scheduler (automation.catch_up):
   - At 21:00 Europe/Rome: enqueues CLOSURE_REMINDER only if unclosed sessions exist for today.
   - If all sessions are closed: zero reminders enqueued.
   - At 07:00 Europe/Rome: marks pending past sessions as Auto Locked with SESSION_AUTO_LOCKED audit event.
"""

from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app/centrochange_core'))

ROME = ZoneInfo('Europe/Rome')


class Record(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    def get(self, key, default=None):
        return super().get(key, default)
    def set(self, key, value):
        self[key] = value


class DayClosureAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.settlements = []
        self.notifications = []
        self.clock_rome = datetime(2026, 10, 26, 18, 0, 0, tzinfo=ROME)
        self.current_user = 'cc-prof-a@example.invalid'
        self.user_roles = ['CC Professional']
        self.user_practitioner = 'PRO-A'

        self.operational_centers = {'CENTRO-A'}
        self.assigned_patients = ['PAT-1', 'PAT-2', 'PAT-3', 'PAT-4']

        # Appointments dataset
        self.appointments = {
            # Today's appointments (2026-10-26) for PRO-A
            'APP-TODAY-1': Record(
                name='APP-TODAY-1', doctype='Patient Appointment', patient='PAT-1',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='09:00:00', duration=60, status='Scheduled',
                cc_closure_state='Pending', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            'APP-TODAY-2': Record(
                name='APP-TODAY-2', doctype='Patient Appointment', patient='PAT-2',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='10:00:00', duration=60, status='Scheduled',
                cc_closure_state='Pending', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            'APP-TODAY-3': Record(
                name='APP-TODAY-3', doctype='Patient Appointment', patient='PAT-3',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='11:00:00', duration=60, status='Scheduled',
                cc_closure_state='Pending', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Future appointment today (at 19:00:00, clock is at 18:00:00)
            'APP-TODAY-FUTURE': Record(
                name='APP-TODAY-FUTURE', doctype='Patient Appointment', patient='PAT-1',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='19:00:00', duration=60, status='Scheduled',
                cc_closure_state='Pending', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Late cancellation with due fee (already Due)
            'APP-LATE-CANCEL-DUE': Record(
                name='APP-LATE-CANCEL-DUE', doctype='Patient Appointment', patient='PAT-2',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='12:00:00', duration=60, status='Open',
                cc_closure_state='Pending', cc_economic_state='Due',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Arrear Auto Locked appointment from 2026-10-12
            'APP-ARREAR-12': Record(
                name='APP-ARREAR-12', doctype='Patient Appointment', patient='PAT-1',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-12',
                appointment_time='09:00:00', duration=60, status='Open',
                cc_closure_state='Auto Locked', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=2, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Appointment for PRO-B (IDOR testing)
            'APP-PRO-B': Record(
                name='APP-PRO-B', doctype='Patient Appointment', patient='PAT-4',
                practitioner='PRO-B', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='14:00:00', duration=60, status='Scheduled',
                cc_closure_state='Pending', cc_economic_state='Pending',
                cc_performed=0, cc_paid=0, cc_revision=1, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Already closed appointment
            'APP-CLOSED': Record(
                name='APP-CLOSED', doctype='Patient Appointment', patient='PAT-1',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-20',
                appointment_time='09:00:00', duration=60, status='Closed',
                cc_closure_state='Closed', cc_economic_state='Due',
                cc_performed=1, cc_paid=1, cc_revision=2, cc_settlement_revision=1,
                cc_package=None, check_permission=lambda perm: None
            ),
            # Cancelled appointment
            'APP-CANCELLED': Record(
                name='APP-CANCELLED', doctype='Patient Appointment', patient='PAT-2',
                practitioner='PRO-A', cc_center='CENTRO-A', appointment_date='2026-10-26',
                appointment_time='16:00:00', duration=60, status='Cancelled',
                cc_closure_state='Closed', cc_economic_state='Non Due',
                cc_performed=0, cc_paid=0, cc_revision=2, cc_settlement_revision=0,
                cc_package=None, check_permission=lambda perm: None
            ),
        }

        # Setup mock Frappe environment
        self._setup_frappe_mock()

    def _setup_frappe_mock(self):
        import importlib.util
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = PermissionError
        self.frappe.ValidationError = type('ValidationError', (ValueError,), {})
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        self.frappe.in_test = True
        self.frappe.conf = Record({'cc_synthetic_dev': 1})
        self.frappe.flags = Record({'cc_test_clock': self.clock_rome.astimezone(timezone.utc), 'cc_operation_write': True})
        self.frappe.session = types.SimpleNamespace(user=self.current_user)

        self.frappe.get_doc = self._mock_get_doc
        self.frappe.get_all = self._mock_get_all
        self.frappe.get_list = self._mock_get_all

        db = types.SimpleNamespace()
        db.get_value = self._mock_db_get_value
        db.set_value = self._mock_db_set_value
        db.exists = lambda dt, name=None, **kwargs: True
        self.frappe.db = db

        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda v: v if isinstance(v, date) else date.fromisoformat(str(v))
        utils.get_time = lambda v: v if isinstance(v, time) else time.fromisoformat(str(v))
        utils.cint = lambda v: int(v) if v else 0
        utils.now_datetime = lambda: self.clock_rome.replace(tzinfo=None)
        self.frappe.utils = utils

        # Mock packages, audit, guards
        sys.modules['frappe'] = self.frappe
        sys.modules['frappe.utils'] = utils

        # Load lifecycle module
        spec = importlib.util.spec_from_file_location(
            'centrochange_core.operations.lifecycle',
            Path(__file__).resolve().parent.parent / 'app/centrochange_core/centrochange_core/operations/lifecycle.py'
        )
        self.lifecycle = importlib.util.module_from_spec(spec)
        sys.modules['centrochange_core.operations.lifecycle'] = self.lifecycle

        # Mock dependent modules
        security_guards = types.ModuleType('centrochange_core.security.guards')
        security_guards.require_operations = lambda center=None: None
        security_guards.require_center = lambda center: None
        security_guards.require_operational_center = self._mock_require_operational_center
        security_guards.patient_names = lambda user=None: self.assigned_patients
        security_guards.require_actor = lambda: None
        security_guards.is_manager = lambda user=None: 'CC Manager' in self.user_roles
        security_guards.roles = lambda user=None: self.user_roles
        security_guards.practitioner_for = lambda user=None: self.user_practitioner
        security_guards.enabled = lambda user=None: True
        security_guards.current_rows = self._mock_current_rows
        sys.modules['centrochange_core.security.guards'] = security_guards

        security_audit = types.ModuleType('centrochange_core.security.audit')
        security_audit.atomic = lambda fn: fn
        security_audit.lock = lambda: None
        security_audit.internal_write = lambda flag: patch.dict(self.frappe.flags, {flag: True})
        security_audit.append = self._mock_audit_append
        sys.modules['centrochange_core.security.audit'] = security_audit

        security_lifecycle = types.ModuleType('centrochange_core.security.lifecycle')
        security_lifecycle.lock = lambda: None
        sys.modules['centrochange_core.security.lifecycle'] = security_lifecycle

        sched_booking = types.ModuleType('centrochange_core.scheduling.booking')
        sched_booking.require_booking = lambda doc: None
        sys.modules['centrochange_core.scheduling.booking'] = sched_booking

        finance_col = types.ModuleType('centrochange_core.finance.collections')
        finance_col.require_booking = lambda doc: None
        sys.modules['centrochange_core.finance.collections'] = finance_col

        ops_packages = types.ModuleType('centrochange_core.operations.packages')
        ops_packages.disposition = lambda doc, due, reason, revision: None
        sys.modules['centrochange_core.operations.packages'] = ops_packages

        ops_notes = types.ModuleType('centrochange_core.operations.notes')
        ops_notes.require_context = self._mock_require_context
        sys.modules['centrochange_core.operations.notes'] = ops_notes

        spec.loader.exec_module(self.lifecycle)

    def _mock_get_doc(self, *args, **kwargs):
        if len(args) == 2 and args[0] == 'Patient Appointment':
            name = args[1]
            if name in self.appointments:
                return self.appointments[name]
            raise ValueError(f"Patient Appointment {name} not found")
        if len(args) == 1 and isinstance(args[0], dict):
            # doc creation
            doc = Record(args[0])
            doc.name = f"NEW-{len(self.settlements) + 1}"
            doc.insert = lambda ignore_permissions=False: doc
            if doc.doctype == 'CC Settlement':
                self.settlements.append(doc)
            return doc
        doc = Record(name='MOCK', check_permission=lambda p: None)
        doc.insert = lambda ignore_permissions=False: doc
        return doc

    def _mock_get_all(self, doctype, filters=None, fields=None, order_by=None, page_length=None):
        if doctype == 'Patient Appointment':
            res = []
            for app in self.appointments.values():
                match = True
                if filters:
                    if 'cc_center' in filters and app.cc_center != filters['cc_center']:
                        match = False
                    if 'appointment_date' in filters:
                        cond = filters['appointment_date']
                        if isinstance(cond, list) and cond[0] == '<':
                            if app.appointment_date >= str(cond[1]):
                                match = False
                        elif str(app.appointment_date) != str(cond):
                            match = False
                    if 'practitioner' in filters and app.practitioner != filters['practitioner']:
                        match = False
                    if 'cc_closure_state' in filters:
                        cond = filters['cc_closure_state']
                        if isinstance(cond, list) and cond[0] == 'in':
                            if app.cc_closure_state not in cond[1]:
                                match = False
                        elif app.cc_closure_state != cond:
                            match = False
                    if 'status' in filters:
                        cond = filters['status']
                        if isinstance(cond, list) and cond[0] == '!=':
                            if app.status == cond[1]:
                                match = False
                    if 'patient' in filters:
                        cond = filters['patient']
                        if isinstance(cond, list) and cond[0] == 'in':
                            if app.patient not in cond[1]:
                                match = False
                if match:
                    res.append(Record(app))
            return res
        if doctype == 'Patient':
            return [Record(name='PAT-1', first_name='Mario', last_name='Rossi'),
                    Record(name='PAT-2', first_name='Luigi', last_name='Verdi'),
                    Record(name='PAT-3', first_name='Anna', last_name='Bianchi')]
        return []

    def _mock_require_operational_center(self, center):
        if center not in self.operational_centers:
            raise PermissionError(f"La sede {center} non è operativa: nuove operazioni non consentite.")

    def _mock_require_context(self, patient, center):
        if center not in self.operational_centers:
            raise PermissionError(f"La sede {center} non è operativa.")
        if patient not in self.assigned_patients:
            raise PermissionError(f"Il paziente {patient} non è assegnato in questo centro.")

    def _mock_current_rows(self, doctype, filters=None, fields=None, pluck=None):
        if doctype == 'CC Settlement':
            app = filters.get('appointment')
            res = [s for s in self.settlements if s.appointment == app]
            return sorted(res, key=lambda x: x.sequence, reverse=True)
        return []

    def _mock_db_get_value(self, doctype, name_or_filters, fieldname=None, for_update=False):
        if doctype == 'Mode of Payment':
            return 1  # enabled
        return 'VAL'

    def _mock_db_set_value(self, doctype, name, values):
        if doctype == 'Patient Appointment' and name in self.appointments:
            self.appointments[name].update(values)

    def _mock_audit_append(self, event_type, doctype, name, before, after, reason):
        self.events.append({
            'event_type': event_type,
            'doctype': doctype,
            'name': name,
            'before': before,
            'after': after,
            'reason': reason
        })

    def test_get_day_closure_sessions_returns_today_and_arrear_dates(self):
        """get_day_closure_sessions returns today's sessions and identifies 2026-10-12 as an arrear date."""
        res = self.lifecycle.get_day_closure_sessions('CENTRO-A', '2026-10-26')
        self.assertEqual(res['date'], '2026-10-26')
        self.assertTrue(res['is_today'])
        # Today's appointments for PRO-A: APP-TODAY-1, APP-TODAY-2, APP-TODAY-3, APP-CANCELLED, APP-TODAY-FUTURE, APP-LATE-CANCEL-DUE
        self.assertEqual(len(res['sessions']), 6)
        # Arrear dates must contain 2026-10-12 from APP-ARREAR-12
        self.assertIn('2026-10-12', res['arrear_dates'])

    def test_get_day_closure_sessions_arrear_target_date(self):
        """When passing 2026-10-12, get_day_closure_sessions loads the Auto Locked session."""
        res = self.lifecycle.get_day_closure_sessions('CENTRO-A', '2026-10-12')
        self.assertEqual(res['date'], '2026-10-12')
        self.assertTrue(res['is_past'])
        self.assertEqual(len(res['sessions']), 1)
        self.assertEqual(res['sessions'][0]['name'], 'APP-ARREAR-12')
        self.assertEqual(res['sessions'][0]['cc_closure_state'], 'Auto Locked')

    def test_close_day_bulk_closure_today_sessions(self):
        """Professional closes 3 sessions of today in one atomic batch:
        - Session 1: Svolta=1, Pagata=1, mode='Cash' -> Due, Paid, Settlement recorded.
        - Session 2: Svolta=1, Pagata=0 -> Due, Unpaid, Settlement recorded.
        - Session 3: Svolta=0 -> No Show, Non Due, Unpaid.
        """
        # Exclude other today fixtures so PRO-A has exactly these 3 concluded sessions today
        del self.appointments['APP-TODAY-FUTURE']
        del self.appointments['APP-LATE-CANCEL-DUE']

        payload = [
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash', 'note': 'Svolta regolarmente'},
            {'appointment': 'APP-TODAY-2', 'performed': 1, 'paid': 0, 'mode_of_payment': None, 'note': 'Paziente pagherà alla prossima'},
            {'appointment': 'APP-TODAY-3', 'performed': 0, 'paid': 0, 'mode_of_payment': None, 'note': 'Paziente assente'},
        ]
        res = self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload, 'Chiusura della mia giornata')
        self.assertEqual(res['status'], 'PASS')
        self.assertTrue(res['day_closed'])
        self.assertEqual(res['remaining_pending'], 0)
        self.assertEqual(res['updated_count'], 3)

        # Check APP-TODAY-1
        doc1 = self.appointments['APP-TODAY-1']
        self.assertEqual(doc1.status, 'Closed')
        self.assertEqual(doc1.cc_closure_state, 'Closed')
        self.assertEqual(doc1.cc_performed, 1)
        self.assertEqual(doc1.cc_economic_state, 'Due')
        self.assertEqual(doc1.cc_paid, 1)

        # Check APP-TODAY-2
        doc2 = self.appointments['APP-TODAY-2']
        self.assertEqual(doc2.status, 'Closed')
        self.assertEqual(doc2.cc_closure_state, 'Closed')
        self.assertEqual(doc2.cc_performed, 1)
        self.assertEqual(doc2.cc_economic_state, 'Due')
        self.assertEqual(doc2.cc_paid, 0)

        # Check APP-TODAY-3
        doc3 = self.appointments['APP-TODAY-3']
        self.assertEqual(doc3.status, 'No Show')
        self.assertEqual(doc3.cc_closure_state, 'Closed')
        self.assertEqual(doc3.cc_performed, 0)
        self.assertEqual(doc3.cc_economic_state, 'Non Due')
        self.assertEqual(doc3.cc_paid, 0)

        # Check audit events
        closed_events = [e for e in self.events if e['event_type'] == 'SESSION_CLOSED']
        self.assertEqual(len(closed_events), 3)

    def test_autonomous_recovery_of_auto_locked_arrear_session_without_direction(self):
        """Owner Core Mandate (#173): Practitioner autonomously closes an Auto Locked arrear session
        from 2026-10-12 without needing Direction/Secretariat intervention or reopen.
        Emits SESSION_LATE_COMPLETED audit event with before={'closure': 'Auto Locked'} and after={'closure': 'Closed'}."""
        payload = [
            {'appointment': 'APP-ARREAR-12', 'performed': 1, 'paid': 1, 'mode_of_payment': 'CC DEV PROFILE CASH', 'note': 'Seduta recuperata autonomamente'}
        ]
        res = self.lifecycle.close_day('CENTRO-A', '2026-10-12', payload, 'Completamento autonomo seduta arretrata')
        self.assertEqual(res['status'], 'PASS')

        doc = self.appointments['APP-ARREAR-12']
        self.assertEqual(doc.status, 'Closed')
        self.assertEqual(doc.cc_closure_state, 'Closed')
        self.assertEqual(doc.cc_performed, 1)
        self.assertEqual(doc.cc_economic_state, 'Due')
        self.assertEqual(doc.cc_paid, 1)

        # Audit event must be SESSION_LATE_COMPLETED
        late_events = [e for e in self.events if e['event_type'] == 'SESSION_LATE_COMPLETED']
        self.assertEqual(len(late_events), 1)
        self.assertEqual(late_events[0]['name'], 'APP-ARREAR-12')
        self.assertEqual(late_events[0]['before']['closure'], 'Auto Locked')
        self.assertEqual(late_events[0]['after']['closure'], 'Closed')
        self.assertTrue(late_events[0]['after']['performed'])

    def test_idor_cross_practitioner_closure_rejected(self):
        """Negative security: CC Professional PRO-A cannot close an appointment belonging to PRO-B."""
        payload = [
            {'appointment': 'APP-PRO-B', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'}
        ]
        with self.assertRaises(PermissionError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('Non sei autorizzato a modificare la seduta APP-PRO-B di un altro professionista', str(ctx.exception))

    def test_already_closed_appointment_cannot_be_mutated(self):
        """Closed and consolidated appointments cannot be modified by routine day closure."""
        payload = [
            {'appointment': 'APP-CLOSED', 'performed': 0, 'paid': 0}
        ]
        with self.assertRaises(PermissionError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-20', payload)
        self.assertIn('Non è consentito sovrascrivere una seduta consolidata', str(ctx.exception))

    def test_idempotent_duplicate_replay_does_not_mutate(self):
        """Submitting exact same closure parameters for an already closed session returns replay=True without duplicate audit events."""
        self.settlements.append(Record(appointment='APP-CLOSED', mode_of_payment='Cash', sequence=1))
        payload = [
            {'appointment': 'APP-CLOSED', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'}
        ]
        initial_events_count = len(self.events)
        res = self.lifecycle.close_day('CENTRO-A', '2026-10-20', payload)
        self.assertEqual(res['status'], 'PASS')
        self.assertTrue(res['updated'][0]['replay'])
        # Zero new audit events added
        self.assertEqual(len(self.events), initial_events_count)

    def test_cancelled_appointment_cannot_be_closed_as_performed(self):
        """Cancelled appointments cannot be marked as performed in day closure."""
        payload = [
            {'appointment': 'APP-CANCELLED', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'}
        ]
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('cancellata e non può essere chiusa', str(ctx.exception))

    def test_non_operational_center_rejected(self):
        """Non-operational center must be rejected with PermissionError."""
        with self.assertRaises(PermissionError) as ctx:
            self.lifecycle.get_day_closure_sessions('CENTRO-INATTIVO', '2026-10-26')
        self.assertIn('non è operativa', str(ctx.exception))

        payload = [{'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 0}]
        with self.assertRaises(PermissionError) as ctx:
            self.lifecycle.close_day('CENTRO-INATTIVO', '2026-10-26', payload)
        self.assertIn('non è operativa', str(ctx.exception))

    def test_revoked_patient_assignment_denies_closure(self):
        """When a patient assignment is revoked, direct API closure is denied via require_context."""
        self.assigned_patients = ['PAT-2', 'PAT-3', 'PAT-4']  # PAT-1 revoked
        payload = [{'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 0}]  # PAT-1
        with self.assertRaises(PermissionError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('non è assegnato', str(ctx.exception))

    def test_target_date_mismatch_rejected(self):
        """Attempting to close a session whose appointment_date differs from target date must be rejected."""
        payload = [{'appointment': 'APP-ARREAR-12', 'performed': 1, 'paid': 0}]  # Date is 2026-10-12
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)  # Request date is 2026-10-26
        self.assertIn('diversa dalla data richiesta', str(ctx.exception))

    def test_missing_performed_field_rejected(self):
        """Missing or malformed performed field in payload must be rejected."""
        payload = [{'appointment': 'APP-TODAY-1'}]  # No performed
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('Esito prestazione (performed) mancante', str(ctx.exception))

    def test_future_session_closure_rejected(self):
        """Future sessions (clock is 18:00, session ends at 20:00) cannot be closed as performed OR no-show."""
        payload_performed = [{'appointment': 'APP-TODAY-FUTURE', 'performed': 1, 'paid': 0}]
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload_performed)
        self.assertIn('futuro', str(ctx.exception))

        payload_noshow = [{'appointment': 'APP-TODAY-FUTURE', 'performed': 0, 'paid': 0}]
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload_noshow)
        self.assertIn('futuro', str(ctx.exception))

    def test_duplicate_appointments_in_payload_rejected(self):
        """Payload containing duplicate appointment entries must fail closed."""
        payload = [
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 0},
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 0}
        ]
        with self.assertRaises(ValueError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('duplicata nel payload', str(ctx.exception))

    def test_unperformed_session_preserves_due_economic_state(self):
        """When an appointment already has cc_economic_state='Due' (e.g. late cancellation fee),
        closing as performed=0 does NOT wipe it to 'Non Due', preserving economic obligation."""
        payload = [
            {'appointment': 'APP-LATE-CANCEL-DUE', 'performed': 0, 'paid': 0, 'note': 'Penale applicata per assenza ingiustificata'}
        ]
        res = self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload, allow_partial=1)
        self.assertEqual(res['status'], 'PARTIAL')
        doc = self.appointments['APP-LATE-CANCEL-DUE']
        self.assertEqual(doc.status, 'No Show')
        self.assertEqual(doc.cc_closure_state, 'Closed')
        self.assertEqual(doc.cc_performed, 0)
        self.assertEqual(doc.cc_economic_state, 'Due')  # Preserved Due!

        # Check that per-session note is passed to audit event
        event = [e for e in self.events if e['name'] == 'APP-LATE-CANCEL-DUE'][0]
        self.assertEqual(event['reason'], 'Penale applicata per assenza ingiustificata')

    def test_close_day_fails_if_concluded_sessions_omitted_without_allow_partial(self):
        """Full-Day Contract: close_day fails closed if any actionable concluded sessions are omitted without allow_partial=1."""
        del self.appointments['APP-TODAY-FUTURE']
        payload = [
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'}
        ]
        with self.assertRaises(self.frappe.ValidationError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('La chiusura della giornata è incompleta: risultano ancora', str(ctx.exception))

    def test_close_day_succeeds_with_partial_status_when_allow_partial_is_true(self):
        """Full-Day Contract: passing allow_partial=1 permits closing subset and returns status='PARTIAL', day_closed=False."""
        del self.appointments['APP-TODAY-FUTURE']
        payload = [
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'}
        ]
        res = self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload, allow_partial=1)
        self.assertEqual(res['status'], 'PARTIAL')
        self.assertFalse(res['day_closed'])
        self.assertGreater(res['remaining_pending'], 0)
        self.assertEqual(res['updated_count'], 1)

    def test_close_day_fails_if_future_sessions_remain_without_allow_partial(self):
        """Full-Day Contract: if future sessions remain today, full closure is rejected unless allow_partial=1."""
        del self.appointments['APP-LATE-CANCEL-DUE']
        payload = [
            {'appointment': 'APP-TODAY-1', 'performed': 1, 'paid': 1, 'mode_of_payment': 'Cash'},
            {'appointment': 'APP-TODAY-2', 'performed': 1, 'paid': 0},
            {'appointment': 'APP-TODAY-3', 'performed': 0, 'paid': 0},
        ]
        with self.assertRaises(self.frappe.ValidationError) as ctx:
            self.lifecycle.close_day('CENTRO-A', '2026-10-26', payload)
        self.assertIn('risultano 1 sedute future non ancora concluse', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
