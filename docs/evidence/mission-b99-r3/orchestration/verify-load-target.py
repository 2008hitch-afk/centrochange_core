import ops,pathlib,time,json,tarfile,hashlib,subprocess
r=ops.ROOT;archive=r/'target-image.oci.tar';assert json.loads((r/'build-target.result.json').read_text())['exit_code']==0
ops.safe();assert not subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R3'],text=True).strip()
# Serialized integrity verification, then serialized paced Docker import.
with tarfile.open(archive) as tf:
 count=0
 for member in tf:
  if member.isfile() and member.name.startswith('blobs/sha256/'):
   h=hashlib.sha256();f=tf.extractfile(member)
   while chunk:=f.read(1024*1024):h.update(chunk)
   assert h.hexdigest()==member.name.rsplit('/',1)[1];count+=1
h=hashlib.sha256()
with archive.open('rb') as f:
 while chunk:=f.read(1024*1024):h.update(chunk)
(r/'target-oci-integrity.json').write_text(json.dumps({'verified_blobs':count,'bytes':archive.stat().st_size,'sha256':h.hexdigest()}))
print('TARGET OCI INTEGRITY PASS',flush=True)
with open(r/'target-load.log','w') as log:
 p=subprocess.Popen(['docker','load'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);start=time.time()
 import threading
 def load_guard():
  while p.poll() is None:
   if (r/'safety-stop.json').exists():p.terminate();return
   time.sleep(1)
 threading.Thread(target=load_guard,daemon=True).start()
 with archive.open('rb') as src:
  while chunk:=src.read(1024*1024):
   ops.safe()
   d=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1])
   while d['psi']['full']>=0.2 or d['psi']['some']>=1:
    time.sleep(5);ops.safe();d=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1])
   p.stdin.write(chunk);p.stdin.flush();time.sleep(0.25)
 p.stdin.close();rc=p.wait(timeout=900)
(r/'target-load.result.json').write_text(json.dumps({'exit_code':rc,'seconds':time.time()-start,'input_rate_limit_bps':4194304,'actual_unpack_writer':'host Docker/containerd; global configuration untouched; no concurrent lab or builder'}));assert rc==0;ops.safe()
tag='centrochange-b99-r3:target1650-e85fce588de6';image=json.loads(subprocess.check_output(['docker','image','inspect',tag],text=True))[0]['Id'];(r/'target-image.json').write_text(json.dumps({'tag':tag,'immutable_id':image},indent=2))
expected={str(p.relative_to(ops.SOURCE/'app/centrochange_core')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ops.SOURCE/'app/centrochange_core').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
code="import pathlib,hashlib,json,subprocess,frappe,erpnext,builder,healthcare\nexpected="+repr(expected)+"\nbase=pathlib.Path('/home/frappe/frappe-bench/apps/centrochange_core');assert all((base/n).exists() and hashlib.sha256((base/n).read_bytes()).hexdigest()==v for n,v in expected.items());assert frappe.__version__=='16.50.0';assert erpnext.__version__=='16.50.0'\npins={x:subprocess.check_output(['git','-C','/home/frappe/frappe-bench/apps/'+x,'rev-parse','HEAD'],text=True).strip() for x in ['builder','healthcare']};assert pins['builder']=='37e958bc4f801d06d0438c21b97b42c45c4eaa51';assert pins['healthcare']=='dda107b26e3a0fe1dbd65c7257371235de054a04'\nprint(json.dumps({'status':'PASS','versions':{'frappe':frappe.__version__,'erpnext':erpnext.__version__,'builder':builder.__version__,'healthcare':healthcare.__version__},'pins':pins,'core_file_parity':len(expected)}))\n"
upstream=json.loads((r/'official-target-fingerprints.json').read_text())
code+="upstream="+repr(upstream)+"\nassert all(hashlib.sha256(pathlib.Path('/home/frappe/frappe-bench/apps',n).read_bytes()).hexdigest()==v['sha256'] for n,v in upstream.items());print('OFFICIAL_TARGET_BYTE_PARITY_PASS='+str(len(upstream)))\n"
ops.cmd(['docker','run','-i','--name','centrochange-b99-r3-target-pin-check','--label','centrochange.mission=B99-R3','--network','none','--memory','512m','--memory-swap','512m','--entrypoint','/home/frappe/frappe-bench/env/bin/python',image],'target-pin-check',code);print('TARGET PINS AND CORE PARITY PASS',flush=True)
