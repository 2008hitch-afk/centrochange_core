"""Read-only topology adapter for the one permitted isolated #139 rehearsal.

Every backend Python command targets the clone name only. The Frappe code run
inside it may mutate the clone as part of the actual executor path.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import time
import urllib.request

PROJECT = 'cc139-w5-isolated'
SERVICES = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long',
            'scheduler', 'db', 'redis-cache', 'redis-queue')
REPO = Path(__file__).resolve().parent.parent


def _read(args, *, input_text=None):
    result = subprocess.run(args, input=input_text, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{args[0]} {args[1]} failed on isolated target')
    return result.stdout


def verify_clone_scope():
    observed = {}
    for service in SERVICES:
        name = f'{PROJECT}-{service}-1'
        rows = json.loads(_read(['docker', 'inspect', name]))
        if len(rows) != 1:
            raise RuntimeError('clone container inventory differs')
        item = rows[0]
        labels = item['Config'].get('Labels') or {}
        if labels.get('com.docker.compose.project') != PROJECT or \
                labels.get('com.docker.compose.service') != service:
            raise RuntimeError('clone ownership differs')
        if not item['State']['Running'] or \
                (item['State'].get('Health') or {}).get('Status') not in (None, 'healthy'):
            raise RuntimeError('clone service unhealthy')
        for mount in item['Mounts']:
            if mount['Type'] != 'volume' or not mount.get('Name', '').startswith(PROJECT + '-'):
                raise RuntimeError('clone mount is shared or not a private volume')
        if set(item['NetworkSettings']['Networks']) != {PROJECT + '-net'}:
            raise RuntimeError('clone network scope differs')
        observed[service] = item
    frontend = observed['frontend']['NetworkSettings']['Ports']['8080/tcp']
    if len(frontend) != 1 or frontend[0]['HostIp'] != '127.0.0.2' or \
            frontend[0]['HostPort'] != '8082':
        raise RuntimeError('clone frontend is not on isolated loopback')
    return observed


def load_clone_module():
    verify_clone_scope()
    source = REPO / 'infra/goal02_install_one_command.py'
    spec = importlib.util.spec_from_file_location('issue139_clone_goal02', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def backend_python(code):
        return _read(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1',
                      '-w', '/home/frappe/frappe-bench/sites',
                      f'{PROJECT}-backend-1', '/home/frappe/frappe-bench/env/bin/python'],
                     input_text=code)

    def snapshot():
        containers = verify_clone_scope()
        result = {}
        for service, item in containers.items():
            health = (item['State'].get('Health') or {}).get('Status')
            result[service] = {'id': item['Id'], 'image': item['Image'], 'health': health,
                               'mounts': sorted((m['Type'], m.get('Name'), m['Source'],
                                                 m['Destination']) for m in item['Mounts'])}
        return result

    def http_ready():
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(30):
            try:
                request = urllib.request.Request('http://127.0.0.2:8082/api/method/ping',
                                                 headers={'Host': 'centrochange.local'})
                with opener.open(request, timeout=4) as response:
                    if response.status == 200 and json.load(response)['message'] == 'pong':
                        return
            except Exception:
                time.sleep(2)
        raise RuntimeError('isolated clone HTTP unavailable')

    module.backend_python = backend_python
    module.snapshot = snapshot
    module.http_ready = http_ready
    return module
