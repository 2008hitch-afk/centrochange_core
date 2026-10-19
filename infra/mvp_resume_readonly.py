#!/usr/bin/env python3
"""Resume acceptance only on the exact installed DEV; never deploy or restore."""
import argparse,importlib.util,json,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('issue139_install_gate.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
 assert os.geteuid()==0
 root=(g.RUN_ROOT/a.run).resolve();assert root.parent==g.RUN_ROOT.resolve()
 report=json.loads((root/'report.json').read_text());checkpoint=json.loads((root/'checkpoint.json').read_text())
 assert report['candidate']==g.SOURCE and report['status']=='BLOCKED' and not report.get('failure')
 assert 'candidate_backend_started; schema_and_centers_preserved' in report['runtime_mutations']
 m=g.old_probe()
 def invariants():
  snap=json.loads(json.dumps(m.snapshot()));assert all(snap[n]['image']==report['candidate_image'] for n in g.APP)
  assert all(snap[n]==checkpoint['services'][n] for n in g.TECH)
  assert m.runtime_fingerprint()==checkpoint['data']
  assert g.permission_fingerprint(m)==checkpoint['permissions']
  assert g.schema_fingerprint(m)==checkpoint['schema']
  assert m.hooks()==m.GUARDS
  assert g.ENV.read_bytes()==(root/'runtime.env.checkpoint').read_bytes()
  assert g.ACTIVE_OVERLAY.read_bytes()==g.OVERLAY.read_bytes()
  m.http_ready()
 invariants()
 evidence=g.STATE/'browser-evidence'/('issue139-'+a.run)/'readonly-resumed'
 g.browser('mvp_devfirst_readonly.cjs',evidence)
 result=json.loads((evidence/'devfirst-readonly.json').read_text())
 assert result['status']=='ESSENTIAL_PASS'
 invariants()
 report['tests']['essential_readonly']=result
 report['tests']['financial_acceptance']={'status':'BLOCKED','reason':'Accounting cleanup concurrency/retention unverified; no writes attempted'}
 report['tests']['security_38_mutative']={'status':'BLOCKED','reason':'Shared fixture cleanup not verified; essential denial checks executed read-only'}
 report['installation_essential_status']='PASS'
 report['status']='DEV_UPDATED_WITH_GAPS'
 report['after_data']=checkpoint['data']
 report['evidence_directory']=str(evidence)
 report['acceptance_resume']={'reason':'Runner used absent btn-login selector; corrected to existing Continua button. Original executor stopped during read-only acceptance, no fixture mutation or rollback.', 'runner_sha256':g.file_sha(g.REPO/'infra/browser/mvp_devfirst_readonly.cjs'),'resume_sha256':g.file_sha(__file__)}
 g.report_write(root/'report.json',report)
 print(json.dumps({'status':report['status'],'critical':len(result['critical']),'functional':result['functional']}))
if __name__=='__main__':main()
