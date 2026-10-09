import ops,json,subprocess,pathlib,time
r=ops.ROOT;ops.safe()
c=json.loads(subprocess.check_output(['docker','inspect','centrochange-b99-r3-builder'],text=True))[0]
assert c['Config']['Labels']['centrochange.mission']=='B99-R3'
s=json.loads((r/'memory-samples.jsonl').read_text().splitlines()[-1]);assert s['psi']['full']<0.1 and s['psi']['some']<0.5 and s['io_psi']['full']<1
cg='/sys/fs/cgroup/system.slice/docker-'+c['Id']+'.scope'
assert pathlib.Path(cg,'memory.max').read_text().strip()=='2147483648'
assert pathlib.Path(cg,'cgroup.freeze').read_text().strip()=='1' and c['State']['Paused']==False
name='centrochange-b99-r3-thaw-'+str(int(time.time()))
ops.cmd(['docker','run','--name',name,'--label','centrochange.mission=B99-R3','--network','none','--user','0','--memory','64m','--memory-swap','64m','--mount','type=bind,source='+cg+',target=/only-builder-cgroup','--entrypoint','sh',ops.IMAGE,'-c','test "$(cat /only-builder-cgroup/memory.max)" = 2147483648 && echo 0 > /only-builder-cgroup/cgroup.freeze'],'resume-own-frozen-cgroup')
assert pathlib.Path(cg,'cgroup.freeze').read_text().strip()=='0'
print('R3 builder thawed after verified stability; limits preserved')
