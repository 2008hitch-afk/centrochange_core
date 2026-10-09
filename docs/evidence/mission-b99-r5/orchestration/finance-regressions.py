import ops,subprocess,sys,time,json
r=ops.ROOT;rows=[]
for name in ['security','finance','receivables','banking','incoming','professional','reporting','sdi','ts']:
 ops.safe();start=time.time()
 p=subprocess.run([sys.executable,str(r/'run_suite.py'),name+'_acceptance','--env-file',str(r/'runtime.env')],capture_output=True,text=True,timeout=480)
 (r/('http-'+name+'.log')).write_text(ops.redact(p.stdout+p.stderr));row={'suite':name,'status':'PASS' if p.returncode==0 else 'FAIL','exit_code':p.returncode,'seconds':time.time()-start};rows.append(row);(r/'finance-results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
