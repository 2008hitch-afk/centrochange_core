#!/usr/bin/env python3
"""Run the existing decisive synthetic suites sequentially on the current DEV image."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = Path(args.output_dir).resolve()
    if output == root or root in output.parents:
        raise ValueError('Temporary acceptance output must stay outside Git')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    commands = [('direct', ['docker', 'exec', 'centrochange-dev-backend-1', 'bench', '--site', 'centrochange.local', 'execute', 'centrochange_core.operations.integration_acceptance.run'])]
    for suite in ('security', 'finance', 'receivables', 'banking', 'incoming', 'professional', 'reporting', 'sdi', 'ts', 'browser', 'finance_browser'):
        command = [sys.executable, str(root / 'infra' / (suite + '_acceptance.py')), '--env-file', args.env_file]
        if suite == 'security':
            command += ['--with-booking', '--with-operations']
        if suite in ('browser', 'finance_browser'):
            command += ['--output-dir', str(output / suite)]
        commands.append((suite, command))
    reports = []
    for name, command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        log = output / (name + '.log')
        log.write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(name + ' failed; inspect ' + str(log))
        records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        if not any(record.get('status') == 'PASS' for record in records):
            raise RuntimeError(name + ' did not report PASS')
        reports.append({'suite': name, 'status': 'PASS', 'log': str(log)})
        print(json.dumps(reports[-1]), flush=True)
    (output / 'summary.json').write_text(json.dumps({'status': 'PASS', 'suites': reports}, indent=2) + '\n')


if __name__ == '__main__':
    os.umask(0o077)
    main()
