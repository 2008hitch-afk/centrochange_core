#!/usr/bin/env python3
"""Read-only comparison of installed upstream bytes with exact official commits."""
import concurrent.futures
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import urllib.request

PINS = {
    'frappe': ('frappe/frappe', '6a329d068416768ec47ccd3326b9cc95a8d7bf99'),
    'erpnext': ('frappe/erpnext', '81a6f97566b83609c3917404a560b673050e907d'),
    'healthcare': ('earthians/marley', '934d6c162868139dfbe80c23d6102adb7ec25adb'),
    'builder': ('frappe/builder', '41987c064da4650e6901b5da82b7c76add452ebf'),
}
FILES = {
    'frappe': ['frappe/website/page_renderers/template_page.py', 'frappe/model/document.py', 'frappe/utils/password.py', 'frappe/__init__.py', 'frappe/utils/background_jobs.py'],
    'erpnext': ['erpnext/accounts/doctype/payment_entry/payment_entry.py', 'erpnext/accounts/doctype/sales_invoice/sales_invoice.py', 'erpnext/accounts/doctype/bank_transaction/bank_transaction.py'],
    'healthcare': ['healthcare/healthcare/doctype/patient/patient.py', 'healthcare/healthcare/doctype/patient_appointment/patient_appointment.py', 'healthcare/healthcare/doctype/practitioner_schedule/practitioner_schedule.py'],
    'builder': ['builder/__init__.py'],
}


def main():
    paths = ['apps/' + app + '/' + path for app, rows in FILES.items() for path in rows]
    expression = 'from pathlib import Path;from hashlib import sha256;import json;print(json.dumps({p:sha256(Path(p).read_bytes()).hexdigest() for p in ' + repr(paths) + '}))'
    actual = json.loads(subprocess.check_output(['docker', 'exec', 'centrochange-dev-backend-1', 'python', '-c', expression], text=True))
    def compare(pair):
        app, path = pair
        repository, commit = PINS[app]
        url = 'https://raw.githubusercontent.com/' + repository + '/' + commit + '/' + path
        with urllib.request.urlopen(url, timeout=30) as response:
            expected = sha256(response.read()).hexdigest()
        installed = actual['apps/' + app + '/' + path]
        assert expected == installed, app + '/' + path + ' differs from official pin'
        return {'app': app, 'commit': commit, 'path': path, 'sha256': installed, 'source': url, 'status': 'PASS'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(compare, [(app, path) for app, rows in FILES.items() for path in rows]))
    print(json.dumps({'status': 'PASS', 'checks': records}, indent=2))


if __name__ == '__main__':
    main()
