import ops,subprocess,sys,json,time
r=ops.ROOT
try:
 p=subprocess.run([sys.executable,str(r/'run-target-regressions.py')],capture_output=True,text=True);(r/'run-target-regressions.py.log').write_text(ops.redact(p.stdout+p.stderr));print('TARGET_REGRESSION_EXIT',p.returncode,flush=True)
finally:
 ops.safe();print('ENTER FINAL REAL ROLLBACK',flush=True);p=subprocess.run([sys.executable,str(r/'rollback-current.py')],capture_output=True,text=True,timeout=3600);(r/'final-rollback.py.log').write_text(ops.redact(p.stdout+p.stderr));print('FINAL_ROLLBACK_EXIT',p.returncode,flush=True)
