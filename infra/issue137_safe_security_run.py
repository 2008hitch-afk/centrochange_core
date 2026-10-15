#!/usr/bin/env python3
"""Run the existing exact synthetic fixture suite once, with a before/after data gate."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parent.parent
STATE = Path('/home/empv26/.local/state/centrochange-single')
EXECUTOR = REPO / 'infra/goal02_install_one_command.py'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-data', required=True)
    parser.add_argument('--expected-communication', required=True)
    parser.add_argument('--isolated-project', choices=['cc139-w5-isolated'])
    parser.add_argument('--env-file', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or sys.flags.isolated != 1:
        raise SystemExit('Requires sudo python3 -I on the authorized host')
    if args.isolated_project:
        allowed_parent = STATE / 'issue139-full-rehearsal'
        if args.env_file is None or args.env_file.name != 'runtime.env' or \
                args.env_file.parent.parent.resolve() != allowed_parent.resolve() or \
                not args.env_file.is_file() or args.env_file.is_symlink() or \
                args.env_file.stat().st_mode & 0o077:
            raise SystemExit('isolated env file outside private rehearsal scope')
        spec = importlib.util.spec_from_file_location('issue139_clone_adapter',
                                                      REPO / 'infra/issue139_clone_adapter.py')
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        module = adapter.load_clone_module()
        state = args.env_file.parent
    else:
        if args.env_file is not None:
            raise SystemExit('custom env file requires isolated project')
        spec = importlib.util.spec_from_file_location('goal02_installed', EXECUTOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state = STATE
    module.http_ready()
    before_services = module.snapshot()
    module.hooks()
    before = module.runtime_fingerprint()
    if before['sha256'] != args.expected_data or before['communication_sha256'] != args.expected_communication:
        raise SystemExit('BLOCKED: current synthetic fingerprint differs from this run checkpoint')
    run_dir = state / 'browser-evidence' / ('issue137-fixture-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    run_dir.mkdir(mode=0o700)
    (run_dir / 'before.json').write_text(json.dumps(before, sort_keys=True))
    command = [sys.executable, '-I', str(REPO / 'infra/security_acceptance.py'), '--env-file',
               str(state / 'runtime.env'), '--with-booking', '--with-operations']
    if args.isolated_project:
        command += ['--isolated-project', args.isolated_project]
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    (run_dir / 'suite.log').write_text(result.stdout + '\n' + result.stderr)
    after = module.runtime_fingerprint()
    (run_dir / 'after.json').write_text(json.dumps(after, sort_keys=True))
    same = before == after
    services_same = module.snapshot() == before_services
    status = 'PASS' if result.returncode == 0 and same and services_same else 'FAIL'
    print(json.dumps({'status':status,'suite_exit':result.returncode,
                      'data_unchanged':same,'services_unchanged':services_same,
                      'private_evidence':str(run_dir)}))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
