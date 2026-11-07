"""Preparation and real acceptance on a throwaway isolated Frappe/MariaDB site only."""
import frappe
from centrochange_core.security.audit import internal_write
from centrochange_core.uat import presentation_seed


def prepare():
    if frappe.session.user != "Administrator" or frappe.conf.get("cc_synthetic_dev") != 1:
        frappe.throw("Only a fresh synthetic clone can prepare presentation acceptance.")
    if any(frappe.db.count(dt) for dt in
           ("Patient", "Healthcare Practitioner", "Customer", "Patient Appointment")):
        frappe.throw("Clone is not empty.")
    with internal_write("cc_center_state_write"):
        branch = frappe.get_doc({"doctype": "Branch", "branch": "Centro Change Milano",
             "cc_operational": 1}).insert(ignore_permissions=True)
    price_list = frappe.get_doc({"doctype": "Price List", "price_list_name": "Listino Centro Change",
         "enabled": 1, "selling": 1, "currency": "EUR"}).insert(ignore_permissions=True)
    frappe.db.set_value("Branch", branch.name, "cc_price_list", price_list.name)
    # ERPNext default Selling Settings may still point to the *group* root.
    # Create a dedicated leaf only on this disposable clone, not in STAGING.
    root = frappe.db.get_value("Customer Group", {"is_group": 1, "parent_customer_group": ["is", "not set"]}, "name")
    if not root:
        frappe.throw("Manca la radice Gruppo clienti di ERPNext nel clone.")
    child = frappe.get_doc({"doctype": "Customer Group",
        "customer_group_name": "Clienti Centro Change", "is_group": 0,
        "parent_customer_group": root}).insert(ignore_permissions=True)
    frappe.db.set_single_value("Selling Settings", "customer_group", child.name)

    for key, spec in presentation_seed._fixture()["services"].items():
        item = frappe.get_doc({"doctype": "Item", "item_code": "CC-PRESENT-" + key,
            "item_name": spec["label"], "item_group": "Services", "stock_uom": "Nos",
            "is_stock_item": 0, "is_sales_item": 1}).insert(ignore_permissions=True)
        profile = frappe.get_doc({"doctype": "Appointment Type",
            "appointment_type": "CC-PRESENT-" + key, "allow_booking_for": "Practitioner",
            "default_duration": spec["minutes"], "cc_service_item": item.name,
            "cc_first_meeting": int(key == "FIRST")}).insert(ignore_permissions=True)
        frappe.get_doc({"doctype": "Item Price", "item_code": item.name,
            "price_list": price_list.name, "price_list_rate": spec["eur"],
            "currency": "EUR", "valid_from": "2020-01-01"}).insert(ignore_permissions=True)
        frappe.get_doc({"doctype": "CC Center Service", "center": branch.name,
            "appointment_type": profile.name, "enabled": 1}).insert(ignore_permissions=True)
    if not frappe.db.exists("Mode of Payment", "Contanti"):
        frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Contanti",
            "type": "Cash", "enabled": 1}).insert(ignore_permissions=True)
    frappe.db.set_single_value("Healthcare Settings", "send_registration_msg", 0)
    frappe.db.set_single_value("Healthcare Settings", "collect_registration_fee", 0)
    frappe.db.commit()
    return {"center": branch.name, "services": 2, "state": "EMPTY"}


def run():
    """Bench execute: all lifecycle/receipt work executes in a real DB transaction."""
    if frappe.session.user != "Administrator" or frappe.conf.get("cc_synthetic_dev") != 1:
        frappe.throw("Clone-only acceptance.")
    centers = frappe.get_all("Branch", filters={"branch": "Centro Change Milano"}, pluck="name")
    assert len(centers) == 1
    center = centers[0]
    data = presentation_seed._fixture()
    plan = presentation_seed.plan(center)
    assert plan["status"] == "READY"
    backup = frappe.conf.get("cc_presentation_backup_sha256")
    first = presentation_seed.apply(center, plan["dataset_sha256"], backup)
    assert first["status"] == "PASS"
    replay = presentation_seed.apply(center, plan["dataset_sha256"], backup)
    assert replay["status"] == "EXISTS"
    state = presentation_seed.inspect()
    assert state["status"] == "EXISTS"

    from centrochange_core.finance import patient_reporting
    assert frappe.db.count("Patient") == 18
    assert frappe.db.count("Healthcare Practitioner") == 4
    assert frappe.db.count("Customer") == 17
    assert frappe.db.count("Patient Appointment") == 35
    assert frappe.db.count("CC Economic Source Link") == 35
    assert frappe.db.count("CC Operational Receipt") == 10
    assert frappe.db.count("Sales Invoice") == 0
    assert frappe.db.count("Payment Entry") == 0
    assert frappe.db.count("GL Entry") == 0
    assert frappe.db.count("Email Queue") == 0
    professionals = frappe.get_all("Healthcare Practitioner", fields=["name", "user_id", "status"])
    assert len({p.user_id for p in professionals}) == 4
    assert all(p.status == "Active" and frappe.db.get_value("User", p.user_id, "enabled")
               for p in professionals)
    for patient in frappe.get_all("Patient", fields=["name", "first_name", "customer", "uid"]):
        assert not patient.first_name.startswith("SYNTHETIC")
        assert patient.customer
        assert patient.uid.startswith(data["ownership_tag"])

    names = frappe.get_all("Patient", filters={"last_name": "Caruso"},
                           fields=["name", "customer"])
    assert len(names) == 2 and names[0].customer == names[1].customer
    fiscal = frappe.db.get_value("Customer", names[0].customer, "customer_name")
    assert fiscal == "Laura Caruso"
    appointments = frappe.get_all("Patient Appointment", fields=[
        "cc_service_label", "cc_price_snapshot", "duration", "appointment_date",
        "cc_closure_state", "cc_economic_state", "cc_performed", "cc_paid"])
    free = [a for a in appointments if a.cc_service_label == "Primo colloquio conoscitivo"]
    sessions = [a for a in appointments if a.cc_service_label == "Seduta"]
    assert len(free) == 10 and len(sessions) == 25
    assert all(a.duration == 20 and a.cc_price_snapshot == 0 for a in free)
    assert all(a.duration == 45 and a.cc_price_snapshot == 44 for a in sessions)
    assert sum(a.cc_paid for a in sessions) == 8
    assert sum(a.cc_economic_state == "Waived" for a in free) == 7
    assert sum(a.cc_closure_state in ("Pending", "Auto Locked") for a in sessions) >= 10
    return {"status": "PASS", "counts": first["counts"], "replay": True,
            "customer_group": "Laura Caruso / 2 patients", "no_messages": True,
            "no_posted_accounting": True}
