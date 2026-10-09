import ops,subprocess,sys,json,time,datetime
r=ops.ROOT;rows=[];deadline=datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp()
try:
 for script in ['uat','professional','patient','expectations','ts_detail','confirmation','search','accounting','permissions','walkthrough','ui_v1','print','states','agenda_geometry']:
  ops.safe();assert time.time()<deadline-600
  start=time.time();p=subprocess.run([sys.executable,str(r/'run_suite.py'),'uat_browser_acceptance','--script',script,'--output-dir',str(r/('browser-retry-'+script))],capture_output=True,text=True,timeout=480)
  (r/('browser-retry-'+script+'.log')).write_text(ops.redact(p.stdout+p.stderr));row={'suite':script,'status':'PASS' if p.returncode==0 else 'FAIL','seconds':time.time()-start};rows.append(row);(r/'target-browser-retry.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
finally:
 ops.safe();print('ENTER FINAL REAL ROLLBACK',flush=True);p=subprocess.run([sys.executable,str(r/'rollback-current.py')],capture_output=True,text=True,timeout=3600);(r/'final-rollback-after-browser.log').write_text(ops.redact(p.stdout+p.stderr));print('FINAL_ROLLBACK_EXIT',p.returncode,flush=True)
