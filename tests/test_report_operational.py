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
        self.assertEqual(data['sessions']['A']['period_cash_cents'], -500)
        self.assertEqual(data['sessions']['B']['state'], 'Non dovuto')
        self.assertEqual(data['state_counts']['Parziale'], 1)
        self.assertEqual(data['session_remaining_cents'], 1900)
    def test_pending_unknown_and_legacy_paid_do_not_invent_cash(self):
        sessions = [dict(name='A',cc_price_snapshot=44,cc_currency_snapshot='EUR',cc_economic_state='Pending',cc_paid=0),dict(name='B',cc_price_snapshot=44,cc_currency_snapshot='EUR',cc_economic_state='Due',cc_paid=1)]
        data=module.summarize(sessions, [], '2026-01-01', '2026-01-31')
        self.assertEqual(data['cash_cents'],0)
        self.assertEqual(data['sessions']['A']['state'],'Da definire')
        self.assertEqual(data['sessions']['B']['state'],'Saldata')
        self.assertIsNone(data['sessions']['B']['allocated_cents'])
        self.assertIsNone(data['session_remaining_cents'])
    def test_cumulative_payment_allocations_remain_separate(self):
        sessions = [dict(name=n, cc_price_snapshot=44, cc_currency_snapshot='EUR', cc_economic_state='Due', cc_paid=0) for n in ('A', 'B')]
        receipts = [dict(receipt_date='2026-02-03', allocations='[{"appointment":"A","cents":4400},{"appointment":"B","cents":1000}]')]
        result = module.summarize(sessions, receipts, '2026-02-01', '2026-02-28')
        self.assertEqual(result['sessions']['A']['state'], 'Saldata')
        self.assertEqual(result['sessions']['B']['state'], 'Parziale')
        self.assertEqual(result['sessions']['B']['remaining_cents'], 3400)
        self.assertEqual(result['cash_cents'], 5400)
        self.assertEqual(result['sessions']['A']['period_cash_cents'], 4400)
        self.assertEqual(result['sessions']['B']['period_cash_cents'], 1000)

    def test_future_unpaid_session_does_not_create_operational_debt(self):
        session = dict(name='F',cc_price_snapshot=44,cc_currency_snapshot='EUR',cc_economic_state='Due',cc_classified_future=True)
        data = module.summarize([session], [], '2026-01-01', '2026-01-31')
        self.assertEqual(data['sessions']['F']['state'], 'In programma')
        self.assertEqual(data['session_remaining_cents'], 0)

    def test_reject_bad_data_and_mixed_currency(self):
        session=[dict(name='A',cc_price_snapshot=44,cc_currency_snapshot='USD',cc_economic_state='Due',cc_paid=0)]
        with self.assertRaises(ValueError): module.summarize(session, [], '2026-01-01', '2026-01-31')
        with self.assertRaises(ValueError): module.summarize([], [dict(receipt_date='2026-01-01',allocations='[{"appointment":"A","cents":"100"}]')], '2026-01-01','2026-01-31')

if __name__=='__main__': unittest.main()
