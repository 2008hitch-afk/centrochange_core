"""Read-only gap probes on actual installed synthetic data; outputs no secrets."""
import json
import frappe
from centrochange_core.finance import banking, reporting, files
from centrochange_core.security import audit_view
from centrochange_core.uat.demo import credentials

frappe.init(site="centrochange.local", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
assert frappe.conf.get("cc_synthetic_dev") == 1 and frappe.conf.get("cc_uat_demo") == 1
frappe.set_user("Administrator")
fixture = credentials()
center = fixture["centers"][0]
results = {}
try:
    results["versions"] = {app: __import__(app).__version__ for app in ("frappe", "erpnext", "healthcare", "builder")}
    results["centers"] = frappe.get_all("Branch", fields=["name", "cc_operational"], order_by="name")
    movements = frappe.get_all("Bank Transaction", filters={"cc_center": center, "docstatus": 1}, pluck="name")
    frappe.set_user(fixture["users"]["f"]["name"])
    traces = []
    for name in movements:
        value = banking.candidates(name)
        trace = {"movement": name, "state": value["state"], "documents": value.get("reconciled_documents", [])}
        for doc in trace["documents"]:
            if frappe.db.exists("Sales Invoice", doc["name"]):
                trace["native_invoice_exists"] = True
                trace["native_balance"] = frappe.db.get_value("Sales Invoice", doc["name"], "outstanding_amount")
        traces.append(trace)
    results["current_bank_trace"] = traces
    invoice = frappe.db.get_value("Sales Invoice", {"cc_center": center, "docstatus": 1}, "name")
    attachments = []
    for role in ("m", "s", "f", "t"):
        frappe.set_user(fixture["users"][role]["name"])
        doc = frappe.get_doc({"doctype": "File", "file_name": "AUDIT-SYNTHETIC-receipt.pdf", "is_private": 1,
                              "attached_to_doctype": "Sales Invoice", "attached_to_name": invoice})
        doc.__islocal = 1  # Native insert marks this before before_insert/validate.
        try:
            files.protected(doc)
            result = "GUARD_ALLOWED"
        except frappe.PermissionError as error:
            result = "DENIED: " + str(error)
        attachments.append({"role": role, "result": result, "file_inserted": False})
    results["manual_administrative_attachment_guard"] = attachments
    frappe.set_user("Administrator")
    sources = frappe.get_all("CC Audit Event", fields=["name", "event_type", "event_time"], order_by="creation desc", limit_page_length=3)
    tested = []
    for row in sources:
        date = str(frappe.utils.getdate(row.event_time))
        frappe.set_user(fixture["users"]["m"]["name"])
        found = any(x.name == row.name for x in audit_view.events(date, date, event_type=row.event_type)["events"])
        assert found
        tested.append({"id": row.name, "event_type": row.event_type, "found": found})
    for role in ("s", "a", "b", "c", "f", "t"):
        frappe.set_user(fixture["users"][role]["name"])
        try:
            audit_view.events(date, date)
        except frappe.PermissionError:
            continue
        raise AssertionError("unexpected audit access: " + role)
    results["current_audit_trace"] = {"events": tested, "six_roles_denied": True}
    frappe.set_user(fixture["users"]["f"]["name"])
    reporting.export_csv(center, "2026-09-01", "2026-10-31")
    lines = frappe.response["filecontent"].splitlines()
    results["finance_csv_human_output"] = {"header": lines[0], "first_data": lines[1], "row_count": len(lines)-1}
    results["current_finance_totals"] = reporting.summary(center, "2026-09-01", "2026-10-31")["totals"]
    frappe.set_user("Administrator")
    results["payment_methods"] = frappe.get_all("Payment Entry", fields=["name", "payment_type", "mode_of_payment"], order_by="name")
    from inspect import signature
    from centrochange_core.finance import receivables, incoming
    results["payment_signatures"] = {"receivables.pay": str(signature(receivables.pay)), "incoming.pay": str(signature(incoming.pay))}
    from centrochange_core.security.guards import require_operations
    inactive = []
    for role in ("m", "s", "a", "b", "c", "f", "t"):
        frappe.set_user(fixture["users"][role]["name"])
        try:
            require_operations(fixture["centers"][1])
        except frappe.PermissionError:
            inactive.append(role)
        else:
            raise AssertionError("Inactive center operational access allowed")
    results["inactive_center_operations_denied"] = inactive
    frappe.set_user("Administrator")
    results["scheduler"] = {"paused": frappe.conf.get("pause_scheduler"), "disabled": frappe.conf.get("disable_scheduler"),
        "methods": frappe.get_all("Scheduled Job Type", filters={"method": ["like", "centrochange_core.%"]}, fields=["method", "frequency", "stopped", "last_execution"], order_by="method")}
    print("AUDIT_READONLY=" + json.dumps(results, default=str, sort_keys=True))
finally:
    frappe.db.rollback()
    frappe.destroy()
