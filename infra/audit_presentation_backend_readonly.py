"""Read-only Frappe/Healthcare/ERPNext graph audit for the already-loaded presentation site.

Run from an initialized bench console, as Administrator. This file does not
create/update/delete records, execute SQL writes, enqueue tasks or call a
posting/sending API. It prints only aggregate counts and status identifiers.
It must NOT be used to reload the fixture or retry the original seeder.
"""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from importlib.resources import files
import json
import sys


def run():
    import frappe

    checks = []

    def verify(code, condition, actual=None, expected=None):
        item = {"check": code, "result": "PASS" if bool(condition) else "FAIL"}
        if actual is not None:
            item["actual"] = actual
        if expected is not None:
            item["expected"] = expected
        checks.append(item)

    def flag(name):
        return str(frappe.conf.get(name, "")).strip().lower() in ("1", "true")

    site = getattr(frappe.local, "site", None)
    if (not site or site != frappe.conf.get("cc_presentation_site")
            or not flag("cc_synthetic_dev")
            or frappe.session.user != "Administrator"):
        raise RuntimeError("Audit refused: must be Administrator on the explicitly bound synthetic STAGING site.")

    recipe = json.loads(files("centrochange_core.uat")
                        .joinpath("presentation_dataset_v1.json").read_text(encoding="utf-8"))
    assert recipe["schema"] == "centrochange-presentation-v1"
    tag = recipe["ownership_tag"]
    all_pros = recipe["professionals"]
    all_patients = recipe["patients"]
    all_appts = recipe["appointments"]
    patient_map = {r["id"]: r for r in all_patients}
    pro_map = {r["id"]: r for r in all_pros}
    payer_map = {r["id"]: r for r in recipe["payers"]}
    as_date = lambda value: str(value)[:10]
    as_time = lambda value: str(value)[:5]

    apps = set(frappe.get_installed_apps())
    verify("STACK.ERPNext+Healthcare+CentroChange",
           {"erpnext", "healthcare", "centrochange_core"} <= apps)
    patient_meta = frappe.get_meta("Patient")
    verify("SCHEMA.native_Patient_customer",
           patient_meta.has_field("customer") and patient_meta.has_field("cc_external_payer")
           and patient_meta.has_field("cc_fiscal_mapping_confirmed"))
    verify("SAFETY.seed_disabled", not flag("cc_presentation_seed"))
    verify("SAFETY.emails_muted", flag("mute_emails"))
    verify("SAFETY.HC_registration_SMS_disabled",
           not bool(frappe.db.get_single_value("Healthcare Settings", "send_registration_msg")))

    disallowed = ("Sales Invoice", "Purchase Invoice", "Payment Entry", "GL Entry",
                  "Email Queue", "CC Fiscal Transaction", "CC Fiscal Attempt")
    accounting = {dt: frappe.db.count(dt) for dt in disallowed}
    for dt, count in accounting.items():
        verify("NO_EXTERNAL_OR_LEDGER." + dt.replace(" ", "_"), count == 0, count, 0)

    ps = frappe.get_all("Patient",
        fields=["name", "patient_name", "first_name", "last_name", "uid", "customer",
                "cc_external_payer", "cc_fiscal_mapping_confirmed"],
        page_length=1000)
    cs = frappe.get_all("Customer",
        fields=["name", "customer_name", "disabled"], page_length=1000)
    pros = frappe.get_all("Healthcare Practitioner",
        fields=["name", "first_name", "last_name", "user_id", "supplier", "status", "cc_profile_center"],
        page_length=1000)
    appts = frappe.get_all("Patient Appointment",
        fields=["name", "patient", "practitioner", "appointment_type", "cc_center", "company",
                "appointment_date", "appointment_time", "duration", "cc_service_item",
                "cc_service_label", "cc_price_snapshot", "cc_currency_snapshot",
                "status", "cc_closure_state", "cc_economic_state", "cc_paid", "cc_performed"],
        page_length=1000)
    assignments = frappe.get_all("CC Patient Assignment",
        fields=["name", "patient", "practitioner", "center", "active"], page_length=1000)
    memberships = frappe.get_all("CC Center Membership",
        fields=["name", "user", "center", "active"], page_length=1000)
    sources = frappe.get_all("CC Economic Source Link",
        fields=["name", "appointment", "patient", "customer", "practitioner", "supplier",
                "center", "company", "cost_center", "service_item", "service_label",
                "duration", "price", "currency", "economic_state", "performed",
                "operational_paid", "snapshot_hash", "source_key"],
        page_length=1000)
    receipts = frappe.get_all("CC Operational Receipt",
        fields=["name", "patient", "center", "receipt_date", "mode_of_payment", "allocations"],
        page_length=1000)
    counts = {"professionals": len(pros), "patients": len(ps),
              "customers": len(cs), "appointments": len(appts),
              "assignments": len(assignments), "economic_sources": len(sources),
              "operational_receipts": len(receipts)}
    expected = {"professionals": 4, "patients": 18, "customers": 17,
                "appointments": 35, "assignments": 18,
                "economic_sources": 35, "operational_receipts": 10}
    for kind, number in expected.items():
        verify("CARDINALITY." + kind, counts[kind] == number, counts[kind], number)

    patients = {r.uid: r for r in ps if r.uid}
    patient_ids = {}
    for person in all_patients:
        match = patients.get(tag + "-" + person["id"])
        if match:
            patient_ids[person["id"]] = match.name
    verify("PATIENT.UIDs_unique_and_exact", len(patient_ids) == 18 and len(patients) == len(ps),
           len(patient_ids), 18)
    by_p_name = {r.name: r for r in ps}
    by_customer = {r.name: r for r in cs}
    pro_by_email = {p.user_id: p for p in pros}
    pro_ids = {}
    role_ok = True
    pro_active = True
    for person in all_pros:
        practitioner = pro_by_email.get(person["email"])
        if practitioner:
            pro_ids[person["id"]] = practitioner.name
            user = frappe.db.get_value("User", person["email"], ["enabled"], as_dict=True)
            roles = frappe.get_all("Has Role",
                filters={"parenttype": "User", "parent": person["email"], "role": "CC Professional"},
                pluck="name", page_length=20)
            role_ok = role_ok and bool(roles)
            pro_active = pro_active and bool(user and user.enabled and practitioner.status == "Active"
                                           and practitioner.supplier and
                                           frappe.db.exists("Supplier", practitioner.supplier))
        else:
            pro_active = False
            role_ok = False
    verify("PROFESSIONAL.login_enabled_supplier_mapped",
           len(pro_ids) == 4 and pro_active and len(pro_by_email) == 4)
    verify("PROFESSIONAL.correct_Frappe_role", role_ok)
    centers = {r.center for r in assignments if r.active}
    center = next(iter(centers)) if len(centers) == 1 else None
    verify("CENTER.single_operational_scope", center is not None)
    if center is None:
        result = {"status": "FAIL", "checks": checks, "counts": counts,
                  "reason": "No unique current center for patient assignments"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return result

    branch = frappe.db.get_value("Branch", center,
        ["cc_operational", "cc_company", "cc_cost_center"], as_dict=True)
    accounting_center = (frappe.db.get_value("Cost Center", branch.cc_cost_center,
        ["company", "is_group", "disabled"], as_dict=True)
        if branch and branch.cc_cost_center else None)
    verify("ERPNext.company_and_leaf_cost_center",
           bool(branch and branch.cc_operational and branch.cc_company
                and accounting_center and accounting_center.company == branch.cc_company
                and not accounting_center.is_group and not accounting_center.disabled))
    verify("ERPNext.Customer_master_links",
           all(p.customer in by_customer and p.cc_fiscal_mapping_confirmed for p in ps))
    assigned = {r.patient: r for r in assignments if r.active}
    verify("HEALTHCARE.patient_assignment_unique",
           len(assigned) == 18 and len(assignments) == 18)
    verify("HEALTHCARE.assignment_to_professional",
           all(person_id in patient_ids and person_id in patient_map
               and patient_ids[person_id] in assigned
               and assigned[patient_ids[person_id]].center == center
               and assigned[patient_ids[person_id]].practitioner == pro_ids.get(patient_map[person_id]["practitioner"])
               for person_id in patient_ids))
    verify("SECURITY.professional_memberships",
           all(any(m.user == person["email"] and m.center == center and m.active
                   for m in memberships) for person in all_pros)
           and all(practitioner.cc_profile_center == center for practitioner in pros))
    group = frappe.db.get_single_value("Selling Settings", "customer_group")
    verify("ERPNext.customer_group_leaf",
           bool(group) and not bool(frappe.db.get_value("Customer Group", group, "is_group")))
    verify("ERPNext.Contanti_enabled",
           bool(frappe.db.get_value("Mode of Payment", "Contanti", "enabled")))

    fiscal_ok = len(patient_ids) == 18
    linked_customers = set()
    actual_customer_patient = defaultdict(list)
    for pid, person in patient_map.items():
        row = by_p_name.get(patient_ids.get(pid))
        if row is None or row.customer not in by_customer:
            fiscal_ok = False
            continue
        linked_customers.add(row.customer)
        actual_customer_patient[row.customer].append(pid)
        payer = payer_map[person["payer"]]
        external = payer["kind"] == "external"
        if bool(row.cc_external_payer) != external:
            fiscal_ok = False
        if not external and by_customer[row.customer].customer_name != (
                person["first_name"] + " " + person["last_name"]):
            fiscal_ok = False
        if external and by_customer[row.customer].customer_name != payer["display_name"]:
            fiscal_ok = False
    shared = [set(pids) for pids in actual_customer_patient.values() if len(pids) > 1]
    verify("PATIENT_TO_CUSTOMER.17_distinct", len(linked_customers) == 17, len(linked_customers), 17)
    verify("PATIENT_TO_CUSTOMER.self_and_third_party", fiscal_ok)
    verify("PATIENT_TO_CUSTOMER.Caruso_siblings", shared == [{"P17", "P18"}])

    date_time_to_appt = defaultdict(list)
    for row in appts:
        date_time_to_appt[(row.patient, as_date(row.appointment_date),
                           as_time(row.appointment_time))].append(row)
    appt_ids = {}
    matching = True
    for item in all_appts:
        patient_name = patient_ids.get(item["patient"])
        options = date_time_to_appt.get((patient_name, item["date"], item["time"]), [])
        if len(options) != 1:
            matching = False
            continue
        session = options[0]
        appt_ids[item["id"]] = session.name
        doc_patient = patient_map[item["patient"]]
        service = recipe["services"][item["service"]]
        if (session.practitioner != pro_ids.get(doc_patient["practitioner"])
                or session.cc_center != center
                or Decimal(str(session.cc_price_snapshot)) != Decimal(service["eur"])
                or Decimal(str(session.duration)) != Decimal(service["minutes"])
                or session.cc_currency_snapshot != "EUR"
                or (item["service"] == "FIRST" and
                    not session.cc_service_label.casefold().startswith("primo colloquio conoscitivo"))
                or (item["service"] == "SESSION" and session.cc_service_label != "Seduta")):
            matching = False
    verify("APPOINTMENTS.35_correct_patient_professional_price_duration",
           matching and len(appt_ids) == 35 and len(set(appt_ids.values())) == 35)
    appt_by_name = {a.name: a for a in appts}
    source_per_appt = defaultdict(list)
    for src in sources:
        source_per_appt[src.appointment].append(src)
    source_ok = len(source_per_appt) == 35 and all(len(v) == 1 for v in source_per_appt.values())
    for appt in appts:
        links = source_per_appt.get(appt.name, [])
        patient = by_p_name.get(appt.patient)
        professional = next((p for p in pros if p.name == appt.practitioner), None)
        if len(links) != 1 or not patient or not professional:
            source_ok = False
            continue
        src = links[0]
        if (src.patient != appt.patient or src.customer != patient.customer
                or src.practitioner != appt.practitioner or src.supplier != professional.supplier
                or src.center != center or src.company != branch.cc_company
                or src.cost_center != branch.cc_cost_center
                or src.service_item != appt.cc_service_item
                or src.currency != "EUR"
                or Decimal(str(src.price)) != Decimal(str(appt.cc_price_snapshot))
                or Decimal(str(src.duration)) != Decimal(str(appt.duration))
                or src.source_key != src.snapshot_hash):
            source_ok = False
    verify("ECONOMIC_SOURCE_LINK.35_lossless_native_snapshots", source_ok)

    allocated = defaultdict(int)
    receipt_ok = True
    cents_total = 0
    for receipt in receipts:
        if receipt.center != center or receipt.mode_of_payment != "Contanti":
            receipt_ok = False
        try:
            entries = json.loads(receipt.allocations)
        except (TypeError, ValueError):
            entries = []
            receipt_ok = False
        if len(entries) != 1:
            receipt_ok = False
        for entry in entries:
            name = entry.get("appointment")
            cents = entry.get("cents")
            if (not isinstance(cents, int) or isinstance(cents, bool) or cents <= 0
                    or name not in appt_by_name
                    or appt_by_name[name].patient != receipt.patient):
                receipt_ok = False
            else:
                allocated[name] += cents
                cents_total += cents
    verify("RECEIPTS.10_valid_allocations", receipt_ok and len(receipts) == 10)
    verify("RECEIPTS.cash_392_EUR", cents_total == 39200, cents_total, 39200)
    states_ok = True
    for item in all_appts:
        row = appt_by_name.get(appt_ids.get(item["id"]))
        if not row:
            states_ok = False
            continue
        expected_cents = {"paid": 4400, "partial": 2000}.get(item["state"], 0)
        if allocated[row.name] != expected_cents:
            states_ok = False
        if item["state"] == "paid" and not row.cc_paid:
            states_ok = False
        if item["state"] != "paid" and row.cc_paid:
            states_ok = False
        if item["service"] == "FIRST" and item["state"] == "past_completed":
            if row.cc_economic_state != "Waived":
                states_ok = False
        if item["state"] == "cancelled_timely" and row.status != "Cancelled":
            states_ok = False
    verify("LIFECYCLE.closure_waivers_paid_partial_cancelled", states_ok)

    # Both user-visible report projections must reconcile to the same dated
    # operational receipt cash, and must not invent ERPNext Payment Entries.
    report_ok = False
    try:
        from centrochange_core.finance.patient_reporting import patient_view
        from centrochange_core.finance.report_dashboard import professional
        start, end = "2026-10-01", "2026-11-30"
        customer_report = patient_view(center, start, end)
        professional_report = professional(center, start, end)
        by_customer_cash = sum(int(r["operational"]["cash_cents"])
                               for r in customer_report["rows"])
        report_ok = (
            len(customer_report["rows"]) == 17
            and by_customer_cash == 39200
            and int(professional_report["cash_cents"]) == 39200
            and int(professional_report["total"]) == 35
        )
        verify("REPORTS.customer_and_professional_cash_reconciliation",
               report_ok, {"fiscal_subjects": len(customer_report["rows"]),
                           "customer_cash_cents": by_customer_cash,
                           "professional_cash_cents": professional_report["cash_cents"],
                           "professional_sessions": professional_report["total"]},
               {"fiscal_subjects": 17, "cash_cents": 39200, "sessions": 35})
    except Exception as exc:
        verify("REPORTS.customer_and_professional_cash_reconciliation",
               False, {"exception_type": type(exc).__name__})

    status = "PASS" if all(c["result"] == "PASS" for c in checks) else "FAIL"
    result = {"status": status, "site_check": "bound synthetic STAGING",
              "checks": checks, "counts": counts,
              "writes_executed": 0, "report_contains_personal_data": False}
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    if run()["status"] != "PASS":
        raise SystemExit(2)
