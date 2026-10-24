"""Unit and regression tests for operational reporting, role scoping, temporal edge-cases and volumetric scalability (>500 sessions)."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'app/centrochange_core/centrochange_core/operations/reporting.py'
ROME = ZoneInfo('Europe/Rome')


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
        self.test_clock = datetime(2026, 10, 24, 12, 0, 0, tzinfo=ROME)

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
        self.frappe.in_test = True
        self.frappe.conf = types.SimpleNamespace(cc_synthetic_dev=1)
        self.frappe.flags = {'cc_test_clock': self.test_clock}
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
                    if filters and filters.get('cc_center') and a.cc_center != filters['cc_center']:
                        continue
                    if filters and filters.get('practitioner') and a.practitioner != filters['practitioner']:
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
        self.frappe.utils = types.SimpleNamespace(
            getdate=lambda d: date.fromisoformat(str(d)) if isinstance(d, str) else d,
            get_time=lambda t: time.fromisoformat(str(t)[:8]) if isinstance(t, str) else t,
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
        self.assertEqual(eur['operational_unpaid'], 1)  # Only APP-2 (APP-3 is cancelled, APP-4 is future)
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
        self.assertEqual(eur['sessions'], 3)
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
        self.assertTrue(content.startswith('\ufeff'))
        self.assertIn('Paziente 2', content)
        self.assertNotIn('Paziente 1', content)
        self.assertIn('centrochange-report-centro.csv', self.frappe.response['filename'])

    def test_temporal_transition_no_overlap(self):
        """A session scheduled today at 15:00 is future at 12:00, but to_close at 16:30."""
        # 1. At 12:00 (before session): APP-4 is future
        self.frappe.flags['cc_test_clock'] = datetime(2026, 10, 24, 12, 0, 0, tzinfo=ROME)
        res_future = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', kpi='future')
        res_toclose = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', kpi='to_close')
        self.assertIn('APP-4', [a['name'] for a in res_future['appointments']])
        self.assertNotIn('APP-4', [a['name'] for a in res_toclose['appointments']])

        # 2. At 16:30 (after session duration 60 min): APP-4 is to_close, NOT future
        self.frappe.flags['cc_test_clock'] = datetime(2026, 10, 24, 16, 30, 0, tzinfo=ROME)
        res_future_later = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', kpi='future')
        res_toclose_later = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', kpi='to_close')
        self.assertNotIn('APP-4', [a['name'] for a in res_future_later['appointments']])
        self.assertIn('APP-4', [a['name'] for a in res_toclose_later['appointments']])

    def test_volumetric_pagination_over_500_sessions(self):
        """Simulate 550 appointments: 300 PRO-A, 250 PRO-B. Test server-side pagination, order stability, role clamp."""
        big_dataset = []
        for i in range(1, 551):
            prac = 'PRO-A' if i <= 300 else 'PRO-B'
            status = 'Closed' if i % 3 == 0 else ('Cancelled' if i % 10 == 0 else 'Scheduled')
            performed = 1 if status == 'Closed' else 0
            paid = 1 if (performed and i % 2 == 0) else 0
            econ = 'Non Due' if status == 'Cancelled' else 'Due'
            big_dataset.append(Record(
                name=f'APP-VOL-{i:04d}',
                patient=f'PAT-{(i % 20) + 1}',
                patient_name=f'Paziente {(i % 20) + 1}',
                practitioner=prac,
                practitioner_name=f'Dott. {prac}',
                cc_center='CENTRO-A',
                appointment_date='2026-10-15',
                appointment_time=f'{(9 + (i % 8)):02d}:00:00',
                duration=45,
                status=status,
                cc_closure_state=status,
                cc_economic_state=econ,
                cc_performed=performed,
                cc_paid=paid,
                cc_late_cancellation=0,
                cc_service_label='Visita Volumetrica',
                cc_price_snapshot=100.0,
                cc_currency_snapshot='EUR'
            ))

        self.appointments = big_dataset

        # 1. Full summary count
        summary = self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-31')
        self.assertEqual(summary['total_appointments'], 550)
        self.assertFalse(summary['truncated'])

        # 2. Server-side pagination: page 1 (50 items)
        page1 = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-31', kpi='all', page=1, page_length=50)
        self.assertEqual(page1['total'], 550)
        self.assertEqual(len(page1['appointments']), 50)
        self.assertEqual(page1['page'], 1)
        self.assertEqual(page1['total_pages'], 11)

        # 3. Server-side pagination: page 2 (50 items)
        page2 = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-31', kpi='all', page=2, page_length=50)
        self.assertEqual(page2['total'], 550)
        self.assertEqual(len(page2['appointments']), 50)
        self.assertEqual(page2['page'], 2)
        # Ensure no overlap between page 1 and page 2
        p1_names = {a['name'] for a in page1['appointments']}
        p2_names = {a['name'] for a in page2['appointments']}
        self.assertEqual(len(p1_names.intersection(p2_names)), 0)

        # 4. Server-side pagination: last page 11 (50 items)
        page11 = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-31', kpi='all', page=11, page_length=50)
        self.assertEqual(len(page11['appointments']), 50)

        # 5. Role scoping on >500 sessions: Professional A receives exactly 300 sessions
        self.manager = False
        self.actor_roles = ['CC Professional']
        prof_summary = self.reporting.summary('CENTRO-A', '2026-10-01', '2026-10-31')
        self.assertEqual(prof_summary['total_appointments'], 300)
        prof_page1 = self.reporting.sessions('CENTRO-A', '2026-10-01', '2026-10-31', kpi='all', page=1, page_length=50)
        self.assertEqual(prof_page1['total'], 300)
        self.assertEqual(prof_page1['total_pages'], 6)
        self.assertTrue(all(a['practitioner'] == 'PRO-A' for a in prof_page1['appointments']))

        # 6. Export CSV exports all 300 sessions for Professional A
        self.reporting.export_csv('CENTRO-A', '2026-10-01', '2026-10-31', kpi='all')
        csv_content = self.frappe.response['filecontent']
        lines = csv_content.strip().split('\r\n') if '\r\n' in csv_content else csv_content.strip().split('\n')
        # 1 header line + 300 data lines = 301 lines
        self.assertEqual(len(lines), 301)
        self.assertIn('centrochange-report-professionista.csv', self.frappe.response['filename'])

    def test_owner_uat_scenario_8_sessions_unpaid_reconciliation(self):
        """Owner UAT evidence: 8 sessions (6 performed unpaid, 2 cancelled).
        Guarantee: KPI=6 <-> Header (6) <-> exactly 6 rows returned <-> CSV exports exactly 6 rows.
        Cancelled sessions MUST NOT appear in operational_unpaid and MUST NOT be labeled as unpaid.
        """
        fixtures = []
        for i in range(1, 7):
            fixtures.append(Record(
                name=f'APP-PERF-{i}',
                patient=f'PAT-{i}',
                patient_name=f'Paziente {i}',
                practitioner='PRO-A',
                practitioner_name='Dott. A',
                cc_center='CENTRO-A',
                appointment_date='2026-09-10',
                appointment_time=f'{9+i:02d}:00:00',
                duration=50,
                status='Closed',
                cc_closure_state='Closed',
                cc_economic_state='Due',
                cc_performed=1,
                cc_paid=0,
                cc_late_cancellation=0,
                cc_service_label='Seduta psicologica',
                cc_price_snapshot=100.0,
                cc_currency_snapshot='EUR'
            ))
        for j in (1, 2):
            fixtures.append(Record(
                name=f'APP-CANC-{j}',
                patient=f'PAT-CANC-{j}',
                patient_name=f'Paziente C {j}',
                practitioner='PRO-A',
                practitioner_name='Dott. A',
                cc_center='CENTRO-A',
                appointment_date='2026-09-15',
                appointment_time=f'{15+j:02d}:00:00',
                duration=50,
                status='Cancelled',
                cc_closure_state='Closed',
                cc_economic_state='Non Due',
                cc_performed=0,
                cc_paid=0,
                cc_late_cancellation=0,
                cc_service_label='Seduta psicologica',
                cc_price_snapshot=100.0,
                cc_currency_snapshot='EUR'
            ))
        self.appointments = fixtures

        summary = self.reporting.summary('CENTRO-A', '2026-09-01', '2026-09-30', practitioner='PRO-A')
        eur = summary['currencies']['EUR']
        self.assertEqual(eur['sessions'], 8)
        self.assertEqual(eur['performed'], 6)
        self.assertEqual(eur['cancelled'], 2)
        self.assertEqual(eur['operational_paid'], 0)
        self.assertEqual(eur['operational_unpaid'], 6)
        self.assertEqual(eur['due'], 6)
        self.assertEqual(eur['due_snapshot_amount'], 600.0)

        # Drilldown for operational_unpaid must return exactly 6 rows (NOT 8!)
        drilldown_unpaid = self.reporting.sessions('CENTRO-A', '2026-09-01', '2026-09-30', practitioner='PRO-A', kpi='operational_unpaid')
        self.assertEqual(drilldown_unpaid['total'], 6)
        self.assertEqual(len(drilldown_unpaid['appointments']), 6)
        self.assertTrue(all(a['status'] != 'Cancelled' for a in drilldown_unpaid['appointments']))
        self.assertTrue(all(a['cc_classified_unpaid'] is True for a in drilldown_unpaid['appointments']))
        self.assertTrue(all(a['cc_classified_cancelled'] is False for a in drilldown_unpaid['appointments']))

        # Drilldown for cancelled must return exactly 2 rows
        drilldown_cancelled = self.reporting.sessions('CENTRO-A', '2026-09-01', '2026-09-30', practitioner='PRO-A', kpi='cancelled')
        self.assertEqual(drilldown_cancelled['total'], 2)
        self.assertEqual(len(drilldown_cancelled['appointments']), 2)
        self.assertTrue(all(a['status'] == 'Cancelled' for a in drilldown_cancelled['appointments']))
        self.assertTrue(all(a['cc_classified_cancelled'] is True for a in drilldown_cancelled['appointments']))

        # Export CSV for operational_unpaid must have exactly 6 data rows
        self.reporting.export_csv('CENTRO-A', '2026-09-01', '2026-09-30', practitioner='PRO-A', kpi='operational_unpaid')
        csv_lines = [l for l in self.frappe.response['filecontent'].strip().split('\n') if l.strip()]
        self.assertEqual(len(csv_lines), 7)  # 1 header + 6 rows
        for line in csv_lines[1:]:
            self.assertIn('Da incassare', line)
            self.assertNotIn('annullata', line)

        # Export CSV for cancelled must have exactly 2 data rows
        self.reporting.export_csv('CENTRO-A', '2026-09-01', '2026-09-30', practitioner='PRO-A', kpi='cancelled')
        csv_canc_lines = [l for l in self.frappe.response['filecontent'].strip().split('\n') if l.strip()]
        self.assertEqual(len(csv_canc_lines), 3)  # 1 header + 2 rows
        for line in csv_canc_lines[1:]:
            self.assertIn('— (annullata)', line)
            self.assertNotIn('Da incassare', line)

    def test_owner_uat_scenario_3_sessions_reconciliation(self):
        """Owner UAT second scenario: 3 sessions total:
        0 performed, 2 to_close (past end time without closure), 1 cancelled.
        """
        self.frappe.flags['cc_test_clock'] = datetime(2026, 10, 24, 18, 0, 0, tzinfo=ROME)
        fixtures = [
            Record(name='APP-TOCLOSE-1', patient='PAT-1', patient_name='Paziente 1', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-24',
                   appointment_time='10:00:00', duration=60, status='Scheduled', cc_closure_state='Pending',
                   cc_economic_state='Due', cc_performed=0, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita 1', cc_price_snapshot=100.0, cc_currency_snapshot='EUR'),
            Record(name='APP-TOCLOSE-2', patient='PAT-2', patient_name='Paziente 2', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-24',
                   appointment_time='14:00:00', duration=60, status='Scheduled', cc_closure_state='Pending',
                   cc_economic_state='Due', cc_performed=0, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita 2', cc_price_snapshot=100.0, cc_currency_snapshot='EUR'),
            Record(name='APP-CANC-1', patient='PAT-3', patient_name='Paziente 3', practitioner='PRO-A',
                   practitioner_name='Dott. A', cc_center='CENTRO-A', appointment_date='2026-10-24',
                   appointment_time='16:00:00', duration=60, status='Cancelled', cc_closure_state='Closed',
                   cc_economic_state='Non Due', cc_performed=0, cc_paid=0, cc_late_cancellation=0,
                   cc_service_label='Visita 3', cc_price_snapshot=100.0, cc_currency_snapshot='EUR'),
        ]
        self.appointments = fixtures

        summary = self.reporting.summary('CENTRO-A', '2026-10-24', '2026-10-24', practitioner='PRO-A')
        eur = summary['currencies']['EUR']
        self.assertEqual(eur['sessions'], 3)
        self.assertEqual(eur['performed'], 0)
        self.assertEqual(eur['to_close'], 2)
        self.assertEqual(eur['cancelled'], 1)
        # In a scenario with 0 performed sessions, 'Svolte senza pagamento' is strictly 0!
        # Unclosed sessions awaiting confirmation are classified as 'to_close', NOT as performed unpaid.
        self.assertEqual(eur['operational_unpaid'], 0)

        # Opening to_close (2) shows exactly 2 rows
        res_toclose = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', practitioner='PRO-A', kpi='to_close')
        self.assertEqual(res_toclose['total'], 2)
        self.assertEqual(len(res_toclose['appointments']), 2)

        # Opening operational_unpaid (0) shows exactly 0 rows
        res_unpaid = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', practitioner='PRO-A', kpi='operational_unpaid')
        self.assertEqual(res_unpaid['total'], 0)
        self.assertEqual(len(res_unpaid['appointments']), 0)

        # Opening cancelled (1) shows exactly 1 row
        res_cancelled = self.reporting.sessions('CENTRO-A', '2026-10-24', '2026-10-24', practitioner='PRO-A', kpi='cancelled')
        self.assertEqual(res_cancelled['total'], 1)
        self.assertEqual(len(res_cancelled['appointments']), 1)


if __name__ == '__main__':
    unittest.main()
