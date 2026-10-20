#!/usr/bin/env python3
"""Refresh only the 11 native Form JS client-cache entries after #75 update.

The script verifies the exact installed image and source, synthetic data,
permissions and hooks before and after. It writes only bounded Redis client
cache keys; no Site database row, service or application file is changed.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('issue75_gate_for_meta', ROOT/'infra/issue75_native_ux_install.py')
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)
gate = wrapper.gate
IMAGE = 'sha256:17380aa9aed4ee287d8c46ed1d851fe94ef42aa6586f3b9f379e0b8aff3f3602'
DOCTYPES = ('Patient','Healthcare Practitioner','Sales Invoice','Item','Item Price',
            'Appointment Type','CC Center Service','CC Package Template',
            'Purchase Invoice','Payment Entry','Bank Transaction')

CODE = r'''
import frappe,json,sys
from frappe.desk.form.meta import get_meta
names=json.loads(sys.argv[1]); execute=sys.argv[2]=='execute'
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
try:
    rows=[]
    for dt in names:
        fresh=get_meta(dt,cached=False).get('__js') or ''
        cached=get_meta(dt,cached=True).get('__js') or ''
        if 'Come compilare' not in fresh:
            raise RuntimeError(dt+': pinned native Form source marker absent')
        stale='Come compilare' not in cached
        if execute and stale:
            frappe.client_cache.delete_value('doctype_form_meta::'+dt)
            cached=get_meta(dt,cached=True).get('__js') or ''
            if 'Come compilare' not in cached:
                raise RuntimeError(dt+': bounded client-cache refresh failed')
        rows.append({'doctype':dt,'stale_before':stale,'fresh_after':('Come compilare' in cached)})
    print('CC_NATIVE_META='+json.dumps(rows))
finally:
    frappe.db.rollback();frappe.destroy()
'''

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def probe():
    module = gate.old_probe()
    services = module.snapshot()
    require(len(services)==9 and all(services[name]['image']==IMAGE for name in gate.APP),
            'installed application image or service count drift')
    require(module.hooks()==module.GUARDS,'security/language hooks drift')
    return module,services,module.runtime_fingerprint(),gate.permission_fingerprint(module)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    require(os.geteuid()==0 and socket.gethostname()=='srv2033673',
            'approved host and sudo required')
    image=json.loads(subprocess.check_output(['docker','image','inspect',IMAGE]))[0]
    require(image['Config']['Labels'].get('centrochange.source')==gate.SOURCE,
            'installed source label drift')
    module,before,data,permissions=probe()
    command=['docker','exec','-i','-u','frappe','-e','FRAPPE_STREAM_LOGGING=1',
             '-w','/home/frappe/frappe-bench/sites','centrochange-dev-backend-1',
             '/home/frappe/frappe-bench/env/bin/python','-I','-',json.dumps(DOCTYPES),
             'execute' if args.execute else 'dry-run']
    result=subprocess.run(command,input=CODE,text=True,capture_output=True)
    if result.returncode:
        log=gate.STATE/'issue75-native-meta-error.log'
        fd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as stream: stream.write(result.stderr)
    require(result.returncode==0,'bounded native Form metadata refresh failed; private stderr retained')
    marker=next((line.partition('=')[2] for line in result.stdout.splitlines()
                 if line.startswith('CC_NATIVE_META=')),None)
    require(marker is not None,'native Form metadata proof missing')
    rows=json.loads(marker)
    require(len(rows)==len(DOCTYPES) and [row['doctype'] for row in rows]==list(DOCTYPES),
            'native Form metadata inventory drift')
    if args.execute: require(all(row['fresh_after'] for row in rows),'stale Form metadata remains')
    _,after,after_data,after_permissions=probe()
    require(after==before and after_data==data and after_permissions==permissions,
            'services, synthetic data or permissions changed during metadata refresh')
    print(json.dumps({'status':'PASS','mode':'execute' if args.execute else 'dry-run',
                      'refreshed':sum(row['stale_before'] for row in rows) if args.execute else 0,
                      'stale_before':sum(row['stale_before'] for row in rows),
                      'services':len(after),'data_sha256':data['sha256']}))

if __name__=='__main__':
    main()
