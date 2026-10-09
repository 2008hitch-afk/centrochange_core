import ops,json,subprocess,time
r=ops.ROOT
conf=json.loads(ops.cmd(ops.compose('config','--format','json'),'validated-config'))
assert sum(int(v['mem_limit']) for v in conf['services'].values())==2147483648
existing=set(subprocess.check_output(['docker','volume','ls','-q'],text=True).split())
assert not existing.intersection(conf['volumes'])
assert all(n.startswith(ops.PROJECT+'-r4-fit-') for n in [*conf['volumes'],*conf['networks']])
ops.cmd(ops.compose('up','-d','r4-fit-db','r4-fit-redis-cache','r4-fit-redis-queue'),'current-db-up')
for _ in range(90):
 ops.safe()
 if subprocess.check_output(['docker','inspect','-f','{{.State.Health.Status}}',ops.PROJECT+'-r4-fit-db-1'],text=True).strip()=='healthy':break
 time.sleep(2)
else:raise RuntimeError('DB health')
ops.restore_current('restore-checkpoint')
print('CURRENT checkpoint restored',flush=True)
target=json.loads((r/'target-image.json').read_text())['immutable_id']
ops.oneoff("import subprocess\nsubprocess.run(['bench','--site','b99.local','migrate'],check=True)\n",'migrate-r4',image=target)
print('TARGET isolated migration PASS',flush=True)
# Supported cached bundler only: rebuild manifest from existing immutable built artifacts.
ops.oneoff("import subprocess\nsubprocess.run(['bench','build','--using-cached','--apps','frappe,erpnext,builder,healthcare,centrochange_core'],check=True)\nsubprocess.run(['bench','--site','b99.local','clear-cache'],check=True)\n",'native-cached-assets',image=target)
print('Native cached assets restored',flush=True)
supp=r/'supplement-private-uat'
ops.cmd(['docker','run','--name',ops.PROJECT+'-r4-fit-supplement','--label','centrochange.mission=B99-R4','--network','none','--user','0','--memory','32m','--memory-swap','32m','--mount','type=bind,source='+str(supp)+',target=/supplement,readonly','--mount','type=volume,source='+ops.PROJECT+'-r4-fit-sites,target=/sites','--entrypoint','sh',ops.IMAGE,'-c','mkdir -p /sites/b99.local/private/uat && cp /supplement/demo.json /sites/b99.local/private/uat/demo.json && chown -R 1000:1000 /sites/b99.local/private/uat && chmod 600 /sites/b99.local/private/uat/demo.json'],'private-manifest-restore')
(r/'compose.json').write_text((r/'compose-target.json').read_text())
ops.cmd(ops.compose('up','-d','--no-build'),'target-up')
print('TARGET R4 started',flush=True)
