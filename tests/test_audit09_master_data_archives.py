"""Offline contract tests for AUDIT-09: Master Data Archives & Server-Side Search."""
from datetime import date
import importlib.util
import types
import unittest
from tests.test_premium_scoped_api import ScopedApiTest, FakeDoc, FakeRow, Denied, Invalid, ROOT


class Audit09MasterDataSearchTest(ScopedApiTest):
    def setUp(self):
        super().setUp()
        self.db.get_value = lambda dt, name, field: 'Listino A' if field == 'cc_price_list' else 'Valore'

    def test_finance_party_projection_is_consistent_and_does_not_invent_names(self):
        aliases = {'Customer': {'C-OWNED': 'Cliente 1'}, 'Supplier': {'S-OWNED': 'Professionista 1'}}
        cases = [
            ('Sales Invoice', {'customer': 'C-OWNED', 'customer_name': 'CC-HTTP-TEST'}, 'Cliente 1'),
            ('Sales Invoice', {'customer': 'CC-MVP-POS-x', 'customer_name': 'CC-MVP-POS-x'}, 'Cliente del documento'),
            ('Sales Invoice', {'customer': 'C-REAL', 'customer_name': 'Nome reale'}, 'Nome reale'),
            ('Purchase Invoice', {'supplier': 'S-OWNED', 'supplier_name': 'CC-HTTP-TEST'}, 'Professionista 1'),
            ('Purchase Invoice', {'supplier': 'S-REAL', 'supplier_name': 'Fornitore reale'}, 'Fornitore reale'),
            ('Payment Entry', {'party_type': 'Customer', 'party': 'C-OWNED'}, 'Cliente 1'),
            ('Payment Entry', {'party_type': 'Supplier', 'party': 'S-OWNED'}, 'Professionista 1'),
            ('Payment Entry', {'payment_type': 'Internal Transfer'}, ''),
        ]
        for doctype, row, expected in cases:
            with self.subTest(doctype=doctype, row=row):
                self.assertEqual(self.documents._party_values(doctype, row, aliases), expected)
                doc = FakeDoc(doctype, 'D-1', **row)
                with unittest.mock.patch.object(self.documents, '_party_aliases', return_value=aliases):
                    self.assertEqual(self.documents._party(doc), expected)

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
                return [FakeRow(name='PAY-A', posting_date='2026-10-28', payment_type='Receive', party_type='Customer', party='CUS-001', paid_amount=100, received_amount=100, unallocated_amount=0, mode_of_payment='Bonifico', docstatus=1, modified='v1')]

            self.frappe.get_list = listing

            result = payments.records('A', '2026-01-01', '2026-12-31', 50, 0, search='CUS-001')
            self.assertEqual(len(result['rows']), 1)
            self.assertEqual(result['rows'][0]['party_label'], 'CUS-001')
            self.assertIn('or_filters', observed)
            self.assertEqual(observed['or_filters']['party'], ['like', '%CUS-001%'])

    def test_reporting_records_paginated_and_over_500_all_three_doctypes(self):
        from unittest.mock import patch
        self.guards.current_rows = lambda dt, filters, fields=None: []
        self.guards.centers = lambda: ['A']
        self.guards.roles = lambda: ['CC Manager']
        finance_guards = types.ModuleType('centrochange_core.finance.guards')
        finance_guards.require_finance = lambda center: None
        finance_guards.allowed = lambda write=False: True
        finance_pkg = types.ModuleType('centrochange_core.finance')
        finance_pkg.professional_economics = types.SimpleNamespace(POLICY={})
        finance_pkg.admin_queue = types.SimpleNamespace()
        ops_reporting = types.ModuleType('centrochange_core.operations.reporting')
        ops_reporting.safe_cell = lambda v: str(v or '')

        with patch.dict('sys.modules', {
            'centrochange_core.finance.guards': finance_guards,
            'centrochange_core.finance': finance_pkg,
            'centrochange_core.operations.reporting': ops_reporting,
        }):
            spec = importlib.util.spec_from_file_location('centrochange_core.finance.reporting', ROOT / 'finance/reporting.py')
            reporting = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(reporting)

            for doctype, party_key in [
                ('Sales Invoice', 'customer'),
                ('Purchase Invoice', 'supplier'),
                ('Bank Transaction', 'reference_number'),
            ]:
                dataset = [
                    {
                        'name': f'{doctype[:3].upper()}-{i:04d}',
                        'docstatus': 1,
                        party_key: f'PARTY-{i:04d}',
                        'cc_center': 'A',
                    }
                    for i in range(525)
                ]
                observed = {}

                def listing(dt, filters=None, fields=None, order_by=None, start=0, page_length=20, **kwargs):
                    observed.clear()
                    observed.update({'doctype': dt, 'filters': filters, 'start': start, 'page_length': page_length, **kwargs})
                    filtered = [r for r in dataset if r['cc_center'] == filters.get('cc_center')]
                    or_f = kwargs.get('or_filters')
                    if or_f:
                        needle = list(or_f.values())[0][1].strip('%')
                        filtered = [r for r in filtered if needle in r['name'] or needle in r[party_key]]
                    return filtered[start:start + page_length]

                self.frappe.get_list = listing

                # 1. Paginated page 1 (limit=100, offset=0) over 525 records succeeds without 500-row crash
                p1 = reporting.records('A', doctype, search='', limit=100, offset=0)
                self.assertEqual(len(p1['rows']), 100)
                self.assertTrue(p1['has_more'])
                self.assertEqual(observed['start'], 0)
                self.assertEqual(observed['page_length'], 101)

                # 2. Paginated page 6 (limit=100, offset=500) reaches rows 500..524 (>500 boundary)
                p6 = reporting.records('A', doctype, search='', limit=100, offset=500)
                self.assertEqual(len(p6['rows']), 25)
                self.assertFalse(p6['has_more'])
                self.assertEqual(p6['rows'][-1]['name'], f'{doctype[:3].upper()}-0524')

                # 3. Server-side search finds record at index 520 directly on page 1
                s_res = reporting.records('A', doctype, search='0520', limit=100, offset=0)
                self.assertEqual(len(s_res['rows']), 1)
                self.assertFalse(s_res['has_more'])
                self.assertEqual(s_res['rows'][0]['name'], f'{doctype[:3].upper()}-0520')
                self.assertIn('or_filters', observed)

                # 4. Unpaginated legacy call (limit=None) still enforces the 500-row cap
                with self.assertRaises(Invalid):
                    reporting.records('A', doctype, search='')


if __name__ == '__main__':
    unittest.main()
