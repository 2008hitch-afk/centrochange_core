"""Tests for exception propagation around Frappe acceptance fixtures."""
import json
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra"))

import fixture_command


METHOD = "centrochange_core.finance.receivables_acceptance.prepare_browser_invoice"


class FixtureCommandTests(unittest.TestCase):
    def test_traceback_keeps_exception_cause_and_context_but_redacts_values(self):
        raw = '''Traceback (most recent call last):
  File "/home/frappe/frappe-bench/apps/centrochange_core/finance/receivables_acceptance.py", line 24, in prepare_browser_invoice
    raise frappe.ValidationError("bad patient")
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/home/frappe/frappe-bench/apps/frappe/frappe/commands/utils.py", line 280, in execute
frappe.ValidationError: account "SINV-SYN-0001" for jane@example.invalid password=hunter2 token=abc123 customer=CUST-001
'''
        value = fixture_command.sanitize_diagnostic(raw)
        self.assertIn("frappe.ValidationError", value)
        self.assertIn("prepare_browser_invoice", value)
        self.assertIn("During handling of the above exception", value)
        self.assertIn("password=[REDACTED]", value)
        self.assertIn("token=[REDACTED]", value)
        self.assertIn("[REDACTED_EMAIL]", value)
        self.assertNotIn("hunter2", value)
        self.assertNotIn("abc123", value)
        self.assertNotIn("SINV-SYN-0001", value)
        self.assertNotIn("CUST-001", value)

    def test_fixture_invocation_uses_direct_driver_not_bench_execute(self):
        envelope = {"status": "PASS", "value": {"name": "synthetic"}}
        completed = fixture_command.subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=fixture_command.RESULT_PREFIX + json.dumps(envelope) + "\n", stderr="")
        with patch.object(fixture_command.subprocess, "run", return_value=completed) as run:
            self.assertEqual(fixture_command.execute_fixture(METHOD, {"fixture": {"tag": "CC-HTTP-test"}}), envelope["value"])
        command = run.call_args.args[0]
        self.assertIn("FRAPPE_STREAM_LOGGING=1", command)
        self.assertNotIn("execute", command)
        self.assertEqual(command[-3], "env/bin/python")
        self.assertEqual(command[-2], "-c")
        request = json.loads(run.call_args.kwargs["input"])
        self.assertEqual(request["method"], METHOD)
        self.assertEqual(request["site"], "centrochange.local")

    def test_failure_preserves_sanitized_original_exception_in_private_file(self):
        diagnostic = '''Traceback (most recent call last):
  File "/home/frappe/frappe-bench/apps/centrochange_core/finance/receivables_acceptance.py", line 24, in prepare_browser_invoice
frappe.ValidationError: customer "synthetic" password=raw-password sample@example.invalid
'''
        envelope = {"status": "ERROR", "diagnostic": diagnostic, "rollback_error_type": None}
        completed = fixture_command.subprocess.CompletedProcess(
            args=[], returncode=2,
            stdout=fixture_command.RESULT_PREFIX + json.dumps(envelope) + "\n", stderr="")
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(fixture_command.subprocess, "run", return_value=completed):
                with self.assertRaises(fixture_command.FixtureCommandError) as caught:
                    fixture_command.execute_fixture(METHOD, diagnostic_dir=temporary)
            error = caught.exception
            self.assertEqual(error.method, METHOD)
            self.assertEqual(error.returncode, 2)
            self.assertIn("frappe.ValidationError", error.diagnostic)
            self.assertIn("password=[REDACTED]", error.diagnostic)
            self.assertNotIn("raw-password", error.diagnostic)
            self.assertIsNotNone(error.diagnostic_path)
            self.assertEqual(error.diagnostic_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(temporary).stat().st_mode & 0o777, 0o700)
            saved = error.diagnostic_path.read_text()
            self.assertIn("frappe.ValidationError", saved)
            self.assertNotIn("raw-password", saved)

    def test_fixture_method_and_target_are_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "not allowlisted"):
            fixture_command.execute_fixture("frappe.db.sql")
        with self.assertRaisesRegex(ValueError, "outside the approved"):
            fixture_command.execute_fixture(METHOD, backend="unrelated-backend-1")
        with self.assertRaisesRegex(ValueError, "outside the approved"):
            fixture_command.execute_fixture(METHOD, site="another.local")

    def test_failure_path_rolls_back_before_returning_diagnostics(self):
        self.assertIn("frappe.db.rollback()", fixture_command._DRIVER)
        self.assertIn("frappe.db.commit()", fixture_command._DRIVER)
        self.assertIn("cc_synthetic_dev", fixture_command._DRIVER)
        self.assertIn('frappe.set_user("Administrator")', fixture_command._DRIVER)

    def test_fixture_failures_do_not_leak_success_payload_if_process_exits_late(self):
        envelope = {"status": "PASS", "value": {"password": "do-not-log"}}
        completed = fixture_command.subprocess.CompletedProcess(
            args=[], returncode=2,
            stdout=fixture_command.RESULT_PREFIX + json.dumps(envelope) + "\n", stderr="")
        with patch.object(fixture_command.subprocess, "run", return_value=completed):
            with self.assertRaises(fixture_command.FixtureCommandError) as caught:
                fixture_command.execute_fixture(METHOD)
        self.assertNotIn("do-not-log", str(caught.exception))
        self.assertIn("without a structured Frappe diagnostic", str(caught.exception))

    def test_shared_security_fixture_runner_no_longer_discards_or_exposes_traceback(self):
        import security_acceptance
        envelope = {"status": "ERROR", "diagnostic": "Traceback (most recent call last):\nfrappe.ValidationError: password=secret123", "rollback_error_type": None}
        completed = fixture_command.subprocess.CompletedProcess(
            args=[], returncode=2,
            stdout=fixture_command.RESULT_PREFIX + json.dumps(envelope) + "\n", stderr="")
        with patch.object(fixture_command.subprocess, "run", return_value=completed):
            with self.assertRaises(fixture_command.FixtureCommandError) as caught:
                security_acceptance.execute(METHOD)
        self.assertIn("frappe.ValidationError", str(caught.exception))
        self.assertIn("password=[REDACTED]", str(caught.exception))
        self.assertNotIn("secret123", str(caught.exception))

    def test_related_fixture_flows_use_the_same_diagnostic_transport(self):
        shared = ("finance_acceptance.py", "banking_acceptance.py", "incoming_acceptance.py",
                  "receivables_acceptance.py", "reporting_acceptance.py", "professional_acceptance.py",
                  "sdi_acceptance.py", "ts_acceptance.py")
        for name in shared:
            source = (ROOT / "infra" / name).read_text()
            self.assertIn("from security_acceptance import execute", source, name)
        for name in ("browser_acceptance.py", "finance_browser_acceptance.py"):
            source = (ROOT / "infra" / name).read_text()
            self.assertIn("from fixture_command import execute_fixture", source, name)
            self.assertNotIn("Private DEV fixture command failed", source, name)

        relevant = shared + ("security_acceptance.py", "browser_acceptance.py", "finance_browser_acceptance.py")
        for name in relevant:
            tree = ast.parse((ROOT / "infra" / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
                    method = node.args[0].value
                    if isinstance(method, str) and method.startswith("centrochange_core."):
                        self.assertIn(method, fixture_command.ALLOWED_METHODS, f"{name}: {method}")


if __name__ == "__main__":
    unittest.main()
