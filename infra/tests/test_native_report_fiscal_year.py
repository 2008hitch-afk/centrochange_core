import ast
import datetime
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
class FiscalYearTests(unittest.TestCase):
 def filters(self, years):
  source=Path('app/centrochange_core/centrochange_core/finance/native_reports.py').read_text()
  fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_filters')
  class D(dict):
   __getattr__=dict.__getitem__
   __setattr__=dict.__setitem__
  def throw(message):raise ValueError(message)
  frappe=types.SimpleNamespace(_dict=D,as_json=lambda x:x,throw=throw)
  native=types.ModuleType('erpnext.accounts.utils');native.get_fiscal_years=lambda **kw:years
  utils=types.ModuleType('frappe.utils');utils.getdate=lambda x:datetime.date.fromisoformat(str(x))
  ns={'frappe':frappe}
  with patch.dict(sys.modules,{'erpnext.accounts.utils':native,'frappe.utils':utils}):
   exec(compile(ast.Module(body=[fn],type_ignores=[]),'native_filters','exec'),ns)
   return ns['_filters']('trial_balance',types.SimpleNamespace(cc_company='synthetic',cc_cost_center='center'),datetime.date(2026,10,5),datetime.date(2026,10,5))
 def test_native_shared_year_matches(self):
  y=types.SimpleNamespace(name='2026',year_start_date='2026-01-01',year_end_date='2026-12-31')
  self.assertEqual(self.filters([y]).fiscal_year,'2026')
 def test_missing_and_ambiguous_rejected(self):
  y=types.SimpleNamespace(name='2026',year_start_date='2026-01-01',year_end_date='2026-12-31')
  for years in ([],[y,y]):
   with self.assertRaises(ValueError):self.filters(years)
