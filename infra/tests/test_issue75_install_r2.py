"""Issue #75 second attempt retains read-only security gates without stale Manager login."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


EXECUTOR = Path(__file__).resolve().parents[1] / 'issue75_form_affordance_install.py'
spec = importlib.util.spec_from_file_location('issue75_r2_executor_test', EXECUTOR)
executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(executor)


class BrowserGateTests(unittest.TestCase):
    def test_manager_is_deferred_but_remaining_critical_checks_are_required(self):
        seen = []
        original = executor._browser

        def fake(script, output, **kwargs):
            seen.append(script)
            output.mkdir()
            (output / 'devfirst-readonly.json').write_text(json.dumps({
                'status': 'ESSENTIAL_PASS', 'deferred_roles': ['m'],
                'critical': [{'status': 'PASS'} for _ in range(27)],
            }))
            return 'browser passed'

        executor._browser = fake
        try:
            with tempfile.TemporaryDirectory() as temp:
                result = executor.browser_with_manager_login_deferred(
                    'mvp_devfirst_readonly.cjs', Path(temp) / 'browser')
            self.assertEqual(result, 'browser passed')
            self.assertEqual(seen, ['issue75_dev_readonly_without_manager.cjs'])
        finally:
            executor._browser = original

    def test_missing_or_failed_security_check_blocks(self):
        original = executor._browser

        def fake(script, output, **kwargs):
            output.mkdir()
            (output / 'devfirst-readonly.json').write_text(json.dumps({
                'status': 'ESSENTIAL_PASS', 'deferred_roles': ['m'],
                'critical': [{'status': 'PASS'} for _ in range(26)]
                + [{'status': 'FAIL'}],
            }))
            return 'incorrect pass'

        executor._browser = fake
        try:
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(executor.gate.Stop):
                    executor.browser_with_manager_login_deferred(
                        'mvp_devfirst_readonly.cjs', Path(temp) / 'browser')
        finally:
            executor._browser = original


if __name__ == '__main__':
    unittest.main()
