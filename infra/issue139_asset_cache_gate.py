#!/usr/bin/env python3
"""Check Frappe's bench asset cache; invalidate it only after an Owner gate.

The default mode is read-only. ``--invalidate`` changes one Redis cache key,
``assets_json``. It never builds assets, writes Site data or restarts a service.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

SITE = "centrochange.local"
BACKEND = "centrochange-dev-backend-1"
EXPECTED_IMAGE = "sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af"
BUNDLES = ("desk.bundle.css", "erpnext.bundle.css", "report.bundle.css")
KNOWN_STALE = {
    "desk.bundle.css": "/assets/frappe/dist/css/desk.bundle.7IQ4MBII.css",
    "erpnext.bundle.css": "/assets/erpnext/dist/css/erpnext.bundle.2XFOQZJL.css",
    "report.bundle.css": "/assets/frappe/dist/css/report.bundle.UX3MMGCD.css",
}
STALE_CSS_BUNDLES = {
    "erpnext-web.bundle.css", "erpnext.bundle.css", "erpnext_email.bundle.css",
    "desk.bundle.css", "email.bundle.css", "leaflet.bundle.css", "login.bundle.css",
    "print.bundle.css", "print_format.bundle.css", "report.bundle.css",
    "web_form.bundle.css", "website.bundle.css",
}
KNOWN_MISMATCH_KEYS = STALE_CSS_BUNDLES | {"rtl_" + key for key in STALE_CSS_BUNDLES}

PROBE = r'''
import json, pathlib, frappe
frappe.init(site="centrochange.local", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
keys=("desk.bundle.css", "erpnext.bundle.css", "report.bundle.css")
manifest=json.loads(pathlib.Path("assets/assets.json").read_text())
rtl=pathlib.Path("assets/assets-rtl.json")
if rtl.is_file():
    manifest.update(json.loads(rtl.read_text()))
cached=frappe.cache.get_value("assets_json", shared=True)
before={k:(cached or {}).get(k) for k in keys}
expected={k:manifest.get(k) for k in keys}
existing={k:bool(expected[k] and pathlib.Path(expected[k].lstrip("/")).is_file()) for k in keys}
all_files_present=all(pathlib.Path(v.lstrip("/")).is_file() for v in manifest.values())
if not all(existing.values()) or not all_files_present or any(not v for v in expected.values()):
    raise RuntimeError("Manifest asset missing on disk")
diff_before=sorted(k for k in set(manifest)|(set(cached or {})) if manifest.get(k)!=(cached or {}).get(k))
if INVAL:
    if before == expected:
        raise RuntimeError("Cache already matches; no invalidation needed")
    frappe.cache.delete_value("assets_json", shared=True)
    frappe.client_cache.clear_cache()
after=frappe.utils.get_assets_json()
diff_after=sorted(k for k in set(manifest)|set(after) if manifest.get(k)!=after.get(k))
print("CC_ASSET_GATE="+json.dumps({"manifest":expected,"cache_before":before,"cache_after":{k:after.get(k) for k in keys},"files_present":existing,"all_files_present":all_files_present,"manifest_count":len(manifest),"mismatch_keys_before":diff_before,"mismatch_keys_after":diff_after},sort_keys=True))
frappe.db.rollback()
frappe.destroy()
'''


def command(args: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed with exit {result.returncode}; output kept private")
    return result.stdout


def image_and_scope(expected_image: str) -> None:
    image = command(["docker", "inspect", "--format", "{{.Image}}", BACKEND]).strip()
    if image != expected_image:
        raise RuntimeError("Backend image changed; re-evaluate this gate")
    names = command(["docker", "ps", "--filter", "label=com.docker.compose.project=centrochange-dev", "--format", "{{.Names}}"]).splitlines()
    if len(names) != 9 or BACKEND not in names:
        raise RuntimeError("Single-stack service inventory changed")


def check_served_assets(manifest: dict) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for key in BUNDLES:
        path = manifest[key]
        if not path.startswith("/assets/") or not path.endswith(".css"):
            raise RuntimeError(f"Unexpected asset path for {key}")
        request = urllib.request.Request("http://127.0.0.1:8082" + path,
                                         headers={"Host": SITE}, method="HEAD")
        try:
            with opener.open(request, timeout=8) as response:
                if response.status != 200 or "text/css" not in response.headers.get("Content-Type", ""):
                    raise RuntimeError(f"Asset response invalid for {key}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Asset HTTP {exc.code} for {key}") from exc


def probe(invalidate: bool = False) -> dict:
    source = PROBE.replace("INVAL", "True" if invalidate else "False")
    output = command(["docker", "exec", "-i", "-e", "FRAPPE_STREAM_LOGGING=1", "-w",
                      "/home/frappe/frappe-bench/sites", BACKEND,
                      "/home/frappe/frappe-bench/env/bin/python"], input_text=source)
    return json.loads(next(line.removeprefix("CC_ASSET_GATE=") for line in output.splitlines()
                           if line.startswith("CC_ASSET_GATE=")))


def integrity() -> tuple[dict, list[str], dict]:
    path = Path(__file__).with_name("goal02_install_one_command.py")
    spec = importlib.util.spec_from_file_location("goal02_install_one_command", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.runtime_fingerprint(), module.hooks(), module.snapshot()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invalidate", action="store_true", help="Owner-authorized one-key Redis mutation")
    parser.add_argument("--expected-image", default=EXPECTED_IMAGE,
                        help="Exact authorized backend image sha256")
    args = parser.parse_args()
    image_and_scope(args.expected_image)
    data_before, hooks_before, services_before = integrity()
    if any(services_before[name]["image"] != args.expected_image for name in
           ("backend", "frontend", "websocket", "queue-short", "queue-long", "scheduler")):
        raise RuntimeError("Six application images are not identical to expected image")
    before = probe()
    check_served_assets(before["manifest"])
    if args.invalidate:
        if before["cache_before"] == before["manifest"]:
            raise RuntimeError("Cache already current; nothing to change")
        if before["cache_before"] != KNOWN_STALE:
            raise RuntimeError("Cached asset mapping differs from the documented stale mapping")
        if set(before["mismatch_keys_before"]) != KNOWN_MISMATCH_KEYS:
            raise RuntimeError("Unexpected manifest/cache differences")
        after = probe(True)
        if after["cache_after"] != after["manifest"] or after["mismatch_keys_after"]:
            raise RuntimeError("Cache invalidation failed verification")
        check_served_assets(after["manifest"])
        result = {"status": "CACHE_INVALIDATED", **after}
    else:
        result = {"status": "MATCH" if not before["mismatch_keys_after"] else "STALE", **before}
    data_after, hooks_after, services_after = integrity()
    if data_after != data_before or hooks_after != hooks_before or services_after != services_before:
        raise RuntimeError("Synthetic data, security hooks or service identities changed")
    result["data_sha256"] = data_after["sha256"]
    result["communication_sha256"] = data_after["communication_sha256"]
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] != "STALE" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, StopIteration, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        sys.exit(3)
