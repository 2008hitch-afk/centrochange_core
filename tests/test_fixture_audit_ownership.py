"""Financial fixture teardown removes only audit rows owned by that fixture."""

import importlib.util
from pathlib import Path
import unittest


MODULE = (Path(__file__).resolve().parents[1] / "app/centrochange_core/centrochange_core"
          / "security/fixture_cleanup.py")
SPEC = importlib.util.spec_from_file_location("cc_fixture_cleanup", MODULE)
cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup)


class FixtureAuditOwnershipTests(unittest.TestCase):
    def test_owned_voucher_audit_can_be_removed_before_native_voucher(self):
        groups = {"Payment Entry": ["PAY-1"], "CC Audit Event": ["AUD-1"]}
        events = [{"name": "AUD-1", "reference_doctype": "Payment Entry",
                   "reference_name": "PAY-1", "reason": "Another synthetic reason"}]
        self.assertEqual(cleanup.owned_audit_ids(events, groups, "CC-HTTP-ABC1234567"), ["AUD-1"])

    def test_unowned_or_missing_audit_fails_closed(self):
        groups = {"Payment Entry": ["PAY-1"], "CC Audit Event": ["AUD-1"]}
        with self.assertRaises(ValueError):
            cleanup.owned_audit_ids([], groups, "CC-HTTP-ABC1234567")
        with self.assertRaises(ValueError):
            cleanup.owned_audit_ids([{"name": "AUD-1", "reference_doctype": "Payment Entry",
                                      "reference_name": "PAY-OTHER", "reason": "Different"}],
                                    groups, "CC-HTTP-ABC1234567")

    def test_native_corrections_precede_original_invoice(self):
        class Voucher(dict):
            def __init__(self, name, **fields):
                super().__init__(fields)
                self.doctype = "Sales Invoice"
                self.name = name

        original = Voucher("INV-1")
        amendment = Voucher("INV-1-1", amended_from="INV-1")
        credit = Voucher("INV-1-CREDIT", return_against="INV-1")
        ordered = cleanup.native_dependents_first(
            [original, amendment, credit], ("Sales Invoice",)
        )
        self.assertEqual(ordered[-1].name, "INV-1")
        self.assertEqual({row.name for row in ordered[:-1]}, {"INV-1-1", "INV-1-CREDIT"})

    def test_only_named_fixture_native_dependents_are_selected(self):
        groups = {"CC Admin Exception": ["EX-1", "EX-1"],
                  "CC Payment Override": ["OVERRIDE-1"],
                  "CC Notification": ["NOTICE-1"],
                  "CC TS Input Review": ["TS-1"], "Patient": ["PAT-1"]}
        selected = cleanup.native_link_dependents(groups)
        self.assertEqual(selected["CC Admin Exception"], ["EX-1"])
        self.assertEqual(selected["CC TS Input Review"], ["TS-1"])
        self.assertEqual(selected["CC Payment Override"], ["OVERRIDE-1"])
        self.assertEqual(selected["CC Notification"], ["NOTICE-1"])
        self.assertNotIn("Patient", selected)


if __name__ == "__main__":
    unittest.main()
