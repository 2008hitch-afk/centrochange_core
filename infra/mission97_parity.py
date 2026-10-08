#!/usr/bin/env python3
"""Exact committed app bytes plus all isolated application image identities."""
import argparse,hashlib,json,subprocess
from mission97_lab import ROOT,PROJECT,isolation

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-ref',required=True);a=p.parse_args();isolation()
 prefix='app/centrochange_core/'
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',a.source_ref,'--',prefix],cwd=ROOT,text=True).splitlines()
 expected={path[len(prefix):]:hashlib.sha256(subprocess.check_output(['git','show',a.source_ref+':'+path],cwd=ROOT)).hexdigest() for path in paths}
 code="import hashlib,json,pathlib,sys; root=pathlib.Path('/home/frappe/frappe-bench/apps/centrochange_core');print(json.dumps({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in json.load(sys.stdin)}))"
 actual=json.loads(subprocess.check_output(['docker','exec','-i',PROJECT+'-backend-1','env/bin/python','-c',code],input=json.dumps(list(expected)),text=True));assert actual==expected
 names=[PROJECT+'-'+s+'-1' for s in ['backend','frontend','websocket','scheduler','queue-short','queue-long']]
 items=json.loads(subprocess.check_output(['docker','inspect']+names,text=True));images={c['Image'] for c in items};assert len(images)==1 and all(c['State']['Running'] for c in items)
 print(json.dumps({'status':'PASS','source_commit':subprocess.check_output(['git','rev-parse',a.source_ref],cwd=ROOT,text=True).strip(),'tracked_app_files':len(expected),'app_manifest_sha256':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest(),'image_id':next(iter(images)),'application_services':len(items),'source_overlays':False}))
if __name__=='__main__':main()
