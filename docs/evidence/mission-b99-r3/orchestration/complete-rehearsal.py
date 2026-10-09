import ops,pathlib,json,subprocess,time,sys,datetime
r=ops.ROOT;rows=[];rollback_deadline=datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp()
def run(script,timeout):
 ops.safe();start=time.time()
 p=subprocess.run([sys.executable,str(r/script)],capture_output=True,text=True,timeout=timeout)
 (r/(script+'.log')).write_text(ops.redact(p.stdout+p.stderr));row={'stage':script,'exit_code':p.returncode,'seconds':time.time()-start};rows.append(row);(r/'pipeline.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True);return p.returncode
assert json.loads((r/'target-load.result.json').read_text())['exit_code']==0
assert json.loads((r/'target-pin-check.result.json').read_text())['exit_code']==0
stable=0
while stable<3:
 ops.safe();d=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1]);stable=stable+1 if d['psi']['full']<0.1 and d['psi']['some']<0.5 and d['io_psi']['full']<1 else 0;time.sleep(5)
print('REUSE COMPLETED TARGET IMPORT AND VERIFIED PINS',flush=True)
clone_started=False
try:
 clone_started=True
 if run('clone-migrate-target.py',1800)==0:
  remaining=rollback_deadline-time.time()-300
  if remaining>0:run('run-target-regressions.py',remaining)
finally:
 if clone_started:
  ops.safe();print('ENTER REAL ROLLBACK',flush=True);run('rollback-current.py',3600)
print('PIPELINE COMPLETE',flush=True)
