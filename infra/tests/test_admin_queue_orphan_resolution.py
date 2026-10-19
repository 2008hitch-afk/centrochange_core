"""The queue may close a vanished source without deleting its audit fact."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[2] / (
    'app/centrochange_core/centrochange_core/finance/admin_queue.py')
FUNCTION = next(node for node in ast.parse(SOURCE.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name == '_save_resolved_condition')


class OrphanQueueResolutionTests(unittest.TestCase):
    def helper(self, existing):
        db = SimpleNamespace(exists=Mock(side_effect=lambda dt, name: existing.get((dt, name), False)))
        frappe = SimpleNamespace(db=db, throw=Mock(side_effect=ValueError))
        namespace = {'frappe': frappe}
        exec(compile(ast.Module(body=[FUNCTION], type_ignores=[]), str(SOURCE), 'exec'), namespace)
        return namespace['_save_resolved_condition'], frappe

    def document(self):
        return SimpleNamespace(reference_doctype='CC Incoming Invoice', reference_name='vanished',
            center='A', assignee=None, resolution_reason='Underlying condition resolved',
            flags=SimpleNamespace(ignore_links=False), save=Mock())

    def test_missing_source_closes_with_retained_reference_and_scoped_link_exception(self):
        helper, frappe = self.helper({('DocType', 'CC Incoming Invoice'): True, ('Branch', 'A'): True})
        doc = self.document()
        helper(doc)
        self.assertTrue(doc.flags.ignore_links)
        self.assertEqual(doc.reference_name, 'vanished')
        self.assertIn('riferimento storico conservato', doc.resolution_reason)
        doc.save.assert_called_once_with(ignore_permissions=True)
        frappe.db.exists.assert_any_call('CC Incoming Invoice', 'vanished')

    def test_valid_source_uses_normal_link_validation(self):
        helper, frappe = self.helper({('CC Incoming Invoice', 'vanished'): True})
        doc = self.document()
        helper(doc)
        self.assertFalse(doc.flags.ignore_links)
        self.assertEqual(doc.resolution_reason, 'Underlying condition resolved')
        doc.save.assert_called_once_with(ignore_permissions=True)

    def test_other_broken_link_fails_closed(self):
        helper, frappe = self.helper({('DocType', 'CC Incoming Invoice'): True, ('Branch', 'A'): True})
        doc = self.document()
        doc.assignee = 'missing-user'
        with self.assertRaises(ValueError):
            helper(doc)
        doc.save.assert_not_called()

    def test_missing_reference_doctype_fails_closed(self):
        helper, frappe = self.helper({('Branch', 'A'): True})
        doc = self.document()
        with self.assertRaises(ValueError):
            helper(doc)
        doc.save.assert_not_called()


if __name__ == '__main__':
    unittest.main()
