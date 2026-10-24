"""Real isolated Frappe/MariaDB load and reconciliation test (>500 appointments).

Tests:
1. Load of 550 synthetic Patient Appointments across MariaDB database.
2. Reconciliation between summary KPIs, drilldown sessions, and CSV export.
3. Specific fix coverage:
   - Late cancellations with due tariff (cc_late_cancellation=1, cc_economic_state='Due', status='Cancelled')
     properly included in summary due, drilldown sessions, and CSV export.
   - Timely cancellations and package-covered cancellations excluded from due.
   - Currency filtering: EUR and USD completely isolated across KPIs, drilldown, and CSV exports.
4. Role-based scoping:
   - CC Manager: access to all practitioners and center totals.
   - CC Professional: strict scoping to practitioner's own appointments; cross-practitioner access denied.
5. Real performance & memory envelope measurement on MariaDB.
6. Zero mutation guarantee: All test fixtures run in an isolated transaction rolled back in finally.
"""

import os
import sys
import time
import types
import unittest
from pathlib import Path


def _is_running_in_frappe():
    try:
        import frappe
        return hasattr(frappe, 'init')
    except ImportError:
        return False


def _run_real_mariadb_test():
    import tracemalloc
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import frappe

    # Connect to Frappe database if not already connected
    if not frappe.db:
        frappe.init('centrochange.local', sites_path='sites')
        frappe.connect()

    # Load local reporting module from app code
    app_reporting_path = Path('/home/frappe/frappe-bench/apps/centrochange_core/centrochange_core/operations/reporting.py')
    import centrochange_core.operations.reporting as mod

    center = 'CC-HTTP-UAT0000001 A'
    prac_a = 'HLC-PRAC-2026-00001'
    prac_b = 'HLC-PRAC-2026-00002'
    start_date = '2026-11-01'
    end_date = '2026-11-30'
    today_rome = datetime(2026, 11, 20, 12, 0, tzinfo=ZoneInfo('Europe/Rome'))

    # Set test flags and deterministic Europe/Rome test clock
    frappe.flags.in_test = True
    frappe.flags.cc_test_clock = today_rome

    initial_count = frappe.db.count('Patient Appointment')

    try:
        # Generate 550 synthetic appointments:
        # - 200 EUR Closed performed=1, paid=1, price=100 (Prac A: 100, Prac B: 100)
        # - 150 EUR Closed performed=1, paid=0, price=100 (Prac A: 80, Prac B: 70)
        # - 50 EUR Cancelled timely: status=Cancelled, econ=Non Due, late=0, price=100 (Prac A: 30, Prac B: 20)
        # - 25 EUR Cancelled late due: status=Cancelled, econ=Due, late=1, price=80 (Prac A: 15, Prac B: 10)
        # - 25 EUR Cancelled late package: status=Cancelled, econ=Package Covered, late=1, price=0 (Prac A: 15, Prac B: 10)
        # - 50 EUR Scheduled future: status=Scheduled, date=2026-11-28, performed=0, paid=0, econ=Due, price=100 (Prac A: 30, Prac B: 20)
        # - 50 USD Closed: 30 paid (price 120), 20 unpaid (price 120) (Prac A: 30, Prac B: 20)
        # Total = 200 + 150 + 50 + 25 + 25 + 50 + 50 = 550 appointments
        # Prac A total: 100 + 80 + 30 + 15 + 15 + 30 + 30 = 300 appointments
        # Prac B total: 100 + 70 + 20 + 10 + 10 + 20 + 20 = 250 appointments

        patient_for_prac = lambda p: 'CC-HTTP-UAT0000001 Alfa' if p == prac_a else 'CC-HTTP-UAT0000001 Zeta'

        rows = []
        for i in range(200):
            prac = prac_a if i < 100 else prac_b
            rows.append((f'SYNTH-MDB-PP-{i:04d}', '2026-11-15', '09:00:00', 'Closed', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Due', 100.0, 'EUR', 0, 1, 1))

        for i in range(150):
            prac = prac_a if i < 80 else prac_b
            rows.append((f'SYNTH-MDB-PU-{i:04d}', '2026-11-16', '10:00:00', 'Closed', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Due', 100.0, 'EUR', 0, 1, 0))

        for i in range(50):
            prac = prac_a if i < 30 else prac_b
            rows.append((f'SYNTH-MDB-CT-{i:04d}', '2026-11-17', '11:00:00', 'Cancelled', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Non Due', 100.0, 'EUR', 0, 0, 0))

        for i in range(25):
            prac = prac_a if i < 15 else prac_b
            rows.append((f'SYNTH-MDB-CLD-{i:04d}', '2026-11-18', '12:00:00', 'Cancelled', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Due', 80.0, 'EUR', 1, 0, 0))

        for i in range(25):
            prac = prac_a if i < 15 else prac_b
            rows.append((f'SYNTH-MDB-CLP-{i:04d}', '2026-11-19', '14:00:00', 'Cancelled', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Package Covered', 0.0, 'EUR', 1, 0, 0))

        for i in range(50):
            prac = prac_a if i < 30 else prac_b
            rows.append((f'SYNTH-MDB-SF-{i:04d}', '2026-11-28', '15:00:00', 'Scheduled', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Due', 100.0, 'EUR', 0, 0, 0))

        for i in range(50):
            prac = prac_a if i < 30 else prac_b
            is_paid = 1 if i < 30 else 0
            rows.append((f'SYNTH-MDB-USD-{i:04d}', '2026-11-16', '16:00:00', 'Closed', patient_for_prac(prac), 'Paziente', prac, 'Dottore', center, 'Due', 120.0, 'USD', 0, 1, is_paid))

        assert len(rows) == 550, f'Expected 550 synthetic records, got {len(rows)}'

        sql = """
            INSERT INTO `tabPatient Appointment` (
                name, docstatus, idx, duration, add_video_conferencing, invoiced, paid_amount,
                appointment_based_on_check_in, position_in_queue, reminded,
                appointment_date, appointment_time, status, patient, patient_name,
                practitioner, practitioner_name, cc_center, cc_economic_state,
                cc_price_snapshot, cc_currency_snapshot, cc_late_cancellation,
                cc_performed, cc_paid, cc_revision, cc_cancel_notice_seconds, cc_settlement_revision
            ) VALUES (%s, 0, 0, 60, 0, 0, 0, 0, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 0, 1)
        """
        for r in rows:
            frappe.db.sql(sql, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14]))

        count_in_db = frappe.db.count('Patient Appointment')
        assert count_in_db == initial_count + 550, f'Expected {initial_count + 550} rows, got {count_in_db}'

        # Start memory tracing
        tracemalloc.start()

        # ---------------------------------------------------------
        # 1. Role CC Manager (full scope, center overview)
        # ---------------------------------------------------------
        frappe.set_user('cc-http-uat0000001-m@example.invalid')

        t0 = time.perf_counter()
        summary_res = mod.summary(center, start_date, end_date)
        summary_time_ms = (time.perf_counter() - t0) * 1000

        eur = summary_res['currencies']['EUR']
        usd = summary_res['currencies']['USD']

        # Exact KPI checks for EUR
        assert eur['sessions'] == 500, f"EUR sessions mismatch: {eur['sessions']}"
        assert eur['performed'] == 350, f"EUR performed mismatch: {eur['performed']}"
        assert eur['operational_paid'] == 200, f"EUR paid mismatch: {eur['operational_paid']}"
        assert eur['operational_unpaid'] == 150, f"EUR unpaid mismatch: {eur['operational_unpaid']}"
        assert eur['cancelled'] == 100, f"EUR cancelled mismatch: {eur['cancelled']}"
        assert eur['future'] == 50, f"EUR future mismatch: {eur['future']}"
        assert eur['due'] == 425, f"EUR due mismatch: {eur['due']}"
        assert eur['due_snapshot_amount'] == 42000.0, f"EUR due amount mismatch: {eur['due_snapshot_amount']}"

        # Exact KPI checks for USD
        assert usd['sessions'] == 50, f"USD sessions mismatch: {usd['sessions']}"
        assert usd['operational_paid'] == 30, f"USD paid mismatch: {usd['operational_paid']}"
        assert usd['operational_unpaid'] == 20, f"USD unpaid mismatch: {usd['operational_unpaid']}"
        assert usd['due'] == 50, f"USD due mismatch: {usd['due']}"
        assert usd['due_snapshot_amount'] == 6000.0, f"USD due amount mismatch: {usd['due_snapshot_amount']}"

        # ---------------------------------------------------------
        # 2. Reconcile Sessions Drilldown for KPI 'due' (EUR)
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        sessions_due_eur = mod.sessions(center, start_date, end_date, kpi='due', currency='EUR', page=1, page_length=50)
        sessions_time_ms = (time.perf_counter() - t0) * 1000

        assert sessions_due_eur['total'] == 425, f"Total due sessions mismatch: {sessions_due_eur['total']} vs 425"
        assert sessions_due_eur['total_pages'] == 9, f"Total pages mismatch: {sessions_due_eur['total_pages']} vs 9"
        assert len(sessions_due_eur['appointments']) == 50, f"Page 1 length mismatch: {len(sessions_due_eur['appointments'])}"

        # Verify page 9
        sessions_p9 = mod.sessions(center, start_date, end_date, kpi='due', currency='EUR', page=9, page_length=50)
        assert len(sessions_p9['appointments']) == 25, f"Page 9 length mismatch: {len(sessions_p9['appointments'])}"

        # Verify that late cancellations with due tariff ARE returned in sessions
        all_due_names = set()
        for p in range(1, 10):
            p_res = mod.sessions(center, start_date, end_date, kpi='due', currency='EUR', page=p, page_length=50)
            for app in p_res['appointments']:
                all_due_names.add(app['name'])
                assert (app.get('cc_currency_snapshot') or 'EUR') == 'EUR', f"Non-EUR record in EUR due sessions: {app}"

        assert 'SYNTH-MDB-CLD-0000' in all_due_names, "Late cancellation with due tariff missing from due sessions!"
        assert 'SYNTH-MDB-CT-0000' not in all_due_names, "Timely cancellation erroneously present in due sessions!"
        assert 'SYNTH-MDB-CLP-0000' not in all_due_names, "Package covered cancellation erroneously present in due sessions!"

        # ---------------------------------------------------------
        # 3. Reconcile CSV Export for KPI 'due' (EUR)
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        mod.export_csv(center, start_date, end_date, kpi='due', currency='EUR')
        csv_time_ms = (time.perf_counter() - t0) * 1000

        csv_content = frappe.response.get('filecontent', '')
        csv_lines = [l for l in csv_content.strip().split('\n') if l.strip()]
        assert len(csv_lines) - 1 == 425, f"CSV rows mismatch: {len(csv_lines) - 1} vs 425"

        # ---------------------------------------------------------
        # 4. Multi-Currency Filtering Isolation (USD)
        # ---------------------------------------------------------
        usd_unpaid = mod.sessions(center, start_date, end_date, kpi='operational_unpaid', currency='USD', page=1, page_length=50)
        assert usd_unpaid['total'] == 20, f"USD unpaid mismatch: {usd_unpaid['total']} vs 20"
        for app in usd_unpaid['appointments']:
            assert app['cc_currency_snapshot'] == 'USD', f"Currency leak in USD sessions: {app}"

        mod.export_csv(center, start_date, end_date, kpi='operational_unpaid', currency='USD')
        usd_csv_content = frappe.response.get('filecontent', '')
        usd_csv_lines = [l for l in usd_csv_content.strip().split('\n') if l.strip()]
        assert len(usd_csv_lines) - 1 == 20, f"USD CSV rows mismatch: {len(usd_csv_lines) - 1} vs 20"
        for l in usd_csv_lines[1:]:
            assert 'USD' in l, f"Non-USD row in USD CSV: {l}"

        # ---------------------------------------------------------
        # 5. Role CC Professional Isolation & Fail-Closed Negative Tests
        # ---------------------------------------------------------
        frappe.set_user('cc-http-uat0000001-a@example.invalid')
        summary_prof = mod.summary(center, start_date, end_date)
        prof_eur = summary_prof['currencies']['EUR']
        prof_usd = summary_prof['currencies']['USD']

        assert prof_eur['sessions'] == 270, f"Prof A EUR sessions mismatch: {prof_eur['sessions']}"
        assert prof_usd['sessions'] == 30, f"Prof A USD sessions mismatch: {prof_usd['sessions']}"
        assert prof_eur['sessions'] + prof_usd['sessions'] == 300, "Practitioner A sees more than 300 appointments!"

        # Direct cross-practitioner & unauthorized center negative checks
        for fn in [
            lambda: mod.summary(center, start_date, end_date, practitioner=prac_b),
            lambda: mod.sessions(center, start_date, end_date, practitioner=prac_b),
            lambda: mod.export_csv(center, start_date, end_date, practitioner=prac_b),
            lambda: mod.summary('UNAUTHORIZED-CENTER', start_date, end_date),
            lambda: mod.sessions('UNAUTHORIZED-CENTER', start_date, end_date),
            lambda: mod.export_csv('UNAUTHORIZED-CENTER', start_date, end_date),
        ]:
            denied = False
            try:
                fn()
            except frappe.PermissionError:
                denied = True
            assert denied, f"Direct unauthorized call did not raise PermissionError: {fn}"

        # Guest user negative checks
        frappe.set_user('Guest')
        for fn in [
            lambda: mod.summary(center, start_date, end_date),
            lambda: mod.sessions(center, start_date, end_date),
            lambda: mod.export_csv(center, start_date, end_date),
        ]:
            denied = False
            try:
                fn()
            except frappe.PermissionError:
                denied = True
            assert denied, f"Guest user was not denied: {fn}"

        # Reset user back to Administrator for test harness cleanup
        frappe.set_user('Administrator')

        # Stop memory tracing
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results = {
            'status': 'PASS',
            'appointments_tested': 550,
            'summary_time_ms': round(summary_time_ms, 2),
            'sessions_time_ms': round(sessions_time_ms, 2),
            'csv_time_ms': round(csv_time_ms, 2),
            'peak_memory_kb': round(peak_mem / 1024, 2),
            'initial_db_count': initial_count,
            'reconciled_eur_due_kpi': eur['due'],
            'reconciled_eur_due_sessions': sessions_due_eur['total'],
            'reconciled_eur_due_csv': len(csv_lines) - 1,
            'reconciled_usd_unpaid_kpi': usd['operational_unpaid'],
            'reconciled_usd_unpaid_sessions': usd_unpaid['total'],
            'reconciled_usd_unpaid_csv': len(usd_csv_lines) - 1,
        }
        return results
    finally:
        frappe.db.rollback()
        final_count = frappe.db.count('Patient Appointment')
        assert final_count == initial_count, f"Rollback failed: {final_count} vs {initial_count}"


class TestMariaDBLoadAndReconciliation(unittest.TestCase):
    """Test MariaDB load and reconciliation on >500 appointments in isolated database."""

    def test_mariadb_load_and_reconciliation(self):
        if _is_running_in_frappe():
            res = _run_real_mariadb_test()
            self.assertEqual(res['status'], 'PASS')
            self.assertEqual(res['appointments_tested'], 550)
            self.assertEqual(res['reconciled_eur_due_kpi'], 425)
            self.assertEqual(res['reconciled_eur_due_sessions'], 425)
            self.assertEqual(res['reconciled_eur_due_csv'], 425)
            return

        target_backend = os.environ.get('CC_VOLUME_TEST_BACKEND')
        if not target_backend:
            raise unittest.SkipTest("Skipping real MariaDB load test: CC_VOLUME_TEST_BACKEND not set and not running in Frappe")

        # Refuse to run against shared DEV or production containers
        if 'centrochange-dev' in target_backend or 'prod' in target_backend:
            raise RuntimeError(f"Safety violation: CC_VOLUME_TEST_BACKEND must not target shared DEV or PROD container ({target_backend})")

        import subprocess
        try:
            check = subprocess.run(
                ['docker', 'inspect', '-f', '{{.State.Running}}', target_backend],
                capture_output=True, text=True, timeout=3
            )
            is_running = (check.returncode == 0 and 'true' in check.stdout.lower())
        except Exception:
            is_running = False

        if not is_running:
            raise unittest.SkipTest(f"Isolated Frappe/MariaDB container {target_backend} is not running")

        # Run inside isolated container with worktree code injected
        root_dir = Path(__file__).resolve().parents[1]
        reporting_file = root_dir / 'app/centrochange_core/centrochange_core/operations/reporting.py'
        reporting_code = reporting_file.read_text(encoding='utf-8')

        harness_script = f"""
import frappe, types, sys
reporting_code = {repr(reporting_code)}
mod = types.ModuleType('centrochange_core.operations.reporting')
mod.__file__ = 'reporting.py'
exec(reporting_code, mod.__dict__)
sys.modules['centrochange_core.operations.reporting'] = mod

test_file = {repr(Path(__file__).read_text(encoding='utf-8'))}
test_mod = types.ModuleType('test_mdb')
exec(test_file, test_mod.__dict__)

import json
res = test_mod._run_real_mariadb_test()
print('RESULT_JSON:' + json.dumps(res))
"""
        proc = subprocess.run(
            ['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', target_backend, 'env/bin/python'],
            input=harness_script,
            text=True,
            capture_output=True,
            timeout=60
        )
        if proc.returncode != 0:
            self.fail(f"MariaDB load test failed (code {proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

        import json
        for line in proc.stdout.splitlines():
            if line.startswith('RESULT_JSON:'):
                res = json.loads(line[len('RESULT_JSON:'):])
                self.assertEqual(res['status'], 'PASS')
                self.assertEqual(res['appointments_tested'], 550)
                self.assertEqual(res['reconciled_eur_due_kpi'], 425)
                self.assertEqual(res['reconciled_eur_due_sessions'], 425)
                self.assertEqual(res['reconciled_eur_due_csv'], 425)
                self.assertEqual(res['reconciled_usd_unpaid_kpi'], 20)
                self.assertEqual(res['reconciled_usd_unpaid_sessions'], 20)
                self.assertEqual(res['reconciled_usd_unpaid_csv'], 20)
                return

        self.fail(f"No result JSON found in output:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")


if __name__ == '__main__':
    unittest.main()
