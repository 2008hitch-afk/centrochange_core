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
confidential_flags=[]
functions={name:frappe.get_attr(name) for name in expected}
# Isolated rollback-only negative checks against actual current principal reads.
from centrochange_core.security.api import before_request as api_guard
from centrochange_core.scheduling.public_booking import SERVICE_USER
from centrochange_core.operations.install import AUTOMATION_USER
from centrochange_core.uat.demo import credentials
fixture=credentials()
principal_denials=[]
for user in (SERVICE_USER,AUTOMATION_USER):
 frappe.set_user(user)
 try:api_guard()
 except frappe.PermissionError:principal_denials.append('interactive service principal denied')
 else:raise AssertionError('Service principal was allowed')
frappe.set_user('Administrator')
disabled=fixture['users']['c']['name']
frappe.db.savepoint('m97_disabled')
try:
 frappe.db.set_value('User',disabled,'enabled',0,update_modified=False)
 frappe.set_user(disabled)
 try:api_guard()
 except frappe.PermissionError:principal_denials.append('disabled principal denied')
 else:raise AssertionError('Disabled principal was allowed')
finally:
 frappe.db.rollback(save_point='m97_disabled');frappe.set_user('Administrator')
def wrapper(name,fn):
 def call(*args,**kwargs):
  called.append(name)
  result=fn(*args,**kwargs)
  if name.endswith('diagnostics.before_request'):confidential_flags.append(bool(frappe.flags.cc_confidential_request))
  return result
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
 ping_called=list(called)
 if app==expected:
  called.clear()
  response_private=client.get('/api/method/ping?doctype=CC%20Private%20Note',base_url='http://mission97.local')
  assert response_private.status_code==403
  assert called==expected[:4]
  assert confidential_flags[-1] is True
report={'principal_guard_negative_checks':principal_denials,'confidential_request_redacted_before_private_note_denial':app==expected,'app_hooks':app,'effective_hooks':effective,'http_ping_status':response.status_code,'invoked':ping_called,'expected':expected,'status':'PASS' if app==expected and ping_called==expected else 'CONFIRMED_RUNTIME_GAP','instrumentation':'process-local unittest.mock wrappers around original functions; real pinned WSGI initialization; no app/server patch'}
print('CC_M97_JSON='+json.dumps(report))
'''.replace('EXPECTED',repr(EXPECTED))
 result=execute(code)
 line=next(line for line in result.splitlines() if line.startswith('CC_M97_JSON='))
 print(line.split('=',1)[1])
if __name__=='__main__':main()
