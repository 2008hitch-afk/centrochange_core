import ops,time,json,subprocess,pathlib
r=ops.ROOT;stable=0
while True:
 ops.safe();d=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1]);stable=stable+1 if d['psi']['full']<0.1 and d['psi']['some']<0.5 and d['io_psi']['full']<1 else 0
 if stable>=3:
  c=json.loads(subprocess.check_output(['docker','inspect','centrochange-b99-r3-builder'],text=True))[0]
  cg=pathlib.Path('/sys/fs/cgroup/system.slice/docker-'+c['Id']+'.scope')
  if c['State']['Running'] and c['State']['Paused']==False and (cg/'cgroup.freeze').read_text().strip()=='1':
   p=subprocess.run(['python3',str(r/'resume-own-frozen-cgroup.py')],capture_output=True,text=True);print(ops.redact(p.stdout+p.stderr),flush=True);stable=0
  if not c['State']['Running']:break
 time.sleep(5)
