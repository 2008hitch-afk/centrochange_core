"""Checks for the two presentation gaps observed on the installed DEV."""
import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RemainingMvpPresentationTests(unittest.TestCase):
    def test_native_accounting_headers_are_italian_without_changing_report_fields(self):
        source = (ROOT / 'app/centrochange_core/centrochange_core/finance/native_reports.py').read_text()
        tree = ast.parse(source)
        labels = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == 'COLUMN_LABELS'
                              for target in node.targets))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == '_column_label')
        namespace = {'frappe': type('Frappe', (), {'_': staticmethod(lambda value: value)})(), 're': re}
        exec(compile(ast.Module(body=[labels, function], type_ignores=[]), '<labels>', 'exec'), namespace)
        label = namespace['_column_label']
        for original, expected in {
            'Account': 'Conto', 'Opening (Dr)': 'Saldo iniziale (Dare)',
            'Closing (Cr)': 'Saldo finale (Avere)', 'Debit (EUR)': 'Dare (EUR)',
            'Voucher No': 'Numero documento', 'Supplier Invoice No': 'Numero fattura fornitore',
        }.items():
            self.assertEqual(label(original), expected)
        self.assertEqual(label('Custom pinned ERPNext column'), 'Custom pinned ERPNext column')
        self.assertIn('row.get(column.get("fieldname"))', source)

    def test_incoming_document_shares_existing_attachment_panel(self):
        source = (ROOT / 'app/centrochange_core/centrochange_core/public/js/finance_workspace.js').read_text()
        self.assertIn("attachmentPanel($('#detail'),'CC Incoming Invoice',row.name)", source)
        self.assertIn("attachmentPanel($('#detail'),dt,row.name)", source)


if __name__ == '__main__':
    unittest.main()
