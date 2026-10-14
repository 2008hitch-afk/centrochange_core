#!/usr/bin/env python3
"""Exact synthetic orphan recovery plan; apply only after a separate Owner approval.

Inspect is read-only. Apply snapshots the three complete rows privately before a
single database transaction. Restore is available from that private snapshot.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile


STATE = Path('/home/empv26/.local/state/centrochange-single')
SITE = 'centrochange.local'
CONFIRMATION = 'nq7fe9a7te'
AUDIT = 'nq7cpubodl'
COMMUNICATION = 'nq7pmkk53k'
APPOINTMENT = 'HLC-APP-2026-00026'
CENTER = 'CC-HTTP-9277857997 A'
CURRENT = '19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10'
RESTORED = '0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a'
NAMES = {'CC Booking Confirmation': CONFIRMATION,
         'CC Audit Event': AUDIT, 'Communication': COMMUNICATION}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_frappe(code):
    result = subprocess.run(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1',
                             '-w', '/home/frappe/frappe-bench/sites',
                             'centrochange-dev-backend-1',
                             '/home/frappe/frappe-bench/env/bin/python'],
                            input=code, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'Frappe probe failed, exit {result.returncode}; private output suppressed')
    line = next((x for x in result.stdout.splitlines() if x.startswith('CC_CLEANUP_JSON=')), None)
    if not line:
        raise RuntimeError('Frappe cleanup result missing')
    return json.loads(line.split('=', 1)[1])


COMMON = '''import hashlib,json,re,frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
assert frappe.conf.get("cc_synthetic_dev")==1 and frappe.conf.get("cc_uat_demo")==1
frappe.set_user("Administrator")
names={"CC Booking Confirmation":"nq7fe9a7te","CC Audit Event":"nq7cpubodl","Communication":"nq7pmkk53k"}
types=["Patient","Healthcare Practitioner","Patient Appointment","Sales Invoice","Purchase Invoice","Payment Entry","Bank Transaction","CC Audit Event","CC Booking Confirmation","CC Fiscal Transaction","CC Professional Comparison"]
def fingerprint(exclude=False):
 rows={dt:frappe.get_all(dt,fields=["name","modified"],order_by="name",limit_page_length=0) for dt in types}
 if exclude:
  for dt in ("CC Booking Confirmation","CC Audit Event"):
   rows[dt]=[r for r in rows[dt] if r.name!=names[dt]]
 return hashlib.sha256(json.dumps(rows,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
def rows():
 return {dt:frappe.db.sql("SELECT * FROM `tab"+dt+"` WHERE name=%s",(name,),as_dict=True) for dt,name in names.items()}
def check_present():
 found=rows()
 assert all(len(found[dt])==1 for dt in names),"exact record missing or duplicated"
 c,a,m=(found[x][0] for x in ("CC Booking Confirmation","CC Audit Event","Communication"))
 assert c.appointment=="HLC-APP-2026-00026" and c.center=="CC-HTTP-9277857997 A"
 assert c.communication==m.name and str(c.recipient).endswith("@example.invalid")
 assert a.event_type=="BOOKING_CONFIRMATION_SIMULATED" and a.reference_doctype=="CC Booking Confirmation" and a.reference_name==c.name
 assert m.reference_doctype=="Patient Appointment" and m.reference_name==c.appointment
 assert str(m.recipients).endswith("@example.invalid") and m.sender=="cc-public-booking-service@example.invalid"
 assert not frappe.db.exists("Patient Appointment",c.appointment) and not frappe.db.exists("Branch",c.center)
 assert frappe.db.count("CC Booking Confirmation",{"appointment":c.appointment})==1
 assert frappe.db.count("Communication",{"reference_doctype":"Patient Appointment","reference_name":c.appointment})==1
 assert frappe.db.count("CC Audit Event",{"reference_doctype":"CC Booking Confirmation","reference_name":c.name})==1
 assert frappe.db.count("CC Audit Event",{"reference_doctype":"Communication","reference_name":m.name})==0
 for dt,field in (("CC Payment Notice","communication"),("Communication","in_reply_to"),("Email Queue","communication")):
  assert frappe.db.count(dt,{field:m.name})==0,(dt,field)
 assert frappe.db.count("CC Booking Confirmation",{"communication":m.name})==1
 for dt,name in names.items():
  for dep,filters in (("File",{"attached_to_doctype":dt,"attached_to_name":name}),
                      ("Comment",{"reference_doctype":dt,"reference_name":name}),
                      ("DocShare",{"share_doctype":dt,"share_name":name}),
                      ("Version",{"ref_doctype":dt,"docname":name})):
   assert frappe.db.count(dep,filters)==0,(dt,dep)
 return found
'''


def inspect():
    code = COMMON + '''
try:
 found=check_present()
 assert fingerprint()=="19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10"
 assert fingerprint(True)=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 print("CC_CLEANUP_JSON="+json.dumps({"status":"INSPECT_PASS","names":names,"current":fingerprint(),"projected":fingerprint(True)}))
finally:frappe.db.rollback();frappe.destroy()
'''
    return run_frappe(code)


def verify_clean():
    code = COMMON + '''
try:
 assert fingerprint()=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 assert all(not frappe.db.exists(dt,name) for dt,name in names.items())
 assert not frappe.db.exists("Patient Appointment","HLC-APP-2026-00026")
 assert frappe.db.count("CC Booking Confirmation",{"appointment":"HLC-APP-2026-00026"})==0
 assert frappe.db.count("Communication",{"reference_doctype":"Patient Appointment","reference_name":"HLC-APP-2026-00026"})==0
 assert frappe.db.count("CC Audit Event",{"reference_doctype":"CC Booking Confirmation","reference_name":"nq7fe9a7te"})==0
 print("CC_CLEANUP_JSON="+json.dumps({"status":"CLEAN_VERIFIED","fingerprint":fingerprint()}))
finally:frappe.db.rollback();frappe.destroy()
'''
    return run_frappe(code)


def private_snapshot():
    code = COMMON + '''
try:
 found=check_present()
 assert fingerprint()=="19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10"
 assert fingerprint(True)=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 print("CC_CLEANUP_JSON="+json.dumps({"rows":found,"before":fingerprint(),"after":fingerprint(True)},default=str))
finally:frappe.db.rollback();frappe.destroy()
'''
    data = run_frappe(code)
    directory = STATE / 'goal02-cleanup'
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise RuntimeError('private snapshot directory unsafe')
    fd, path = tempfile.mkstemp(prefix='exact-orphans-', suffix='.json', dir=directory)
    try:
        os.fchmod(fd, 0o600)
        payload = (json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()
        with os.fdopen(fd,'wb') as handle:
            handle.write(payload)
            handle.flush();os.fsync(handle.fileno())
        return Path(path), digest(payload)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise


def apply(snapshot, checksum):
    payload = snapshot.read_bytes()
    if snapshot.is_symlink() or snapshot.stat().st_mode & 0o077 or digest(payload) != checksum:
        raise RuntimeError('private snapshot integrity mismatch')
    data = json.loads(payload)
    if data['before'] != CURRENT or data['after'] != RESTORED or set(data['rows']) != set(NAMES):
        raise RuntimeError('snapshot scope mismatch')
    code = COMMON + '''
try:
 found=check_present()
 assert fingerprint()=="19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10"
 assert fingerprint(True)=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 assert json.dumps(found,sort_keys=True,default=str)=='''+repr(json.dumps(data['rows'],sort_keys=True))+'''
 for dt in ("CC Audit Event","Communication","CC Booking Confirmation"):
  frappe.db.delete(dt,{"name":names[dt]})
 assert all(not frappe.db.exists(dt,name) for dt,name in names.items())
 assert fingerprint()=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 frappe.db.commit()
 print("CC_CLEANUP_JSON="+json.dumps({"status":"CLEANUP_PASS","fingerprint":fingerprint()}))
except:frappe.db.rollback();raise
finally:frappe.destroy()
'''
    return run_frappe(code)


def restore(snapshot, checksum):
    payload = snapshot.read_bytes()
    if snapshot.is_symlink() or snapshot.stat().st_mode & 0o077 or digest(payload) != checksum:
        raise RuntimeError('private snapshot integrity mismatch')
    data = json.loads(payload)
    if data['before'] != CURRENT or data['after'] != RESTORED or set(data['rows']) != set(NAMES):
        raise RuntimeError('snapshot scope mismatch')
    code = COMMON + '''
try:
 assert fingerprint()=="0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a"
 assert all(not frappe.db.exists(dt,name) for dt,name in names.items())
 saved=json.loads('''+repr(json.dumps(data['rows']))+''')
 for dt in ("Communication","CC Booking Confirmation","CC Audit Event"):
  row=saved[dt][0]
  assert row["name"]==names[dt]
  columns=list(row)
  assert all(re.fullmatch(r"[A-Za-z0-9_]+",field) for field in columns)
  sql="INSERT INTO `tab"+dt+"` ("+",".join("`"+field+"`" for field in columns)+") VALUES ("+",".join(["%s"]*len(columns))+")"
  frappe.db.sql(sql,tuple(row.values()))
 assert fingerprint()=="19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10"
 frappe.db.commit()
 print("CC_CLEANUP_JSON="+json.dumps({"status":"RESTORE_PASS","fingerprint":fingerprint()}))
except:frappe.db.rollback();raise
finally:frappe.destroy()
'''
    return run_frappe(code)


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--inspect', action='store_true')
    modes.add_argument('--verify-clean', action='store_true')
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--restore', type=Path)
    parser.add_argument('--snapshot-sha256')
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(),sort_keys=True))
        return
    if args.verify_clean:
        print(json.dumps(verify_clean(),sort_keys=True))
        return
    if os.geteuid() != 0 or socket.gethostname() != 'srv2033673':
        raise RuntimeError('requires authorized sudo on srv2033673')
    if args.apply:
        snapshot, checksum = private_snapshot()
        result = apply(snapshot, checksum)
        print(json.dumps({**result,'private_snapshot':str(snapshot),'snapshot_sha256':checksum},sort_keys=True))
    else:
        if not args.snapshot_sha256 or not str(args.restore).startswith(str(STATE / 'goal02-cleanup') + '/'):
            raise RuntimeError('exact private snapshot and SHA-256 required')
        print(json.dumps(restore(args.restore,args.snapshot_sha256),sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__}))
        sys.exit(1)
