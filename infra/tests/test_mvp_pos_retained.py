"""Guards for the single-site, retained-ledger POS acceptance fixture."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = (ROOT / 'infra/mvp_pos_retained_runtime.py').read_text()
HOST = (ROOT / 'infra/mvp_pos_retained_acceptance.py').read_text()


class RetainedPosFixture(unittest.TestCase):
    def test_no_direct_accounting_delete_or_global_settings_mutation(self):
        tree = ast.parse(RUNTIME)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        called = {ast.unparse(call.func) for call in calls}
        self.assertFalse({'frappe.delete_doc', 'frappe.db.delete',
                          'native_accounting_cleanup'} & called)
        self.assertIn('payment.cancel', called)
        self.assertIn('receivables.cancel', called)
        self.assertNotIn("set_value('Accounts Settings'", RUNTIME)

    def test_fixture_has_native_italian_invoice_prerequisites(self):
        self.assertIn("'fiscal_code': 'SYNTHETICDEV00000'", RUNTIME)
        self.assertIn("'customer_type': 'Individual'", RUNTIME)
        self.assertIn("'type': 'Bank'", RUNTIME)
        self.assertIn('2099-01-12', RUNTIME)
        self.assertIn("p.docstatus<2", RUNTIME)
        self.assertIn('frappe.db.rollback()', RUNTIME)

    def test_host_checks_backup_baseline_and_preexisting_documents(self):
        tree = ast.parse(HOST)
        called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        for required in ('backup_ok', 'module.runtime_fingerprint',
                         'preexisting_records', 'gate.permission_fingerprint'):
            self.assertIn(required, called)
        self.assertIn("runtime('preflight'", HOST)
        self.assertIn("runtime('finalize'", HOST)
        self.assertNotIn('recover_http', HOST)


if __name__ == '__main__':
    unittest.main()
