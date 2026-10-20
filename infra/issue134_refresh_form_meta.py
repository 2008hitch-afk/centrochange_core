#!/usr/bin/env python3
"""Refresh only stale #134 Frappe FormMeta client-cache entries on the pinned DEV.

This is a cache repair after the authorized image update, not an application
deployment. Run as root for Docker access; it does not write Site data.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e"
DATA = "82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd"
APPS = ("backend", "frontend", "websocket", "queue-short", "queue-long", "scheduler")
DIFFS = {
    "Item": ["__list_js"],
    "Item Price": ["__list_js"],
    "Appointment Type": ["__list_js"],
    "Sales Invoice": ["__js", "__list_js"],
    "Purchase Invoice": ["__js", "__list_js"],
    "Payment Entry": ["__js", "__list_js"],
    "Bank Transaction": ["__js", "__list_js"],
}
UNCHANGED = ("Patient", "Healthcare Practitioner", "CC Center Service", "CC Package Template")


def command(args, *, input_text=None):
    result = subprocess.run(args, input=input_text, text=True, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed; private diagnostics retained in process output")
    return result.stdout.strip()


def fingerprint():
    spec = importlib.util.spec_from_file_location("goal02_probe", ROOT / "infra/goal02_install_one_command.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.runtime_fingerprint()["sha256"]


PROBE = r'''
import frappe,json
from frappe.desk.form.meta import FormMeta,get_meta
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
expected=json.loads(EXPECTED)
unchanged=json.loads(UNCHANGED)
keys=("__js","__list_js")
stale=[]
for doctype in tuple(expected)+tuple(unchanged):
    cached=frappe.client_cache.get_value("doctype_form_meta::"+doctype)
    fresh=FormMeta(doctype,cached=False)
    actual=[key for key in keys if cached and cached.get(key)!=fresh.get(key)]
    if doctype in expected:
        assert not cached or actual in ([],expected[doctype]), "unexpected cached metadata delta: "+doctype
    else:
        assert not actual, "unrelated metadata changed: "+doctype
    if actual: stale.append(doctype)
if APPLY:
    for doctype in stale:
        frappe.client_cache.delete_value("doctype_form_meta::"+doctype)
    for doctype in stale:
        served=get_meta(doctype)
        fresh=FormMeta(doctype,cached=False)
        assert all(served.get(key)==fresh.get(key) for key in keys), "metadata refresh failed: "+doctype
frappe.db.rollback()
frappe.destroy()
print(json.dumps({"status":"PASS","stale_doctypes":stale,"cache_mutations":len(stale) if APPLY else 0}))
'''


def probe(apply):
    source = PROBE.replace("EXPECTED", repr(json.dumps(DIFFS))).replace("UNCHANGED", repr(json.dumps(UNCHANGED)))
    source = source.replace("APPLY", "True" if apply else "False")
    output = command(["docker", "exec", "-i", "-w", "/home/frappe/frappe-bench/sites",
                      "centrochange-dev-backend-1", "/home/frappe/frappe-bench/env/bin/python", "-I", "-"],
                     input_text=source)
    return json.loads(output.splitlines()[-1])


def main():
    if os.geteuid() != 0 or sys.argv[1:] not in (["--dry-run"], ["--apply"]):
        raise RuntimeError("exact mode with Docker privileges required")
    apply = sys.argv[1] == "--apply"
    names = command(["docker", "ps", "--filter", "label=com.docker.compose.project=centrochange-dev",
                     "--format", "{{.Names}}"]).splitlines()
    if len(names) != 9 or set(names) != {f"centrochange-dev-{name}-1" for name in APPS} | {
        "centrochange-dev-db-1", "centrochange-dev-redis-cache-1", "centrochange-dev-redis-queue-1"}:
        raise RuntimeError("DEV service inventory mismatch")
    for service in APPS:
        observed = command(["docker", "inspect", "--format", "{{.Image}}", f"centrochange-dev-{service}-1"])
        if observed != IMAGE:
            raise RuntimeError("candidate image mismatch")
    before = fingerprint()
    if before != DATA:
        raise RuntimeError("Owner data fingerprint drift before cache repair")
    dry = probe(False)
    if not apply:
        print(json.dumps({"status":"DRY_RUN_PASS","image":IMAGE,"data_sha256":before,
                          "stale_doctypes":dry["stale_doctypes"]}))
        return
    result = probe(True)
    after = fingerprint()
    if after != before:
        raise RuntimeError("Owner data fingerprint changed during cache repair")
    if set(result["stale_doctypes"]) != set(dry["stale_doctypes"]):
        raise RuntimeError("cache changed between verification and repair")
    print(json.dumps({"status":"PASS","image":IMAGE,"data_sha256":after,
                      "stale_doctypes":result["stale_doctypes"],"keys_cleared":result["cache_mutations"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status":"STOP","reason":str(error)[:160]}))
        raise SystemExit(1)
