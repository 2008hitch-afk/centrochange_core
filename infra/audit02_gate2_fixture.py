#!/usr/bin/env python3
"""Private, test-owned A/B fixture for AUDIT-02; run only with the Owner DEV gate.

This is a bench-side harness, not a whitelisted API or a product migration.
Credentials and the exact created-ID inventory must stay outside Git.
"""

import json
import os
from pathlib import Path
import re
import secrets
import sys

import frappe
from frappe.utils.password import update_password

from centrochange_core.security.audit import internal_write
from centrochange_core.security.lifecycle import set_assignment, set_membership


SITE = "centrochange.local"
TAG = "CC-HTTP-G2NAV161AA"
ROLES = {
    "m": "CC Manager", "s": "CC Secretariat", "a": "CC Professional",
    "b": "CC Professional", "c": "CC Professional", "f": "CC Finance",
    "t": "CC Accountant",
}
BASE = Path("/tmp/cc161-gate2")
INVENTORY = BASE / "inventory.json"
CREDENTIALS = BASE / "credentials.json"


def private_write(path, value):
    BASE.mkdir(mode=0o700, exist_ok=True)
    os.chmod(BASE, 0o700)
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")


def guard():
    if frappe.conf.get("cc_synthetic_dev") != 1 or frappe.session.user != "Administrator":
        raise RuntimeError("Synthetic Site and Administrator required")
    if not all(frappe.db.exists("Role", role) for role in set(ROLES.values())):
        raise RuntimeError("Approved role definitions missing")
    if INVENTORY.exists() or CREDENTIALS.exists():
        raise RuntimeError("Fixture inventory already exists")
    matches = frappe.get_all("Branch", filters={"cc_operational": 1}, fields=["name", "branch"])
    if len(matches) != 1 or matches[0].name != "CC-HTTP-UAT0000001 A":
        raise RuntimeError("Unexpected operational center baseline")
    for key in ROLES:
        if frappe.db.exists("User", f"{TAG.lower()}-{key}@example.invalid"):
            raise RuntimeError("Fixture user collision")
    if frappe.db.exists("Branch", TAG + " B"):
        raise RuntimeError("Fixture Branch collision")
    for suffix in ("A", "B"):
        if frappe.db.exists("Patient", {"uid": TAG + "-" + suffix}):
            raise RuntimeError("Fixture Patient collision")
    return matches[0].name


def create():
    center_a = guard()
    frappe.in_test = True
    result = {"tag": TAG, "center_a": center_a, "center_b": None,
              "users": {}, "patients": {}, "practitioners": {},
              "memberships": [], "assignments": []}
    passwords = {}
    try:
        for key, role in ROLES.items():
            email = f"{TAG.lower()}-{key}@example.invalid"
            frappe.get_doc({"doctype": "User", "email": email,
                            "first_name": TAG + " " + key, "enabled": 1,
                            "language": "it", "send_welcome_email": 0,
                            "roles": [{"role": role}]}).insert(ignore_permissions=True)
            password = secrets.token_urlsafe(32)
            update_password(email, password)
            result["users"][key] = email
            passwords[key] = {"name": email, "password": password}
        # The established synthetic fixture pattern uses the internal flag only
        # for the new test-owned Branch. Historical Branch rows remain untouched.
        with internal_write("cc_center_state_write"):
            result["center_b"] = frappe.get_doc({
                "doctype": "Branch", "branch": TAG + " B", "cc_operational": 1,
            }).insert().name
        scopes = {"m": (center_a, result["center_b"]),
                  "s": (center_a, result["center_b"]),
                  "a": (center_a,), "b": (result["center_b"],),
                  "c": (center_a, result["center_b"]),
                  "f": (center_a,), "t": (result["center_b"],)}
        for key, centers in scopes.items():
            for center in centers:
                row = set_membership(result["users"][key], center, 1, TAG)
                result["memberships"].append(row["name"])
        for key in ("a", "b", "c"):
            result["practitioners"][key] = frappe.get_doc({
                "doctype": "Healthcare Practitioner", "first_name": TAG + " " + key,
                "status": "Active", "user_id": result["users"][key],
            }).insert().name
        for suffix in ("A", "B"):
            result["patients"][suffix] = frappe.get_doc({
                "doctype": "Patient", "first_name": TAG + " " + suffix,
                "sex": "Female", "uid": TAG + "-" + suffix,
            }).insert().name
        for suffix, key, center in (("A", "a", center_a),
                                    ("B", "b", result["center_b"])):
            row = set_assignment(result["patients"][suffix], center,
                                 result["practitioners"][key], 1, TAG)
            result["assignments"].append(row["name"])
        frappe.db.commit()
        private_write(INVENTORY, result)
        private_write(CREDENTIALS, {"tag": TAG, "centers": [center_a, result["center_b"]],
                                    "users": passwords})
        print(json.dumps({"status": "FIXTURE_CREATED", "tag": TAG,
                          "centers": 2, "users": len(result["users"]),
                          "patients": len(result["patients"]),
                          "memberships": len(result["memberships"]),
                          "assignments": len(result["assignments"])}))
    except Exception:
        frappe.db.rollback()
        raise
    finally:
        frappe.in_test = False


