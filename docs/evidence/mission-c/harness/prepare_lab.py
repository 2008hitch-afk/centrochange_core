import pathlib,json,subprocess,datetime,os
r=pathlib.Path(__file__).parent;old=pathlib.Path('/home/empv26/.local/state/centrochange-b99-r5-final-20261009');os.chmod(r,0o700)
allc=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-aq'],text=True).split()],text=True));protected=[{'id':c['Id'],'name':c['Name'],'image':c['Image'],'state':c['State']['Status'],'started':c['State']['StartedAt'],'restart':c['RestartCount'],'mounts':[{k:m.get(k) for k in ['Type','Name','Destination','RW']} for m in c['Mounts']],'networks':sorted(c['NetworkSettings']['Networks'])} for c in allc];(r/'protected-before.json').write_text(json.dumps(protected));(r/'own-containers.json').write_text('{}')
for name in ['safety.py','protected-events.py']:
 s=(old/name).read_text().replace('B99-R5','C109')
 if name=='safety.py':s=s.replace("datetime.datetime.fromisoformat('2026-10-09T21:47:00+02:00').timestamp()","datetime.datetime.fromisoformat(json.loads((r/'activation.json').read_text())['hard_stop']).timestamp()")
 (r/name).write_text(s)
# Dedicated Compose, no source-volume mounts. Database copied only after confirmed clean stop.
c=json.loads((old/'compose-target.json').read_text());s=json.dumps(c).replace('centrochange-b99-r5-r5-fit-','centrochange-c109-c-fit-').replace('centrochange-b99-r5','centrochange-c109').replace('r5-fit-','c-fit-').replace('B99-R5','C109').replace('8099','8109');c=json.loads(s)
for service in c['services'].values():
 service.setdefault('labels',{}).update({'centrochange.mission':'C109'})
 if 'environment' in service:
  for k in list(service['environment']):
   # DB password comes from copied synthetic database; never printed.
   pass
(r/'compose.json').write_text(json.dumps(c,indent=2));(r/'runtime.env').write_text((old/'runtime.env').read_text());os.chmod(r/'runtime.env',0o600)
# Do not print resolved config: includes local credentials.
config=json.loads(subprocess.check_output(['docker','compose','--env-file',str(r/'runtime.env'),'-f',str(r/'compose.json'),'config','--format','json'],text=True));assert config['name']=='centrochange-c109';assert sum(int(v['mem_limit']) for v in config['services'].values())==2147483648
existingv=set(subprocess.check_output(['docker','volume','ls','-q'],text=True).split());existingn=set(subprocess.check_output(['docker','network','ls','--format','{{.Name}}'],text=True).split());assert not existingv.intersection(config['volumes']);assert not existingn.intersection(config['networks']);assert all(k.startswith('centrochange-c109-') for k in [*config['volumes'],*config['networks']])
for service in config['services'].values():
 assert all(m['type']=='volume' and m['source'].startswith('centrochange-c109-') for m in service.get('volumes',[]))
 for port in service.get('ports',[]):assert port['host_ip']=='127.0.0.1' and str(port['published'])=='8109'
(r/'isolation-static.json').write_text(json.dumps({'pass':True,'project':config['name'],'volumes':list(config['volumes']),'networks':list(config['networks']),'aggregate_memory':2147483648},indent=2))
print('C109 configuration validated: exclusive resources, loopback 8109, memory 2GiB; source R5 remains stopped.')
