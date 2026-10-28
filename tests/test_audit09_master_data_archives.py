"""Offline contract tests for AUDIT-09: Master Data Archives & Server-Side Search."""
from datetime import date
import importlib.util
import types
import unittest
from tests.test_premium_scoped_api import ScopedApiTest, FakeDoc, Denied, Invalid, ROOT


class Audit09MasterDataSearchTest(ScopedApiTest):
    def setUp(self):
        super().setUp()
        self.db.get_value = lambda dt, name, field: 'Listino A' if field == 'cc_price_list' else 'Valore'

    def test_patients_server_side_search_and_bounding(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)

        observed = {}
        def listing(doctype, **kwargs):
            observed.update(kwargs)
            return [types.SimpleNamespace(name='PAT-A', patient_name='Mario Rossi', first_name='Mario', last_name='Rossi', email='mario@example.invalid', modified='v1')]

        self.frappe.get_list = listing
        self.frappe.get_all = lambda doctype, **kwargs: ['PAT-A']

        # Normal search query
        result = profiles.patients('A', 50, 0, search='Rossi')
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['name'], 'PAT-A')
        self.assertIn('or_filters', observed)
        self.assertEqual(observed['or_filters']['last_name'], ['like', '%Rossi%'])
        self.assertEqual(observed['or_filters']['first_name'], ['like', '%Rossi%'])
        self.assertEqual(observed['or_filters']['email'], ['like', '%Rossi%'])

        # Over-length search query raises Invalid
        with self.assertRaises(Invalid):
            profiles.patients('A', 50, 0, search='A' * 101)

    def test_catalog_records_server_side_search(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.catalog', ROOT / 'catalog.py')
        catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(catalog)

        observed = {}
        def listing(doctype, **kwargs):
            if doctype == 'CC Center Service':
                return [types.SimpleNamespace(name='SERV-1', appointment_type='TYPE-A')]
            observed.update(kwargs)
            return [types.SimpleNamespace(name='ITEM-001', item_name='Psicoterapia individuale', item_group='Services', stock_uom='Nos', is_stock_item=0, is_sales_item=1, disabled=0, modified='v1')]

        self.frappe.get_list = listing
        self.frappe.get_all = lambda doctype, **kwargs: ['ITEM-001']

        result = catalog.records('A', 'Item', 50, 0, search='Psicoterapia')
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0].name, 'ITEM-001')
        self.assertIn('or_filters', observed)
        self.assertEqual(observed['or_filters']['item_name'], ['like', '%Psicoterapia%'])

    def test_payments_records_server_side_search(self):
        from unittest.mock import patch
        finance_guards = types.ModuleType('centrochange_core.finance.guards')
        finance_guards.require_finance = lambda center: None
        frappe_utils = types.ModuleType('frappe.utils')
        frappe_utils.getdate = lambda d: date.fromisoformat(d) if isinstance(d, str) else d
        with patch.dict('sys.modules', {'centrochange_core.finance.guards': finance_guards, 'frappe.utils': frappe_utils}):
            spec = importlib.util.spec_from_file_location('centrochange_core.finance.payments', ROOT / 'finance/payments.py')
            payments = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(payments)

            observed = {}
            def listing(doctype, **kwargs):
                observed.update(kwargs)
                return [types.SimpleNamespace(name='PAY-A', posting_date='2026-10-28', payment_type='Receive', party_type='Customer', party='CUS-001', paid_amount=100, received_amount=100, unallocated_amount=0, mode_of_payment='Bonifico', docstatus=1, modified='v1')]

            self.frappe.get_list = listing

            result = payments.records('A', '2026-01-01', '2026-12-31', 50, 0, search='CUS-001')
            self.assertEqual(len(result['rows']), 1)
            self.assertIn('or_filters', observed)
            self.assertEqual(observed['or_filters']['party'], ['like', '%CUS-001%'])


if __name__ == '__main__':
    unittest.main()
