#!/usr/bin/env python3
"""Runtime read-back and process-local WSGI invocation proof; no permanent patches."""
import json
from mission97_lab import execute

EXPECTED=[
 'centrochange_core.finance.request_guard.before_request',
 'centrochange_core.security.diagnostics.before_request',
 'centrochange_core.security.api.before_request',
 'centrochange_core.operations.notes.request_guard',
 'centrochange_core.operations.website_brand.client_language',
 'centrochange_core.operations.website_brand.login_language',
]

def main():
 code='''from contextlib import ExitStack
from unittest.mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Response
from frappe.app import application
expected=EXPECTED
app=frappe.get_hooks('before_request',app_name='centrochange_core')
effective=frappe.get_hooks('before_request')
called=[]
functions={name:frappe.get_attr(name) for name in expected}
def wrapper(name,fn):
 def call(*args,**kwargs):
  called.append(name)
  return fn(*args,**kwargs)
 return call
frappe.db.rollback();frappe.destroy()
import os
os.chdir('/home/frappe/frappe-bench/sites')
with ExitStack() as stack:
 for name in expected:
  fn=functions[name]
  stack.enter_context(patch(name,wrapper(name,fn)))
 client=Client(application,Response)
 response=client.get('/api/method/ping',base_url='http://mission97.local')
 assert response.status_code==200
 assert response.json.get('message')=='pong'
report={'app_hooks':app,'effective_hooks':effective,'http_ping_status':response.status_code,'invoked':called,'expected':expected,'status':'PASS' if app==expected and called==expected else 'CONFIRMED_RUNTIME_GAP','instrumentation':'process-local unittest.mock wrappers around original functions; real pinned WSGI initialization; no app/server patch'}
print('CC_M97_JSON='+json.dumps(report))
'''.replace('EXPECTED',repr(EXPECTED))
 result=execute(code)
 line=next(line for line in result.splitlines() if line.startswith('CC_M97_JSON='))
 print(line.split('=',1)[1])
if __name__=='__main__':main()
