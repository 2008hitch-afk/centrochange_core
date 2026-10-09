import ops,json,subprocess,importlib.util
r=ops.ROOT;rr=r/'rollback';spec=importlib.util.spec_from_file_location('ro',rr/'ops.py');ro=importlib.util.module_from_spec(spec);spec.loader.exec_module(ro)
ro.cmd(ro.compose('stop',*json.loads((rr/'compose.json').read_text())['services']),'pause-restored-runtime-for-role-read')
ops.cmd(ops.compose('up','-d','r3-fit-db','r3-fit-redis-cache','r3-fit-redis-queue'),'target-db-read-only-up')
import time
for _ in range(60):
 if subprocess.check_output(['docker','inspect','-f','{{.State.Health.Status}}',ops.PROJECT+'-r3-fit-db-1'],text=True).strip()=='healthy':break
 time.sleep(1)
code="import frappe,json\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\nprint('ROLES='+json.dumps(frappe.get_all('Has Role',fields=['parent','parenttype','role'],order_by='parent, parenttype, role')));frappe.db.rollback();frappe.destroy()"
out=ops.oneoff(code,'target-normalized-roles',image=json.loads((r/'target-image.json').read_text())['immutable_id'])
v=json.loads(next(x for x in out.splitlines() if x.startswith('ROLES=')).split('=',1)[1]);a=json.loads((r/'current-normalized-roles.json').read_text());normalize=lambda rows:{tuple(sorted(x.items())) for x in rows};before=normalize(a);after=normalize(v);delta={'added':[dict(x) for x in sorted(after-before)],'removed':[dict(x) for x in sorted(before-after)],'normalized_semantic_roles_preserved':before==after};(r/'target-role-delta.json').write_text(json.dumps(delta,indent=2));print(json.dumps(delta))
ops.cmd(ops.compose('stop','r3-fit-db','r3-fit-redis-cache','r3-fit-redis-queue'),'target-db-read-only-stop')
ro.cmd(ro.compose('up','-d','--no-build',*json.loads((rr/'compose.json').read_text())['services']),'restore-current-runtime-after-role-read')
