"""Ephemeral GitHub Actions runner ONLY; no contact with client DEV/STAGING."""
from datetime import datetime, timedelta
import http.cookiejar
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
import test_audit09_isolated_clone as clone

root = Path(__file__).resolve().parent.parent
if os.environ.get("GITHUB_ACTIONS") != "true" or not os.environ.get("RUNNER_TEMP"):
    raise RuntimeError("AUDIT-11 isolated clone may run only on ephemeral GitHub Actions")
if os.environ.get("CC_CLONE_IMAGE") != "cc201-audit11-ci:local":
    raise RuntimeError("AUDIT-11 CI must run the locally built pinned candidate, not a legacy image")


def run_http_acceptance():
    """Real HTTP verification on the isolated clone container over port 8099."""
    port = clone.PORT
    base_url = f"http://127.0.0.1:{port}"
    host_header = "centrochange.local"
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    http_checks = []

    def request(path, data=None, csrf=None, method=None):
        url = f"{base_url}{path}"
        headers = {"Host": host_header, "Accept": "application/json"}
        payload = None
        if data is not None:
            payload = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if csrf:
            headers["X-Frappe-CSRF-Token"] = csrf
        req = urllib.request.Request(url, data=payload, headers=headers, method=method or ("POST" if data is not None else "GET"))
        try:
            with opener.open(req, timeout=20) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(body)
                except Exception:
                    parsed = {"raw": body}
                return status, parsed
        except urllib.error.HTTPError as error:
            status = error.code
            body = error.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return status, parsed

    # 1. Fetch /primo_incontro to extract CSRF token and set session cookie
    req_page = urllib.request.Request(f"{base_url}/primo_incontro", headers={"Host": host_header})
    with opener.open(req_page, timeout=20) as resp:
        page_html = resp.read().decode("utf-8")
    csrf_match = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', page_html)
    assert csrf_match, f"Failed to extract CSRF token from /primo_incontro HTML (length {len(page_html)}): {page_html[:500]}"
    csrf_token = csrf_match.group(1)
    assert csrf_token and len(csrf_token) >= 16, "Invalid CSRF token extracted"
    http_checks.append("guest_page_csrf_token_extracted")

    now = datetime.now(ZoneInfo("Europe/Rome")).date()
    next_monday = now + timedelta(days=(7 - now.weekday()) % 7 or 7)
    day = next_monday.isoformat()
    horizon_date = (now + timedelta(days=120)).isoformat()
    day_119 = (now + timedelta(days=119)).isoformat()
    too_far_date = (now + timedelta(days=121)).isoformat()
    past_date = (now - timedelta(days=1)).isoformat()

    # 2. GET available_slots for valid route and mode
    status, res = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=sede&start_date={day}")
    assert status == 200, f"available_slots returned {status}: {res}"
    msg = res.get("message", {})
    assert msg.get("route") == "Marco" and msg.get("mode") == "sede"
    assert msg.get("duration") == 20 and msg.get("price") == 0 and msg.get("currency") == "EUR"
    assert isinstance(msg.get("slots"), list) and len(msg["slots"]) > 0
    http_checks.append("http_get_available_slots_200")

    # 3. GET boundary checks (+120d, +119d, +121d, past, invalid mode)
    status_120, res_120 = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=sede&start_date={horizon_date}")
    assert status_120 == 200
    for s in res_120.get("message", {}).get("slots", []):
        assert s["date"] <= horizon_date, f"Slot {s['date']} leaked past horizon"
    http_checks.append("http_get_slots_120d_boundary_no_leak")

    status_119, res_119 = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=sede&start_date={day_119}")
    assert status_119 == 200
    for s in res_119.get("message", {}).get("slots", []):
        assert s["date"] <= horizon_date, f"Slot {s['date']} leaked past horizon from day 119"
    http_checks.append("http_get_slots_119d_boundary_no_leak")

    status_121, _ = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=sede&start_date={too_far_date}")
    assert status_121 in (417, 500), f"Expected 417/500 for +121d, got {status_121}"
    http_checks.append("http_get_slots_121d_rejected")

    status_past, _ = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=sede&start_date={past_date}")
    assert status_past in (417, 500), f"Expected 417/500 for past date, got {status_past}"
    http_checks.append("http_get_slots_past_date_rejected")

    status_invalid_mode, _ = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Marco&mode=unauthorized&start_date={day}")
    assert status_invalid_mode in (401, 403), f"Expected 403 for invalid mode, got {status_invalid_mode}"
    http_checks.append("http_get_slots_invalid_mode_denied")

    # 4. POST first_meeting with CSRF token (genuine public booking via guest form)
    free_slot = msg["slots"][-1]
    booking_payload = {
        "route": "Marco", "mode": "sede",
        "first_name": "HTTP Synthetic", "last_name": "Guest",
        "email": "cc11-http-guest@example.invalid", "sex": "Other",
        "appointment_date": free_slot["date"], "appointment_time": free_slot["time"],
        "request_key": "cc11-http-guest-key-1",
    }
    status_ok, res_ok = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting", data=booking_payload, csrf=csrf_token)
    assert status_ok == 200, f"first_meeting failed: {res_ok}"
    msg_ok = res_ok.get("message", {})
    assert msg_ok.get("replay") is False
    assert msg_ok.get("confirmation", {}).get("state") == "Simulated Sent"
    booking_name = msg_ok.get("name")
    assert booking_name, "No appointment name returned"
    http_checks.append("http_post_first_meeting_with_csrf_200_ok")

    # 5. POST first_meeting replay idempotency
    status_replay, res_replay = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting", data=booking_payload, csrf=csrf_token)
    assert status_replay == 200
    msg_replay = res_replay.get("message", {})
    assert msg_replay.get("replay") is True
    assert msg_replay.get("name") == booking_name
    http_checks.append("http_post_replay_idempotency_verified")

    # 6. POST guest unauthenticated ingress semantics (Frappe native guest handling)
    status_guest, res_guest = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting", data=booking_payload, csrf=None)
    assert status_guest == 200
    assert res_guest.get("message", {}).get("replay") is True
    http_checks.append("http_post_guest_native_semantics_verified")

    # 7. POST parameter manipulation and tampering
    status_bad_route, _ = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting",
                                  data={**booking_payload, "route": "Hacker", "request_key": "cc11-tamper-route"}, csrf=csrf_token)
    assert status_bad_route in (417, 500)
    http_checks.append("http_post_tampered_route_rejected")

    status_bad_mode, _ = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting",
                                 data={**booking_payload, "mode": "vip", "request_key": "cc11-tamper-mode"}, csrf=csrf_token)
    assert status_bad_mode in (417, 500)
    http_checks.append("http_post_tampered_mode_rejected")

    status_post_121, _ = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting",
                                 data={**booking_payload, "appointment_date": too_far_date, "request_key": "cc11-tamper-121"}, csrf=csrf_token)
    assert status_post_121 in (417, 500)
    http_checks.append("http_post_121d_rejected")

    # 8. POST email privacy & anti-enumeration (P1):
    # Booking with an email that is ALREADY registered as a patient must succeed with HTTP 200,
    # return the exact same response schema/status, and not leak identity existence or throw "L'identità esiste già".
    _, f_slots_res = request(f"/api/method/centrochange_core.scheduling.public_booking.available_slots?route=Francesca&mode=online&start_date={day}")
    f_slots = f_slots_res.get("message", {}).get("slots", [])
    assert f_slots, "No slots found for Francesca online"
    free_slot_dup = f_slots[-1]

    dup_email_payload = {
        "route": "Francesca", "mode": "online",
        "first_name": "Privacy Check", "last_name": "Guest",
        "email": "cc11-http-guest@example.invalid", # Already booked above!
        "sex": "Female",
        "appointment_date": free_slot_dup["date"], "appointment_time": free_slot_dup["time"],
        "request_key": "cc11-http-privacy-dup-key",
    }
    status_dup, res_dup = request("/api/method/centrochange_core.scheduling.public_booking.first_meeting", data=dup_email_payload, csrf=csrf_token)
    assert status_dup == 200, f"Privacy check failed with status {status_dup}: {res_dup}"
    msg_dup = res_dup.get("message", {})
    assert set(msg_dup.keys()) == set(msg_ok.keys()), "Response schema differed for duplicate email"
    assert msg_dup.get("replay") is False
    assert msg_dup.get("confirmation", {}).get("state") == "Simulated Sent"
    assert "esiste già" not in json.dumps(res_dup), "Email existence leaked in response body"
    http_checks.append("http_post_email_privacy_indistinguishable_200")

    return http_checks


try:
    clone.setup_clone(seed_audit11_types=True)
    backend = (root / "infra/audit11_clone_backend.py").read_text(encoding="utf-8")
    output = clone.run_cmd(
        ["docker", "exec", "-i", "-e", "FRAPPE_STREAM_LOGGING=1",
         "-w", "/home/frappe/frappe-bench", clone.BACKEND_CONTAINER,
         "env/bin/python", "-"],
        input_str=backend,
    )
    lines = [json.loads(line) for line in output.splitlines()
             if line.startswith("{") and '"status"' in line]
    assert len(lines) == 1 and lines[0].get("status") == "PASS", "No verified Frappe result"
    assert lines[0]["count"] == 4
    print("AUDIT11_NATIVE_FRAPPE_ISOLATED_PASS", json.dumps(lines[0]), flush=True)

    http_checks = run_http_acceptance()
    print("AUDIT11_HTTP_ISOLATED_PASS", json.dumps({"status": "PASS", "checks": http_checks}), flush=True)
finally:
    clone.cleanup()
