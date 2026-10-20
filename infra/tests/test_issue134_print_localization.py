"""Pinned Frappe 16.50 invoice print presentation, with no Site or DB writes."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe
from bs4 import BeautifulSoup

MODULE = Path(__file__).resolve().parents[2] / (
    'app/centrochange_core/centrochange_core/operations/website_brand.py')
spec = importlib.util.spec_from_file_location('cc_print_locale', MODULE)
locale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locale)


class InvoicePrintTests(TestCase):
    def test_invoice_labels_words_time_and_canonical_values(self):
        original = '''<div class="print-format"><h1>Sales Invoice</h1>
          <div class="custom-html" data-fieldname="custom_html_WJGFzvLg"><div><div>Sales Invoice</div></div></div>
          <div class="custom-html" data-fieldname="custom_html_WbBDnaVv"><div><div>Billed To</div></div></div>
          <span class="heading">Billed To:</span><span class="value">Sales Invoice</span>
          <table class="table-header"><tr><td>No.</td><td>Subtotal</td></tr></table>
          <div data-fieldname="in_words"><div class="value">EUR One Hundred only.</div></div>
          <div data-fieldname="posting_time"><div class="value">09:30:00</div></div>
          <table><tr><td data-fieldname="item_name">CC-HTTP-UAT0000001 Session</td>
          <td data-fieldname="item_code">CC-HTTP-UAT0000001 Session</td></tr></table>
          <div class="value">Billed To:</div></div>'''
        doc = SimpleNamespace(currency='EUR', grand_total=100,
                              in_words='EUR One Hundred only.')
        with patch.object(frappe, 'get_doc', return_value=doc) as get_doc:
            result = locale.localize_print_labels(original, 'SYN-INV-1')
        get_doc.assert_called_once_with('Sales Invoice', 'SYN-INV-1')
        soup = BeautifulSoup(result, 'html.parser')
        self.assertEqual(soup.h1.text, 'Fattura paziente')
        self.assertEqual([n.text for n in soup.select('.custom-html div div')],
                         ['Fattura paziente', 'Intestatario'])
        self.assertEqual(soup.select_one('.heading').text, 'Intestatario:')
        self.assertEqual([x.text for x in soup.select('.table-header td')], ['N.', 'Subtotale'])
        self.assertEqual(soup.select_one('[data-fieldname="in_words"] .value').text,
                         'Cento euro e zero centesimi.')
        self.assertEqual(soup.select_one('[data-fieldname="posting_time"] .value').text, '09:30')
        self.assertEqual(soup.select_one('td[data-fieldname="item_name"]').text,
                         'Seduta dimostrativa')
        self.assertEqual(soup.select_one('td[data-fieldname="item_code"]').text,
                         'CC-HTTP-UAT0000001 Session')
        self.assertEqual(soup.select('.value')[-1].text, 'Billed To:')

    def test_non_eur_words_and_advanced_values_stay_unchanged(self):
        html = '<div data-fieldname="in_words"><div class="value">USD One Hundred only.</div></div>'
        doc = SimpleNamespace(currency='USD', grand_total=100,
                              in_words='USD One Hundred only.')
        with patch.object(frappe, 'get_doc', return_value=doc):
            self.assertIn('USD One Hundred only.', locale.localize_print_labels(html, 'SYN-INV-2'))

    def test_other_document_print_is_not_localized_by_context(self):
        frappe.local.path = 'printview'
        frappe.local.response = {}
        frappe.local.request = SimpleNamespace(path='/printview')
        frappe.local.form_dict = frappe._dict(doctype='Purchase Invoice', name='SYN-PI-1')
        frappe.local.session = SimpleNamespace(user='Guest')
        values = frappe._dict(body='<h1>Sales Invoice</h1>', template='www/printview.html')
        with patch.object(frappe, 'get_roles', return_value=[]):
            locale.context(values)
        self.assertEqual(values.body, '<h1>Sales Invoice</h1>')

    def test_invoice_pdf_api_render_uses_print_context_not_request_path(self):
        frappe.local.path = 'api/method/frappe.utils.print_format.download_pdf'
        frappe.local.response = {}
        frappe.local.request = SimpleNamespace(path='/api/method/frappe.utils.print_format.download_pdf')
        frappe.local.form_dict = frappe._dict(doctype='Sales Invoice', name='SYN-INV-3')
        frappe.local.session = SimpleNamespace(user='Guest')
        values = frappe._dict(doctype='Sales Invoice', body='<h1>Sales Invoice</h1>',
                              template='www/printview.html')
        with patch.object(frappe, 'get_doc', return_value=SimpleNamespace(
                currency='EUR', grand_total=1, in_words='EUR One only.')):
            locale.context(values)
        self.assertEqual(BeautifulSoup(values.body, 'html.parser').h1.text, 'Fattura paziente')

    def test_client_time_display_uses_boot_hook_without_changing_server_defaults(self):
        for user, roles, expected in (
                ('demo-finance', ['CC Finance'], 'HH:mm'),
                ('demo-pro', ['CC Professional'], 'HH:mm'),
                ('Administrator', ['CC Manager'], 'HH:mm:ss'),
                ('unrelated-user', ['Guest'], 'HH:mm:ss')):
            with self.subTest(user=user), patch.object(frappe, 'get_roles', return_value=roles):
                frappe.local.session = SimpleNamespace(user=user)
                boot = SimpleNamespace(sysdefaults={'time_format': 'HH:mm:ss'})
                locale.client_time_format(boot)
                self.assertEqual(boot.sysdefaults['time_format'], expected)


if __name__ == '__main__':
    import unittest
    unittest.main()
