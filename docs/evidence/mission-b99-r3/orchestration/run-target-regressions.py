import pathlib,json,subprocess,sys,time,datetime,os
import ops
r=ops.ROOT;rows=[];end=datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp()
def suite(name,args):
 ops.safe();remaining=end-time.time()
 if remaining<600:raise RuntimeError('ROLLBACK_RESERVE_REACHED')
 started=time.time()
 try:
  p=subprocess.run(args,text=True,capture_output=True,timeout=min(480,remaining-300));status='PASS' if p.returncode==0 else 'FAIL';output=p.stdout+p.stderr;rc=p.returncode
 except subprocess.TimeoutExpired as e:status='FAIL';output='HARNESS_TIMEOUT';rc=124
 (r/(name+'.log')).write_text(ops.redact(output));row={'suite':name,'status':status,'exit_code':rc,'seconds':time.time()-started};rows.append(row);(r/'target-regressions.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True);ops.safe()
# Fresh TARGET authentication and runtime health before fixture-heavy browser checks.
import urllib.request
for _ in range(90):
 try:
  if urllib.request.urlopen('http://127.0.0.1:8099/api/method/ping',timeout=3).status==200:break
 except Exception:pass
 time.sleep(2)
else:raise RuntimeError('TARGET HTTP unavailable')
# Protect synthetic demo authentication values in diagnostic/browser error output.
secret_code="import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\nfrom centrochange_core.uat import demo\nprint('CREDENTIALS='+json.dumps(demo.credentials(),default=str));frappe.destroy()\n"
p=subprocess.run(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',ops.BACKEND,'env/bin/python'],input=secret_code,text=True,capture_output=True);assert p.returncode==0
values=json.loads(next(x for x in p.stdout.splitlines() if x.startswith('CREDENTIALS=')).split('=',1)[1]);sensitive=[]
def collect(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ['password','pwd'] and isinstance(v,str):sensitive.append(v)
   else:collect(v)
 elif isinstance(obj,list):
  for v in obj:collect(v)
collect(values);(r/'sensitive-values.json').write_text(json.dumps(sensitive));(r/'sensitive-values.json').chmod(0o600)
suite('target-backend-240',[sys.executable,str(r/'backend_review.py')])
suite('target-hooks-six',[sys.executable,str(r/'hooks_http.py'),'mission97_hooks'])
suite('target-http-55',[sys.executable,str(r/'hooks_http.py'),'mission97_http','--phase','after'])
for name in ['security','finance','receivables','banking','incoming','professional','reporting','sdi','ts']:
 args=[sys.executable,str(r/'run_suite.py'),name+'_acceptance','--env-file',str(r/'runtime.env')]
 if name=='security':args+=['--with-booking','--with-operations']
 suite('target-'+name,args)
for script in ['uat','professional','patient','expectations','ts_detail','confirmation','search','accounting','permissions','walkthrough','ui_v1','print','states','agenda_geometry']:
 suite('target-browser-'+script,[sys.executable,str(r/'run_suite.py'),'uat_browser_acceptance','--script',script,'--output-dir',str(r/('browser-'+script))])
print('TARGET REGRESSION COMPLETE',flush=True)
