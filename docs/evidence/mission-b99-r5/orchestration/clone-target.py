import ops,json,subprocess,time,pathlib
r=ops.ROOT;project=ops.PROJECT
proof=json.loads((r/'image-build/image-proof.json').read_text())
ops.stable()
# Completed OCI import is reused by immutable manifest digest.
ops.stable()
tag='centrochange-b99-r5:compat-'+proof['product_revision'][:12]
img=json.loads(subprocess.check_output(['docker','image','inspect',proof['manifest']],text=True))[0]
assert img['Id'] in [proof['manifest'],proof['config']]
(r/'patched-image.json').write_text(json.dumps({'id':img['Id'],'tag':tag,'revision':proof['product_revision'],'base':'sha256:10e701947cccc377dc1d3c2082a03ef69b81d14da8e08fac75f07e78bcf974ce'},indent=2))
for n in ['compose.json','compose-target.json']:
 c=json.loads((r/n).read_text())
 for v in c['services'].values():
  if v['image'].startswith('sha256:'):v['image']=img['Id']
 (r/n).write_text(json.dumps(c,indent=2))
conf=json.loads(ops.cmd(ops.compose('config','--format','json'),'validated-config'))
assert sum(int(v['mem_limit']) for v in conf['services'].values())==2147483648
# Resources were created by the first R5 attempt; immutable R5 namespace remains exclusive.
assert all(n.startswith(project+'-r5-fit-') for n in [*conf['volumes'],*conf['networks']])
# Verify stopped, clean source database; source volumes mounted read-only.
src='centrochange-b99-r4-r4-fit-db-1';state=json.loads(subprocess.check_output(['docker','inspect',src],text=True))[0]
assert not state['State']['Running'] and not state['State']['OOMKilled'] and state['State']['ExitCode']==0
ops.cmd(ops.compose('create','--no-build'),'create-isolated-resources')
for suffix in ['sites','assets']:
 source='centrochange-b99-r4-r4-fit-'+suffix;dest=project+'-r5-fit-'+suffix
 consumers=subprocess.check_output(['docker','ps','-q','--filter','volume='+source],text=True).split();assert not consumers
 ops.cmd(['docker','run','--name',project+'-r5-fit-copy-retry-'+suffix,'--label','centrochange.mission=B99-R5','--label','com.docker.compose.project='+project,'--network','none','--user','0','--memory','128m','--memory-swap','128m','--cpus','1','--device-read-bps','/dev/sda:8mb','--device-write-bps','/dev/sda:4mb','--mount','type=volume,source='+source+',target=/source,readonly','--mount','type=volume,source='+dest+',target=/destination','--entrypoint','sh',ops.IMAGE,'-c','if [ -d /destination/assets ] && [ ! -L /destination/assets ] && [ -L /source/assets ]; then mv /destination/assets /destination/assets-initial-copyup; fi; cp -a /source/. /destination/'],'clone-'+suffix,timeout=900)
print('R4 migrated TARGET copied read-only into R5 exclusive volumes',flush=True)
ops.cmd(ops.compose('up','-d','--no-build'),'target-up')
for _ in range(90):
 ops.safe()
 try:
  import urllib.request
  if urllib.request.urlopen('http://127.0.0.1:8099/api/method/ping',timeout=3).status==200:break
 except Exception:pass
 time.sleep(2)
else:raise RuntimeError('TARGET R5 HTTP unavailable')
print('R5 TARGET READY, no build/bootstrap/migration repeated',flush=True)
