#!/usr/bin/env python3
"""Private synthetic UAT management. Run with Docker group access, never via RPC."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def execute(method):
    result = subprocess.run(['docker', 'exec', 'centrochange-dev-backend-1', 'bench', '--site',
        'centrochange.local', 'execute', 'centrochange_core.uat.demo.' + method], capture_output=True, text=True)
    if result.returncode:
        # Raw trace stays external; never echo credentials returned by bench.
        path = Path('/tmp/cc-uat-private-error.log')
        with path.open('w') as stream:
            os.chmod(path, 0o600)
            stream.write(result.stdout + result.stderr)
        raise RuntimeError('Private UAT command failed: ' + method + '; trace outside Git: ' + str(path))
    return json.loads(result.stdout.strip())


def outside(path):
    path = Path(path).resolve()
    repository = Path(__file__).resolve().parent.parent
    if path == repository or repository in path.parents:
        raise ValueError('Private UAT credentials must remain outside Git')
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('seed', 'inspect', 'validate', 'reset', 'handoff'))
    parser.add_argument('--credentials-file', default='/tmp/cc-uat-demo-credentials.json')
    args = parser.parse_args()
    if args.action == 'handoff':
        path = outside(args.credentials_file)
        with path.open('w') as stream:
            os.chmod(path, 0o600)
            json.dump(execute('credentials'), stream, sort_keys=True)
        print(json.dumps({'status': 'PASS', 'credentials_file': str(path), 'mode': '0600', 'synthetic_only': True}))
    elif args.action == 'validate':
        for _ in range(60):
            result = execute('validate')
            if result['status'] != 'PARTIAL':
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return
            time.sleep(1)
        print(json.dumps(result))
        raise RuntimeError('Synthetic fiscal workers have not completed')
    else:
        print(json.dumps(execute(args.action), ensure_ascii=False, sort_keys=True))
        if args.action == 'reset':
            outside(args.credentials_file).unlink(missing_ok=True)


if __name__ == '__main__':
    os.umask(0o077)
    main()
