import ops,sys,subprocess,json,time
r=ops.ROOT;rows=[]
for script in ['uat','professional','patient','expectations','ts_detail','confirmation','search','accounting','permissions','walkthrough','ui_v1','print','states','agenda_geometry']:
 ops.safe();started=time.time()
 try:
  p=subprocess.run([sys.executable,str(r/'run_suite.py'),'uat_browser_acceptance','--script',script,'--output-dir',str(r/('browser-'+script))],capture_output=True,text=True,timeout=480)
  output=p.stdout+p.stderr;rc=p.returncode
 except subprocess.TimeoutExpired:output='HARNESS_TIMEOUT';rc=124
 (r/('browser-'+script+'.log')).write_text(ops.redact(output));rows.append({'suite':script,'status':'PASS' if rc==0 else 'FAIL','exit_code':rc,'seconds':time.time()-started});(r/'browser-results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
 ops.safe()
