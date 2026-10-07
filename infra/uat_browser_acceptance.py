#!/usr/bin/env python3
"""Browser validation against persistent demo; credentials never enter Git/stdout."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from uat_demo import execute, outside


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--script', choices=('uat','professional','patient','audit','expectations','bank_trace','ts_detail','confirmation','search','accounting','permissions'), default='uat')
    parser.add_argument('--agenda-only', action='store_true', help='Read-only agenda/role validation preserving current UAT financial mutations')
    parser.add_argument('--exercise', action='store_true', help='Mutate only owned synthetic overdue demo; reset afterwards')
    args = parser.parse_args()
    output = outside(args.output_dir)
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    fixture = execute('credentials')
    fixture['demo'] = execute('inspect')
    descriptor, credential = tempfile.mkstemp(prefix='cc-uat-browser-', suffix='.json')
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(fixture, stream)
        os.chmod(credential, 0o600)
        root = Path(__file__).resolve().parent
        result = subprocess.run(['docker', 'build', '-t', 'centrochange-browser-qa:1.58.2', str(root / 'browser')], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('Pinned browser build failed')
        result = subprocess.run(['docker', 'run', '--rm', '--network', 'host', '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '-v', credential + ':/qa-fixture.json:ro', '-v', str(output) + ':/qa-results',
            '-e', 'CC_BASE_URL=http://centrochange.local:8082', '-e', 'CC_UAT_AGENDA_ONLY=' + ('1' if args.agenda_only else '0'), '-e', 'CC_UAT_EXERCISE=' + ('1' if args.exercise else '0'), 'centrochange-browser-qa:1.58.2', 'node', '/qa/' + args.script + '.cjs'], capture_output=True, text=True)
        (output / 'uat.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('UAT browser failed; inspect external ' + str(output / 'uat.log'))
        report = json.loads(result.stdout.strip().splitlines()[-1])
        (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        Path(credential).unlink(missing_ok=True)


if __name__ == '__main__':
    os.umask(0o077)
    main()
