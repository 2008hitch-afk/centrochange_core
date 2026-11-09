"""Offline read-only contract for STAGING professional + public booking preflight."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "infra" / "qa_professional_public_readonly.py"
FORBIDDEN = {"insert", "save", "submit", "cancel", "delete", "delete_doc",
             "set_value", "set_single_value", "commit", "rollback", "truncate",
             "set_user", "enqueue", "sendmail", "send", "sql", "db_set"}


class PresentationProfessionalPublicPreflightTest(unittest.TestCase):
    def test_script_is_read_only_and_scope_guards_exist(self):
        source = PREFLIGHT.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(PREFLIGHT))
        dangerous = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN:
                dangerous.append((node.lineno, node.func.attr))
            if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "open"}:
                dangerous.append((node.lineno, node.func.id))
        self.assertFalse(dangerous, dangerous)
        self.assertIn("cc_presentation_site", source)
        self.assertIn("cc_synthetic_dev", source)
        self.assertIn("Administrator", source)
        self.assertNotIn("@frappe.whitelist", source)

    def test_professional_acl_and_public_booking_require_both_directors(self):
        content = PREFLIGHT.read_text(encoding="utf-8")
        for fragment in ("professional", "patient_scope_and_fiscal_denial",
                         "four_distinct_enabled_system_users",
                         "both_director_routes_enabled", '"Marco", "Francesca"',
                         "guest_booking_service_user_enabled",
                         "routes_target_active_center_professionals",
                         "two_distinct_free_20_minute_modes",
                         "both_routes_have_schedule_windows",
                         "no_real_email_confirmation_enabled",
                         "READY_FOR_CLONE_HTTP"):
            self.assertIn(fragment, content)


if __name__ == "__main__":
    unittest.main()
