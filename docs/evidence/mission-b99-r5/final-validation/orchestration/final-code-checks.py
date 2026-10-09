import ops,json,subprocess,sys,time,hashlib,pathlib
r=ops.ROOT;rows=[]
for name,args in [
 ('backend-240',[sys.executable,str(r/'backend_review.py')]),
 ('hooks-six',[sys.executable,str(r/'hooks_http.py'),'mission97_hooks']),
 ('http-55',[sys.executable,str(r/'hooks_http.py'),'mission97_http','--phase','after']),
 ('security-booking-operations',[sys.executable,str(r/'run_suite.py'),'security_acceptance','--env-file',str(r/'runtime.env'),'--with-booking','--with-operations'])]:
 ops.safe();start=time.time();p=subprocess.run(args,capture_output=True,text=True,timeout=480)
 (r/(name+'.log')).write_text(ops.redact(p.stdout+p.stderr));row={'suite':name,'status':'PASS' if p.returncode==0 else 'FAIL','exit_code':p.returncode,'seconds':time.time()-start};rows.append(row);(r/'final-code-results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
 ops.safe()
proof=json.loads((r/'image-build/image-proof.json').read_text());expected={}
for n in proof['files']:
 expected[n.removeprefix('app/centrochange_core/')]=hashlib.sha256(subprocess.check_output(['git','-C',str(ops.SOURCE),'show',proof['product_revision']+':'+n])).hexdigest()
code="import pathlib,hashlib\nexpected="+repr(expected)+"\nbase=pathlib.Path('/home/frappe/frappe-bench/apps/centrochange_core')\nobserved={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in expected}\nassert observed==expected\nprint('APP_PARITY='+json.dumps(observed))\n"
code+="import subprocess\nprint('VERSIONS='+json.dumps({a:__import__(a).__version__ for a in ['frappe','erpnext','healthcare','builder']}))\nfrappe.destroy()\n"
print(ops.execute(code,'final-app-parity-pins'))
ops.execute((r/'inventory-code.py').read_text(),'final-target-inventory')
