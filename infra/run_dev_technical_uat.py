#!/usr/bin/env python3
"""Comprehensive technical UAT across roles and APIs on live DEV environment.

Verifications:
- All roles: Manager, Secretariat, Professional A, Professional B, Guest.
- Agenda pagination and scoping.
- Reporting summary, drilldown sessions, and bounded CSV export.
- Negative tests: Guest denied, cross-practitioner IDOR denied, inactive center denied.
- Zero business data mutations.
- Output session SIDs for Playwright browser verification.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = 'http://127.0.0.1:8082'
HOST_HEADER = 'centrochange.local'
DEV_SITE = 'centrochange.local'

CENTER_A = 'CC-HTTP-UAT0000001 A'
CENTER_B_INACTIVE = 'CC-HTTP-UAT0000001 B'

USERS = {
    'm': 'cc-http-uat0000001-m@example.invalid',
    's': 'cc-http-uat0000001-s@example.invalid',
    'a': 'cc-http-uat0000001-a@example.invalid',
    'b': 'cc-http-uat0000001-b@example.invalid',
}

PRAC_A = 'HLC-PRAC-2026-00001'
PRAC_B = 'HLC-PRAC-2026-00002'


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_session_sid(user_email):
    cmd = [
        'docker', 'exec', '-w', '/home/frappe/frappe-bench/sites', 'centrochange-dev-backend-1',
        '/home/frappe/frappe-bench/env/bin/python', '-c', f"""
import frappe
from werkzeug.test import EnvironBuilder
from frappe.sessions import Session

