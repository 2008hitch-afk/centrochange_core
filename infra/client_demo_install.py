#!/usr/bin/env python3
"""PR #141 one-shot DEV presentation update using the proven #139 executor.

The imported executor retains its backup, source-byte, Compose, integrity,
essential authorization and single-rollback checks. Only exact pins and the
Owner gate identity differ; no command is sent to the shared DEV in dry-run.
"""
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
BASE_EXECUTOR = REPO / 'infra/issue139_install_gate.py'
BASE_EXECUTOR_SHA = 'c6905c90221ea8e3774dad712898c9bb74c41bf9b53fa4f0419ffa9c7df58b6d'
if hashlib.sha256(BASE_EXECUTOR.read_bytes()).hexdigest() != BASE_EXECUTOR_SHA:
    raise SystemExit('base executor drift')
spec = importlib.util.spec_from_file_location('issue139_proven_gate', BASE_EXECUTOR)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

gate.__file__ = str(HERE)  # exact --executor-sha256 applies to this wrapper
gate.SOURCE = 'cf0eff79a74de4ec36cb20611e5c518de5ba7f8e'
gate.BASE_SOURCE = 'a03386c41a78692fd4b6d370ec56b1d21d613841'
gate.BASE_IMAGE = 'sha256:e2df539cc99fee6965102f539c0969dbec98d2ad59bf7c0d9631d4e03774acdb'
gate.BASE_TAG = 'centrochange-single:mvp-devfirst-a03386c-v3'
gate.IMAGE = 'centrochange-single:client-demo-cf0eff7'
gate.OVERLAY = REPO / 'infra/compose.client_demo.yaml'
gate.ACTIVE_OVERLAY_SHA = 'd9ed2e0b724fefedf8b08b6795bff47b44c0da9adc56a9264c9263d3e4329c4e'
gate.RUN_ROOT = gate.STATE / 'client-demo-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    'infra/issue139_install_gate.py': BASE_EXECUTOR_SHA,
    'infra/compose.client_demo.yaml': 'c773c834c484c5fa185582663c4affa395a1a9199a35e15e3a6936630f1ef90a',
    'infra/browser/issue137_owner_uat_sweep.cjs': 'ae0a466ea35b1dfd5867fe2b0709d21f30900bd89d3d59f7f6c45c018d3d8ef9',
    'infra/browser/client_demo_readiness.cjs': '1da26718231cb052a48dc1361fdee233fc4868e7b15ac1c8294c87b845744ef7',
    'infra/tests/test_client_demo_list.cjs': '959a0556635d567fe05183af5e23c42b109cce872c00d8e1f50495a00a243d5a',
}

def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue','candidate','executor_sha256','authorize',
                'window_start_utc','operation_deadline_utc','recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 141
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'CLIENT_DEMO_ONE_CUMULATIVE_DEV_UPDATE',
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
