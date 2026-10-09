import ops,pathlib,time,subprocess,json,datetime
r=ops.ROOT;builder='centrochange-b99-r3-builder';ref='moby/buildkit:v0.33.1@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea'
while not (r/'copy-cache-resume.result.json').exists():ops.safe();time.sleep(5)
assert json.loads((r/'copy-cache-resume.result.json').read_text())['exit_code']==0
stable=0
while stable<3:
 ops.safe();s=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1]);stable=stable+1 if s['psi']['full']<0.1 and s['io_psi']['full']<1 else 0;time.sleep(5)
assert not subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R3'],text=True).strip()
exists=subprocess.run(['docker','inspect',builder],capture_output=True).returncode==0
if exists:ops.cmd(['docker','start',builder],'restart-io-bounded-builder')
else:
 ops.cmd(['docker','run','-d','--name',builder,'--label','centrochange.mission=B99-R3','--label','centrochange.heavy=true','--privileged','--memory','2g','--memory-swap','2g','--cpus','1','--device-read-bps','/dev/sda:8388608','--device-write-bps','/dev/sda:4194304','--restart','no','--mount','type=volume,source=centrochange-b99-r3-fit-buildkit-state,target=/var/lib/buildkit','--mount','type=bind,source='+str(r/'buildkitd.toml')+',target=/etc/buildkit/buildkitd.toml,readonly',ref],'start-io-bounded-builder')
c=json.loads(subprocess.check_output(['docker','inspect',builder],text=True))[0];cg=pathlib.Path('/sys/fs/cgroup/system.slice/docker-'+c['Id']+'.scope');assert (cg/'memory.max').read_text().strip()=='2147483648';assert (cg/'memory.swap.max').read_text().strip()=='0';assert 'wbps=4194304' in (cg/'io.max').read_text();assert 'rbps=8388608' in (cg/'io.max').read_text();(r/'builder-effective-limits.json').write_text(json.dumps({'memory_max':(cg/'memory.max').read_text(),'swap_max':(cg/'memory.swap.max').read_text(),'io_max':(cg/'io.max').read_text(),'actual_writer_cgroup':str(cg)},indent=2))
if subprocess.run(['docker','buildx','inspect','centrochange-b99-r3-builder'],capture_output=True).returncode:ops.cmd(['docker','buildx','create','--name','centrochange-b99-r3-builder','--driver','remote','docker-container://'+builder],'create-remote-builder')
ops.cmd(['docker','buildx','inspect','centrochange-b99-r3-builder','--bootstrap'],'verify-remote-builder')
print('TARGET BUILD STARTED',flush=True)
args=['docker','buildx','build','--builder','centrochange-b99-r3-builder','--platform','linux/amd64','--progress','plain','--label','org.opencontainers.image.revision=e85fce588de6012a47da302710b9f9c615211279','-t','centrochange-b99-r3:target1650-e85fce588de6','--output','type=oci,dest='+str(r/'target-image.oci.tar')+',compression=gzip','-f',str(r/'Dockerfile.target'),str(ops.SOURCE)]
start=time.time();deadline=datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp();timeout=min(7200,deadline-time.time()-2700);assert timeout>0
try:
 with open(r/'build-target.log','w') as out:
  p=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT)
  try:rc=p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.terminate();rc=124
 (r/'build-target.result.json').write_text(json.dumps({'exit_code':rc,'elapsed_seconds':time.time()-start}));ops.safe();assert rc==0
 print('TARGET BUILD PASS',flush=True)
finally:
 subprocess.run(['docker','unpause',builder],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','stop','--time','15',builder],stdout=subprocess.DEVNULL)
