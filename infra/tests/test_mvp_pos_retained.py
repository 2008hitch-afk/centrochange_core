"""Guards for the single-site, retained-ledger POS acceptance fixture."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = (ROOT / 'infra/mvp_pos_retained_runtime.py').read_text()
HOST = (ROOT / 'infra/mvp_pos_retained_acceptance.py').read_text()
BROWSER = (ROOT / 'infra/browser/mvp_pos_retained_live.cjs').read_text()


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
        self.assertIn("frappe.utils.add_days('2099-01-12', 7 * week)", RUNTIME)
        self.assertIn("'appointment_date': appointment_date", RUNTIME)
        self.assertIn("p.docstatus<2", RUNTIME)
        self.assertIn('frappe.db.rollback()', RUNTIME)
        self.assertIn('open administrative exception has an unexpected missing source', RUNTIME)
        self.assertIn("row.reference_name == 'oqgogla0e5'", RUNTIME)
        self.assertIn("if stage == 'prepare':", RUNTIME)
        self.assertIn('admin_queue.refresh(center.name', RUNTIME)

    def test_host_checks_backup_baseline_and_preexisting_documents(self):
        tree = ast.parse(HOST)
        called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        for required in ('backup_ok', 'module.runtime_fingerprint',
                         'preexisting_records', 'gate.permission_fingerprint'):
            self.assertIn(required, called)
        self.assertIn("runtime('preflight'", HOST)
        self.assertIn("runtime('finalize'", HOST)
        self.assertIn('permission_scope_after_fixture(module, tag)', HOST)
        self.assertIn("'preexisting_permissions':", HOST)
        self.assertIn("'fixture_shares':", HOST)
        self.assertNotIn('recover_http', HOST)

    def test_browser_uses_live_login_control_and_waits_for_invoice_actions(self):
        self.assertIn('.form-login button[type="submit"]', BROWSER)
        self.assertNotIn('.form-login .btn-login', BROWSER)
        self.assertIn("name: 'Registra pagamento', exact: true}).waitFor()", BROWSER)
        self.assertIn("page.waitForFunction(name => document.querySelector('#detail')", BROWSER)
        self.assertIn('const professionalContext = await browser.newContext(', BROWSER)


if __name__ == '__main__':
    unittest.main()
