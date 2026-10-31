"""Run AUDIT-10 only in an ephemeral external CI runner."""
import json
import os
import subprocess
from pathlib import Path
import test_audit09_isolated_clone as clone

root = Path(__file__).resolve().parent.parent
try:
    clone.setup_clone()
    source = (root / 'infra/audit10_clone_backend.py').read_text()
    out = clone.run_cmd(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', clone.BACKEND_CONTAINER, 'env/bin/python', '-'], input_str=source)
    result = next(json.loads(line) for line in out.splitlines() if line.startswith('{') and 'status' in line)
    assert result['status'] == 'PASS', result
    print('AUDIT10_BACKEND', json.dumps(result), flush=True)
    race_source = (root / 'infra/audit10_clone_race.py').read_text()
    race = clone.run_cmd(['docker', 'exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', clone.BACKEND_CONTAINER, 'env/bin/python', '-'], input_str=race_source)
    assert 'AUDIT10_CONCURRENCY_PASS' in race, race
    print(race, flush=True)
    env = dict(os.environ, NODE_PATH=str(root / 'frontend/premium/node_modules'), CC_ARTIFACT_DIR=os.environ.get('CC_ARTIFACT_DIR', str(root / '.audit10-artifacts')))
    subprocess.run(['node', str(root / 'infra/audit10_clone_browser.cjs')], env=env, check=True)
    assert not result['inactive_center_expands_historical_access'], 'SECURITY: new membership in inactive center expanded historical patient access'
    print('AUDIT10_ISOLATED_TESTS_PASS', flush=True)
finally:
    clone.cleanup()
