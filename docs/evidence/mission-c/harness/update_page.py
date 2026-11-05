import pathlib,json,subprocess,time
r=pathlib.Path(__file__).parent
assert not (r/'safety-stop.json').exists();assert time.time()-(r/'monitor-heartbeat').stat().st_mtime<15
args=['docker','compose','--env-file',str(r/'runtime.env'),'-f',str(r/'compose.json')]
p=subprocess.run(['python3',str(r/'product/infra/mission_c_image.py'),'--base-archive','/home/empv26/.local/state/centrochange-b99-r5-20261009/image-build/r5-target.oci.tar','--source',str(r/'product'),'--output',str(r/'desk-delta.oci.tar')],capture_output=True,text=True,check=True);proof=json.loads(p.stdout);(r/'image-proof.json').write_text(json.dumps(proof))
p=subprocess.run(['docker','load','-i',str(r/'desk-delta.oci.tar')],capture_output=True,text=True,check=True);(r/'load-desk-image.log').write_text(p.stdout+p.stderr)
c=json.loads((r/'compose.json').read_text())
for v in c['services'].values():
 if v['image'].startswith('sha256:'):v['image']=proof['image']
(r/'compose.json').write_text(json.dumps(c,indent=2))
p=subprocess.run(args+['up','-d','--no-build'],capture_output=True,text=True,check=True);(r/'update-page.log').write_text(p.stdout+p.stderr)
print('C109 updated immutable Page image '+proof['image'])
