import csv
import json
from pathlib import Path
import tempfile
import unittest

from infra.issue134_review_inventory import review


class RenderedInventoryReviewTests(unittest.TestCase):
    def test_keeps_every_visible_string_not_only_known_english(self):
        screens=[{'role':'f','width':1440,'screen':'/app/purchase-invoice',
                  'items':[{'kind':'text','text':'A new untranslated native phrase'},
                           {'kind':'title','text':'11:05:49'},
                           {'kind':'text','text':'Data 2026-10-20'},
                           {'kind':'text','text':'Nessuna fattura'}]}]
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.json'; output=Path(tmp)/'review.csv'
            source.write_text(json.dumps(screens))
            result=review([source],output)
            with output.open(newline='') as stream: rows=list(csv.DictReader(stream))
        self.assertEqual(result['unique_visible_items'],4)
        self.assertEqual({row['text'] for row in rows},
                         {'A new untranslated native phrase','11:05:49',
                          'Data 2026-10-20','Nessuna fattura'})
        self.assertIn('VISIBLE_SECONDS',rows[[r['text'] for r in rows].index('11:05:49')]['hint'])
        self.assertIn('VISIBLE_ISO_DATE',rows[[r['text'] for r in rows].index('Data 2026-10-20')]['hint'])


if __name__=='__main__': unittest.main()
