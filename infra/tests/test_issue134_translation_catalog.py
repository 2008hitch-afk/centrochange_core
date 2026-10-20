"""Pinned Frappe v16 CSV translation contract and Agenda immutability."""
import csv
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / 'app/centrochange_core/centrochange_core/translations/it.csv'
AGENDA = (
    'app/centrochange_core/centrochange_core/centro_change_core/page/'
    'cc_unified_desk/cc_unified_desk.css',
    'app/centrochange_core/centrochange_core/public/js/workspace.js',
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

    def test_agenda_source_bytes_unchanged(self):
        for relative in AGENDA:
            old = subprocess.check_output(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT)
            self.assertEqual((ROOT / relative).read_bytes(), old, relative)


if __name__ == '__main__':
    unittest.main()
