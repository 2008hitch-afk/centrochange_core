"""Read-only preflight before client demo: professional accounts + public first meeting.

This script must run as Administrator inside the already configured STAGING
bench console. No writes, no session impersonation, no email delivery and no
guest bookings. JSON output contains only aggregated PASS/FAIL diagnostics.
Actual login and guest booking remain separate browser acceptance tests on a
RESTORED ISOLATED CLONE, never on the populated staging database.
"""
from collections import defaultdict
from importlib.resources import files
import json


def run():
    import frappe
    from centrochange_core.scheduling.public_offer import configured_type, validate_free_offer, PublicOfferError
    from centrochange_core.scheduling.booking import snapshot

    results = []
    def check(group, name, good, detail=None):
        entry = {"area": group, "check": name, "result": "PASS" if bool(good) else "FAIL"}
        if detail is not None:
            entry["detail"] = detail
        results.append(entry)

    site = getattr(frappe.local, "site", None)
    if (frappe.session.user != "Administrator" or not site
            or site != frappe.conf.get("cc_presentation_site")
            or str(frappe.conf.get("cc_synthetic_dev")).lower() not in ("1", "true")):
        raise RuntimeError("Guard: exclusively Administrator on the configured synthetic STAGING site")

    data = json.loads(files("centrochange_core.uat")
                      .joinpath("presentation_dataset_v1.json").read_text(encoding="utf-8"))
    center_rows = frappe.get_all("CC Patient Assignment",
        fields=["patient", "practitioner", "center", "active"], page_length=1000)
    center_ids = {a.center for a in center_rows if a.active}
    check("scope", "one_presentation_center", len(center_ids) == 1)
    center = next(iter(center_ids)) if len(center_ids) == 1 else None
    check("safety", "outbound_email_muted",
          str(frappe.conf.get("mute_emails")).lower() in ("1", "true"))
    check("safety", "healthcare_registration_sms_disabled",
          not bool(frappe.db.get_single_value("Healthcare Settings", "send_registration_msg")))
    check("safety", "no_new_seed", not bool(frappe.conf.get("cc_presentation_seed")))
    check("safety", "no_email_queue", frappe.db.count("Email Queue") == 0)
    check("safety", "no_sales_invoices", frappe.db.count("Sales Invoice") == 0)

    practitioner_rows = frappe.get_all("Healthcare Practitioner",
        fields=["name", "user_id", "status", "supplier", "cc_profile_center"],
        page_length=1000)
    patients = frappe.get_all("Patient",
        fields=["name", "uid", "customer"], page_length=1000)
    appointments = frappe.get_all("Patient Appointment",
        fields=["name", "patient", "practitioner", "cc_center"], page_length=1000)
    members = frappe.get_all("CC Center Membership",
        fields=["user", "center", "active"], page_length=1000)
    memberships = {(m.user, m.center) for m in members if m.active}
    active_assignments = defaultdict(list)
    for item in center_rows:
        if item.active:
            active_assignments[item.patient].append(item)
    seed_emails = {p["email"] for p in data["professionals"]}
    seed_practitioners = [p for p in practitioner_rows if p.user_id in seed_emails]
    check("inventory", "professional_count_4", len(seed_practitioners) == 4)
    check("inventory", "patient_count_18", len(patients) == 18)
    check("inventory", "appointment_count_35", len(appointments) == 35)

    by_login = {p.user_id: p for p in practitioner_rows if p.user_id}
    by_uid = {p.uid: p for p in patients}
    fixture_professionals = data["professionals"]
    fixture_patients = data["patients"]
    pro_ids = {}
    valid_logins = len(seed_practitioners) == 4 and len({p.user_id for p in seed_practitioners if p.user_id}) == 4
    valid_membership = valid_logins
    valid_roles = valid_logins
    forbidden = {"CC Manager", "CC Finance", "CC Accountant", "System Manager"}
    for person in fixture_professionals:
        login = person["email"]
        pro = by_login.get(login)
        if pro:
            pro_ids[person["id"]] = pro.name
        user = frappe.db.get_value("User", login, ["enabled", "user_type"], as_dict=True)
        roles = set(frappe.get_roles(login)) if user else set()
        valid_logins = valid_logins and bool(user and user.enabled and
                user.user_type == "System User" and pro and pro.status == "Active")
        valid_membership = valid_membership and bool(pro and center and
                (login, center) in memberships and pro.cc_profile_center == center
                and pro.supplier and frappe.db.exists("Supplier", pro.supplier))
        valid_roles = valid_roles and ("CC Professional" in roles and not roles & forbidden)
    check("professional", "four_distinct_enabled_system_users", valid_logins)
    check("professional", "center_membership_and_supplier", valid_membership)
    check("professional", "limited_role_no_management_or_finance", valid_roles)

    patient_names = {}
    for person in fixture_patients:
        row = by_uid.get(data["ownership_tag"] + "-" + person["id"])
        if row:
            patient_names[person["id"]] = row.name
    assignments_ok = len(patient_names) == 18 and len(active_assignments) == 18
    for person in fixture_patients:
        patient = patient_names.get(person["id"])
        match = active_assignments.get(patient, [])
        assignments_ok = assignments_ok and len(match) == 1 and (
            match[0].practitioner == pro_ids.get(person["practitioner"])
            and match[0].center == center)
    check("professional", "all_patients_assigned_to_correct_professional", assignments_ok)

    acl_ok = len(pro_ids) == 4 and len(patient_names) == 18
    if acl_ok:
        for person in fixture_professionals:
            login = person["email"]
            own = next((patient_names[p["id"]] for p in fixture_patients
                        if p["practitioner"] == person["id"]), None)
            other = next((patient_names[p["id"]] for p in fixture_patients
                          if p["practitioner"] != person["id"]), None)
            if not own or not other:
                acl_ok = False
                continue
            own_doc, other_doc = frappe.get_doc("Patient", own), frappe.get_doc("Patient", other)
            if (not frappe.has_permission("Patient", "read", doc=own_doc, user=login)
                    or frappe.has_permission("Patient", "read", doc=other_doc, user=login)
                    or frappe.has_permission("Customer", "read",
                        doc=frappe.get_doc("Customer", own_doc.customer), user=login)):
                acl_ok = False
    check("professional", "patient_scope_and_fiscal_denial", acl_ok)
    own_agenda = len(pro_ids) == 4 and bool(center)
    if own_agenda:
        for person in fixture_professionals:
            visible_practitioner = pro_ids.get(person["id"])
            subset = [a for a in appointments if a.practitioner == visible_practitioner
                      and a.cc_center == center]
            own_agenda = own_agenda and len(subset) > 0
    check("professional", "all_four_have_scoped_agenda_data", own_agenda)

    service_login = "cc-public-booking-service@example.invalid"
    service_user = frappe.db.get_value("User", service_login, "enabled")
    check("public", "guest_booking_service_user_enabled", bool(service_user))
    route_records = frappe.get_all("CC Public Booking Route",
        fields=["name", "route", "center", "practitioner", "enabled"],
        page_length=20)
    routed = {r.route: r for r in route_records if r.enabled}
    required_directors = {"Marco", "Francesca"}
    check("public", "both_director_routes_enabled",
          required_directors <= set(routed))
    route_targets = True
    if center and required_directors <= set(routed):
        for key in required_directors:
            r = routed[key]
            pro = next((p for p in practitioner_rows if p.name == r.practitioner), None)
            route_targets = route_targets and bool(r.center == center and pro and
                pro.status == "Active" and (pro.user_id, center) in memberships)
    else:
        route_targets = False
    check("public", "routes_target_active_center_professionals", route_targets)

    mapping = frappe.conf.get("cc_public_first_meeting_types")
    modes_ok = True
    mode_names = {}
    for mode in ("sede", "online"):
        try:
            name = configured_type(mapping, mode)
            mode_names[mode] = name
            # First call validates center + canonical Item Price, then validates
            # the public 20 min / EUR 0 and readable in-person/online label.
            if not center:
                modes_ok = False
                continue
            snapshot_row = snapshot(name, center)
            validate_free_offer(snapshot_row, mode)
            service = frappe.db.get_value("CC Center Service",
                    {"center": center, "appointment_type": name}, "enabled")
            if not service:
                modes_ok = False
        except (frappe.ValidationError, frappe.PermissionError,
                PublicOfferError, ValueError, KeyError):
            modes_ok = False
    check("public", "two_distinct_free_20_minute_modes",
          modes_ok and len(set(mode_names.values())) == 2)
    schedules_ok = route_targets
    if route_targets:
        for route in routed.values():
            if route.route not in required_directors:
                continue
            active = frappe.get_all("Practitioner Schedule",
                filters={"cc_practitioner": route.practitioner,
                         "cc_center": center, "disabled": 0},
                pluck="name", page_length=100)
            schedule_rows = (frappe.get_all("Healthcare Schedule Time Slot",
                filters={"parent": ["in", active]}, pluck="name", page_length=1000)
                if active else [])
            schedules_ok = schedules_ok and bool(schedule_rows)
    check("public", "both_routes_have_schedule_windows", schedules_ok)
    check("public", "no_real_email_confirmation_enabled",
          not bool(frappe.conf.get("cc_email_booking_confirmation_enabled")))

    # The following require real HTTP sessions; do not report them as passed
    # based on database records or static code inspection.
    state = "READY_FOR_CLONE_HTTP" if all(r["result"] == "PASS" for r in results) else "BLOCKED"
    report = {"status": state, "checks": results,
        "total_pass": sum(r["result"] == "PASS" for r in results),
        "total_fail": sum(r["result"] == "FAIL" for r in results),
        "next_gate": "Authenticated professional login + Guest booking HTTP/desktop/mobile on isolated clone",
        "database_writes": 0}
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    if run()["status"] != "READY_FOR_CLONE_HTTP":
        raise SystemExit(2)
