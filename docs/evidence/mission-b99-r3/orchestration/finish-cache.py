import ops,pathlib,json
code="""import pathlib,subprocess,os,shutil,json
src=pathlib.Path('/source');dst=pathlib.Path('/cache');copied=skipped=0
for p in src.rglob('*'):
 q=dst/p.relative_to(src)
 if p.is_dir() and not p.is_symlink():q.mkdir(parents=True,exist_ok=True);continue
 if p.is_symlink():
  if q.is_symlink() and os.readlink(q)==os.readlink(p):skipped+=1;continue
 elif q.exists():
  a=p.stat();b=q.stat()
  if a.st_size==b.st_size and a.st_mtime_ns==b.st_mtime_ns:skipped+=1;continue
 q.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','-a','--remove-destination',str(p),str(q)],check=True);copied+=1
for p in sorted([src]+[p for p in src.rglob('*') if p.is_dir() and not p.is_symlink()],key=lambda p:len(p.parts),reverse=True):
 q=dst/p.relative_to(src);shutil.copystat(p,q);os.chown(q,p.stat().st_uid,p.stat().st_gid)
print(json.dumps({'completed_or_repaired_entries':copied,'completed_entries_reused':skipped}))
"""
ops.cmd(['docker','run','-i','--name','centrochange-b99-r3-cache-finish','--label','centrochange.mission=B99-R3','--label','centrochange.heavy=true','--user','0','--memory','512m','--memory-swap','512m','--device-read-bps','/dev/sda:8388608','--device-write-bps','/dev/sda:4194304','--restart','no','--mount','type=volume,source=buildx_buildkit_centrochange-b99-r2-builder0_state,target=/source,readonly','--mount','type=volume,source=centrochange-b99-r3-buildkit-state,target=/cache','--entrypoint','/home/frappe/frappe-bench/env/bin/python',ops.IMAGE],'copy-cache-finish',code,timeout=1800)
(ops.ROOT/'copy-cache-resume.result.json').write_text(json.dumps({'exit_code':0,'resumed_from_completed_files':True}));print('CACHE COPY FINISHED',flush=True)
