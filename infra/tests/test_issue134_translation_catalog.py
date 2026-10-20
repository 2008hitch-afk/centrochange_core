"""Pinned Frappe v16 CSV translation contract and Agenda immutability."""
import csv
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / 'app/centrochange_core/centrochange_core/translations/it.csv'
AGENDA = (
    'app/centrochange_core/centrochange_core/centro_change_core/page/'
    'cc_unified_desk/cc_unified_desk.css',
    'app/centrochange_core/centrochange_core/public/css/workspace.css',
)
BASE = '74de552e42dda437d82eae44f7b57418864102c4'


class ItalianCatalogTests(unittest.TestCase):
    def test_csv_has_unique_nonempty_translations(self):
        seen = {}
        with CSV.open(newline='', encoding='utf-8') as stream:
            for number, row in enumerate(csv.reader(stream), 1):
                self.assertIn(len(row), (2, 3), number)
                self.assertTrue(row[0].strip() and row[1].strip(), number)
                key = (row[0], row[2] if len(row) == 3 else '')
                self.assertNotIn(key, seen, (number, seen.get(key)))
                seen[key] = row[1]
        self.assertEqual(seen[('Charges', 'Healthcare Practitioner')], 'Tariffe professionali')
        self.assertEqual(seen[('Occupation', '')], 'Professione')
        self.assertEqual(seen[('Immutable Incoming Source', '')],
                         'Origine del documento ricevuto (non modificabile)')
        # These keys come from a rendered, role-based browser inventory, not
        # from a static scan of the previous list of 46 known strings.
        for source in (
            'Clear all filters', '1 Filter Applied', 'Internal Transfer', 'Payment',
            'Credit Note Issued', 'Unpaid and Discounted',
            'Partly Paid and Discounted', 'Overdue and Discounted',
            'Debit Note Issued', 'Add attachment', 'Disable Rounded Total',
            'Stock Ledger', 'On Net Total',
            'Select, to make the practitioner searchable with these fields',
            'All active prices for this item across buying and selling price lists.',
        ):
            self.assertIn((source, ''), seen)

    def test_agenda_source_bytes_unchanged(self):
        for relative in AGENDA:
            old = subprocess.check_output(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT)
            self.assertEqual((ROOT / relative).read_bytes(), old, relative)
        # The shared workspace module also renders the separate Notifications
        # detail panel. Only its confirmation text presenter may differ.
        workspace = 'app/centrochange_core/centrochange_core/public/js/workspace.js'
        old = subprocess.check_output(['git', 'show', f'{BASE}:{workspace}'], cwd=ROOT).decode()
        new = (ROOT / workspace).read_text()
        without_confirmation = lambda value: re.sub(r'^function confirmationText\(.*$', '', value, flags=re.M)
        self.assertEqual(without_confirmation(new), without_confirmation(old))


if __name__ == '__main__':
    unittest.main()
