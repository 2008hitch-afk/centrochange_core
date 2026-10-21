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


if __name__ == "__main__":
    unittest.main()
