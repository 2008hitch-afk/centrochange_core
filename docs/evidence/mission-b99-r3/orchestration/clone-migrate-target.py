import ops,pathlib,json,subprocess,time,datetime
r=ops.ROOT;old=pathlib.Path('/home/empv26/.local/state/centrochange-b99-r2-20261009');target=json.loads((r/'target-image.json').read_text())['immutable_id'];assert json.loads((r/'target-pin-check.result.json').read_text())['exit_code']==0
assert time.time()<datetime.datetime.fromisoformat('2026-10-09T15:01:00+02:00').timestamp()-1800
conf=json.loads(ops.cmd(ops.compose('config','--format','json'),'r3-config-validated'));assert all(x['name'].startswith(ops.PROJECT+'-r3-') for x in conf['volumes'].values());assert all(x['name'].startswith(ops.PROJECT+'-r3-') for x in conf['networks'].values())
for svc in conf['services'].values():
 assert svc['labels']['centrochange.mission']=='B99-R3'
 for mount in svc.get('volumes',[]):assert mount['type']=='volume' and mount['source'].startswith(ops.PROJECT+'-r3-')
ops.cmd(ops.compose('up','-d','r3-db','r3-redis-cache','r3-redis-queue'),'current-clone-db-up')
for _ in range(90):
 ops.safe()
 if subprocess.check_output(['docker','inspect','-f','{{.State.Health.Status}}',ops.PROJECT+'-r3-db-1'],text=True).strip()=='healthy':break
 time.sleep(2)
else:raise RuntimeError('R3 DB not healthy')
ops.restore_current('clone-current');print('CURRENT RESTORED INTO R3',flush=True)
prefix="import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\n"
ops.oneoff(prefix+(r/'inventory-code.py').read_text(),'clone-current-inventory')
def inv(path):return json.loads(next(x for x in path.read_text().splitlines() if x.startswith('INVENTORY=')).split('=',1)[1])
a=inv(old/'current-inventory-retry.log');b=inv(r/'clone-current-inventory.log');comparison={k:a[k]==b[k] for k in ['schema','metadata','business','files','installed_apps']};(r/'current-clone-reconciliation.json').write_text(json.dumps(comparison,indent=2));assert all(comparison.values()),'CURRENT restore inventory differs; preserve and diagnose before TARGET'
print('CURRENT CLONE RECONCILIATION PASS',flush=True)
# Supported migration only, no product/manual SQL patch.
conf=json.loads((r/'compose.json').read_text())
for svc in conf['services'].values():
 if svc['image']==ops.IMAGE:svc['image']=target
(r/'compose-target.json').write_text(json.dumps(conf,indent=2))
code="import subprocess\nsubprocess.run(['bench','--site','b99.local','migrate'],check=True)\nsubprocess.run(['bench','--site','b99.local','enable-scheduler'],check=True)\n"
try:
 ops.oneoff(code,'migrate-target',image=target)
except Exception:
 (r/'target-migration-status.json').write_text(json.dumps({'status':'FAIL','rollback_required':True}));raise
(r/'target-migration-status.json').write_text(json.dumps({'status':'PASS','rollback_required':True}));print('TARGET MIGRATION PASS',flush=True)
ops.oneoff(prefix+(r/'inventory-code.py').read_text(),'target-inventory',image=target)
# Runtime config is versioned orchestration; keep CURRENT config preserved.
(r/'compose-current.json').write_text((r/'compose.json').read_text());(r/'compose.json').write_text((r/'compose-target.json').read_text())
ops.cmd(ops.compose('up','-d','--no-build','r3-backend','r3-websocket','r3-queue-short','r3-queue-long','r3-scheduler','r3-frontend'),'target-runtime-up');print('TARGET RUNTIME STARTED',flush=True)
