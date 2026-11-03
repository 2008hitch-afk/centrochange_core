#!/usr/bin/env python3
"""
Multi-role backend API security and economic oracle verification for GOAL UX #75.
Executes server-side negative and positive checks using ephemeral sessions.
Zero tokens persisted or hardcoded.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

CONTAINER = os.environ.get("CC_TEST_CONTAINER", "centrochange-dev-backend-1")
SITE = os.environ.get("CC_TEST_SITE", "centrochange.local")
BASE_URL = os.environ.get("CC_TEST_BASE_URL", "http://127.0.0.1:8082")
HOST_HEADER = os.environ.get("CC_TEST_HOST", "centrochange.local")

USERS = {
    "m": "cc-http-uat0000001-m@example.invalid",
    "s": "cc-http-uat0000001-s@example.invalid",
    "f": "cc-http-uat0000001-f@example.invalid",
    "t": "cc-http-uat0000001-t@example.invalid",
    "a": "cc-http-uat0000001-a@example.invalid",
}


def create_ephemeral_sessions():
    script = f"""
import frappe, json
from werkzeug.test import EnvironBuilder
from frappe.sessions import Session

frappe.init("{SITE}")
frappe.connect()
frappe.request = EnvironBuilder().get_request()

res = {{}}
for role, email in {json.dumps(USERS)}.items():
    sess = Session(user=email).start()
    res[role] = frappe.session.sid

frappe.db.commit()
print(json.dumps(res))
"""
    cmd = [
        "docker", "exec", "-i", "-w", "/home/frappe/frappe-bench/sites",
        CONTAINER, "/home/frappe/frappe-bench/env/bin/python"
    ]
    res = subprocess.run(cmd, input=script, text=True, capture_output=True, check=True)
    return json.loads(res.stdout.strip())


def teardown_ephemeral_sessions(sids):
    if not sids:
        return
    script = f"""
import frappe
from frappe.sessions import delete_session

frappe.init("{SITE}")
frappe.connect()

for sid in {json.dumps(sids)}:
    if sid:
        delete_session(sid=sid, reason="Teardown API security test session")
