"""AUDIT-11 Frappe/MariaDB integration acceptance on a disposable CI-only site.

This file runs inside the single-use clone only. All records have synthetic
identities and live in a savepoint; no client site/configuration is accessed.
It checks the real Frappe services, but not HTTP CSRF or browser visual UAT.
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import frappe

frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.in_test = True
frappe.set_user("Administrator")

from centrochange_core.uat import demo
from centrochange_core.scheduling.public_booking import available_slots, first_meeting

assert frappe.conf.get("cc_synthetic_dev") == 1 and frappe.conf.get("cc_uat_demo") == 1
seed = demo.read()["fixture"]
assert seed["tag"] == "CC-HTTP-UAT0000001"
assert len(seed["catalog"]["CC Public Booking Route"]) == 1
assert len(seed["practitioners"]) == 2

center = seed["centers"][0]
original_route = seed["catalog"]["CC Public Booking Route"][0]
other_route = "Francesca" if original_route == "Marco" else "Marco"
assert original_route in ("Marco", "Francesca")
assert not frappe.db.exists("CC Public Booking Route", other_route), "Unexpected route on disposable site"
assert frappe.db.get_value("Branch", center, "cc_operational")
price_list = frappe.db.get_value("Branch", center, "cc_price_list")
assert price_list and frappe.db.get_value("Price List", price_list, "currency") == "EUR"
assert frappe.db.get_value("CC Public Booking Route", original_route, "practitioner") == seed["practitioners"][0]

frappe.db.savepoint("audit11_free_public_test")
previous_config = frappe.conf.get("cc_public_first_meeting_types")
baseline_email_queue = frappe.db.count("Email Queue")
checks = []
try:
    types = {}
    for mode, label in (("sede", "in sede"), ("online", "online")):
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": f"CC11-UAT-{mode.upper()}-20",
            "item_name": f"CC11 UAT colloquio conoscitivo {label}",
            "item_group": "Services",
            "stock_uom": "Nos", "is_stock_item": 0, "is_sales_item": 1,
        }).insert(ignore_permissions=True)
        appointment_type = frappe.get_doc({
            "doctype": "Appointment Type",
            "appointment_type": f"CC11 UAT 20 MIN {mode.upper()}",
            "allow_booking_for": "Practitioner",
            "default_duration": 20, "cc_service_item": item.name, "cc_first_meeting": 1,
        }).insert(ignore_permissions=True)
        frappe.get_doc({
            "doctype": "Item Price", "item_code": item.name,
            "price_list": price_list, "price_list_rate": 0,
            "currency": "EUR", "valid_from": "2020-01-01",
        }).insert(ignore_permissions=True)
        frappe.get_doc({
            "doctype": "CC Center Service", "center": center,
            "appointment_type": appointment_type.name, "enabled": 1,
        }).insert(ignore_permissions=True)
        types[mode] = appointment_type.name
    assert len(set(types.values())) == 2
    frappe.conf.cc_public_first_meeting_types = types

    # The second Director has an existing synthetic schedule seeded by demo.seed.
    frappe.get_doc({
        "doctype": "CC Public Booking Route", "route": other_route,
        "center": center, "practitioner": seed["practitioners"][1],
        "appointment_type": types["sede"], "enabled": 1,
    }).insert(ignore_permissions=True)

    now = datetime.now(ZoneInfo("Europe/Rome")).date()
    next_monday = now + timedelta(days=(7 - now.weekday()) % 7 or 7)
    day = next_monday.isoformat()
    assert 0 < (next_monday - now).days <= 7

    bookings = {}
    for director in ("Marco", "Francesca"):
        for mode in ("sede", "online"):
            frappe.set_user("Guest")
            projection = available_slots(director, day, mode)
            assert projection["mode"] == mode and projection["route"] == director
            assert projection["duration"] == 20 and projection["price"] == 0 and projection["currency"] == "EUR"
            assert projection["slots"], f"No free slot for {director}/{mode} on synthetic next Monday"
            slot = projection["slots"][0]
            email = f"cc11-{director.lower()}-{mode}@example.invalid"
            payload = {
                "route": director, "mode": mode,
                "first_name": "CC11 Synthetic", "last_name": "Guest",
                "email": email, "sex": "Other",
                "appointment_date": slot["date"],
                "appointment_time": slot["time"],
                "request_key": f"cc11-{director}-{mode}",
            }
            result = first_meeting(**payload)
            assert result["replay"] is False
            assert result["confirmation"]["state"] == "Simulated Sent"
            if director == "Marco" and mode == "sede":
                replay = first_meeting(**payload)
                assert replay["name"] == result["name"] and replay["replay"] is True
                assert replay["confirmation"]["replay"] is True
                checks.append("replay_one_appointment_one_confirmation")
            frappe.set_user("Administrator")
            doc = frappe.get_doc("Patient Appointment", result["name"])
            assert doc.appointment_type == types[mode]
            assert int(float(doc.duration)) == 20 and float(doc.cc_price_snapshot) == 0
            assert mode in doc.cc_service_label.casefold()
            assert doc.practitioner == frappe.db.get_value("CC Public Booking Route", director, "practitioner")
            assert frappe.db.count("Patient Appointment", {"patient": doc.patient}) == 1
            assert frappe.db.count("CC Booking Confirmation", {"appointment": doc.name}) == 1
            bookings[(director, mode)] = {"name": result["name"], "slot": slot}
            checks.append(f"real_frappe_booking_{director.lower()}_{mode}_free_20m")

    # Same Director must not be double-booked across the two public modes.
    booked = bookings[("Marco", "sede")]["slot"]
    frappe.set_user("Guest")
    after = available_slots("Marco", day, "online")
    assert booked not in after["slots"], "Cross-mode slot conflict leaked"

    # A request key is scoped to its original mode, route and user payload.
    original = bookings[("Marco", "sede")]
    wrong_replay = {
        "route": "Marco", "mode": "online",
        "first_name": "CC11 Synthetic", "last_name": "Guest",
        "email": "cc11-marco-sede@example.invalid", "sex": "Other",
        "appointment_date": original["slot"]["date"],
        "appointment_time": original["slot"]["time"],
        "request_key": "cc11-Marco-sede",
    }
    try:
        first_meeting(**wrong_replay)
    except Exception:
        checks.append("mode_changed_replay_denied")
    else:
        raise AssertionError("Replay with changed mode did not fail")
    for illegal_mode in ("group", "other", ""):
        try:
            available_slots("Marco", day, illegal_mode)
        except frappe.PermissionError:
            checks.append("unapproved_mode_denied")
        else:
            raise AssertionError("Unapproved guest mode accepted")

    # Guest mode selection cannot silently become on-site through omitted args.
    try:
        available_slots("Marco", day)
    except TypeError:
        checks.append("missing_mode_rejected")
    else:
        raise AssertionError("Missing mode unexpectedly accepted")

    frappe.conf.cc_public_first_meeting_types = {}
    try:
        available_slots("Marco", day, "sede")
    except frappe.PermissionError:
        checks.append("unconfigured_catalog_fails_closed")
    else:
        raise AssertionError("Missing private catalog mapping accepted")
    frappe.conf.cc_public_first_meeting_types = types

    # Date boundary and negative security checks for available_slots and first_meeting
    frappe.set_user("Guest")
    past_date = (now - timedelta(days=1)).isoformat()
    too_far_date = (now + timedelta(days=121)).isoformat()
    at_horizon_date = (now + timedelta(days=120)).isoformat()

    try:
        available_slots("Marco", past_date, "sede")
    except frappe.ValidationError:
        checks.append("slots_past_date_rejected")
    else:
        raise AssertionError("available_slots accepted past date")

    try:
        available_slots("Marco", too_far_date, "sede")
    except frappe.ValidationError:
        checks.append("slots_121_days_rejected")
    else:
        raise AssertionError("available_slots accepted date beyond 120 days")

    try:
        slots_120 = available_slots("Marco", at_horizon_date, "sede")
        assert isinstance(slots_120.get("slots"), list)
        checks.append("slots_120_days_boundary_accepted")
    except frappe.ValidationError:
        raise AssertionError("available_slots rejected 120 days boundary")

    try:
        first_meeting(
            route="Marco", mode="sede",
            first_name="CC11 Synthetic", last_name="Boundary",
            email="cc11-past@example.invalid", sex="Other",
            appointment_date=past_date, appointment_time="10:00:00",
            request_key="cc11-boundary-past",
        )
    except frappe.ValidationError:
        checks.append("booking_past_date_rejected")
    else:
        raise AssertionError("first_meeting accepted past date")

    try:
        first_meeting(
            route="Marco", mode="sede",
            first_name="CC11 Synthetic", last_name="Boundary",
            email="cc11-too-far@example.invalid", sex="Other",
            appointment_date=too_far_date, appointment_time="10:00:00",
            request_key="cc11-boundary-too-far",
        )
    except frappe.ValidationError:
        checks.append("booking_121_days_rejected")
    else:
        raise AssertionError("first_meeting accepted date beyond 120 days")

    try:
        first_meeting(
            route="Marco", mode="sede",
            first_name="CC11 Synthetic", last_name="Boundary",
            email="cc11-unavailable@example.invalid", sex="Other",
            appointment_date=day, appointment_time="03:00:00",
            request_key="cc11-boundary-unavailable",
        )
    except Exception:
        checks.append("booking_unavailable_slot_rejected")
    else:
        raise AssertionError("first_meeting accepted unavailable slot at 03:00")

    already_booked = bookings[("Marco", "sede")]["slot"]
    try:
        first_meeting(
            route="Marco", mode="sede",
            first_name="CC11 Synthetic", last_name="Colliding",
            email="cc11-colliding@example.invalid", sex="Other",
            appointment_date=already_booked["date"], appointment_time=already_booked["time"],
            request_key="cc11-different-request-collision",
        )
    except Exception:
        checks.append("booking_conflicting_slot_rejected")
    else:
        raise AssertionError("first_meeting accepted already booked slot")

    frappe.set_user("Administrator")
    assert frappe.db.count("Email Queue") == baseline_email_queue
    checks.append("no_real_email_queue")
    assert len(bookings) == 4
    print(json.dumps({"status": "PASS", "scope": "isolated_native_frappe_only",
                      "count": len(bookings), "checks": checks}), flush=True)
finally:
    frappe.set_user("Administrator")
    frappe.conf.cc_public_first_meeting_types = previous_config
    frappe.db.rollback(save_point="audit11_free_public_test")
    frappe.destroy()