def owned_inventory():
    data = json.loads(INVENTORY.read_text())
    if data.get("tag") != TAG or data.get("center_a") != "CC-HTTP-UAT0000001 A":
        raise RuntimeError("Fixture inventory mismatch")
    if not re.fullmatch(r"CC-HTTP-G2NAV161AA B", data.get("center_b", "")):
        raise RuntimeError("Fixture Branch ID mismatch")
    for key, user in data["users"].items():
        if key not in ROLES or user != f"{TAG.lower()}-{key}@example.invalid":
            raise RuntimeError("Fixture User ID mismatch")
    for suffix, patient in data["patients"].items():
        if suffix not in ("A", "B") or frappe.db.get_value("Patient", patient, "uid") != TAG + "-" + suffix:
            raise RuntimeError("Fixture Patient ownership mismatch")
    for key, name in data["practitioners"].items():
        if frappe.db.get_value("Healthcare Practitioner", name, "user_id") != data["users"][key]:
            raise RuntimeError("Fixture Practitioner ownership mismatch")
    for name in data["memberships"]:
        row = frappe.db.get_value("CC Center Membership", name, ["user", "center"], as_dict=True)
        if not row or row.user not in data["users"].values() or row.center not in (data["center_a"], data["center_b"]):
            raise RuntimeError("Fixture membership ownership mismatch")
    for name in data["assignments"]:
        row = frappe.db.get_value("CC Patient Assignment", name, ["patient", "center"], as_dict=True)
        if not row or row.patient not in data["patients"].values() or row.center not in (data["center_a"], data["center_b"]):
            raise RuntimeError("Fixture assignment ownership mismatch")
    return data


def verify():
    from centrochange_core.operations.workspace import bootstrap, patient_search
    from centrochange_core.operations.profiles import patient_detail
    data = owned_inventory()
    patients = data["patients"]
    centers = (data["center_a"], data["center_b"])
    checked = 0

    def forbidden(action):
        nonlocal checked
        try:
            action()
        except frappe.PermissionError:
            checked += 1
        else:
            raise AssertionError("Accesso non autorizzato consentito")

    for key, allow in (("m", (0, 1)), ("s", (0, 1)),
                       ("a", (0,)), ("b", (1,)), ("c", (0, 1))):
        frappe.set_user(data["users"][key])
        for index, center in enumerate(centers):
            if index in allow:
                response = bootstrap(center)
                assert response["center"] == center
                found = patient_search(center, TAG)["patients"]
                expected = patients["A" if index == 0 else "B"]
                if key == "c":
                    assert not found
                else:
                    assert expected in [row.name for row in found]
                wrong = patients["B" if index == 0 else "A"]
                forbidden(lambda: patient_detail(center=center, name=wrong))
                checked += 3
            else:
                forbidden(lambda: bootstrap(center))
                forbidden(lambda: patient_search(center, TAG))
    for key in ("f", "t"):
        frappe.set_user(data["users"][key])
        forbidden(lambda: bootstrap(centers[0]))
        forbidden(lambda: bootstrap(centers[1]))
    frappe.set_user("Guest")
    forbidden(lambda: bootstrap(centers[0]))
    frappe.set_user("Administrator")
    print(json.dumps({"status": "FIXTURE_API_PASS", "checks": checked}))


def destroy():
    data = owned_inventory()
    # Any new clinical or financial link is an Owner-owned change until reviewed.
    for doctype, filters in (
        ("Patient Appointment", {"patient": ["in", list(data["patients"].values())]}),
        ("Sales Invoice", {"cc_center": data["center_b"]}),
        ("Payment Entry", {"cc_center": data["center_b"]}),
    ):
        if frappe.db.exists(doctype, filters):
            raise RuntimeError("Fixture gained an unreviewed dependent; teardown blocked")
    users = list(data["users"].values())
    patients = list(data["patients"].values())
    # Reuse the existing, private synthetic fixture teardown. It verifies ownership
    # and removes linked child/auth/share/audit records by exact IDs. Pass only the
    # new Branch B: the historical operational A must never enter its delete set.
    from centrochange_core.security.dev_acceptance import destroy_http
    outcome = destroy_http({
        "tag": TAG,
        "users": {key: {"name": user} for key, user in data["users"].items()},
        "patients": patients,
        "practitioners": list(data["practitioners"].values()),
        "centers": [data["center_b"]],
    })
    if outcome.get("cleanup") != "PASS" or not frappe.db.get_value("Branch", data["center_a"], "cc_operational"):
        raise RuntimeError("Fixture cleanup or historical center preservation failed")
    print(json.dumps({"status": "FIXTURE_REMOVED", "users": len(users),
                      "patients": len(patients), "branches": 1}))


if __name__ == "__main__":
    os.umask(0o077)
    if len(sys.argv) != 2 or sys.argv[1] not in ("create", "verify", "destroy"):
        raise SystemExit("usage: audit02_gate2_fixture.py create|verify|destroy")
    frappe.init(SITE, sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    frappe.set_user("Administrator")
    try:
        {"create": create, "verify": verify, "destroy": destroy}[sys.argv[1]]()
    finally:
        frappe.set_user("Administrator")
        frappe.destroy()