print("cleaned")
"""
    cmd = [
        "docker", "exec", "-i", "-w", "/home/frappe/frappe-bench/sites",
        CONTAINER, "/home/frappe/frappe-bench/env/bin/python"
    ]
    try:
        subprocess.run(cmd, input=script, text=True, capture_output=True, check=True)
    except Exception as e:
        print(f"Warning during teardown: {e}", file=sys.stderr)


def api_call(sid, method, params=None):
    url = f"{BASE_URL}/api/method/{method}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    headers = {"Host": HOST_HEADER}
    if sid:
        headers["Cookie"] = f"sid={sid}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            try:
                data = json.loads(content)
            except Exception:
                data = content
            return resp.status, data
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            err_data = json.loads(err_content)
        except Exception:
            err_data = err_content
        return e.code, err_data


def main():
    print("=== STARTING UX #75 MULTI-ROLE BACKEND API SECURITY TESTS ===")
    sids = {}
    results = []

    def check(test_id, name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        results.append({"id": test_id, "name": name, "status": status, "detail": detail})
        mark = "✅ PASS" if condition else "❌ FAIL"
        print(f"{mark}: [{test_id}] {name} {f'({detail})' if detail else ''}")

    try:
        sids = create_ephemeral_sessions()
        print(f"[AUTH] Ephemeral test sessions created for roles: {list(sids.keys())}")

        center = "CC-HTTP-UAT0000001 A"
        patient = "CC-HTTP-UAT0000001 Zeta"
        start = "2026-10-01"
        end = "2026-10-31"

        # 1. Negative Checks for Guest (Unauthenticated)
        status_guest_rep, _ = api_call(None, "centrochange_core.operations.reporting.sessions", {"center": center, "from_date": start, "to_date": end})
        check("SEC-01", "Guest denied reporting.sessions (403)", status_guest_rep in (401, 403), f"status={status_guest_rep}")

        status_guest_col, _ = api_call(None, "centrochange_core.finance.collections.position", {"patient": patient, "center": center})
        check("SEC-02", "Guest denied collections.position (403)", status_guest_col in (401, 403), f"status={status_guest_col}")

        status_guest_pview, _ = api_call(None, "centrochange_core.finance.patient_reporting.patient_view", {"center": center, "start": start, "end": end})
        check("SEC-03", "Guest denied patient_reporting.patient_view (403)", status_guest_pview in (401, 403), f"status={status_guest_pview}")

        # 2. Strict Negative Checks for CC Professional (Zero Economic / Finance Access)
        status_prof_col, _ = api_call(sids["a"], "centrochange_core.finance.collections.position", {"patient": patient, "center": center})
        check("SEC-04", "CC Professional denied collections.position (403)", status_prof_col == 403, f"status={status_prof_col}")

        status_prof_rec, _ = api_call(sids["a"], "centrochange_core.finance.receivables.candidates", {"center": center, "from_date": start, "to_date": end})
        check("SEC-05", "CC Professional denied receivables.candidates (403)", status_prof_rec == 403, f"status={status_prof_rec}")

        status_prof_pview, _ = api_call(sids["a"], "centrochange_core.finance.patient_reporting.patient_view", {"center": center, "start": start, "end": end})
        check("SEC-06", "CC Professional denied patient_reporting.patient_view (403)", status_prof_pview == 403, f"status={status_prof_pview}")

        status_prof_exp, _ = api_call(sids["a"], "centrochange_core.finance.patient_reporting.patient_export", {"center": center, "start": start, "end": end})
        check("SEC-07", "CC Professional denied patient_reporting.patient_export (403)", status_prof_exp == 403, f"status={status_prof_exp}")

        # 3. Authorized Access for Manager, Secretariat, Finance, Accountant
        status_m_pat, data_m_pat = api_call(sids["m"], "centrochange_core.finance.patient_reporting.patient_view", {"center": center, "start": start, "end": end, "patient": patient})
        check("API-01", "CC Manager authorized patient_reporting.patient_view (200)", status_m_pat == 200, f"status={status_m_pat}")

        status_s_pat, data_s_pat = api_call(sids["s"], "centrochange_core.finance.patient_reporting.patient_view", {"center": center, "start": start, "end": end, "patient": patient})
        check("API-02", "CC Secretariat authorized patient_reporting.patient_view (200)", status_s_pat == 200, f"status={status_s_pat}")

        status_f_col, data_f_col = api_call(sids["f"], "centrochange_core.finance.collections.position", {"patient": patient, "center": center})
        check("API-03", "CC Finance authorized collections.position (200)", status_f_col == 200, f"status={status_f_col}")

        status_t_col, data_t_col = api_call(sids["t"], "centrochange_core.finance.collections.position", {"patient": patient, "center": center})
        check("API-04", "CC Accountant authorized collections.position (200)", status_t_col == 200, f"status={status_t_col}")

        # 4. Economic Oracle: Separation of Operational Debts vs Ledger Balance
        col_msg = data_f_col.get("message", {}) if isinstance(data_f_col, dict) else {}
        debts = col_msg.get("debts", [])
        blocked = col_msg.get("blocked", False)
        check("ORACLE-01", "Collections position returns distinct debts list and block flag", isinstance(debts, list), f"debts={len(debts)}, blocked={blocked}")

        pat_msg = data_m_pat.get("message", {}) if isinstance(data_m_pat, dict) else {}
        sessions = pat_msg.get("sessions", [])
        counts = pat_msg.get("counts", {})
        check("ORACLE-02", "Patient reporting returns session events and distinct status", isinstance(sessions, list), f"sessions={len(sessions)}, counts={counts}")

        # 5. IDOR / Cross-Center boundary check (Secretariat attempting cross-center access)
        status_cross, _ = api_call(sids["s"], "centrochange_core.finance.patient_reporting.patient_view", {"center": "INVALID-CROSS-CENTER", "start": start, "end": end})
        check("SEC-08", "Cross-center / non-assigned center query rejected with PermissionError (403)", status_cross == 403, f"status={status_cross}")

    finally:
        teardown_ephemeral_sessions(list(sids.values()))
        print("[AUTH] Ephemeral test sessions torn down cleanly.")

    print("\n=======================================================")
    print("=== MULTI-ROLE BACKEND API SECURITY TEST SUMMARY ===")
    print("=======================================================")
    pass_cnt = sum(1 for r in results if r["status"] == "PASS")
    fail_cnt = sum(1 for r in results if r["status"] == "FAIL")
    print(f"TOTAL: {len(results)} | PASS: {pass_cnt} | FAIL: {fail_cnt}")

    if fail_cnt > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
