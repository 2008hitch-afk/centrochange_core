"""Refresh one stale Frappe form-meta cache entry after the demo image update.

Run on the host. Only the Sales Invoice client cache key is invalidated; no
database records, services, or other DocType caches are changed.
"""

import subprocess
import sys


CODE = r'''
import frappe
from frappe.desk.form.meta import get_meta

frappe.init(site="centrochange.local", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
try:
    marker = "Paziente dimostrativo POS"
    fresh = get_meta("Sales Invoice", cached=False)
    if marker not in (fresh.get("__list_js") or ""):
        raise RuntimeError("Sales Invoice source marker missing; cache unchanged")
    cached = get_meta("Sales Invoice", cached=True)
    if marker in (cached.get("__list_js") or ""):
        print("ALREADY_CURRENT")
    else:
        frappe.client_cache.delete_value("doctype_form_meta::Sales Invoice")
        verified = get_meta("Sales Invoice", cached=True)
        if marker not in (verified.get("__list_js") or ""):
            raise RuntimeError("Sales Invoice cache refresh failed")
        print("SALES_INVOICE_META_REFRESHED")
finally:
    frappe.destroy()
'''


def main():
    command = [
        "sudo", "-n", "docker", "exec", "-i", "-u", "frappe",
        "-e", "FRAPPE_STREAM_LOGGING=1", "-w", "/home/frappe/frappe-bench/sites", "centrochange-dev-backend-1",
        "/home/frappe/frappe-bench/env/bin/python", "-I", "-",
    ]
    result = subprocess.run(command, input=CODE, text=True, capture_output=True, check=False)
    if result.returncode:
        print("Targeted cache refresh failed; inspect private stderr", file=sys.stderr)
        return result.returncode
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
