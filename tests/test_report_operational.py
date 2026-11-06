import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/finance/report_operational.py'
spec = importlib.util.spec_from_file_location('report_operational', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ReportOperationalTests(unittest.TestCase):
    def test_partial_reversal_and_payment_date_are_separate_from_session_date(self):
        sessions = [dict(name='A', cc_price_snapshot=44, cc_currency_snapshot='EUR', cc_economic_state='Due', cc_paid=0), dict(name='B', cc_price_snapshot=0, cc_currency_snapshot='EUR', cc_economic_state='Non Due', cc_paid=0)]
        receipts = [dict(receipt_date='2026-01-02', allocations='[{"appointment":"A","cents":3000}]'), dict(receipt_date='2026-02-02', allocations='[{"appointment":"A","cents":-500,"reversal_of":"R"}]')]
        data = module.summarize(sessions, receipts, '2026-02-01', '2026-02-28')
        self.assertEqual(data['cash_cents'], -500)
        self.assertEqual(data['sessions']['A']['state'], 'Parziale')
        self.assertEqual(data['sessions']['A']['remaining_cents'], 1900)
        self.assertEqual(data['sessions']['B']['state'], 'Non dovuto')
    def test_pending_unknown_and_legacy_paid_do_not_invent_cash(self):
        sessions = [dict(name='A',cc_price_snapshot=44,cc_currency_snapshot='EUR',cc_economic_state='Pending',cc_paid=0),dict(name='B',cc_price_snapshot=44,cc_currency_snapshot='EUR',cc_economic_state='Due',cc_paid=1)]
        data=module.summarize(sessions, [], '2026-01-01', '2026-01-31')
        self.assertEqual(data['cash_cents'],0)
        self.assertEqual(data['sessions']['A']['state'],'Da definire')
        self.assertEqual(data['sessions']['B']['state'],'Saldata')
        self.assertIsNone(data['sessions']['B']['allocated_cents'])
    def test_reject_bad_data_and_mixed_currency(self):
        session=[dict(name='A',cc_price_snapshot=44,cc_currency_snapshot='USD',cc_economic_state='Due',cc_paid=0)]
        with self.assertRaises(ValueError): module.summarize(session, [], '2026-01-01', '2026-01-31')
        with self.assertRaises(ValueError): module.summarize([], [dict(receipt_date='2026-01-01',allocations='[{"appointment":"A","cents":"100"}]')], '2026-01-01','2026-01-31')

if __name__=='__main__': unittest.main()
