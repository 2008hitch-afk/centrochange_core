import ops,pathlib,json,subprocess,time,sys,datetime
r=ops.ROOT;rows=[];rollback_deadline=datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp()
def run(script,timeout):
 ops.safe();start=time.time()
 p=subprocess.run([sys.executable,str(r/script)],capture_output=True,text=True,timeout=timeout)
 (r/(script+'.log')).write_text(ops.redact(p.stdout+p.stderr));row={'stage':script,'exit_code':p.returncode,'seconds':time.time()-start};rows.append(row);(r/'pipeline.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True);return p.returncode
while True:
 ops.safe()
 if (r/'build-target.result.json').exists():
  # The previous attempt exists; require successful result and stopped builder.
  result=json.loads((r/'build-target.result.json').read_text())
  if result['exit_code']==0 and not subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R3'],text=True).strip():break
 if time.time()>rollback_deadline-3600:raise RuntimeError('TARGET preparation time exhausted')
 time.sleep(5)
assert run('verify-load-target.py',2400)==0,'TARGET immutable pin/integrity gate failed before migration'
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
