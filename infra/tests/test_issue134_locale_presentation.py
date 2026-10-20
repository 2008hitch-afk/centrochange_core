"""Invoice localization is read-only and obeys native document permissions."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe

SOURCE = Path(__file__).resolve().parents[2] / (
    'app/centrochange_core/centrochange_core/operations/locale_presentation.py')
spec = importlib.util.spec_from_file_location('cc_invoice_locale', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InvoiceWordsTests(TestCase):
    def test_readable_eur_invoice_gets_italian_words_without_save(self):
        invoice = SimpleNamespace(currency='EUR', grand_total=100,
                                  check_permission=lambda action: self.assertEqual(action, 'read'))
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(
                frappe, 'get_doc', return_value=invoice) as get_doc:
            self.assertEqual(module.invoice_words('Sales Invoice', 'SYN-INV-1'),
                             'Cento euro e zero centesimi.')
        get_doc.assert_called_once_with('Sales Invoice', 'SYN-INV-1')

    def test_denied_role_cannot_read_document(self):
        with patch.object(frappe, 'throw', side_effect=frappe.PermissionError), patch.object(
                frappe, 'has_permission', return_value=False), patch.object(
                frappe, 'get_doc') as get_doc:
            with self.assertRaises(frappe.PermissionError):
                module.invoice_words('Purchase Invoice', 'SYN-PI-1')
        get_doc.assert_not_called()

    def test_document_level_denial_is_not_bypassed(self):
        def deny(_): raise frappe.PermissionError('denied')
        invoice = SimpleNamespace(currency='EUR', grand_total=100, check_permission=deny)
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(
                frappe, 'get_doc', return_value=invoice):
            with self.assertRaises(frappe.PermissionError):
                module.invoice_words('Sales Invoice', 'SYN-INV-2')

    def test_non_invoice_doctype_rejected_before_document_lookup(self):
        with patch.object(frappe, 'throw', side_effect=frappe.PermissionError), patch.object(
                frappe, 'get_doc') as get_doc:
            with self.assertRaises(frappe.PermissionError):
                module.invoice_words('Patient', 'SYN-PAT-1')
        get_doc.assert_not_called()
