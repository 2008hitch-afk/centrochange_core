import pathlib,json,subprocess,time,datetime
ROOT=pathlib.Path(__file__).parent; PROJECT='centrochange-b99-rehearsal';SITE='b99.local';SOURCE=pathlib.Path('/home/empv26/.local/state/centrochange-b99-execution-20261008/source');IMAGE='sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80';BACKEND=PROJECT+'-r3-backend-1'
def safe():
 assert not (ROOT/'safety-stop.json').exists(),'SAFETY_STOP'
 assert time.time()-(ROOT/'monitor-heartbeat').stat().st_mtime<15,'MONITOR_LOST'
 assert time.time()<datetime.datetime.fromisoformat('2026-10-09T18:01:00+02:00').timestamp(),'DEADLINE'
def redact(t):
 for v in json.loads((ROOT/'credentials.json').read_text()).values(): t=t.replace(v,'[REDACTED]')
 for k,v in json.loads(pathlib.Path('/home/empv26/.local/state/centrochange-b99-r2-20261009/checkpoint/site_config.json').read_text()).items():
  if isinstance(v,str) and k in ['db_password','encryption_key'] and v:t=t.replace(v,'[REDACTED]')
 if (ROOT/'sensitive-values.json').exists():
  for v in json.loads((ROOT/'sensitive-values.json').read_text()):
   if isinstance(v,str) and len(v)>=8:t=t.replace(v,'[REDACTED]')
 return t

def compose(*args):return ['docker','compose','--env-file',str(ROOT/'runtime.env'),'-f',str(ROOT/'compose.json'),*args]
def cmd(args,label,input=None,timeout=1800):
 safe();start=time.time();p=subprocess.run(args,input=input,text=True,capture_output=True,timeout=timeout);(ROOT/(label+'.log')).write_text(redact(p.stdout+p.stderr));(ROOT/(label+'.result.json')).write_text(json.dumps({'exit_code':p.returncode,'elapsed_seconds':time.time()-start}));safe()
 if p.returncode:raise RuntimeError(label+' failed; see sanitized local evidence')
 return p.stdout

def isolation():
 ids=subprocess.check_output(['docker','ps','-aq','--filter','label=centrochange.mission=B99-R3','--filter','label=com.docker.compose.project='+PROJECT],text=True).split();assert ids
 for c in json.loads(subprocess.check_output(['docker','inspect',*ids],text=True)):
  assert all(n in [PROJECT+'-r3-net',PROJECT+'-r3-http'] for n in c['NetworkSettings']['Networks']); assert PROJECT+'-r3-http' not in c['NetworkSettings']['Networks'] or c['Name']== '/'+PROJECT+'-r3-frontend-1'
  for m in c['Mounts']:
   if m['Type']=='bind':
    assert m['Destination']=='/checkpoint' and m['RW']==False;continue
   assert m['Type']=='volume'
   if not m['Name'].startswith(PROJECT+'-'):assert m['Destination']=='/home/frappe/frappe-bench/logs' and subprocess.check_output(['docker','ps','-aq','--no-trunc','--filter','volume='+m['Name']],text=True).split()==[c['Id']]
 return True

def oneoff(code,label,image=None):
 isolation(); return cmd(['docker','run','-i','-e','FRAPPE_STREAM_LOGGING=1','--name',PROJECT+'-r3-'+label,'--label','centrochange.mission=B99-R3','--label','com.docker.compose.project='+PROJECT,'--label','com.docker.compose.service='+label,'--network',PROJECT+'-r3-net','--memory','1536m','--memory-swap','1536m','--restart','no','--mount','type=volume,source='+PROJECT+'-r3-sites,target=/home/frappe/frappe-bench/sites','--workdir','/home/frappe/frappe-bench','--entrypoint','/home/frappe/frappe-bench/env/bin/python',image or IMAGE],label,code)
def execute(code,label='execute'):
 isolation();return cmd(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',BACKEND,'env/bin/python'],label,"import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\n"+code)

CHECKPOINT=pathlib.Path('/home/empv26/.local/state/centrochange-b99-r2-20261009/checkpoint')
def restore_current(label):
 creds=json.loads((ROOT/'credentials.json').read_text())
 db=next(CHECKPOINT.glob('*-database.sql.gz')).name;pub=next(CHECKPOINT.glob('*-files.tgz')).name;private=next(CHECKPOINT.glob('*-private-files.tgz')).name
 code="import pathlib,shutil,subprocess\nbase=pathlib.Path('/home/frappe/frappe-bench/sites');site=base/'b99.local';site.mkdir(exist_ok=True)\nfor d in ['private','public','private/files','public/files','logs']: (site/d).mkdir(parents=True,exist_ok=True)\nshutil.copyfile('/checkpoint/site_config.json',site/'site_config.json');shutil.copyfile('/checkpoint/common_site_config.json',base/'common_site_config.json');shutil.copyfile('/checkpoint/apps.txt',base/'apps.txt')\n"
 argv=['bench','--site',SITE,'restore','/checkpoint/'+db,'--db-root-password',creds['db'],'--with-public-files','/checkpoint/'+pub,'--with-private-files','/checkpoint/'+private,'--force']
 code+="import json\ncfg=json.loads((site/'site_config.json').read_text())\n"
 bootstrap=['bench','new-site',SITE,'--db-host','db','--db-name',None,'--db-password',None,'--mariadb-root-password',creds['db'],'--admin-password',creds['admin'],'--mariadb-user-host-login-scope','%','--force']
 code+='args='+repr(bootstrap)+"\nargs[6]=cfg['db_name'];args[8]=cfg['db_password'];subprocess.run(args,check=True)\nshutil.copyfile('/checkpoint/site_config.json',site/'site_config.json')\n"
 code+='subprocess.run('+repr(argv)+',check=True)\n'
 args=['docker','run','-i','-e','FRAPPE_STREAM_LOGGING=1','--name',PROJECT+'-r3-'+label,'--label','centrochange.mission=B99-R3','--label','com.docker.compose.project='+PROJECT,'--label','com.docker.compose.service='+label,'--network',PROJECT+'-r3-net','--memory','1536m','--memory-swap','1536m','--restart','no','--mount','type=volume,source='+PROJECT+'-r3-sites,target=/home/frappe/frappe-bench/sites','--mount','type=bind,source='+str(CHECKPOINT)+',target=/checkpoint,readonly','--workdir','/home/frappe/frappe-bench','--entrypoint','/home/frappe/frappe-bench/env/bin/python',IMAGE]
 return cmd(args,label,code)
