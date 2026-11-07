"""Deterministic offline checks for the guarded client-presentation dataset.

No Frappe dependency and no database or network access.
"""
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "app/centrochange_core/centrochange_core/uat/presentation_dataset_v1.json"


def load():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def verify(data):
    assert data["schema"] == "centrochange-presentation-v1"
    assert data["ownership_tag"] == "CC-PRESENTATION-20261107-V1"
    assert data["site_scope"].startswith("STAGING ONLY")
    assert data["currency"] == "EUR"
    assert data["services"] == {
        "FIRST": {"label": "Primo colloquio conoscitivo", "minutes": 20, "eur": "0.00"},
        "SESSION": {"label": "Seduta", "minutes": 45, "eur": "44.00"},
    }
    pros = data["professionals"]
    patients = data["patients"]
    payers = data["payers"]
    entries = data["appointments"]
    assert len(pros) == 4 and len(patients) == 18 and len(payers) == 17 and len(entries) == 35
    for field, rows in (("professionals", pros), ("patients", patients), ("payers", payers),
                        ("appointments", entries)):
        assert len({x["id"] for x in rows}) == len(rows), field
    pro_by_id = {r["id"]: r for r in pros}
    patient_by_id = {r["id"]: r for r in patients}
    payer_by_id = {r["id"]: r for r in payers}
    assert len({p["email"] for p in pros}) == 4
    for person in pros + patients:
        assert person["email"].endswith("@presentation.example.invalid")
        assert person["first_name"] and person["last_name"]
        assert not any(word in (person["first_name"] + " " + person["last_name"]).casefold()
                       for word in ("demo", "test", "prova", "synthetic"))
    for professional in pros:
        assert professional["weekdays"]
        assert set(professional["weekdays"]).issubset(
            {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"})
    for patient in patients:
        assert patient["practitioner"] in pro_by_id and patient["payer"] in payer_by_id
        assert patient["gender"] in ("Male", "Female")
        assert date.fromisoformat(patient["dob"]) < date.fromisoformat(data["as_of"])
        payer = payer_by_id[patient["payer"]]
        if payer["kind"] == "patient_self":
            assert payer["patient"] == patient["id"]
            assert payer["display_name"] == patient["first_name"] + " " + patient["last_name"]
        else:
            assert payer["kind"] == "external"
            assert patient["id"] in payer["patients"]
    assert sum(p["kind"] == "patient_self" for p in payers) == 16
    assert sum(p["kind"] == "external" for p in payers) == 1
    assert set(p["id"] for p in patients[-2:]) == set(next(x for x in payers if x["kind"] == "external")["patients"])

    seen = Counter()
    first_meetings = {}
    timing = {}
    minutes_by_service = {key: row["minutes"] for key, row in data["services"].items()}
    for entry in entries:
        patient = patient_by_id[entry["patient"]]
        pro = pro_by_id[patient["practitioner"]]
        kind, state = entry["service"], entry["state"]
        assert kind in minutes_by_service
        start = datetime.fromisoformat(entry["date"] + "T" + entry["time"])
        assert start.strftime("%A") in pro["weekdays"]
        duration = timedelta(minutes=minutes_by_service[kind])
        finish = start + duration
        windows = [(datetime.combine(start.date(), datetime.strptime(a, "%H:%M").time()),
                    datetime.combine(start.date(), datetime.strptime(b, "%H:%M").time()))
                   for a, b in (data["availability"]["morning"], data["availability"]["afternoon"])]
        assert any(a <= start and finish <= b for a, b in windows)
        assert state in {"past_completed", "paid", "partial", "unpaid",
                         "cancelled_timely", "outcome_pending", "future"}
        as_of = date.fromisoformat(data["as_of"])
        if state == "future":
            assert start.date() > as_of
        else:
            assert start.date() < as_of
        if kind == "FIRST":
            assert state in ("past_completed", "future")
            assert patient["id"] not in first_meetings
            first_meetings[patient["id"]] = start
        else:
            assert state != "past_completed"
        if state == "partial":
            assert kind == "SESSION"
            assert Decimal("0.00") < Decimal(entry["paid_eur"]) < Decimal("44.00")
        else:
            assert "paid_eur" not in entry
        for previous_start, previous_finish, previous_pro, previous_patient in timing.get(start.date(), []):
            if pro["id"] == previous_pro or patient["id"] == previous_patient:
                assert finish <= previous_start or start >= previous_finish, entry["id"]
        timing.setdefault(start.date(), []).append(
            (start, finish, pro["id"], patient["id"]))
        seen[(kind, state)] += 1
    for entry in entries:
        if entry["service"] == "SESSION" and entry["patient"] in first_meetings:
            session_date = datetime.fromisoformat(entry["date"] + "T" + entry["time"])
            assert first_meetings[entry["patient"]] < session_date
    assert seen == Counter({
        ("FIRST", "past_completed"): 7, ("FIRST", "future"): 3,
        ("SESSION", "paid"): 8, ("SESSION", "partial"): 2, ("SESSION", "unpaid"): 3,
        ("SESSION", "cancelled_timely"): 2, ("SESSION", "outcome_pending"): 3,
        ("SESSION", "future"): 7,
    })
    expected = data["expected_counts"]
    assert expected["professionals"] == 4 and expected["professional_accounts"] == 4
    assert expected["patients"] == 18 and expected["payers"] == 17
    assert expected["appointments"] == 35 and expected["first_meetings"] == 10
    assert expected["sessions"] == 25 and expected["future_sessions"] == 7
    return {"status": "PASS", "professionals": 4, "patients": 18,
            "payers": 17, "appointments": 35, "breakdown": dict(
                sorted((f"{kind}/{state}", count) for (kind, state), count in seen.items()))}


if __name__ == "__main__":
    print(json.dumps(verify(load()), indent=2, sort_keys=True))
