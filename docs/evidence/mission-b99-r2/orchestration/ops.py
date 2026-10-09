import pathlib,json,subprocess,time,datetime
ROOT=pathlib.Path(__file__).parent; PROJECT='centrochange-b99-rehearsal';SITE='b99.local';SOURCE=pathlib.Path('/home/empv26/.local/state/centrochange-b99-execution-20261008/source');IMAGE='sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80';BACKEND=PROJECT+'-r2-backend-1'
def safe():
 assert not (ROOT/'safety-stop.json').exists(),'SAFETY_STOP'
 assert time.time()-float((ROOT/'monitor-heartbeat').read_text())<15,'MONITOR_LOST'
 assert time.time()<datetime.datetime.fromisoformat('2026-10-09T18:01:00+02:00').timestamp(),'DEADLINE'
def redact(t):
 for v in json.loads((ROOT/'credentials.json').read_text()).values(): t=t.replace(v,'[REDACTED]')
 return t

def compose(*args):return ['docker','compose','--env-file',str(ROOT/'runtime.env'),'-f',str(ROOT/'compose.json'),*args]
def cmd(args,label,input=None,timeout=1800):
 safe();start=time.time();p=subprocess.run(args,input=input,text=True,capture_output=True,timeout=timeout);(ROOT/(label+'.log')).write_text(redact(p.stdout+p.stderr));(ROOT/(label+'.result.json')).write_text(json.dumps({'exit_code':p.returncode,'elapsed_seconds':time.time()-start}));safe()
 if p.returncode:raise RuntimeError(label+' failed; see sanitized local evidence')
 return p.stdout

def isolation():
 ids=subprocess.check_output(['docker','ps','-aq','--filter','label=centrochange.mission=B99-R2'],text=True).split();assert ids
 for c in json.loads(subprocess.check_output(['docker','inspect',*ids],text=True)):
  assert all(n==PROJECT+'-r2-net' for n in c['NetworkSettings']['Networks'])
  for m in c['Mounts']:
   assert m['Type']=='volume'
   if not m['Name'].startswith(PROJECT+'-'):assert m['Destination']=='/home/frappe/frappe-bench/logs' and subprocess.check_output(['docker','ps','-aq','--no-trunc','--filter','volume='+m['Name']],text=True).split()==[c['Id']]
 return True

def oneoff(code,label,image=None):
 isolation(); return cmd(['docker','run','-i','--name',PROJECT+'-r2-'+label,'--label','centrochange.mission=B99-R2','--label','com.docker.compose.project='+PROJECT,'--label','com.docker.compose.service='+label,'--network',PROJECT+'-r2-net','--memory','1536m','--memory-swap','1536m','--restart','no','--mount','type=volume,source='+PROJECT+'-r2-sites,target=/home/frappe/frappe-bench/sites','--workdir','/home/frappe/frappe-bench','--entrypoint','/home/frappe/frappe-bench/env/bin/python',image or IMAGE],label,code)
def execute(code,label='execute'):
 isolation();return cmd(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',BACKEND,'env/bin/python'],label,"import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\n"+code)
