#!/usr/bin/env python3
"""One gated #75 native UX update, derived from the verified #141 DEV executor.

The application source is pinned separately from this executor. The inherited
preflight, encrypted four-part backup, six-service Compose update, integrity
checks and single rollback remain in force. The default dry-run is read-only.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
PARENT = REPO / 'infra/client_demo_install.py'
PARENT_SHA = '2ce4a13c6a7a4010b813a84aefd08f6c13818ed1b1232b1ba13a6c48c6a5ac84'
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
    raise SystemExit('verified parent executor drift')
spec = importlib.util.spec_from_file_location('client_demo_verified_gate', PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
gate = parent.gate
gate.__file__ = str(HERE)
gate.BASE_SOURCE = 'cf0eff79a74de4ec36cb20611e5c518de5ba7f8e'
gate.SOURCE = 'bafa01e71f4c6d4320c1b227efd57287255bd508'
gate.BASE_IMAGE = 'sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834'
gate.BASE_TAG = 'centrochange-single:client-demo-cf0eff7'
gate.IMAGE = 'centrochange-single:issue75-native-bafa01e'
gate.OVERLAY = REPO / 'infra/compose.issue75_native_ux.yaml'
gate.ACTIVE_OVERLAY_SHA = 'c773c834c484c5fa185582663c4affa395a1a9199a35e15e3a6936630f1ef90a'
gate.AGENDA_CSS_SHA = '9c2198cc47265c5fe681c61ce0f38ffca7df5ac35e6a3d59228e7d954a3bc9a5'
gate.RUN_ROOT = gate.STATE / 'issue75-native-ux-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    'infra/client_demo_install.py': PARENT_SHA,
    'infra/compose.issue75_native_ux.yaml': 'a0452c4d27deaf7fb2e4284c6f8b945685aafd5bd9843625845e86a40a2ba93b',
    'infra/browser/issue75_native_ux_live.cjs': 'e115126d69856760209b26016ef945c81518c21a7d67e190ce604656aa6c15d5',
    'infra/tests/test_issue75_native_ux.cjs': 'db654615d121f1ce7ec94f8de3a50e84ac2078dc5e3613ab973df10b656976db',
}

def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue','candidate','executor_sha256','authorize',
                'window_start_utc','operation_deadline_utc','recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 75
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'ISSUE75_NATIVE_UX_ONE_CUMULATIVE_DEV_UPDATE',
                 'Owner gate identity mismatch')
    def parse(key):
        parsed = datetime.fromisoformat(value[key].replace('Z','+00:00'))
        gate.require(parsed.tzinfo is not None,'Owner gate timezone missing')
        return parsed.astimezone(timezone.utc)
    start,end,recover = map(parse,('window_start_utc','operation_deadline_utc','recovery_deadline_utc'))
    now = datetime.now(timezone.utc)
    gate.require(start <= now < (recover if recovery else end), 'Owner window expired')
    gate.require(timedelta(0) < end-start <= timedelta(hours=4)
                 and timedelta(0) < recover-end <= timedelta(hours=1),
                 'Owner window exceeds 4h plus 1h recovery')
    return {'operation_end':end,'recovery_end':recover}

gate.validate_owner_gate = validate_owner_gate

if __name__ == '__main__':
    raise SystemExit(gate.main())
