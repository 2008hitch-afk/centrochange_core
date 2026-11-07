"""Explicitly authorized, bench-only presentation fixture. Never a whitelisted API.

This module is deliberately unusable without staging-only site settings,
Administrator, a real encrypted-backup attestation, and an empty target site.
It never sends fiscal documents, messages, invoices or external payments.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
import fcntl
import json
import os
import re

import frappe

from centrochange_core.security.audit import append, internal_write
from centrochange_core.security import dev_acceptance

ROME = ZoneInfo("Europe/Rome")
FIXTURE = "presentation_dataset_v1.json"
MANIFEST = "client-presentation-v1.json"
REASON = "Inserimento iniziale della situazione operativa"


def _fixture():
    return json.loads(files("centrochange_core.uat").joinpath(FIXTURE).read_text(encoding="utf-8"))


def _digest(data):
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _flag(name):
    return str(frappe.conf.get(name, "")).strip().lower() in ("1", "true")


def _guard(require_backup=False):
    site = getattr(frappe.local, "site", None)
    if (frappe.session.user != "Administrator"
            or not _flag("cc_synthetic_dev")
            or not _flag("cc_presentation_seed")
            or not site
            or frappe.conf.get("cc_presentation_site") != site):
        frappe.throw("Fixture cliente: solo Administrator del sito STAGING esplicitamente autorizzato.",
                     frappe.PermissionError)
    if not _flag("mute_emails"):
        frappe.throw("Disabilita l'email in uscita nel site_config prima del caricamento.")
    if (frappe.db.get_single_value("Healthcare Settings", "send_registration_msg")
            or frappe.db.get_single_value("Healthcare Settings", "collect_registration_fee")):
        frappe.throw("Disattiva SMS e tariffe di registrazione Healthcare prima del caricamento.")
    from centrochange_core.finance.guards import require_synthetic
    require_synthetic()
    if require_backup and not re.fullmatch(r"[0-9a-f]{64}", str(frappe.conf.get("cc_presentation_backup_sha256") or "")):
        frappe.throw("Registra nel site_config lo SHA-256 del backup cifrato già verificato.")


def _private_path():
    parent = Path(frappe.get_site_path("private", "uat"))
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(parent, 0o700)
    return parent / MANIFEST


@contextmanager
def _exclusive():
    lock = _private_path().with_suffix(".lock")
    with lock.open("a") as stream:
        os.chmod(lock, 0o600)
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def _checks(data):
    assert data["schema"] == "centrochange-presentation-v1"
    assert len(data["professionals"]) == 4
    assert len(data["patients"]) == 18
    assert len(data["payers"]) == 17
    assert len(data["appointments"]) == 35
    count = lambda key: sum(1 for a in data["appointments"] if a["service"] == key)
    assert count("FIRST") == 10 and count("SESSION") == 25
    assert sum(a["state"] == "future" for a in data["appointments"]) == 10
    assert all(str(p["email"]).endswith("@presentation.example.invalid") for p in data["patients"] + data["professionals"])
    assert all(p["payer"] in {x["id"] for x in data["payers"]} for p in data["patients"])
    assert len({p["id"] for p in data["patients"]}) == 18


def _site_counts():
    doctypes = ("Patient", "Healthcare Practitioner", "Customer", "Patient Appointment",
                "CC Economic Source Link", "CC Operational Receipt", "Sales Invoice",
                "Payment Entry", "GL Entry")
    return {doctype: frappe.db.count(doctype) for doctype in doctypes}


def _services(center, data):
    from decimal import Decimal
    from centrochange_core.scheduling.booking import snapshot
    rows = frappe.get_all("CC Center Service", filters={"center": center, "enabled": 1},
                          fields=["appointment_type"], page_length=100)
    resolved = {}
    for item in data["services"]:
        recipe = data["services"][item]
        matching = []
        for row in rows:
            profile = frappe.get_doc("Appointment Type", row.appointment_type)
            if not profile.cc_service_item:
                continue
            label = frappe.db.get_value("Item", profile.cc_service_item, "item_name") or ""
            if (label.strip().casefold() == recipe["label"].casefold()
                    and int(profile.default_duration or 0) == recipe["minutes"]
                    and bool(profile.cc_first_meeting) == (item == "FIRST")):
                value = snapshot(profile.name, center)
                if (Decimal(str(value["cc_price_snapshot"])).quantize(Decimal("0.01")) == Decimal(recipe["eur"])
                        and value["cc_currency_snapshot"] == data["currency"]):
                    matching.append(profile.name)
        if len(matching) != 1:
            frappe.throw("Il listino/sede deve avere un solo servizio coerente: "
                         + recipe["label"] + ", " + str(recipe["minutes"]) + " minuti, €" + recipe["eur"])
        resolved[item] = matching[0]
    return resolved


def _preflight(center, data):
    _guard()
    if not center or not frappe.db.exists("Branch", center):
        frappe.throw("Indica esplicitamente una sede già esistente.")
    if not frappe.db.get_value("Branch", center, "cc_operational"):
        frappe.throw("La sede selezionata non è operativa.")
    if datetime.now(ROME).date() >= datetime(2026, 11, 9).date():
        frappe.throw("La data della presentazione è scaduta: rigenera e approva un nuovo calendario.")
    _checks(data)
    counts = _site_counts()
    if any(counts.values()):
        frappe.throw("Il sito contiene già record anagrafici o economici: nessun caricamento consentito.")
    if frappe.db.exists("User", {"email": ["like", "%@presentation.example.invalid"]}):
        frappe.throw("Esistono già account della presentazione, ma manca il manifesto.")
    if not frappe.db.exists("Gender", "Male") or not frappe.db.exists("Gender", "Female"):
        frappe.throw("Configurare Gender Male e Female prima di procedere.")
    # Fail before creating users/suppliers if ERPNext's selling defaults are not usable.
    group = frappe.db.get_single_value("Selling Settings", "customer_group")
    if not group or frappe.db.get_value("Customer Group", group, "is_group"):
        frappe.throw("Configura un gruppo clienti ERPNext ordinario, non una categoria aggregata.")
    if not frappe.db.get_value("Mode of Payment", "Contanti", "enabled"):
        frappe.throw("Serve il metodo di pagamento informativo Contanti, attivo.")
    from centrochange_core.dev_bootstrap import COMPANY
    if frappe.db.get_single_value("Global Defaults", "default_company") != COMPANY:
        frappe.throw("La società predefinita non è quella sintetica autorizzata.")
    return {"services": _services(center, data), "counts": counts}


def _read_manifest(path, data):
    if path.is_symlink():
        frappe.throw("Percorso manifesto non sicuro.")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("dataset_sha256") != _digest(data):
        frappe.throw("La ricetta è cambiata: revisione manuale obbligatoria.")
    for doctype, names in record["created"].items():
        for name in names:
            if not frappe.db.exists(doctype, name):
                frappe.throw("Manifesto presente ma record mancante: non ripetere il caricamento.")
    return {"status": "EXISTS", "counts": record["counts"], "dataset_sha256": record["dataset_sha256"]}


def plan(center):
    """Read-only preflight. The returned digest is the explicit apply approval."""
    data = _fixture()
    _guard()
    path = _private_path()
    if path.is_file():
        return _read_manifest(path, data)
    result = _preflight(center, data)
    return {"status": "READY", "center": center, "dataset_sha256": _digest(data),
            "services": result["services"], "counts": data["expected_counts"],
            "outbound": "disabled", "fiscal": "not generated", "commit": False}


class HistoricalBookingClock(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 10, 1, 8, tzinfo=ROME)
        return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)


def _make_customer(name):
    group = frappe.db.get_single_value("Selling Settings", "customer_group")
    if not group or frappe.db.get_value("Customer Group", group, "is_group"):
        frappe.throw("Configura un gruppo clienti non aggregato prima del caricamento.")
    doc = frappe.get_doc({"doctype": "Customer", "customer_name": name,
        "customer_type": "Individual", "customer_group": group,
        "territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"})
    return doc.insert(ignore_permissions=True, ignore_mandatory=True).name


def _make_user(person):
    from centrochange_core.security.lifecycle import set_membership
    with internal_write("cc_user_roles_write"):
        frappe.get_doc({"doctype": "User", "email": person["email"],
                        "first_name": person["first_name"], "last_name": person["last_name"],
                        "enabled": 1, "language": "it", "send_welcome_email": 0,
                        "roles": [{"role": "CC Professional"}]}).insert(ignore_permissions=True)
    return person["email"]


def _build(center, data, services):
    from centrochange_core.security.lifecycle import set_membership, set_assignment
    from centrochange_core.scheduling.availability import set_schedule
    from centrochange_core.scheduling import booking
    from centrochange_core.operations import lifecycle
    from centrochange_core.finance import bridge, operational_receipts
    from centrochange_core.finance.guards import require_synthetic

    require_synthetic()
    created = {doctype: [] for doctype in ("User", "Healthcare Practitioner", "Patient",
        "Customer", "Patient Appointment", "CC Economic Source Link", "CC Operational Receipt",
        "Practitioner Schedule", "Supplier", "Cost Center")}
    users, professionals, patients, customers, appointments = {}, {}, {}, {}, {}
    reason = REASON
    original_email_count = frappe.db.count("Email Queue")
    for person in data["professionals"]:
        user = _make_user(person)
        created["User"].append(user)
        set_membership(user, center, 1, reason)
        with internal_write("cc_practitioner_center_write"):
            doc = frappe.get_doc({"doctype": "Healthcare Practitioner",
                    "first_name": person["first_name"], "last_name": person["last_name"],
                    "status": "Active", "user_id": user, "cc_profile_center": center}).insert(ignore_permissions=True)
        professionals[person["id"]] = doc.name
        users[person["id"]] = user
        created["Healthcare Practitioner"].append(doc.name)
        slots = [{"day": day, "from_time": start, "to_time": end}
                 for day in person["weekdays"]
                 for start, end in (data["availability"]["morning"], data["availability"]["afternoon"])]
        schedule = set_schedule(doc.name, center, slots, reason)["name"]
        created["Practitioner Schedule"].append(schedule)
    center_before = frappe.db.get_value("Branch", center, "cc_cost_center")
    center_map = bridge.map_center(center, reason)
    if not center_before:
        created["Cost Center"].append(center_map["cost_center"])
    for professional in professionals.values():
        supplier = bridge.map_practitioner(professional, center, reason)["supplier"]
        created["Supplier"].append(supplier)

    third_party = next(x for x in data["payers"] if x["kind"] == "external")
    customers[third_party["id"]] = _make_customer(third_party["display_name"])
    created["Customer"].append(customers[third_party["id"]])
    # No real fiscal identifiers or TS consent are fabricated.
    native_auto_customer = bool(frappe.db.get_single_value("Healthcare Settings", "link_customer_to_patient"))
    for person in data["patients"]:
        customer_id = customers.get(person["payer"])
        if customer_id is None and not native_auto_customer:
            customer_id = _make_customer(person["first_name"] + " " + person["last_name"])
        identity = {
            "doctype": "Patient", "first_name": person["first_name"], "last_name": person["last_name"],
            "sex": person["gender"], "dob": person["dob"], "uid": data["ownership_tag"] + "-" + person["id"],
            "email": person["email"], "invite_user": 0,
            "cc_external_payer": 1 if person["payer"] == third_party["id"] else 0,
            "cc_fiscal_mapping_confirmed": 1,
            "cc_intake_key": sha256((data["ownership_tag"] + ":" + person["id"]).encode()).hexdigest(),
            "cc_intake_hash": sha256((person["id"] + ":" + person["payer"]).encode()).hexdigest(),
        }
        if customer_id:
            identity["customer"] = customer_id
        with internal_write("cc_finance_mapping_write"), internal_write("cc_patient_intake_write"):
            doc = frappe.get_doc(identity).insert(ignore_permissions=True)
        doc.reload()
        if not doc.customer or (customer_id and doc.customer != customer_id):
            frappe.throw("Collegamento Customer incoerente: salvataggio annullato.")
        patients[person["id"]] = doc.name
        if person["payer"] not in customers:
            customers[person["payer"]] = doc.customer
            created["Customer"].append(doc.customer)
        set_assignment(doc.name, center, professionals[person["practitioner"]], 1, reason)
        created["Patient"].append(doc.name)

    with patch("centrochange_core.scheduling.booking.datetime", HistoricalBookingClock):
        for spec in sorted(data["appointments"], key=lambda a: (a["date"], a["time"], a["id"])):
            patient = next(x for x in data["patients"] if x["id"] == spec["patient"])
            result = booking.book(patients[spec["patient"]], professionals[patient["practitioner"]],
                center, services[spec["service"]], spec["date"], spec["time"],
                data["ownership_tag"] + "-" + spec["id"], reason)
            appointments[spec["id"]] = result["name"]
            created["Patient Appointment"].append(result["name"])

    for spec in data["appointments"]:
        if spec["state"] == "future" or spec["state"] == "outcome_pending":
            continue
        doc = frappe.get_doc("Patient Appointment", appointments[spec["id"]])
        start = lifecycle.start_utc(doc)
        if spec["state"] == "cancelled_timely":
            frappe.flags.cc_test_clock = start - timedelta(hours=72)
            lifecycle.cancel(doc.name, reason)
            continue
        frappe.flags.cc_test_clock = start + timedelta(minutes=int(doc.duration) + 60)
        lifecycle.close(doc.name, 0, reason)
        if spec["service"] == "FIRST":
            lifecycle.waive(doc.name, "Primo colloquio gratuito")
        if spec["state"] in ("paid", "partial"):
            operational_receipts.record(
                patients[spec["patient"]], center, spec["date"], "Contanti", reason,
                data["ownership_tag"] + "-RECEIPT-" + spec["id"],
                [{"appointment": doc.name, "amount": "44.00" if spec["state"] == "paid"
                  else spec["paid_eur"]}])
    frappe.flags.cc_test_clock = None
    # Capture projections only after outcomes and operational receipts are final.
    for appointment in appointments.values():
        link = bridge.capture(appointment, reason)["name"]
        created["CC Economic Source Link"].append(link)
    created["CC Operational Receipt"] = frappe.get_all(
        "CC Operational Receipt", filters={"center": center}, pluck="name")
    if frappe.db.count("Email Queue") != original_email_count:
        frappe.throw("Il caricamento ha generato email: annullamento obbligatorio.")
    if len(set(customers.values())) != 17 or len(professionals) != 4 or len(patients) != 18 or len(appointments) != 35:
        frappe.throw("Cardinalità del dataset non corrispondente.")
    if len(created["CC Operational Receipt"]) != 10:
        frappe.throw("Le dieci ricevute operative non risultano coerenti.")
    if frappe.db.count("Sales Invoice") or frappe.db.count("Payment Entry") or frappe.db.count("GL Entry"):
        frappe.throw("Sono stati prodotti documenti/movimenti contabili: annullamento obbligatorio.")
    append("PRESENTATION_DATASET_LOADED", "Branch", center, None,
        {"schema": data["schema"], "dataset_hash": _digest(data),
         "professionals": len(professionals), "patients": len(patients),
         "payers": len(set(customers.values())), "appointments": len(appointments)}, reason)
    return created


@dev_acceptance.synthetic_test
def apply(center, approval_sha256, backup_sha256):
    """Never call through HTTP. Run only via bench execute after preflight/backup."""
    _guard(require_backup=True)
    data = _fixture()
    if not approval_sha256 or approval_sha256 != _digest(data):
        frappe.throw("Il digest approvato non corrisponde al dataset.")
    if not backup_sha256 or backup_sha256 != frappe.conf.get("cc_presentation_backup_sha256"):
        frappe.throw("Il backup cifrato verificato non coincide con l'attestazione del sito.")
    with _exclusive():
        path = _private_path()
        if path.is_file():
            return _read_manifest(path, data)
        previous_clock = frappe.flags.get("cc_test_clock")
        try:
            ready = _preflight(center, data)
            created = _build(center, data, ready["services"])
            manifest = {"schema": data["schema"], "dataset_sha256": _digest(data),
                        "center": center, "counts": data["expected_counts"],
                        "created": created, "backup_sha256": backup_sha256}
            temp = path.with_suffix(".tmp")
            with temp.open("w", encoding="utf-8") as stream:
                os.chmod(temp, 0o600)
                json.dump(manifest, stream, sort_keys=True, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            temp.replace(path)
            frappe.db.commit()
            return {"status": "PASS", "dataset_sha256": _digest(data),
                    "counts": data["expected_counts"], "center": center}
        except Exception:
            frappe.db.rollback()
            path.unlink(missing_ok=True)
            path.with_suffix(".tmp").unlink(missing_ok=True)
            raise
        finally:
            frappe.flags.cc_test_clock = previous_clock
            frappe.set_user("Administrator")


def inspect():
    """Read-only manifest check; no reset or mass deletion is exposed."""
    _guard()
    data = _fixture()
    path = _private_path()
    if not path.is_file():
        return {"status": "NOT_LOADED", "dataset_sha256": _digest(data)}
    return _read_manifest(path, data)