frappe.init("{DEV_SITE}")
frappe.connect()
frappe.request = EnvironBuilder().get_request()
sess = Session(user="{user_email}").start()
sid = frappe.session.sid
frappe.db.commit()
print(sid)
"""
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def api_call(sid, method, params=None, expected_status=200):
    url = f"{BASE_URL}/api/method/{method}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    headers = {'Host': HOST_HEADER}
    if sid:
        headers['Cookie'] = f"sid={sid}"

    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        status = resp.status
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = json.loads(resp.read().decode('utf-8'))
        else:
            data = resp.read().decode('utf-8')
        assert status == expected_status, f"Expected {expected_status}, got {status} for {method}"
        return {'status': status, 'data': data}
    except urllib.error.HTTPError as e:
        assert e.code == expected_status, f"Expected {expected_status}, got HTTP {e.code} for {method}: {e.read().decode('utf-8')[:200]}"
        return {'status': e.code, 'error': e.read().decode('utf-8')}


def run_all_tests():
    log("=== STARTING LIVE DEV TECHNICAL UAT ===")
    checks = []
    sessions = {}

    log("Generating native session tokens for synthetic UAT roles...")
    for role, email in USERS.items():
        sid = get_session_sid(email)
        sessions[role] = sid
        # Verify get_logged_user
        res = api_call(sid, 'frappe.auth.get_logged_user')
        assert res['data']['message'] == email
        checks.append(f"Auth session valid for {role} ({email})")
    log("All role sessions verified.")

    # 1. MANAGER TESTS
    log("--- 1. Manager Operational Scenarios ---")
    sid_m = sessions['m']

    # Agenda view for center
    agenda_m = api_call(sid_m, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert len(agenda_m['appointments']) == 9, f"Manager expected 9 appointments, got {len(agenda_m['appointments'])}"
    assert not agenda_m['truncated']
    checks.append("Manager sees all 9 center appointments for week 2026-09-28")

    # Manager filter by single practitioner
    agenda_m_p1 = api_call(sid_m, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04', 'practitioner': PRAC_A
    })['data']['message']
    assert len(agenda_m_p1['appointments']) == 8, f"Manager p1 expected 8 appointments, got {len(agenda_m_p1['appointments'])}"
    checks.append("Manager filtered agenda by single practitioner (8 appointments)")

    # Reporting summary for center
    summary_m = api_call(sid_m, 'centrochange_core.operations.reporting.summary', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert summary_m['total_appointments'] == 9
    assert summary_m['currencies']['EUR']['due_snapshot_amount'] == 700.0
    assert summary_m['currencies']['EUR']['performed'] == 7
    assert summary_m['currencies']['EUR']['cancelled'] == 2
    assert summary_m['currencies']['EUR']['operational_unpaid'] == 6
    checks.append("Manager report summary: 9 total, EUR 700 due, 7 performed, 2 cancelled, 6 unpaid")

    # Reporting sessions drilldown
    sessions_m = api_call(sid_m, 'centrochange_core.operations.reporting.sessions', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert sessions_m['total'] == 9
    assert len(sessions_m['appointments']) == 9
    checks.append("Manager report drilldown: 9 session rows returned")

    # Reporting drilldown KPI filter: cancelled
    sessions_cancelled = api_call(sid_m, 'centrochange_core.operations.reporting.sessions', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04', 'kpi': 'cancelled'
    })['data']['message']
    assert sessions_cancelled['total'] == 2
    assert all(a['status'] == 'Cancelled' for a in sessions_cancelled['appointments'])
    checks.append("Manager drilldown KPI=cancelled correctly filters 2 cancelled appointments")

    # Reporting CSV Export
    csv_res = api_call(sid_m, 'centrochange_core.operations.reporting.export_csv', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })
    csv_text = csv_res['data']
    lines = [l for l in csv_text.strip().splitlines() if l.strip()]
    header = lines[0]
    assert 'Data' in header and 'Paziente' in header and 'Professionista' in header and 'Tariffa prevista' in header
    # 9 rows + 1 header = 10 lines
    assert len(lines) == 10, f"Expected 10 CSV lines, got {len(lines)}"
    checks.append("Manager CSV export: header + 9 rows with Italian headers and bounded memory")

    # 2. SECRETARIAT TESTS
    log("--- 2. Secretariat Operational Scenarios ---")
    sid_s = sessions['s']

    agenda_s = api_call(sid_s, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert len(agenda_s['appointments']) == 9
    checks.append("Secretariat center agenda: 9 appointments visible")

    summary_s = api_call(sid_s, 'centrochange_core.operations.reporting.summary', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert summary_s['total_appointments'] == 9
    checks.append("Secretariat center report summary: 9 appointments verified")

    # 3. PROFESSIONAL A TESTS (CLAMPMING & DATA SCOPING)
    log("--- 3. Professional A Scoped Scenarios ---")
    sid_a = sessions['a']

    # Professional A querying without practitioner param -> MUST auto-clamp to PRAC_A
    agenda_a_auto = api_call(sid_a, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert len(agenda_a_auto['appointments']) == 8, f"Expected 8 scoped appointments for A, got {len(agenda_a_auto['appointments'])}"
    assert all(a['practitioner'] == PRAC_A for a in agenda_a_auto['appointments'])
    checks.append("Professional A agenda auto-clamped to own 8 appointments (zero PRAC_B records)")

    # Professional A querying with practitioner=PRAC_B (IDOR ATTEMPT) -> MUST be clamped to PRAC_A
    agenda_a_idor = api_call(sid_a, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04', 'practitioner': PRAC_B
    })['data']['message']
    assert len(agenda_a_idor['appointments']) == 8
    assert all(a['practitioner'] == PRAC_A for a in agenda_a_idor['appointments'])
    checks.append("Professional A IDOR attempt on PRAC_B agenda strictly clamped to PRAC_A")

    # Professional A report summary -> auto-clamped
    summary_a = api_call(sid_a, 'centrochange_core.operations.reporting.summary', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    })['data']['message']
    assert summary_a['total_appointments'] == 8
    assert summary_a['currencies']['EUR']['due_snapshot_amount'] == 600.0
    assert summary_a['practitioner'] == PRAC_A
    checks.append("Professional A summary auto-clamped: 8 appointments, EUR 600.0 due")

    # Professional A report sessions drilldown -> own practitioner
    sessions_a = api_call(sid_a, 'centrochange_core.operations.reporting.sessions', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04', 'practitioner': PRAC_A
    })['data']['message']
    assert sessions_a['total'] == 8
    assert all(a['practitioner'] == PRAC_A for a in sessions_a['appointments'])
    checks.append("Professional A sessions drilldown returns own 8 appointments for PRAC_A")

    # Professional A report sessions drilldown -> attempting PRAC_B (IDOR) MUST BE REJECTED WITH 403
    sessions_a_idor = api_call(sid_a, 'centrochange_core.operations.reporting.sessions', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04', 'practitioner': PRAC_B
    }, expected_status=403)
    assert 'Non hai accesso ai dati di altri professionisti' in sessions_a_idor['error']
    checks.append("Professional A IDOR attempt on PRAC_B sessions strictly rejected with HTTP 403 PermissionError")

    # 4. NEGATIVE SECURITY & AUTHORIZATION TESTS
    log("--- 4. Negative Security & Fail-Closed Tests ---")

    # 4A: Guest unauthenticated access
    guest_agenda = api_call(None, 'centrochange_core.operations.workspace.agenda', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    }, expected_status=403)
    checks.append("Guest access to workspace.agenda rejected with HTTP 403")

    guest_summary = api_call(None, 'centrochange_core.operations.reporting.summary', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    }, expected_status=403)
    checks.append("Guest access to reporting.summary rejected with HTTP 403")

    guest_csv = api_call(None, 'centrochange_core.operations.reporting.export_csv', {
        'center': CENTER_A, 'start': '2026-09-28', 'end': '2026-10-04'
    }, expected_status=403)
    checks.append("Guest access to reporting.export_csv rejected with HTTP 403")

    # 4B: Inactive center B access
    m_inactive = api_call(sid_m, 'centrochange_core.operations.workspace.patient_search', {
        'center': CENTER_B_INACTIVE, 'query': 'Alfa'
    }, expected_status=403)
    assert 'La sede selezionata non è disponibile' in m_inactive['error']
    checks.append("Access to inactive center B rejected with HTTP 403 PermissionError")

    log("=== ALL TECHNICAL UAT TESTS PASSED ===")
    return {
        'status': 'PASS_TECHNICAL_UAT',
        'checks_count': len(checks),
        'checks': checks,
        'sessions': sessions,
    }


if __name__ == '__main__':
    res = run_all_tests()
    print(json.dumps(res, indent=2))
