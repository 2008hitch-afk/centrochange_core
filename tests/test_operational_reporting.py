"""Unit and regression tests for operational reporting, role scoping and KPI drilldown."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'app/centrochange_core/centrochange_core/operations/reporting.py'


class Denied(Exception):
    pass


class Record(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    def get(self, key, default=None):
        return super().get(key, default)


class OperationalReportingTests(unittest.TestCase):
    def setUp(self):
        self.manager = True
        self.actor_roles = ['CC Manager']
        self.user_practitioner = 'PRO-A'
        self.appointments = [
            Record(name='APP-1', patient='PAT-1', patient_name='Paziente 1', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-20',
                   appointment_time='09:00:00', duration=60, status='Closed', cc_closure_state='Closed',
                   cc_economic_state='Due', cc_performed=1, cc_paid=1, cc_late_cancellation=0,
                   cc_service_label='Visita A', cc_price_snapshot=100, cc_currency_snapshot='EUR',
                   cc_package=None, cc_package_state=None),
            Record(name='APP-2', patient='PAT-2', patient_name='Paziente 2', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-21',
                   appointment_time='10:00:00', duration=60, status='Closed', cc_closure_state='Closed',
                   cc_economic_state='Due', cc_performed=1, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita B', cc_price_snapshot=80, cc_currency_snapshot='EUR',
                   cc_package=None, cc_package_state=None),
            Record(name='APP-3', patient='PAT-3', patient_name='Paziente 3', practitioner='PRO-B',
                   practitioner_name='Dott. B', cc_center='CENTRO-A', appointment_date='2026-10-22',
                   appointment_time='11:00:00', duration=60, status='Cancelled', cc_closure_state='Closed',
                   cc_economic_state='Non Due', cc_performed=0, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita C', cc_price_snapshot=50, cc_currency_snapshot='EUR',
                   cc_package=None, cc_package_state=None),
            Record(name='APP-4', patient='PAT-1', patient_name='Paziente 1', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-24',
                   appointment_time='15:00:00', duration=60, status='Scheduled', cc_closure_state='Pending',
                   cc_economic_state='Pending', cc_performed=0, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita D', cc_price_snapshot=90, cc_currency_snapshot='EUR',
                   cc_package=None, cc_package_state=None),
        ]
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = Denied
        self.frappe.ValidationError = ValueError
        self.frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.session = types.SimpleNamespace(user='test-user@example.invalid')
        self.frappe.response = {}

        def fake_get_list(doctype, filters=None, fields=None, order_by=None, page_length=None):
            if doctype == 'Patient Appointment':
                result = []
                for a in self.appointments:
                    if filters.get('cc_center') and a.cc_center != filters['cc_center']:
                        continue
                    if filters.get('practitioner') and a.practitioner != filters['practitioner']:
                        continue
                    result.append(Record(a))
                return result
            if doctype == 'Patient':
                return [Record(name='PAT-1', first_name='Mario', last_name='Rossi'),
                        Record(name='PAT-2', first_name='Luigi', last_name='Verdi'),
                        Record(name='PAT-3', first_name='Anna', last_name='Bianchi')]
            return []

        self.frappe.get_list = fake_get_list
        self.frappe.get_all = fake_get_list
        from datetime import date
        self.frappe.utils = types.SimpleNamespace(
            getdate=lambda d: date.fromisoformat(str(d)) if isinstance(d, str) else d,
            get_time=lambda t: t,
            cint=int,
            today=lambda: '2026-10-24',
            formatdate=lambda d, fmt: str(d)
        )
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.enabled = lambda: True
        guards.is_manager = lambda: self.manager
        guards.roles = lambda: self.actor_roles
        guards.require_manager = lambda: None if self.manager else self.frappe.throw('Manager required', Denied)
        guards.require_center = lambda c: None if c == 'CENTRO-A' else self.frappe.throw('Centro negato', Denied)
        guards.practitioner_for = lambda u=None: self.user_practitioner
        guards.current_rows = lambda doctype, filters=None, fields=None, order_by=None: [
            Record(appointment='APP-1', mode_of_payment='POS', sequence=1)
        ] if doctype == 'CC Settlement' else []

        workspace = types.ModuleType('centrochange_core.operations.workspace')
        workspace.require_actor = lambda: None
        workspace.APPOINTMENT_FIELDS = list(self.appointments[0].keys())

        modules = {
            'frappe': self.frappe,
            'frappe.utils': self.frappe.utils,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.guards': guards,
            'centrochange_core.operations': types.ModuleType('centrochange_core.operations'),
            'centrochange_core.operations.workspace': workspace,
        }
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.reporting', SOURCE)
        self.reporting = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.reporting
        spec.loader.exec_module(self.reporting)

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.operations.reporting', None)

    def test_manager_summary_all_practitioners(self):
        res = self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-24')
        self.assertFalse(res['truncated'])
        eur = res['currencies']['EUR']
        self.assertEqual(eur['sessions'], 4)
        self.assertEqual(eur['performed'], 2)
        self.assertEqual(eur['cancelled'], 1)
        self.assertEqual(eur['operational_paid'], 1)
        self.assertEqual(eur['operational_unpaid'], 1)  # Only APP-2 (APP-3 is cancelled non-due, APP-4 is pending)
        self.assertEqual(eur['due'], 2)
        self.assertEqual(eur['due_snapshot_amount'], 180)

    def test_manager_summary_filter_single_practitioner(self):
        res = self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-24', practitioner='PRO-B')
        eur = res['currencies']['EUR']
        self.assertEqual(eur['sessions'], 1)
        self.assertEqual(eur['cancelled'], 1)
        self.assertEqual(eur['performed'], 0)

    def test_professional_role_clamped_to_own_practitioner(self):
        self.manager = False
        self.actor_roles = ['CC Professional']
        res = self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-24')
        self.assertEqual(res['practitioner'], 'PRO-A')
        eur = res['currencies']['EUR']
        self.assertEqual(eur['sessions'], 3)  # Only PRO-A's 3 appointments, PRO-B excluded
        # Foreign practitioner explicitly rejected
        with self.assertRaises(Denied):
            self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-24', practitioner='PRO-B')

    def test_kpi_drilldown_sessions(self):
        res_unpaid = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-24', kpi='operational_unpaid')
        self.assertEqual(res_unpaid['total'], 1)
        self.assertEqual(res_unpaid['appointments'][0]['name'], 'APP-2')
        self.assertEqual(res_unpaid['appointments'][0]['patient_first_name'], 'Luigi')

        res_paid = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-24', kpi='operational_paid')
        self.assertEqual(res_paid['total'], 1)
        self.assertEqual(res_paid['appointments'][0]['name'], 'APP-1')
        self.assertEqual(res_paid['appointments'][0]['mode_of_payment'], 'POS')

        res_cancelled = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-24', kpi='cancelled')
        self.assertEqual(res_cancelled['total'], 1)
        self.assertEqual(res_cancelled['appointments'][0]['name'], 'APP-3')

    def test_export_csv_equivalence(self):
        self.reporting.export_csv('CENTRO-A', '2026-10-01', '2026-10-24', kpi='operational_unpaid')
        self.assertIn('filecontent', self.frappe.response)
        content = self.frappe.response['filecontent']
        self.assertIn('Paziente 2', content)
        self.assertNotIn('Paziente 1', content)


if __name__ == '__main__':
    unittest.main()
