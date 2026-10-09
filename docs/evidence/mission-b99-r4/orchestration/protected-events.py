import pathlib,json,subprocess,select,time
r=pathlib.Path(__file__).parent;protected={x['id'] for x in json.loads((r/'protected-before.json').read_text())};actions={'start','die','stop','kill','restart','pause','unpause','destroy','rename','update'}
own=json.loads((r/'own-containers.json').read_text())
p=subprocess.Popen(['docker','events','--format','{{json .}}'],stdout=subprocess.PIPE,text=True,bufsize=1)
try:
 while not (r/'monitor-finish').exists():
  if p.poll() is not None:(r/'protected-event-alert.json').write_text(json.dumps({'error':'EVENT_STREAM_LOST'}));break
  tmp=r/'events-heartbeat.tmp';tmp.write_text(str(time.time()));tmp.replace(r/'events-heartbeat')
  if select.select([p.stdout],[],[],2)[0]:
   line=p.stdout.readline()
   if not line:continue
   ev=json.loads(line);actor=ev.get('Actor',{});cid=actor.get('ID');act=ev.get('Action');attrs=actor.get('Attributes',{})
   if ev.get('Type')=='container' and attrs.get('centrochange.mission')=='B99-R4':
    own[cid]={'name':'/'+attrs.get('name','unknown'),'heavy':attrs.get('centrochange.heavy')=='true'}
    temp=r/'own-containers.tmp';temp.write_text(json.dumps(own));temp.replace(r/'own-containers.json')
   if (ev.get('Type')=='container' and cid in protected and act in actions) or (ev.get('Type')=='network' and attrs.get('container') in protected and act in ['connect','disconnect']):
    (r/'protected-event-alert.json').write_text(json.dumps({'id':cid,'action':act,'time':ev.get('time')}))
finally:p.terminate()
