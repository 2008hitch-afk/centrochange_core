"""Append a deterministic COPY-only delta to the R5 scratch OCI archive.

Never edits a container or an original image/archive. The old OCI index remains
valid until new content-addressed blobs are complete; replace only that index.
"""
import pathlib,json,tarfile,io,gzip,hashlib
out=pathlib.Path('/output');root=pathlib.Path('/product');archive=out/'r5-target.oci.tar';revision=(out/'revision').read_text().strip();files=json.loads((out/'patch-files.json').read_text())
def serial(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def add(t,name,b):
 x=tarfile.TarInfo(name);x.size=len(b);x.mtime=0;x.mode=0o644;t.addfile(x,io.BytesIO(b))
with tarfile.open(archive,'r:') as t:
 entry=t.getmember('index.json');offset=entry.offset_data;capacity=entry.size;index=json.load(t.extractfile(entry));desc=index['manifests'][0];manifest=json.load(t.extractfile('blobs/sha256/'+desc['digest'].split(':')[1]));config=json.load(t.extractfile('blobs/sha256/'+manifest['config']['digest'].split(':')[1]))
raw=io.BytesIO()
with tarfile.open(fileobj=raw,mode='w') as t:
 for name in sorted(files):
  assert name.startswith('app/centrochange_core/');b=(root/name).read_bytes();x=tarfile.TarInfo('home/frappe/frappe-bench/apps/centrochange_core/'+name.removeprefix('app/centrochange_core/'));x.uid=x.gid=1000;x.uname=x.gname='frappe';x.mode=0o644;x.mtime=0;x.size=len(b);t.addfile(x,io.BytesIO(b))
raw=raw.getvalue();layer=gzip.compress(raw,mtime=0);config['rootfs']['diff_ids'].append('sha256:'+sha(raw));config['history'].append({'created_by':'versioned COPY-only R5 delta '+revision,'created':'2026-10-09T00:00:00Z'});config['config']['Labels']['org.opencontainers.image.revision']=revision;c=serial(config);manifest['config'].update(digest='sha256:'+sha(c),size=len(c));manifest['layers'].append({'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':'sha256:'+sha(layer),'size':len(layer)});m=serial(manifest);desc.update(digest='sha256:'+sha(m),size=len(m));desc['annotations']['org.opencontainers.image.ref.name']='centrochange-b99-r5:compat-'+revision[:12];i=serial(index);assert len(i)<=capacity
with tarfile.open(archive,'a:') as t:
 add(t,'blobs/sha256/'+sha(c),c);add(t,'blobs/sha256/'+sha(layer),layer);add(t,'blobs/sha256/'+sha(m),m)
with archive.open('r+b') as f:f.seek(offset);f.write(i+b' '*(capacity-len(i)));f.flush()
(out/'image-proof.json').write_text(json.dumps({'manifest':'sha256:'+sha(m),'config':'sha256:'+sha(c),'layer':'sha256:'+sha(layer),'diff_id':'sha256:'+sha(raw),'product_revision':revision,'files':files,'method':'versioned OCI COPY-only layers; no compilation or upstream modification','archive_bytes':archive.stat().st_size},indent=2));print('VERSIONED OCI DELTA COMPLETE')
