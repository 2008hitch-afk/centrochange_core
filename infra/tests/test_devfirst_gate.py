"""DEV-FIRST verdicts cannot bypass runtime integrity or security gates."""
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch, Mock
spec=importlib.util.spec_from_file_location('devfirst',Path(__file__).resolve().parents[1]/'issue139_install_gate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class DevFirstTests(unittest.TestCase):
 def test_validation_with_cleanup_is_blocked_not_pass(self):
  result=types.SimpleNamespace(returncode=1,stdout='{"cleanup": "PASS"}',stderr='FixtureCommandError: frappe.exceptions.ValidationError: invalid option')
  with tempfile.TemporaryDirectory() as d, patch.object(g,'run',return_value=result):
   self.assertEqual(g.live_acceptance(Path(d)/'e','fixture.py',[])['status'],'BLOCKED')
 def test_unknown_security_or_failed_cleanup_stops(self):
  for stderr,stdout in [('PermissionError: denied','{"cleanup": "PASS"}'),('FixtureCommandError: frappe.exceptions.ValidationError: invalid','{"cleanup": "FAIL"}'),('AssertionError: unauthorized access','{"cleanup": "PASS"}')]:
   with tempfile.TemporaryDirectory() as d,patch.object(g,'run',return_value=types.SimpleNamespace(returncode=1,stdout=stdout,stderr=stderr)):
    with self.assertRaises(g.Stop):g.live_acceptance(Path(d)/'e','fixture.py',[])
 def test_noncritical_verdict_still_checks_integrity(self):
  module=Mock();module.runtime_fingerprint.return_value={'changed':True}
  with patch.object(g,'live_acceptance',return_value={'status':'BLOCKED'}):
   with self.assertRaisesRegex(g.Stop,'baseline data'):
    g.functional_gate(None,'fixture.py',[],{'module':module,'data':{'original':True}},'image')
 def test_noncritical_verdict_still_checks_permissions(self):
  module=Mock();module.runtime_fingerprint.return_value={}
  with patch.object(g,'live_acceptance',return_value={'status':'BLOCKED'}),patch.object(g,'permission_fingerprint',return_value='changed'):
   with self.assertRaisesRegex(g.Stop,'permission drift'):
    g.functional_gate(None,'fixture.py',[],{'module':module,'data':{},'permissions':'original'},'image')

 def test_application_validation_is_not_authorization_bypass(self):
  for actual,expected,allowed in [(417,200,True),(200,403,False),(200,417,False)]:
   result=types.SimpleNamespace(returncode=1,stdout='{"cleanup": "PASS"}',stderr="AssertionError: "+repr(('/api/report',actual,expected,'ValidationError','sanitized')))
   with tempfile.TemporaryDirectory() as d,patch.object(g,'run',return_value=result):
    if allowed:self.assertEqual(g.live_acceptance(Path(d)/'e','report.py',[])['classification'],'application_validation')
    else:
     with self.assertRaises(g.Stop):g.live_acceptance(Path(d)/'e','report.py',[])
