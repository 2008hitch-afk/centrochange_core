#!/usr/bin/env python3
"""One exact synthetic attachment lifecycle on the installed DEV, with recovery.

The browser creates a new, uniquely tagged *unposted* incoming document. Only
its own source, two private Files and their two audit events may be removed.
No native accounting voucher, ledger entry or Owner document is touched.
"""
import importlib.util
import json
import os
from pathlib import Path
import pwd
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('gate', ROOT / 'infra/issue139_install_gate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
IMAGE = 'sha256:47d753955c81033b11317381b5fdc63aa5e438cec304e57e93a0b6c0215b6758'
RUN = Path('/home/empv26/.local/state/centrochange-single/browser-evidence/mvp-devfirst-3429f7d-targeted')


def probe(module, tag):
    code = '''import json,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
tag=TAG
sources=frappe.get_all("CC Incoming Invoice",filters={"invoice_number":tag},fields=["name","center","payload_file","purchase_invoice"])
rows=[]
for source in sources:
 rows.append({"name":source.name,"center":source.center,"purchase_invoice":source.purchase_invoice,
  "files":frappe.get_all("File",filters={"attached_to_doctype":"CC Incoming Invoice","attached_to_name":source.name},
   fields=["name","file_name","file_url","is_private"]),
  "audit":frappe.get_all("CC Audit Event",filters={"reference_doctype":"CC Incoming Invoice","reference_name":source.name},
   fields=["name","event_type","reason"])})
print("CC_ATTACHMENT_PROBE="+json.dumps({"sources":rows,"counts":{dt:frappe.db.count(dt) for dt in ("CC Incoming Invoice","File","CC Audit Event","Purchase Invoice","GL Entry")}}))
frappe.db.rollback();frappe.destroy()
'''.replace('TAG', json.dumps(tag))
    result = module.backend_python(code)
    return json.loads(next(line.split('=', 1)[1] for line in result.splitlines()
                           if line.startswith('CC_ATTACHMENT_PROBE=')))


def cleanup(module, tag, center):
    code = '''import json,pathlib,frappe
from centrochange_core.security.audit import internal_write
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
tag=TAG;center=CENTER
sources=frappe.get_all("CC Incoming Invoice",filters={"invoice_number":tag},fields=["name","center","payload_file","purchase_invoice"])
assert len(sources)<=1 and all(s.center==center and not s.purchase_invoice for s in sources)
if not sources:
 print("CC_ATTACHMENT_CLEANUP="+json.dumps({"status":"NO_FIXTURE"}))
else:
 source=sources[0]
 assert not frappe.db.exists("Purchase Invoice",{"cc_incoming_source":source.name})
 files=frappe.get_all("File",filters={"attached_to_doctype":"CC Incoming Invoice","attached_to_name":source.name},
   fields=["name","file_name","file_url","is_private"])
 assert 1<=len(files)<=2 and source.payload_file in [f.name for f in files]
 assert all(f.is_private and f.file_url.startswith("/private/files/") and
   (f.name==source.payload_file and f.file_name.startswith("CC-INCOMING-") or
    f.file_name.startswith(tag) and f.file_name.endswith(".pdf")) and
   frappe.db.count("File",{"file_url":f.file_url})==1 for f in files)
 events=frappe.get_all("CC Audit Event",filters={"reference_doctype":"CC Incoming Invoice","reference_name":source.name},
   fields=["name","event_type","reason"])
 assert 1<=len(events)<=2 and all(e.reason==tag and e.event_type in
   ("INCOMING_XML_RETAINED","FINANCIAL_DOCUMENT_ATTACHED") for e in events)
 paths=[pathlib.Path(frappe.get_doc("File",f.name).get_full_path()) for f in files]
 with internal_write("cc_fixture_file_cleanup"):
  frappe.db.set_value("CC Incoming Invoice",source.name,"payload_file",None)
  for f in files:frappe.delete_doc("File",f.name,ignore_permissions=True)
 for dt in ("Comment","Version"):
  fields={"Comment":("reference_doctype","reference_name"),"Version":("ref_doctype","docname")}[dt]
  frappe.db.delete(dt,{fields[0]:"CC Incoming Invoice",fields[1]:source.name})
 frappe.db.delete("CC Audit Event",{"name":["in",[e.name for e in events]]})
 frappe.db.delete("CC Incoming Invoice",{"name":source.name})
 frappe.db.commit()
 assert not frappe.db.exists("CC Incoming Invoice",source.name)
 assert not any(frappe.db.exists("File",f.name) for f in files)
 assert not any(frappe.db.exists("CC Audit Event",e.name) for e in events)
 assert not any(p.exists() for p in paths)
 print("CC_ATTACHMENT_CLEANUP="+json.dumps({"status":"PASS","files":len(files),"audit":len(events)}))
frappe.db.rollback();frappe.destroy()
'''.replace('TAG', json.dumps(tag)).replace('CENTER', json.dumps(center))
    result = module.backend_python(code)
    return json.loads(next(line.split('=', 1)[1] for line in result.splitlines()
                           if line.startswith('CC_ATTACHMENT_CLEANUP=')))


def main():
    assert os.geteuid() == 0 and sys.flags.isolated
    fixture = json.loads((g.STATE / 'demo-owner.json').read_text())
    center = fixture['centers'][0]
    module = g.old_probe()
    services = module.snapshot()
    assert len(services) == 9 and all(services[name]['image'] == IMAGE for name in g.APP)
    assert module.hooks() == module.GUARDS
    before = module.runtime_fingerprint()
    permissions = g.permission_fingerprint(module)
    tag = 'CC-MVP-ATT-' + secrets.token_hex(5)
    pre_probe = probe(module, tag)
    assert not pre_probe['sources']
    directory = RUN / ('attachment-' + tag)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    account = pwd.getpwnam('empv26')
    os.chown(directory, account.pw_uid, account.pw_gid)
    g.private_write(directory / 'marker.json', json.dumps({'tag':tag,'center':center,'status':'STARTED'}).encode())
    browser_result = None
    cleanup_result = None
    failure = None
    try:
        environment = ['PATH=/usr/sbin:/usr/bin:/sbin:/bin','HOME=/home/empv26',
            'NODE_PATH=/tmp/cc-browser-qa/node_modules',
            'LD_LIBRARY_PATH=/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu',
            'CC_BASE_URL=http://centrochange.local:8082',
            f'CC_ISSUE137_FIXTURE={g.STATE / "demo-owner.json"}',
            f'CC_ISSUE137_OUTPUT={directory}',f'CC_MVP_ATTACHMENT_TAG={tag}']
        result = subprocess.run(['runuser','-u','empv26','--','/usr/bin/env',*environment,
            'node',str(ROOT / 'infra/browser/mvp_devfirst_attachment_live.cjs')],
            cwd=ROOT,capture_output=True,text=True,timeout=120)
        g.private_write(directory / 'browser.log',(result.stdout+'\n'+result.stderr).encode())
        browser_result = json.loads((directory / 'attachment-live.json').read_text()) if (directory / 'attachment-live.json').exists() else None
        if result.returncode or not browser_result or not all(x['pass'] for x in browser_result['checks']):
            failure='browser_acceptance_failed'
    except (OSError,subprocess.TimeoutExpired,ValueError) as error:
        failure=type(error).__name__
    finally:
        # Recovery is required even when the browser fails halfway through.
        try:
            cleanup_result = cleanup(module, tag, center)
        except Exception as error:
            cleanup_result = {'status':'FAIL','error_type':type(error).__name__}
            failure = failure or 'exact_cleanup_failed'
    after_probe = probe(module, tag)
    after = module.runtime_fingerprint()
    unchanged = (after == before and g.permission_fingerprint(module) == permissions and
                 module.hooks() == module.GUARDS and module.snapshot() == services and
                 after_probe == pre_probe)
    status = 'PASS' if not failure and cleanup_result['status']=='PASS' and unchanged else 'FAIL'
    report = {'status':status,'browser':browser_result,'failure':failure,'cleanup':cleanup_result,
              'baseline_restored':unchanged,'candidate_image':IMAGE}
    g.private_write(directory / 'report.json', json.dumps(report,indent=2).encode())
    print(json.dumps({'status':status,'checks':len(browser_result['checks']) if browser_result else 0,
                      'cleanup':cleanup_result['status'],'baseline_restored':unchanged,'evidence':str(directory)}))
    return 0 if status=='PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
