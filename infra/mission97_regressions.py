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
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['backend','browser']);p.add_argument('--script',default='uat');p.add_argument('--output-dir',required=True);a=p.parse_args()
 isolation()
 if a.suite=='backend':
  sys.argv=['remediation_acceptance']
  with patch('subprocess.run',run),patch('subprocess.check_output',output):importlib.import_module('remediation_acceptance').main()
 else:
  sys.argv=['uat_browser_acceptance','--script',a.script,'--output-dir',a.output_dir]
  if a.script=='uat':sys.argv+=['--agenda-only']
  with patch('subprocess.run',run),patch('subprocess.check_output',output):importlib.import_module('uat_browser_acceptance').main()
if __name__=='__main__':main()
