"""Frappe wraps MariaDB 1020/1213 as QueryDeadlockError before service handlers see it."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "app/centrochange_core/centrochange_core/security/audit.py"


class AtomicDeadlockRollbackTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        frappe = types.ModuleType("frappe")
        frappe.QueryDeadlockError = type("QueryDeadlockError", (Exception,), {})
        frappe.generate_hash = lambda length: "testsavepoint"
        frappe.db = types.SimpleNamespace(
            savepoint=lambda point: self.calls.append(("savepoint", point)),
            rollback=lambda **kwargs: self.calls.append(("rollback", kwargs)),
            is_deadlocked=lambda error: False,  # wrapper is not MySQLdb.Error
        )
        self.frappe = frappe
        self.modules = patch.dict(sys.modules, {"frappe": frappe})
        self.modules.start()
        spec = importlib.util.spec_from_file_location("cc_audit_deadlock_test", SOURCE)
        self.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.audit)

    def tearDown(self):
        self.modules.stop()

    def test_frappe_wrapped_deadlock_discards_savepoint_and_preserves_error(self):
        @self.audit.atomic
        def operation():
            raise self.frappe.QueryDeadlockError("synthetic conflict")

        with self.assertRaises(self.frappe.QueryDeadlockError):
            operation()
        self.assertEqual(self.calls, [("savepoint", "cc_testsavepoint"), ("rollback", {})])

    def test_ordinary_error_uses_service_savepoint(self):
        @self.audit.atomic
        def operation():
            raise ValueError("synthetic validation")

        with self.assertRaises(ValueError):
            operation()
        self.assertEqual(self.calls, [
            ("savepoint", "cc_testsavepoint"),
            ("rollback", {"save_point": "cc_testsavepoint"}),
        ])

    def test_db_only_service_retries_once_after_full_rollback(self):
        attempts = []

        @self.audit.retry_deadlock_once
        @self.audit.atomic
        def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise self.frappe.QueryDeadlockError("synthetic conflict")
            return "ok"

        self.assertEqual(operation(), "ok")
        self.assertEqual(attempts, [1, 2])
        self.assertEqual(self.calls, [
            ("savepoint", "cc_testsavepoint"), ("rollback", {}),
            ("savepoint", "cc_testsavepoint"),
        ])

    def test_db_only_service_does_not_retry_unbounded(self):
        attempts = []

        @self.audit.retry_deadlock_once
        @self.audit.atomic
        def operation():
            attempts.append(1)
            raise self.frappe.QueryDeadlockError("synthetic conflict")

        with self.assertRaises(self.frappe.QueryDeadlockError):
            operation()
        self.assertEqual(len(attempts), 2)
        self.assertEqual([row for row in self.calls if row[0] == "rollback"],
                         [("rollback", {}), ("rollback", {})])


if __name__ == "__main__":
    unittest.main()
