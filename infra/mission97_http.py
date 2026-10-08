#!/usr/bin/env python3
"""Read-only socket HTTP boundary checks on synthetic isolated principals."""
import argparse,http.cookiejar,json,urllib.request,urllib.parse,urllib.error
from mission97_lab import execute,PRIVATE,PORT,isolation


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['before','after'],required=True);a=p.parse_args();isolation()
 data=execute("from centrochange_core.uat import demo\nprint('FIXTURE='+json.dumps(demo.credentials(),default=str));frappe.db.rollback();frappe.destroy()")
 fixture=json.loads(next(x for x in data.splitlines() if x.startswith('FIXTURE=')).split('=',1)[1])
 base='http://127.0.0.1:'+str(PORT);checks=[]
 def call(opener,path,params=None,post=False):
  url=base+path
  if params and not post:url+='?'+urllib.parse.urlencode(params)
  req=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode() if post else None)
  try:
   with opener.open(req,timeout=45) as r:status=r.status;body=r.read();cache=r.headers.get('Cache-Control','')
  except urllib.error.HTTPError as e:status=e.code;body=e.read();cache=e.headers.get('Cache-Control','')
  try:value=json.loads(body)
  except (ValueError,UnicodeDecodeError):value={}
  return status,value,cache
 for role in ['a','b','c','s','f','t','m','guest']:
  opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  if role!='guest':
   u=fixture['users'][role];status,_,_=call(opener,'/api/method/login',{'usr':u['name'],'pwd':u['password']},True);assert status==200
  status,_,_=call(opener,'/api/method/ping');assert status==200;checks.append({'role':role,'surface':'authenticated/public ping','status':status,'result':'PASS'})
  # Nonexistent report intentionally prevents any accounting payload BEFORE fix.
  status,value,_=call(opener,'/api/method/frappe.desk.query_report.get_script',{'report_name':'M97-NONEXISTENT-REPORT'})
  assert not value.get('message') and not value.get('data'), 'Unexpected data; stop mission and review privately'
  if a.phase=='after' and role!='m':assert status==403,(role,status,value.get('exc_type'))
  else:assert status in (403,404,417), (role,status,value.get('exc_type'))
  checks.append({'role':role,'surface':'native nonexistent query report (no financial data requested)','status':status,'exception_type':value.get('exc_type'),'result':'PASS'})
  if a.phase=='after':
   for prefix in ['erpnext.accounts.m97_nonexistent','erpnext.regional.italy.m97_nonexistent']:
    status,value,_=call(opener,'/api/method/'+prefix)
    if role!='m':assert status==403
    else:assert status in (404,417)
    assert not value.get('message') and not value.get('data')
    checks.append({'role':role,'surface':prefix,'status':status,'result':'PASS'})
   if role!='m':
    status,value,_=call(opener,'/api/method/erpnext.accounts.utils.get_balance_on',{'account':'M97-NONEXISTENT-ACCOUNT'})
    assert status==403 and not value.get('message') and not value.get('data')
    checks.append({'role':role,'surface':'known native accounting helper denied before query','status':status,'result':'PASS'})
    status,value,_=call(opener,'/api/method',{'cmd':'frappe.desk.query_report.get_script','report_name':'M97-NONEXISTENT-REPORT'})
    assert status==403 and not value.get('message') and not value.get('data')
    checks.append({'role':role,'surface':'cmd form native report guard','status':status,'result':'PASS'})
   # Both REST and generic native document path; only clinical author may read.
   status,value,_=call(opener,'/api/method/frappe.client.get',{'doctype':'CC Private Note','name':fixture['private_note']})
   if role=='a':assert status==200
   else:
    assert status in ((401,403) if role=='guest' else (403,))
    assert not value.get('message') and not value.get('data')
   checks.append({'role':role,'surface':'private-note native document API','status':status,'result':'PASS'})
 if a.phase=='after':
  # Retained-session defense: only isolated synthetic User.enabled is toggled;
  # original flag restored in finally, without changing modified or role grants.
  user=fixture['users']['c']['name'];u=fixture['users']['c']
  opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  assert call(opener,'/api/method/login',{'usr':u['name'],'pwd':u['password']},True)[0]==200
  assert call(opener,'/api/method/ping')[0]==200
  assert 'ENABLED=1' in execute("print('ENABLED='+str(frappe.db.get_value('User',"+repr(user)+",'enabled')));frappe.db.rollback();frappe.destroy()")
  try:
   execute("frappe.db.set_value('User',"+repr(user)+",'enabled',0,update_modified=False);frappe.db.commit();frappe.destroy()")
   status,value,_=call(opener,'/api/method/ping')
   assert status==403 and not value.get('message') and not value.get('data')
   checks.append({'role':'c-disabled-retained-session','surface':'actual HTTP ping denied after isolated principal disable','status':status,'result':'PASS'})
  finally:
   execute("frappe.db.set_value('User',"+repr(user)+",'enabled',1,update_modified=False);frappe.db.commit();frappe.destroy()")
  assert 'ENABLED=1' in execute("print('ENABLED='+str(frappe.db.get_value('User',"+repr(user)+",'enabled')));frappe.db.rollback();frappe.destroy()")
 print(json.dumps({'status':'PASS','phase':a.phase,'checks':checks,'synthetic_only':True,'business_mutations':'NONE','raw_responses_recorded':False}))
if __name__=='__main__':main()
