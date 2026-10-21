#!/usr/bin/env python3
"""Read-only preflight or one future Owner-gated native Form update.

This wrapper inherits the verified encrypted backup, six-service install,
data/permission fingerprints and one-rollback path. It does not authorize a
shared DEV mutation: --execute requires a new private exact Owner gate.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
PARENT = REPO / 'infra/issue134_cumulative_install.py'
PARENT_SHA = '05b1210ca2b6ebc4cea96e1b7c93b4e1977ea829885e1589929506e12fa29b20'
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
    raise SystemExit('verified cumulative executor drift')
spec = importlib.util.spec_from_file_location('issue134_cumulative_verified_gate', PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
gate = parent.gate
gate.__file__ = str(HERE)
gate.BASE_SOURCE = 'e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec'
gate.SOURCE = '1f88207c6a71c4bf0252b912fe83313337cab16f'
gate.BASE_IMAGE = 'sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e'
gate.BASE_TAG = 'centrochange-single:issue134-cumulative'
gate.IMAGE = 'centrochange-single:issue75-form-affordance'
gate.OVERLAY = REPO / 'infra/compose.issue75_form_affordance.yaml'
gate.ACTIVE_OVERLAY_SHA = '1eb642e2634312cbd53d033fbe4490bed34b1235e470b644f1ae5283aad2ce41'
gate.RUN_ROOT = gate.STATE / 'issue75-form-affordance-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    # PR #145 updated this test after the previous #75 executor was pinned.
    'infra/tests/test_issue75_native_ux.cjs':
        '12a34991f1dffa6a37ecfb8528412faf2d308891970903dba17e70d718a13183',
    'infra/issue134_cumulative_install.py': PARENT_SHA,
    'infra/compose.issue75_form_affordance.yaml':
        '1dc3d7b91d8176e48df2ae613593f2bfa41911d59a20a92882b591ec8b2bb9a9',
    'infra/browser/issue75_native_form_affordance.cjs':
        '93f2a8feb3ba074e24cfe3acfd6c09ddebb0d108a3829bde06c7b7a3195393cf',
    'infra/issue75_form_affordance_clone.py':
        'd9794fcd9dc946886c77e4fef7acdba2ab062129f63452e9b303d2bfe08c34b3',
}


def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue', 'candidate', 'executor_sha256', 'authorize',
                'window_start_utc', 'operation_deadline_utc', 'recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 75
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'ISSUE75_FORM_AFFORDANCE_ONE_DEV_UPDATE',
                 'Owner gate identity mismatch')
    def parse(key):
        parsed = datetime.fromisoformat(value[key].replace('Z', '+00:00'))
        gate.require(parsed.tzinfo is not None, 'Owner gate timezone missing')
        return parsed.astimezone(timezone.utc)
    start, end, recover = map(parse, ('window_start_utc', 'operation_deadline_utc',
                                      'recovery_deadline_utc'))
    now = datetime.now(timezone.utc)
    gate.require(start <= now < (recover if recovery else end),
                 'Owner window expired')
    gate.require(timedelta(0) < end-start <= timedelta(hours=4)
                 and timedelta(0) < recover-end <= timedelta(hours=1),
                 'Owner window exceeds 4h plus 1h recovery')
    return {'operation_end': end, 'recovery_end': recover}


gate.validate_owner_gate = validate_owner_gate

if __name__ == '__main__':
    raise SystemExit(gate.main())
