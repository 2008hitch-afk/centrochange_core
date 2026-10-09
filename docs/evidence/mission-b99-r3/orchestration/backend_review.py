import lab,subprocess,json,os,sys
from unittest.mock import patch
os.umask(0o077);lab.isolation(); sys.path.insert(0,str(lab.SOURCE/'infra'));import remediation_acceptance as review
original=review.MODULES;excluded=['security.audit_view_acceptance','scheduling.reopen_acceptance','finance.expectation_ui_acceptance','finance.bank_trace_acceptance'];review.MODULES=tuple(x for x in original if x not in excluded)
run=subprocess.run
def isolated(argv,*a,**kw):
 argv=[v.replace('centrochange-dev-backend-1',lab.BACKEND).replace('centrochange.local',lab.SITE) if isinstance(v,str) else v for v in argv]
 assert argv[:2]==['docker','exec'] and lab.BACKEND in argv
 if 'input' in kw:kw['input']=kw['input'].replace('centrochange.local',lab.SITE)
 return run(argv,*a,**kw)
# Rebind only host output path to avoid touching any previous mission artifact.
original_main_source=(lab.SOURCE/'infra/remediation_acceptance.py').read_text().replace("Path('/tmp/cc-remediation-backend.log')","Path("+repr(str(lab.ROOT/'backend-review-private.log'))+")")
scope={'__name__':'g2d_review'};exec(compile(original_main_source,'archived-remediation-test','exec'),scope);scope['MODULES']=review.MODULES
with patch('subprocess.run',isolated):scope['main']()
