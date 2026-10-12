import pathlib,json,subprocess,time,datetime,urllib.request,sys,os
from c109_r14_writer import claim_writer_lease, stop_exact_r14
r=pathlib.Path(__file__).parent;lock=claim_writer_lease(r)
def vm():return dict(x.split() for x in pathlib.Path('/proc/vmstat').read_text().splitlines())
def psi(kind):return {x.split()[0]:float(x.split()[1].split('=')[1]) for x in pathlib.Path('/proc/pressure',kind).read_text().splitlines()}
oom0=int(vm()['oom_kill']);low=pressure=stable=0;out=open(r/'memory-samples.jsonl','a',buffering=1);pending={}
def stop():
 stop_exact_r14()
while not (r/'monitor-finish').exists():
 errs=[];mem={x.split(':')[0]:int(x.split()[1])*1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines()};mp=psi('memory');ip=psi('io');v=vm();oom=int(v['oom_kill']);low=low+1 if mem['MemAvailable']<1024*2**20 else 0;pressure=pressure+1 if mp['full']>=1 or mp['some']>=5 else 0
 if mem['MemAvailable']<768*2**20 or low>=3:errs.append('MEMORY_RESERVE')
 if pressure>=3:errs.append('PSI')
 if (r/'rc22-alert.json').exists() or not (r/'rc22-heartbeat').exists() or time.time()-float((r/'rc22-heartbeat').read_text())>8:errs.append('RC22_INDEPENDENT_MONITOR')
 if oom>oom0:errs.append('OOM')
 if mem['SwapTotal']!=mem['SwapFree']:errs.append('SWAP')
 if (r/'protected-event-alert.json').exists() or time.time()-float((r/'events-heartbeat').read_text())>15:errs.append('PROTECTED_EVENT_MONITOR')
 probes=[];caps=usage=0;builder=lab=False;heavy=[];own=json.loads((r/'own-containers.json').read_text())
 for cid,c in own.items():
  cg=pathlib.Path('/sys/fs/cgroup/system.slice/docker-'+cid+'.scope')
  if not (cg/'memory.max').exists():continue
  try:
   if 'populated 1' not in (cg/'cgroup.events').read_text():continue
   cap=(cg/'memory.max').read_text().strip();sw=(cg/'memory.swap.max').read_text().strip();cur=int((cg/'memory.current').read_text());peak=int((cg/'memory.peak').read_text());events=dict((k,int(v)) for k,v in (x.split() for x in (cg/'memory.events').read_text().splitlines()));paused=(cg/'cgroup.freeze').read_text().strip()=='1'
   isbuild=c.get('phase')=='build';builder|=isbuild;lab|=not isbuild
   if cap=='max':
    # Ignore only a confirmed exited container's transient teardown cgroup.
    running=subprocess.check_output(['docker','inspect','-f','{{.State.Running}}',cid],text=True,timeout=10).strip()
    if running=='false':continue
   if cap=='max' or sw!='0':errs.append('CAP_NOT_ENFORCED')
   else:caps+=int(cap)
   usage+=cur
   if events.get('oom',0) or events.get('oom_kill',0):errs.append('PROBE_OOM')
   probes.append({'name':c['name'],'current':cur,'peak':peak,'max':cap,'events':events,'io_stat':(cg/'io.stat').read_text(),'io_max':(cg/'io.max').read_text(),'local_memory_psi':(cg/'memory.pressure').read_text(),'local_io_psi':(cg/'io.pressure').read_text(),'paused':paused})
   if c['heavy']:heavy.append((cid,c['name'],paused))
  except FileNotFoundError:continue
 if builder and lab:errs.append('PHASE_OVERLAP')
 if caps>(2147483648 if builder else 2684354560):errs.append('CAP_SUM')
 try:
  start=time.time();response=urllib.request.urlopen('http://127.0.0.1:8082/api/method/ping',timeout=10);latency=time.time()-start
  if response.status!=200:errs.append('UAT_HTTP')
 except Exception:errs.append('UAT_HTTP');latency=None
 if time.time()>=datetime.datetime.fromisoformat(json.loads((r/'activation.json').read_text())['hard_stop_utc']).timestamp():errs.append('HARD_DEADLINE')
 sv=os.statvfs('/');disk=sv.f_bavail*sv.f_frsize
 if disk<4*2**30:errs.append('DISK_RESERVE')
 stable=stable+1 if mp['full']<0.1 and mp['some']<0.5 and ip['full']<1 else 0
 for cid,name,paused in heavy:
  process=pending.get(cid)
  if process and process.poll() is None:continue
  action='pause' if not paused and mp['full']>=0.3 else ('unpause' if paused and stable>=3 else None)
  if action and not errs:
   pending[cid]=subprocess.Popen(['docker',action,cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   with open(r/'backoff.jsonl','a') as bf:bf.write(json.dumps({'time':time.time(),'action':action,'container':name,'memory_psi':mp,'io_psi':ip})+'\n')
 out.write(json.dumps({'time':time.time(),'available':mem['MemAvailable'],'psi':mp,'io_psi':ip,'oom':oom,'caps':caps,'usage':usage,'probes':probes,'errors':errs,'disk_available':disk,'rc22_ping_seconds':latency,'reclaim_writeback':{k:int(v) for k,v in v.items() if k.startswith(('pgscan','pgsteal','allocstall')) or k in ['nr_dirty','nr_writeback']}})+'\n');tmp=r/'monitor-heartbeat.tmp';tmp.write_text(str(time.time()));tmp.replace(r/'monitor-heartbeat')
 if errs:(r/'safety-stop.json').write_text(json.dumps(errs));stop();sys.exit(2)
 time.sleep(5)
