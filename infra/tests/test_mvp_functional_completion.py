"""Offline guard tests for the MVP functional completion candidate."""
import ast
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'app/centrochange_core/centrochange_core'


def source(relative):
    return (ROOT/relative).read_text()


class MvpFunctionalCompletionTests(unittest.TestCase):
    def test_pos_is_single_native_payment_and_keeps_existing_security_boundary(self):
        for relative in ('app/centrochange_core/centrochange_core/finance/receivables.py',
                         'app/centrochange_core/centrochange_core/finance/incoming.py'):
            tree=ast.parse(source(relative))
            pay=next(node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='pay')
            self.assertIn('mode_of_payment',[arg.arg for arg in pay.args.args])
            text=source(relative)
            self.assertIn('payment_mode_account(selected_mode',text)
            self.assertIn('payload=[name,str(amount),str(posting_date),reference,bank_account]',text)
            self.assertIn('if selected_mode:',text)
            self.assertIn('cc_request_hash',text)
        adapter=source('app/centrochange_core/centrochange_core/finance/native_adapter.py')
        self.assertIn("mode.enabled",adapter)
        self.assertIn("account.company != company",adapter)
        self.assertIn("account.account_type not in ('Bank', 'Cash')",adapter)
        self.assertIn("payment.append('references'",adapter)
        self.assertIn("'mode_of_payment': mode_of_payment or invoice.get('mode_of_payment')",adapter)
        acceptance=source('app/centrochange_core/centrochange_core/finance/receivables_acceptance.py')
        self.assertIn('single manual card/POS receipt',acceptance)
        self.assertIn('Synthetic POS retry',acceptance)
        self.assertNotIn("'type':'Credit Card'",acceptance)
        self.assertIn('_mode_of_payment_type_for_account',acceptance)

    def test_synthetic_card_mode_uses_pinned_erpnext_native_type(self):
        relative='app/centrochange_core/centrochange_core/finance/receivables_acceptance.py'
        tree=ast.parse(source(relative))
        helper=next(node for node in ast.walk(tree)
                    if isinstance(node,ast.FunctionDef) and node.name=='_mode_of_payment_type_for_account')
        account_type_lookup=any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                                and node.func.attr=='get_value' and len(node.args)>=3
                                and isinstance(node.args[0],ast.Constant) and node.args[0].value=='Account'
                                and isinstance(node.args[2],ast.Constant) and node.args[2].value=='account_type'
                                for node in ast.walk(helper))
        allowed_values=any(isinstance(node,ast.Compare) and isinstance(node.ops[0],ast.NotIn)
                           and isinstance(node.comparators[0],ast.Tuple)
                           and {item.value for item in node.comparators[0].elts
                                if isinstance(item,ast.Constant)}=={'Bank','Cash'}
                           for node in ast.walk(helper))
        self.assertTrue(account_type_lookup)
        self.assertTrue(allowed_values)
        mode_docs=[]
        for node in ast.walk(tree):
            if not isinstance(node,ast.Dict):
                continue
            values={key.value:value for key,value in zip(node.keys,node.values)
                    if isinstance(key,ast.Constant) and isinstance(key.value,str)}
            if isinstance(values.get('doctype'),ast.Constant) and values['doctype'].value=='Mode of Payment':
                mode_docs.append(values)
        self.assertEqual(len(mode_docs),2)
        for doc in mode_docs:
            mode_type=doc.get('type')
            self.assertIsInstance(mode_type,ast.Call)
            self.assertIsInstance(mode_type.func,ast.Name)
            self.assertEqual(mode_type.func.id,'_mode_of_payment_type_for_account')

    def test_browser_invoice_captures_closed_fixture_revision(self):
        text=source('app/centrochange_core/centrochange_core/finance/receivables_acceptance.py')
        section=text.split('def prepare_browser_invoice(fixture):')[1].split('def rejected')[0]
        self.assertLess(section.index('lifecycle.close('),section.index('source=bridge.capture('))
        self.assertLess(section.index('source=bridge.capture('),section.index('invoice=ar.draft('))
        self.assertIn("appointment.patient in fixture['patients']",section)
        self.assertIn('not appointment.cc_package',section)
        self.assertIn('frappe.flags.cc_test_clock=previous',section)

    def test_native_reports_remain_allowlisted_and_center_scoped(self):
        reports=source('app/centrochange_core/centrochange_core/finance/native_reports.py')
        self.assertIn('REPORTS = {"general_ledger", "trial_balance"}',reports)
        self.assertIn('require_finance(center)',reports)
        self.assertIn('operational_centers()',reports)
        self.assertIn('branch.cc_company',reports)
        self.assertIn('branch.cc_cost_center',reports)
        self.assertIn('MAX_ROWS = 2000',reports)
        self.assertIn('Fiscal Year',reports)
        guard=source('app/centrochange_core/centrochange_core/finance/request_guard.py')
        self.assertIn("'frappe.desk.query_report.'",guard)
        self.assertIn("'erpnext.accounts.'",guard)
        self.assertNotIn('native_reports',guard)

    def test_private_native_attachment_service_is_narrow(self):
        attachments=source('app/centrochange_core/centrochange_core/finance/attachments.py')
        files=source('app/centrochange_core/centrochange_core/finance/files.py')
        self.assertIn("PARENTS = {'Sales Invoice', 'Purchase Invoice', 'Bank Transaction', 'CC Incoming Invoice'}",attachments)
        self.assertIn('require_finance(center, write)',attachments)
        self.assertIn('doc.check_permission(\'read\')',attachments)
        self.assertIn('save_file(safe_name, raw, parent.doctype, parent.name, is_private=1)',attachments)
        self.assertIn('MAX_BYTES = 5 * 1024 * 1024',attachments)
        self.assertIn("'.pdf': (b'%PDF-',)",attachments)
        self.assertIn("'.png': (b'\\x89PNG",attachments)
        self.assertIn('financial_attachment_context(doc)',files)
        self.assertIn("frappe.flags.get('cc_finance_attachment_write')",files)
        self.assertIn('financial_attachment_context(doc)',files)
        self.assertIn('Gli allegati finanziari devono restare privati.',files)
        self.assertIn("append('FINANCIAL_DOCUMENT_ATTACHED'",attachments)

    def test_human_exports_use_italian_headers_and_european_dates(self):
        for relative in ('app/centrochange_core/centrochange_core/finance/reporting.py',
                         'app/centrochange_core/centrochange_core/finance/patient_reporting.py',
                         'app/centrochange_core/centrochange_core/operations/reporting.py'):
            text=source(relative)
            self.assertIn("formatdate",text,relative)
        finance=source('app/centrochange_core/centrochange_core/finance/reporting.py')
        self.assertIn('Tipo documento',''+finance)
        self.assertIn('Metodo di pagamento',finance)
        patient=source('app/centrochange_core/centrochange_core/finance/patient_reporting.py')
        self.assertIn('Scadenza effettiva',patient)
        operational=source('app/centrochange_core/centrochange_core/operations/reporting.py')
        self.assertIn("'Data','Ora','Paziente'",operational)

    def test_native_multiselect_keeps_set_semantics_and_mobile_width(self):
        search=source('app/centrochange_core/centrochange_core/public/js/search_select.js')
        self.assertIn('!select.multiple',search)
        self.assertIn('set semantics',search)
        css=source('app/centrochange_core/centrochange_core/public/css/workspace.css')
        self.assertIn('select[multiple]',css)
        self.assertIn('max-width:100%',css)
        self.assertIn('min-width:0',css)

    def test_obsolete_rc22_ids_and_test_source_rewrite_are_removed(self):
        for relative in ('app/centrochange_core/centrochange_core/finance/bank_trace_acceptance.py',
                         'app/centrochange_core/centrochange_core/finance/expectation_ui_acceptance.py',
                         'app/centrochange_core/centrochange_core/security/audit_view_acceptance.py',
                         'app/centrochange_core/centrochange_core/scheduling/reopen_acceptance.py',
                         'infra/browser/bank_trace.cjs'):
            text=source(relative)
            for stale in ('ACC-SINV-2026-00081','HLC-APP-2026-00132','HLC-APP-2026-00133'):
                self.assertNotIn(stale,text,relative)
        probe=source('infra/audit/mvp_rollback_probe.py')
        self.assertNotIn('source.replace(',probe)
        self.assertIn('never rewrites tests in memory',probe)
        surface=source('app/centrochange_core/centrochange_core/operations/surfaces_acceptance.py')
        self.assertIn('ora della seduta non esiste o è ambigua',surface)
        self.assertNotIn('Ambiguous or nonexistent',surface)

    def test_browser_payment_fixture_is_owned_and_recoverable(self):
        runner=source('infra/finance_browser_acceptance.py')
        self.assertIn('prepare_browser_invoice',runner)
        browser=source('infra/browser/finance.cjs')
        self.assertIn('fixture.receivable.invoice',browser)
        fixture=source('app/centrochange_core/centrochange_core/finance/receivables_acceptance.py')
        self.assertIn("fixture.get('finance',{}).get('source')",fixture)
        self.assertNotIn("'type':'Credit Card'",fixture)
        self.assertIn("'type':_mode_of_payment_type_for_account(account)",fixture)
        cleanup=source('app/centrochange_core/centrochange_core/security/dev_acceptance.py')
        self.assertIn("browser_pos=tag+' BROWSER POS'",cleanup)
        self.assertIn("finance.attachments.attach",browser)
        self.assertIn('authorizedBytes.equals(pdf)',browser)
        self.assertIn('authorizedBytes.equals(pdf)',browser)
        self.assertIn('native_reports.run',source('infra/browser/native_reports.cjs'))
        self.assertIn("cleanup.get('cleanup')!='PASS'",runner)
        self.assertIn("cleanup.get('cleanup')!='PASS'",source('infra/reporting_acceptance.py'))
        self.assertIn("cleanup.get('cleanup')!='PASS'",runner)
        self.assertIn("cleanup.get('cleanup')!='PASS'",source('infra/reporting_acceptance.py'))


if __name__=='__main__':
    unittest.main()
