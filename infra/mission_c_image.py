"""COPY-only OCI delta, reusing already loaded immutable R5 layers; no upstream patch.
Input archive remains read-only. Import requires the base blobs already present.
"""
import argparse,tarfile,json,hashlib,io,gzip,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--base-archive',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
root=pathlib.Path(a.source);revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
sha=lambda b:hashlib.sha256(b).hexdigest();serial=lambda d:json.dumps(d,separators=(',',':')).encode()
with tarfile.open(a.base_archive,'r:') as src:
 index=json.load(src.extractfile('index.json'));desc=index['manifests'][0]
 assert desc['digest']=='sha256:342dd48b649aae93fe2e9cc080e44b1ff622b11c900bd084b636af3f2e4624a7'
 manifest=json.load(src.extractfile('blobs/sha256/'+desc['digest'].split(':')[1]));config=json.load(src.extractfile('blobs/sha256/'+manifest['config']['digest'].split(':')[1]))
raw=io.BytesIO();folder='app/centrochange_core/centrochange_core/centro_change_core/page'
files=[root/folder/'__init__.py',*sorted((root/folder/'cc_unified_desk').glob('*')),*sorted((root/'app/centrochange_core/centrochange_core/centro_change_core/sidebar').rglob('*.json')),*[root/'app/centrochange_core/centrochange_core/public/js'/name for name in ('workspace.js','finance_workspace.js','patient_report.js','professional_view.js','audit_view.js','cc_desk_fragments.js')],root/'app/centrochange_core/centrochange_core/public/css/workspace.css',root/'app/centrochange_core/centrochange_core/security/dev_acceptance.py']
with tarfile.open(fileobj=raw,mode='w') as t:
 for f in files:
  if not f.is_file() or f.suffix not in ('.py','.json','.css','.js'):continue
  b=f.read_bytes();x=tarfile.TarInfo('home/frappe/frappe-bench/apps/centrochange_core/'+str(f.relative_to(root/'app/centrochange_core')));x.size=len(b);x.uid=x.gid=1000;x.mode=0o644;x.mtime=0;t.addfile(x,io.BytesIO(b))
blob=raw.getvalue();layer=gzip.compress(blob,mtime=0);config['rootfs']['diff_ids'].append('sha256:'+sha(blob));config['history'].append({'created_by':'versioned Mission C COPY '+revision});config['config']['Labels']['org.opencontainers.image.revision']=revision
cb=serial(config);manifest['config'].update(digest='sha256:'+sha(cb),size=len(cb));manifest['layers'].append({'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':'sha256:'+sha(layer),'size':len(layer)});mb=serial(manifest);desc.update(digest='sha256:'+sha(mb),size=len(mb));desc['annotations']={'org.opencontainers.image.ref.name':'centrochange-c109:prototype-'+revision[:12]}
with tarfile.open(a.output,'w') as t:
 for name,b in [('oci-layout',serial({'imageLayoutVersion':'1.0.0'})),('index.json',serial(index)),('blobs/sha256/'+sha(layer),layer),('blobs/sha256/'+sha(cb),cb),('blobs/sha256/'+sha(mb),mb)]:
  x=tarfile.TarInfo(name);x.size=len(b);x.mode=0o644;t.addfile(x,io.BytesIO(b))
print(json.dumps({'image':'sha256:'+sha(mb),'config':'sha256:'+sha(cb),'revision':revision,'delta_bytes':pathlib.Path(a.output).stat().st_size}))
