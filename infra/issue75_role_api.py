"""Read-only direct HTTP role and assignment regressions for issue #75."""
import argparse
import http.cookiejar
import json
import urllib.parse
import urllib.request

from issue124_role_api import request
from uat_demo import execute


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', required=True)
    fixture = json.load(open(parser.parse_args().fixture))['fixture']
    demo = execute('inspect')
    base = 'http://127.0.0.1:8082'
    center = fixture['centers'][0]
    expected_patients = {'m': 8, 's': 7, 'a': 6, 'b': 1, 'c': 0}
    results = {}
    for role in 'msabcft':
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        user = fixture['users'][role]
        assert request(opener, base + '/api/method/login', {'usr': user['name'], 'pwd': user['password']})[0] == 200
        def get(method, **args):
            return request(opener, base + '/api/method/' + method + '?' + urllib.parse.urlencode(args))
        operational_status, operational_body = get('centrochange_core.operations.workspace.bootstrap', center=center)
        finance_status, _ = get('centrochange_core.finance.patient_reporting.patient_view', center=center, start='2026-09-28', end='2026-10-31')
        invoice_status, _ = request(opener, base + '/api/resource/Sales%20Invoice/' + urllib.parse.quote(demo['invoices']['Theta insoluto scaduto']))
        audit_status, _ = get('centrochange_core.security.audit_view.events', start='2026-10-06', end='2026-10-07')
        if role in expected_patients:
            assert operational_status == 200
            count = len(json.loads(operational_body)['message']['patients'])
            assert count == expected_patients[role], (role, count)
            assert finance_status == (200 if role in 'ms' else 403)
            assert invoice_status == (200 if role in 'ms' else 403)
        else:
            assert operational_status == 403
            count = None
            assert finance_status == invoice_status == 200
        assert audit_status == (200 if role == 'm' else 403)
        results[role] = {'operational': operational_status, 'visible_patients': count,
                         'scoped_finance': finance_status, 'native_invoice': invoice_status, 'audit': audit_status}
    for role, own, other in [('a', 'Alfa', 'Zeta'), ('b', 'Zeta', 'Alfa'), ('c', None, 'Alfa')]:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        user = fixture['users'][role]
        assert request(opener, base + '/api/method/login', {'usr': user['name'], 'pwd': user['password']})[0] == 200
        def history(patient):
            return request(opener, base + '/api/method/centrochange_core.operations.workspace.patient_history?' + urllib.parse.urlencode({'patient': demo['patients'][patient], 'center': center}))[0]
        if own:
            assert history(own) == 200
        assert history(other) == 403
    print(json.dumps({'status': 'PASS', 'roles': results, 'assignment_direct_http': 'PASS', 'mutations': 'NONE'}))


if __name__ == '__main__':
    main()
