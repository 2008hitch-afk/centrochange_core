#!/usr/bin/env python3
"""Verify the immutable DEV application bytes against an explicit Git source commit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-ref', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    prefix = 'app/centrochange_core/'
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.source_ref, '--', prefix], cwd=root, text=True).splitlines()
    expected = {path[len(prefix):]: hashlib.sha256(subprocess.check_output(['git', 'show', args.source_ref + ':' + path], cwd=root)).hexdigest() for path in paths}
    code = "import hashlib,json,pathlib,sys; root=pathlib.Path('/home/frappe/frappe-bench/apps/centrochange_core'); print(json.dumps({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in json.load(sys.stdin)}))"
    actual = json.loads(subprocess.check_output(['docker', 'exec', '-i', 'centrochange-dev-backend-1', 'env/bin/python', '-c', code], input=json.dumps(list(expected)), text=True))
    assert actual == expected, 'Runtime application bytes differ from committed source'
    containers = json.loads(subprocess.check_output(['docker', 'inspect', 'centrochange-dev-backend-1', 'centrochange-dev-frontend-1', 'centrochange-dev-queue-short-1', 'centrochange-dev-queue-long-1', 'centrochange-dev-scheduler-1', 'centrochange-dev-websocket-1'], text=True))
    images = set()
    for container in containers:
        assert container['Config']['Labels']['com.docker.compose.project'] == 'centrochange-dev'
        assert all(mount['Type'] == 'volume' for mount in container['Mounts']), 'Application source bind overlay detected'
        images.add(container['Image'])
    assert len(images) == 1
    digest = hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()
    print(json.dumps({'status': 'PASS', 'source_commit': subprocess.check_output(['git', 'rev-parse', args.source_ref], cwd=root, text=True).strip(), 'tracked_app_files': len(expected), 'app_manifest_sha256': digest, 'runtime_image': next(iter(images)), 'source_overlays': False, 'app_services': len(containers)}))


if __name__ == '__main__':
    main()
