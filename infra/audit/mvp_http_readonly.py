#!/usr/bin/env python3
"""Observe approved role boundaries through HTTP; no business mutation."""
import http.cookiejar
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

fixture = json.loads(Path('/home/empv26/.local/state/centrochange-single/demo-owner.json').read_text())
base = 'http://127.0.0.1:8082'
results = []
for role, user in fixture['users'].items():
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(path, data=None):
        request = urllib.request.Request(base + path, data=urllib.parse.urlencode(data).encode() if data else None,
                                         headers={'Host': 'centrochange.local'})
        try:
            with client.open(request, timeout=20) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())
    status, _ = call('/api/method/login', {'usr': user['name'], 'pwd': user['password']})
    assert status == 200
    center = fixture['centers'][0]
    prefix = '/api/method/'
    for label, method, args in [
        ('native_general_ledger_definition', 'frappe.desk.query_report.get_script', {'report_name': 'General Ledger'}),
        ('native_trial_balance_definition', 'frappe.desk.query_report.get_script', {'report_name': 'Trial Balance'}),
        ('finance_summary', 'centrochange_core.finance.reporting.summary', {'center': center, 'start': '2026-09-01', 'end': '2026-10-31'}),
        ('patient_search', 'centrochange_core.operations.workspace.patient_search', {'center': center, 'text': 'Alfa'}),
    ]:
        status, value = call(prefix + method + '?' + urllib.parse.urlencode(args))
        results.append({'role': role, 'probe': label, 'status': status, 'exception': value.get('exc_type')})
print(json.dumps({'results': results, 'business_mutations': 'NONE'}, indent=2))
