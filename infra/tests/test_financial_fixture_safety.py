"""Execute cleanup policy with fake native documents; no runtime writes."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from contextlib import nullcontext
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'app/centrochange_core/centrochange_core/security/fixture_cleanup.py'
spec=importlib.util.spec_from_file_location('financial_cleanup',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FinancialFixtureTests(unittest.TestCase):
 def runtime(self,enabled=1):
  f=types.ModuleType('frappe');f.session=types.SimpleNamespace(user='Administrator');f.conf={'cc_synthetic_dev':1};f.PermissionError=PermissionError
  f.db=Mock();f.db.get_single_value.return_value=enabled;f.db.exists.return_value=False
  def throw(message,*args):raise ValueError(message)
  f.throw=throw;f.delete_doc=Mock();return f
 def test_preflight_blocks_before_financial_mutation(self):
  f=self.runtime(0)
  with patch.dict(sys.modules,{'frappe':f}):
   with self.assertRaises(ValueError):m.require_native_accounting_cleanup()
  f.delete_doc.assert_not_called()
 def test_native_order_and_idempotent_cancelled_documents(self):
  for state in (1,2):
   f=self.runtime();events=[];docs={}
   for kind in ('Sales Invoice','Payment Entry','Bank Transaction'):
    d=Mock();d.doctype=kind;d.name=kind;d.cc_center='fixture';d.docstatus=state;d.get.return_value=False
    def cancel(d=d):events.append(('cancel',d.doctype));d.docstatus=2
    d.cancel.side_effect=cancel;docs[kind]=d
   f.get_doc=lambda kind,name,**kw:docs[kind]
   f.delete_doc.side_effect=lambda kind,name,**kw:events.append(('delete',kind))
   audit=types.ModuleType('centrochange_core.security.audit');audit.internal_write=lambda flag:nullcontext()
   with patch.dict(sys.modules,{'frappe':f,'centrochange_core.security.audit':audit}):
    m.native_accounting_cleanup({k:[k] for k in docs},['fixture'])
   deletes=[kind for action,kind in events if action=='delete']
   self.assertEqual(deletes,['Bank Transaction','Payment Entry','Sales Invoice'])
   self.assertEqual(len([x for x in events if x[0]=='cancel']),3 if state==1 else 0)
 def test_foreign_document_and_intermediate_error_never_delete(self):
  for foreign in (True,False):
   f=self.runtime();d=Mock();d.doctype='Sales Invoice';d.name='fixture';d.cc_center='other' if foreign else 'fixture';d.docstatus=1;d.get.return_value=False;d.cancel.side_effect=RuntimeError('native cancellation failed');f.get_doc=lambda *a,**k:d
   audit=types.ModuleType('centrochange_core.security.audit');audit.internal_write=lambda flag:nullcontext()
   with patch.dict(sys.modules,{'frappe':f,'centrochange_core.security.audit':audit}):
    with self.assertRaises((ValueError,RuntimeError)):m.native_accounting_cleanup({'Sales Invoice':['fixture']},['fixture'])
   f.delete_doc.assert_not_called()
 def test_browser_setup_does_not_inherit_bank_invoices(self):
  runner=(ROOT/'infra/finance_browser_acceptance.py').read_text()
  self.assertIn("'prepare_bank':False",runner)
  source=(ROOT/'app/centrochange_core/centrochange_core/finance/receivables_acceptance.py').read_text().split('def prepare_browser_invoice(fixture):')[1].split('def rejected')[0]
  self.assertLess(source.index('Fixture già fatturata'),source.index('lifecycle.close('))
  self.assertLess(source.index('Fixture già fatturata'),source.index("'doctype':'Mode of Payment'"))
 def test_cleanup_cannot_fall_through_to_raw_financial_delete(self):
  source=(ROOT/'app/centrochange_core/centrochange_core/security/dev_acceptance.py').read_text()
  self.assertIn('if doctype in financial:\n\t\t\tcontinue',source)
  self.assertIn("if pending_contacts(users)['pending']:",source)

 def test_empty_cleanup_is_idempotent(self):
  f=self.runtime(0)
  audit=types.ModuleType('centrochange_core.security.audit');audit.internal_write=lambda flag:nullcontext()
  with patch.dict(sys.modules,{'frappe':f,'centrochange_core.security.audit':audit}):
   m.native_accounting_cleanup({},[])
  f.db.get_single_value.assert_not_called()
  f.delete_doc.assert_not_called()
 def test_residual_ledger_is_failure(self):
  f=self.runtime();d=Mock();d.doctype='Sales Invoice';d.name='fixture';d.cc_center='fixture';d.docstatus=2;d.get.return_value=False;f.get_doc=lambda *a,**k:d
  f.db.exists.side_effect=lambda kind,name:kind=='GL Entry'
  audit=types.ModuleType('centrochange_core.security.audit');audit.internal_write=lambda flag:nullcontext()
  with patch.dict(sys.modules,{'frappe':f,'centrochange_core.security.audit':audit}):
   with self.assertRaisesRegex(ValueError,'residual'):
    m.native_accounting_cleanup({'Sales Invoice':['fixture'],'GL Entry':['entry']},['fixture'])
