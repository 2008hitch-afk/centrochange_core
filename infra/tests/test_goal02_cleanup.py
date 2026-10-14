"""Offline checks for isolated GOAL-02 test cleanup and diagnostics."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load('app/centrochange_core/centrochange_core/security/fixture_cleanup.py', 'fixture_cleanup')
targeted = load('infra/goal02_targeted_regression.py', 'targeted_regression')
orphan = load('infra/goal02_orphan_cleanup.py', 'orphan_cleanup')


class CleanupContract(unittest.TestCase):
    def test_collects_confirmation_and_simulated_communication(self):
        confirmation = {'name': 'confirmation-1', 'appointment': 'fixture-appointment',
                        'center': 'fixture-center', 'recipient': 'demo@example.invalid',
                        'communication': 'communication-1'}
        communication = {'name': 'communication-1', 'reference_doctype': 'Patient Appointment',
                         'reference_name': 'fixture-appointment', 'recipients': 'demo@example.invalid'}
        expected = {'CC Booking Confirmation': ['confirmation-1'],
                    'Communication': ['communication-1']}
        self.assertEqual(fixture.confirmation_dependents(['fixture-appointment'], ['fixture-center'],
                         [confirmation], [communication]), expected)
        with self.assertRaises(AssertionError):
            fixture.confirmation_dependents(['other-appointment'], ['fixture-center'],
                                             [confirmation], [communication])
        with self.assertRaises(AssertionError):
            fixture.confirmation_dependents(['fixture-appointment'], ['fixture-center'],
                                             [confirmation], [])
        with self.assertRaises(AssertionError):
            fixture.confirmation_dependents(['fixture-appointment'], ['fixture-center'],
                                             [confirmation], [{**communication, 'recipients':'real@example.com'}])

    def test_private_log_uses_unique_file_and_keeps_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            stale = Path(directory) / 'cc-goal02-targeted-regression.log'
            stale.write_text('old report')
            first = targeted.private_failure_log('first', ' error', directory)
            second = targeted.private_failure_log('second', ' error', directory)
            self.assertNotEqual(first, second)
            self.assertEqual(stale.read_text(), 'old report')
            self.assertEqual(first.read_text(), 'first error')
            self.assertEqual(second.read_text(), 'second error')
            self.assertEqual(first.stat().st_mode & 0o777, 0o600)
            self.assertEqual(second.stat().st_mode & 0o777, 0o600)

    def test_private_log_rejects_symlink_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'real').mkdir()
            (root / 'link').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(RuntimeError):
                targeted.private_failure_log('', '', root / 'link')

    def test_orphan_plan_is_three_exact_rows_and_snapshot_gated(self):
        rows = {doctype: [{'name': name}] for doctype, name in orphan.NAMES.items()}
        payload = {'before': orphan.CURRENT, 'after': orphan.RESTORED, 'rows': rows}
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / 'snapshot.json'
            snapshot.write_text(__import__('json').dumps(payload))
            snapshot.chmod(0o600)
            sha = orphan.digest(snapshot.read_bytes())
            with patch.object(orphan, 'run_frappe', return_value={'status':'CLEANUP_PASS'}) as run:
                self.assertEqual(orphan.apply(snapshot, sha)['status'], 'CLEANUP_PASS')
                code = run.call_args.args[0]
                self.assertIn('for dt in ("CC Audit Event","Communication","CC Booking Confirmation")', code)
                self.assertIn('found=check_present()', code)
                self.assertIn('frappe.db.rollback();raise', code)
            with patch.object(orphan, 'run_frappe', return_value={'status':'RESTORE_PASS'}) as run:
                self.assertEqual(orphan.restore(snapshot, sha)['status'], 'RESTORE_PASS')
                self.assertIn('for dt in ("Communication","CC Booking Confirmation","CC Audit Event")',
                              run.call_args.args[0])
            snapshot.write_text(snapshot.read_text() + 'tampered')
            with self.assertRaises(RuntimeError):
                orphan.apply(snapshot, sha)


if __name__ == '__main__':
    unittest.main()
