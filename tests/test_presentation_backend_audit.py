"""Ensure the production data-flow auditor remains read-only and site-bound."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "infra" / "audit_presentation_backend_readonly.py"

# No side-effectful Frappe operations may be introduced into this audit file.
WRITE_METHODS = {
    "insert", "save", "submit", "cancel", "delete", "delete_doc",
    "set_value", "set_single_value", "commit", "truncate", "rollback",
    "enqueue", "sendmail", "send", "sql", "db_set", "set_user",
    "run",  # Only invoke explicitly; exclude audit's own run() definition below.
}


class ReadOnlyBackendAuditTest(unittest.TestCase):
    def test_python_is_parseable_and_contains_no_write_calls(self):
        source = AUDIT.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(AUDIT))
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            if isinstance(target, ast.Attribute) and target.attr in WRITE_METHODS:
                violations.append((node.lineno, target.attr))
            if isinstance(target, ast.Name) and target.id in ("exec", "eval", "open", "system"):
                violations.append((node.lineno, target.id))
        self.assertFalse(violations, f"Side effects are forbidden in audit: {violations}")
        required = [
            "cc_presentation_site", "cc_synthetic_dev", "Administrator",
            "Patient Appointment", "CC Economic Source Link",
            "CC Operational Receipt", "patient_view", "professional",
            "cc_fiscal_mapping_confirmed", "cc_external_payer",
            "cash_392_EUR", "customer_and_professional_cash_reconciliation"
        ]
        for snippet in required:
            self.assertIn(snippet, source)

    def test_time_normalization_matches_frappe_and_recipe(self):
        import importlib.util
        from datetime import time, timedelta
        spec = importlib.util.spec_from_file_location("cc_readonly_audit_time", AUDIT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for sample in ("9:00", "09:00", "9:00:00", time(9, 0),
                       timedelta(hours=9)):
            self.assertEqual(module.normalize_hhmm(sample), "09:00")
        self.assertEqual(module.normalize_hhmm("14:30:00"), "14:30")
        for invalid in ("25:00", "9:61", "foo"):
            with self.assertRaises(ValueError):
                module.normalize_hhmm(invalid)

    def test_audit_is_not_an_endpoint(self):
        source = AUDIT.read_text(encoding="utf-8")
        self.assertNotIn("@frappe.whitelist", source)
        self.assertNotIn("frappe.db.sql", source)


if __name__ == "__main__":
    unittest.main()
