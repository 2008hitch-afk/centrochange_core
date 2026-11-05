import pathlib,json,subprocess,time,fcntl,datetime,urllib.request,sys
r=pathlib.Path(__file__).parent
lock=open('/run/user/1000/centrochange-docker-writer.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
base=json.loads((r/'protected-before.json').read_text()); oom0=int(next(x.split()[1] for x in pathlib.Path('/proc/vmstat').read_text().splitlines() if x.startswith('oom_kill '))); low=pressure=0
out=open(r/'memory-samples.jsonl','a',buffering=1)
def stop():
 ids=subprocess.check_output(['docker','ps','-q','--filter','label=centrochange.mission=B99-R2'],text=True,timeout=10).split()
 builders=subprocess.check_output(['docker','ps','-q','--filter','name=buildx_buildkit_centrochange-b99-r2-builder'],text=True,timeout=10).split()
 if ids+builders:subprocess.run(['docker','stop','--time','15',*ids,*builders],stdout=subprocess.DEVNULL,timeout=60)
while not (r/'monitor-finish').exists():
 errs=[];mem={x.split(':')[0]:int(x.split()[1])*1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines()};psi={x.split()[0]:float(x.split()[1].split('=')[1]) for x in pathlib.Path('/proc/pressure/memory').read_text().splitlines()};oom=int(next(x.split()[1] for x in pathlib.Path('/proc/vmstat').read_text().splitlines() if x.startswith('oom_kill ')))
 low=low+1 if mem['MemAvailable']<1024*2**20 else 0;pressure=pressure+1 if psi['full']>=1 or psi['some']>=5 else 0
 if mem['MemAvailable']<768*2**20 or low>=3:errs.append('MEMORY_RESERVE')
 if pressure>=3:errs.append('PSI')
 if oom>oom0:errs.append('OOM')
 if mem['SwapTotal']!=mem['SwapFree']:errs.append('SWAP')
 ids=subprocess.check_output(['docker','ps','-aq','--no-trunc'],text=True,timeout=10).split();cs=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True,timeout=10));by={c['Id']:c for c in cs}
 for b in base:
  c=by.get(b['id']);
  if not c or c['Image']!=b['image'] or c['RestartCount']!=b['restart'] or c['State']['StartedAt']!=b['started'] or c['State']['Running']!=b['running']:errs.append('PROTECTED_CHANGED')
 probes=[];builder=lab=False;caps=usage=0
 for c in cs:
  own=c['Config'].get('Labels',{}).get('centrochange.mission')=='B99-R2' or c['Name']=='/buildx_buildkit_centrochange-b99-r2-builder0'
  if not own or not c['State']['Running']:continue
  isbuild=c['Name'].startswith('/buildx_buildkit_');builder|=isbuild;lab|=not isbuild
  rel=next(x.split(':',2)[2].strip().lstrip('/') for x in pathlib.Path('/proc',str(c['State']['Pid']),'cgroup').read_text().splitlines() if x.startswith('0::'));cg=pathlib.Path('/sys/fs/cgroup')/rel
  while cg.name!='docker-'+c['Id']+'.scope' and cg!=pathlib.Path('/sys/fs/cgroup'):cg=cg.parent
  if cg.name!='docker-'+c['Id']+'.scope':raise RuntimeError('CONTAINER_CGROUP_NOT_PROVEN')
  cap=(cg/'memory.max').read_text().strip();cur=int((cg/'memory.current').read_text());peak=int((cg/'memory.peak').read_text());events=dict((k,int(v)) for k,v in (x.split() for x in (cg/'memory.events').read_text().splitlines()))
  if cap=='max' or (cg/'memory.swap.max').read_text().strip()!='0':errs.append('CAP_NOT_ENFORCED')
  else:caps+=int(cap)
  usage+=cur
  if events.get('oom',0) or events.get('oom_kill',0):errs.append('PROBE_OOM')
  probes.append({'name':c['Name'],'current':cur,'peak':peak,'max':cap,'events':events})
 if builder and lab:errs.append('PHASE_OVERLAP')
 if caps>(2147483648 if builder else 2684354560):errs.append('CAP_SUM')
 try:
  if urllib.request.urlopen('http://127.0.0.1:8082/api/method/ping',timeout=10).status!=200:errs.append('UAT_HTTP')
 except Exception:errs.append('UAT_HTTP')
 if time.time()>=datetime.datetime.fromisoformat('2026-10-09T18:01:00+02:00').timestamp():errs.append('HARD_DEADLINE')
 io_psi={x.split()[0]:float(x.split()[1].split('=')[1]) for x in pathlib.Path('/proc/pressure/io').read_text().splitlines()};vm=dict(x.split() for x in pathlib.Path('/proc/vmstat').read_text().splitlines());sv=__import__('os').statvfs('/');disk=sv.f_bavail*sv.f_frsize
 if disk<4*2**30:errs.append('DISK_RESERVE')
 out.write(json.dumps({'io_psi':io_psi,'reclaim_writeback':{k:int(v) for k,v in vm.items() if k.startswith(('pgscan','pgsteal','allocstall')) or k in ['nr_dirty','nr_writeback']},'disk_available':disk,'time':time.time(),'available':mem['MemAvailable'],'psi':psi,'oom':oom,'caps':caps,'usage':usage,'probes':probes,'errors':errs})+'\n');(r/'monitor-heartbeat').write_text(str(time.time()))
 if errs:(r/'safety-stop.json').write_text(json.dumps(errs));stop();sys.exit(2)
 time.sleep(5)
