import pathlib,json,subprocess,time
r=pathlib.Path(__file__).parent;project='centrochange-c109';base='sha256:342dd48b649aae93fe2e9cc080e44b1ff622b11c900bd084b636af3f2e4624a7'
def safe():
 assert not (r/'safety-stop.json').exists(),'SAFETY_STOP'
 assert time.time()-(r/'monitor-heartbeat').stat().st_mtime<15,'MONITOR_LOST'
def cmd(args,label,timeout=600):
 safe();p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);(r/(label+'.log')).write_text(p.stdout+p.stderr);safe();assert p.returncode==0,label;return p.stdout
compose=['docker','compose','--env-file',str(r/'runtime.env'),'-f',str(r/'compose.json')]
# Existing layers loaded, tiny COPY delta only; no base archive reimport.
cmd(['docker','load','-i',str(r/'desk-delta.oci.tar')],'load-desk-image')
image=json.loads((r/'image-proof.json').read_text())['image'];cmd(['docker','image','inspect',image,'--format','{{.Id}}'],'verify-desk-image')
c=json.loads((r/'compose.json').read_text())
for v in c['services'].values():
 if v['image']==base:v['image']=image
(r/'compose.json').write_text(json.dumps(c,indent=2))
cmd(compose+['create','--no-build'],'create-exclusive')
for suffix in ['db-data','sites','assets']:
 source='centrochange-b99-r5-r5-fit-'+suffix;dest=project+'-c-fit-'+suffix
 assert not subprocess.check_output(['docker','ps','-q','--filter','volume='+source],text=True).strip()
 cmd(['docker','run','--name',project+'-copy-'+suffix,'--label','centrochange.mission=C109','--label','com.docker.compose.project='+project,'--label','centrochange.heavy=true','--network','none','--user','0','--memory','128m','--memory-swap','128m','--cpus','1','--device-read-bps','/dev/sda:8mb','--device-write-bps','/dev/sda:4mb','--mount','type=volume,source='+source+',target=/source,readonly','--mount','type=volume,source='+dest+',target=/destination','--entrypoint','sh',base,'-c','cp -a /source/. /destination/'],'clone-'+suffix)
 print('Copied isolated '+suffix,flush=True)
cmd(compose+['up','-d','--no-build'],'start-exclusive')
print('C109 started isolated on 8109',flush=True)
