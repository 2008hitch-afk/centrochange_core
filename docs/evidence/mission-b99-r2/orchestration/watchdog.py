import pathlib,time,json,subprocess
r=pathlib.Path(__file__).parent
while not (r/'monitor-finish').exists():
 if time.time()-float((r/'monitor-heartbeat').read_text())>30:
  (r/'safety-stop.json').write_text(json.dumps(['MONITOR_HEARTBEAT_LOST']))
  ids=subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R2'],text=True).split()
  for cid in subprocess.check_output(['docker','ps','-q','--filter','name=buildx_buildkit_centrochange-b99-r2-builder0'],text=True).split():
   if subprocess.check_output(['docker','inspect','-f','{{.Name}}',cid],text=True).strip()=='/buildx_buildkit_centrochange-b99-r2-builder0':ids.append(cid)
  if ids:subprocess.run(['docker','stop','--time','15',*ids],stdout=subprocess.DEVNULL)
  break
 time.sleep(5)
