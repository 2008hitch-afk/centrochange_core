import pathlib,json,subprocess,select,time
r=pathlib.Path(__file__).parent;protected={x['id'] for x in json.loads((r/'protected-before.json').read_text())};actions={'start','die','stop','kill','restart','pause','unpause','destroy','rename','update'}
p=subprocess.Popen(['docker','events','--format','{{json .}}'],stdout=subprocess.PIPE,text=True,bufsize=1)
try:
 while not (r/'monitor-finish').exists():
  if p.poll() is not None:(r/'protected-event-alert.json').write_text(json.dumps({'error':'EVENT_STREAM_LOST'}));break
  (r/'events-heartbeat').write_text(str(time.time()))
  if select.select([p.stdout],[],[],2)[0]:
   line=p.stdout.readline()
   if not line:continue
   ev=json.loads(line);actor=ev.get('Actor',{});cid=actor.get('ID');act=ev.get('Action');attrs=actor.get('Attributes',{})
   if (ev.get('Type')=='container' and cid in protected and act in actions) or (ev.get('Type')=='network' and attrs.get('container') in protected and act in ['connect','disconnect']):
    (r/'protected-event-alert.json').write_text(json.dumps({'id':cid,'action':act,'time':ev.get('time')}))
finally:p.terminate()
