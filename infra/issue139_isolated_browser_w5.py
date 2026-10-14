#!/usr/bin/env python3
"""Read-only W5 against loopback 127.0.0.2 clone, never shared DEV."""
import json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=pathlib.Path('/home/empv26/.local/state/centrochange-single')
OUT=STATE/'issue139-isolated-w5-browser'/('w5-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+f'-{os.getpid()}')
FIXTURE=STATE/'demo-owner.json'
assert os.geteuid()!=0 and FIXTURE.is_file()
OUT.mkdir(mode=0o700,parents=True,exist_ok=False)
print('EVIDENCE_DIR='+str(OUT),flush=True)
base=os.environ.copy()
base.update(NODE_PATH='/tmp/cc-browser-qa/node_modules',
            LD_LIBRARY_PATH='/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
            CC_ISSUE139_BROWSER_IP='127.0.0.2',CC_BASE_URL='http://centrochange.local:8082',
            CC_ISSUE137_FIXTURE=str(FIXTURE))
results=[]
for role in 'msabcft':
    for width in (1440,390):
        folder=OUT/f'sweep-{role}-{width}';folder.mkdir(mode=0o700)
        env=base|{'CC_ISSUE137_ROLE':role,'CC_ISSUE137_WIDTH':str(width),'CC_ISSUE137_OUTPUT':str(folder)}
        p=subprocess.run(['node',str(ROOT/'infra/browser/issue137_owner_uat_sweep.cjs')],env=env,cwd=ROOT,capture_output=True,text=True)
        (folder/'runner.log').write_text(p.stderr[-5000:])
        report=folder/f'issue137-{role}-{width}.json'
        data=json.loads(report.read_text()) if report.is_file() else {}
        row={'role':role,'width':width,'exit':p.returncode,'routes':data.get('uniqueRoutes',0),
             'pass':data.get('summary',{}).get('pass',0),'fail':data.get('summary',{}).get('fail',0),
             'mutations':len(data.get('unexpectedMutations',[]))}
        results.append(row);print(json.dumps(row),flush=True)
for width in (1440,390):
    folder=OUT/f'native-{width}';folder.mkdir(mode=0o700)
    env=base|{'CC_ISSUE137_WIDTH':str(width),'CC_ISSUE137_OUTPUT':str(folder)}
    p=subprocess.run(['node',str(ROOT/'infra/browser/issue139_native_renderer.cjs')],env=env,cwd=ROOT,capture_output=True,text=True)
    (folder/'runner.log').write_text(p.stderr[-5000:])
    report=folder/f'issue139-native-{width}.json'
    data=json.loads(report.read_text()) if report.is_file() else {}
    row={'native_width':width,'exit':p.returncode,'pairs':len(data.get('results',[])),
         'pass':data.get('summary',{}).get('pass',0),'fail':data.get('summary',{}).get('fail',0)}
    results.append(row);print(json.dumps(row),flush=True)
(OUT/'summary.json').write_text(json.dumps(results,indent=2))
print('TOTAL_ROUTES='+str(sum(x.get('routes',0) for x in results)),flush=True)
sys.exit(0 if sum(x.get('routes',0) for x in results)>=128 and all(x['exit']==0 and x['fail']==0 and x.get('mutations',0)==0 for x in results) else 2)
