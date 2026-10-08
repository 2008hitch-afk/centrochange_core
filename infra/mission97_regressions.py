#!/usr/bin/env python3
"""Reuse existing acceptance drivers only against the isolated #97 runtime.

Host-process argv remapping is test orchestration, never a product/core patch.
"""
import argparse, importlib, json, os, subprocess, sys
from pathlib import Path
from unittest.mock import patch
from mission97_lab import PROJECT,SITE,PORT,PRIVATE,isolation

ORIGINAL_RUN=subprocess.run
ORIGINAL_OUTPUT=subprocess.check_output

def mapped(value):
 if isinstance(value,str):
  return value.replace('centrochange-dev-backend-1',PROJECT+'-backend-1').replace('centrochange.local:8082','centrochange.local:'+str(PORT)).replace("site='centrochange.local'",f"site={SITE!r}").replace('centrochange.local',SITE) if 'CC_BASE_URL=' not in value else value.replace(':8082',':'+str(PORT))
 return [mapped(part) for part in value]

def run(argv,*args,**kwargs):
 argv=mapped(argv)
 if 'input' in kwargs:kwargs['input']=mapped(kwargs['input'])
 assert 'centrochange-dev' not in repr(argv)
 return ORIGINAL_RUN(argv,*args,**kwargs)

def output(argv,*args,**kwargs):
 argv=mapped(argv);assert 'centrochange-dev' not in repr(argv)
 return ORIGINAL_OUTPUT(argv,*args,**kwargs)

def main():
 os.umask(0o077)
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['backend','browser','fingerprint','health']);p.add_argument('--script',default='uat');p.add_argument('--output-dir',required=True);a=p.parse_args()
 isolation()
 if a.suite=='health':
  # The existing health probe is executed with isolated constants in this host process.
  code=(Path(__file__).parent/'uat_runtime_health.py').read_text().replace('centrochange-dev',PROJECT).replace('centrochange.local',SITE).replace('8082',str(PORT))
  with patch('subprocess.run',run),patch('subprocess.check_output',output):exec(compile(code,'isolated_uat_runtime_health','exec'),{'__name__':'__main__'})
 elif a.suite=='fingerprint':
  with patch('subprocess.run',run),patch('subprocess.check_output',output):importlib.import_module('ui_dataset_fingerprint').main()
 elif a.suite=='backend':
  sys.argv=['remediation_acceptance']
  backend=importlib.import_module('remediation_acceptance')
  # These four historical probes require Owner-specific rows not present in a fresh lab.
  # Equivalent lifecycle/threshold tests remain in operations.integration_acceptance.
  backend.MODULES=tuple(m for m in backend.MODULES if m not in ('security.audit_view_acceptance','scheduling.reopen_acceptance','finance.expectation_ui_acceptance','finance.bank_trace_acceptance'))
  with patch('subprocess.run',run),patch('subprocess.check_output',output):importlib.import_module('remediation_acceptance').main()
 else:
  sys.argv=['uat_browser_acceptance','--script',a.script,'--output-dir',a.output_dir]
  if a.script=='uat':sys.argv+=['--agenda-only']
  with patch('subprocess.run',run),patch('subprocess.check_output',output):importlib.import_module('uat_browser_acceptance').main()
if __name__=='__main__':main()
