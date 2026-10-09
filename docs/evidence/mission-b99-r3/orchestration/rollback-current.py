import pathlib,json,subprocess,sys,time,secrets,importlib.util,shutil
import ops
r=ops.ROOT;ops.safe()
# Preserve migrated R3 volumes, use entirely new rollback storage/network.
conf=json.loads((r/'compose-current.json').read_text() if (r/'compose-current.json').exists() else (r/'compose.json').read_text())
services=list(conf['services']);ops.cmd(ops.compose('stop',*services),'target-stop-before-rollback')
rr=r/'rollback';rr.mkdir(mode=0o700,exist_ok=True)
base=json.loads((rr/'credentials.json').read_text()) if (rr/'credentials.json').exists() else json.loads((r/'credentials.json').read_text());
if not (rr/'credentials.json').exists():base['db']=secrets.token_hex(24)
(rr/'credentials.json').write_text(json.dumps(base));(rr/'credentials.json').chmod(0o600)
(rr/'runtime.env').write_text('B99_DB_PASSWORD='+base['db']+'\nDB_PASSWORD='+base['db']+'\nADMIN_PASSWORD='+base['admin']+'\nSITE_NAME=b99.local\nHTTP_PORT=8099\n');(rr/'runtime.env').chmod(0o600)
(rr/'compose.json').write_text(json.dumps(json.loads(json.dumps(conf).replace('r3-fit-','r3-fit-rollback-')),indent=2))
s=(r/'ops.py').read_text().replace("PROJECT+'-r3-fit-", "PROJECT+'-r3-fit-rollback-")
s=s.replace("(ROOT/'safety-stop.json')","(ROOT.parent/'safety-stop.json')").replace("(ROOT/'monitor-heartbeat')","(ROOT.parent/'monitor-heartbeat')")
s=s.replace("[PROJECT+'-r3-fit-rollback-net',PROJECT+'-r3-fit-rollback-http']","[PROJECT+'-r3-fit-rollback-net',PROJECT+'-r3-fit-rollback-http',PROJECT+'-r3-fit-net',PROJECT+'-r3-fit-http']")
s=s.replace("assert PROJECT+'-r3-fit-rollback-http' not in c['NetworkSettings']['Networks'] or c['Name']== '/'+PROJECT+'-r3-fit-rollback-frontend-1'","assert PROJECT+'-r3-fit-rollback-http' not in c['NetworkSettings']['Networks'] or c['Name']== '/'+PROJECT+'-r3-fit-rollback-frontend-1'")
(rr/'ops.py').write_text(s)
spec=importlib.util.spec_from_file_location('rollback_ops',rr/'ops.py');ro=importlib.util.module_from_spec(spec);spec.loader.exec_module(ro)
ro.cmd(ro.compose('up','-d','r3-fit-rollback-db','r3-fit-rollback-redis-cache','r3-fit-rollback-redis-queue'),'rollback-db-up')
for _ in range(90):
 ro.safe()
 if subprocess.check_output(['docker','inspect','-f','{{.State.Health.Status}}',ops.PROJECT+'-r3-fit-rollback-db-1'],text=True).strip()=='healthy':break
 time.sleep(2)
else:raise RuntimeError('Rollback DB not healthy')
ro.restore_current('rollback-current');print('REAL CURRENT RESTORE COMPLETED',flush=True)
supp=r/'supplement-private-uat';assert (supp/'demo.json').is_file()
ro.cmd(['docker','run','--name',ops.PROJECT+'-r3-fit-rollback-supplement-'+str(int(time.time())),'--label','centrochange.mission=B99-R3','--network','none','--user','0','--memory','32m','--memory-swap','32m','--mount','type=bind,source='+str(supp)+',target=/supplement,readonly','--mount','type=volume,source='+ops.PROJECT+'-r3-fit-rollback-sites,target=/sites','--entrypoint','sh',ops.IMAGE,'-c','mkdir -p /sites/b99.local/private/uat && cp /supplement/demo.json /sites/b99.local/private/uat/demo.json && chown -R 1000:1000 /sites/b99.local/private/uat && chmod 600 /sites/b99.local/private/uat/demo.json'],'rollback-private-manifest-restore')

prefix="import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\n"
ro.oneoff(prefix+(r/'inventory-code.py').read_text(),'rollback-inventory')
def inventory(path):return json.loads(next(x for x in path.read_text().splitlines() if x.startswith('INVENTORY=')).split('=',1)[1])
a=inventory(pathlib.Path('/home/empv26/.local/state/centrochange-b99-r2-20261009/current-inventory-retry.log'));b=inventory(rr/'rollback-inventory.log');cmp={k:a[k]==b[k] for k in ['schema','metadata','business','files','installed_apps','pins']};(r/'rollback-reconciliation.json').write_text(json.dumps(cmp,indent=2));assert all(cmp.values()),'RESTORE INVENTORY MISMATCH'
print('ROLLBACK INVENTORY RECONCILIATION PASS',flush=True)
ro.oneoff("import subprocess\nsubprocess.run(['bench','--site','b99.local','enable-scheduler'],check=True)",'rollback-enable-scheduler')
ro.cmd(ro.compose('up','-d','--no-build','r3-fit-rollback-backend','r3-fit-rollback-websocket','r3-fit-rollback-queue-short','r3-fit-rollback-queue-long','r3-fit-rollback-scheduler','r3-fit-rollback-frontend'),'rollback-runtime-up')
for _ in range(60):
 try:
  import urllib.request
  if urllib.request.urlopen('http://127.0.0.1:8099/api/method/ping',timeout=3).status==200:break
 except Exception:pass
 time.sleep(2)
else:raise RuntimeError('Restored HTTP unavailable')
out=ro.execute("from centrochange_core.uat import demo\nprint('VALIDATION='+json.dumps(demo.validate(),default=str));frappe.db.rollback();frappe.destroy()",'rollback-demo-validation'); validation=json.loads(next(x for x in out.splitlines() if x.startswith('VALIDATION=')).split('=',1)[1]);assert validation['status']=='PASS'
# Bounded real restored runtime smoke, no external providers or app mutation.
import urllib.request
assert urllib.request.urlopen('http://127.0.0.1:8099/api/method/ping',timeout=10).status==200
out=ro.execute("from centrochange_core.operations.integration_acceptance import run\nprint('RESULT='+json.dumps(run(),default=str));frappe.db.rollback();frappe.destroy()",'rollback-operational-smoke');v=json.loads(next(x for x in out.splitlines() if x.startswith('RESULT=')).split('=',1)[1]);assert v['status']=='PASS'
(r/'rollback-status.json').write_text(json.dumps({'status':'PASS','real_native_restore':True,'full_schema_metadata_business_files_pins_reconciled':True,'http_ping':200,'operational_smoke_checks':len(v['checks'])},indent=2));print('REAL ROLLBACK PASS',flush=True)
