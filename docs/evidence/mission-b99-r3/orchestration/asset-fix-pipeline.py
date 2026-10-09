import ops,time,json,subprocess,sys
r=ops.ROOT
while not (r/'build-target.result.json').exists():ops.safe();time.sleep(5)
assert json.loads((r/'build-target.result.json').read_text())['exit_code']==0
while subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R3'],text=True).strip():ops.safe();time.sleep(5)
for name in ['verify-load-target.py','resume-target-runtime.py','browser-retry-and-rollback.py']:
 ops.safe();p=subprocess.run([sys.executable,str(r/name)],capture_output=True,text=True);(r/(name+'.pipeline.log')).write_text(ops.redact(p.stdout+p.stderr));print(name,p.returncode,flush=True);assert p.returncode==0
