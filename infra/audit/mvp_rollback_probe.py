#!/usr/bin/env python3
"""Audit installed services with real, uncommitted fixtures; never deploy code.

Executed via stdin by the host wrapper. Acceptance modules execute their current
versioned assertions directly; the probe never rewrites tests in memory.
"""
import hashlib
import importlib
import json
import traceback

import frappe

frappe.init(site="centrochange.local", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
assert frappe.conf.get("cc_synthetic_dev") == 1
assert frappe.conf.get("cc_uat_demo") == 1
frappe.set_user("Administrator")

ROOTS = ["Patient", "Healthcare Practitioner", "Patient Appointment", "Customer",
         "Supplier", "Company", "Branch", "Account", "Cost Center", "Item",
         "Item Price", "Price List", "Appointment Type", "Practitioner Schedule",
         "Practitioner Availability", "Sales Invoice", "Purchase Invoice",
         "Payment Entry", "GL Entry", "Payment Ledger Entry", "Bank Transaction",
         "Bank Account", "Bank", "Address", "Contact", "Communication",
         "Mode of Payment", "Sales Taxes and Charges Template", "User Permission",
         "DocShare", "Custom DocPerm", "Role", "Has Role", "File"]

def fingerprint():
    frappe.set_user("Administrator")
    names = set(ROOTS)
    names.update(frappe.get_all("DocType", filters={"name": ["like", "CC %"]}, pluck="name"))
    for name in list(names):
        if frappe.db.exists("DocType", name):
            names.update(f.options for f in frappe.get_meta(name).fields if f.fieldtype in ("Table", "Table MultiSelect"))
    result = {}
    for name in sorted(names):
        if not frappe.db.exists("DocType", name):
            continue
        if frappe.get_meta(name).issingle:
            rows = frappe.db.sql("select field,value from tabSingles where doctype=%s order by field", name, as_dict=True)
        else:
            rows = frappe.get_all(name, fields=["*"], order_by="name", limit_page_length=0)
        payload = json.dumps(rows, sort_keys=True, default=str, separators=(",", ":"))
        result[name] = {"count": len(rows), "sha256": hashlib.sha256(payload.encode()).hexdigest()}
    return result

def no_commit(*args, **kwargs):
    raise RuntimeError("AUDIT STOP: a rollback-only probe attempted commit")

frappe.db.commit = no_commit
before = fingerprint()
print("AUDIT_BASELINE=" + json.dumps(before, sort_keys=True), flush=True)

modules = ["operations.integration_acceptance"]
results = []
try:
    for module in modules:
        frappe.set_user("Administrator")
        try:
            result = importlib.import_module("centrochange_core." + module).run()
            assert result["status"] == "PASS"
            row = {"module": module, "status": "PASS", "result": result}
        except Exception as error:
            row = {"module": module, "status": "FAIL", "error_type": type(error).__name__, "error": str(error), "trace": traceback.format_exc()}
        finally:
            frappe.db.rollback()
        after = fingerprint()
        row["changed_tables"] = [k for k in before if before[k] != after.get(k)]
        results.append(row)
        print("AUDIT_RESULT=" + json.dumps(row, default=str), flush=True)
        if row["changed_tables"]:
            raise RuntimeError("AUDIT STOP: persistent business records changed")
finally:
    frappe.db.rollback()
    print("AUDIT_FINAL=" + json.dumps(fingerprint(), sort_keys=True), flush=True)
    frappe.destroy()
