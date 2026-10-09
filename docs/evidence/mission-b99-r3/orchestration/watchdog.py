import pathlib,time,json,subprocess
r=pathlib.Path(__file__).parent
while not (r/'monitor-finish').exists():
 if time.time()-(r/'monitor-heartbeat').stat().st_mtime>30:
  if not (r/'safety-stop.json').exists():(r/'safety-stop.json').write_text(json.dumps(['MONITOR_HEARTBEAT_LOST']))
  ids=subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R3'],text=True).split()
  for cid in subprocess.check_output(['docker','ps','-q','--filter','name=centrochange-b99-r3-fit-builder'],text=True).split():
   if subprocess.check_output(['docker','inspect','-f','{{.Name}}',cid],text=True).strip()=='/centrochange-b99-r3-fit-builder':ids.append(cid)
  if ids:subprocess.run(['docker','stop','--time','15',*ids],stdout=subprocess.DEVNULL)
  break
 time.sleep(5)
