"""Offline-verified R12 preflight contract; live gate rejects unverified edits."""

import datetime as dt
import hashlib
import json
from pathlib import Path

from c109_rc22_identity import baseline


FILES = (
    "c109_r12_preflight.py", "c109_r12_resources.py", "c109_r12_contract.py", "c109_gated_start.py",
    "c109_guard_access.py", "c109_rc22_identity.py", "c109_rc22_monitor.py",
    "c109_compose_gate.py", "c109_demo_expiry.py", "c109_gated_qa.py",
    "c109_monitored_step.py", "c109_protected_inventory.py",
    "c109_r7_safety_prepare.py", "c109_cgroup_gate.py", "c109_io_gate.py",
    "test_c109_r12_preflight.py",
)
MANIFEST = Path(__file__).with_name("c109_r12_verified.json")


def digest():
    expected = json.loads(MANIFEST.read_text())
    actual = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
              for name in FILES}
    if set(expected) != set(FILES) or expected != actual:
        raise RuntimeError("R12 preflight code differs from offline-verified release")
    return hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()


def require_attestation(root):
    state = root / "app-run"
    attestation = json.loads((state / "r12-preflight-attestation.json").read_text())
    activation = (state / "activation.json").read_bytes()
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(attestation["checked_at"])).total_seconds()
    if (not 0 <= age <= 30 or attestation.get("code_digest") != digest()
            or attestation.get("activation_sha256") != hashlib.sha256(activation).hexdigest()
            or attestation.get("rc22_ids") != baseline(state)):
        raise RuntimeError("R12 preflight attestation absent, stale or mismatched")


def attest(root):
    state = root / "app-run"
    path = state / "r12-preflight-attestation.json"
    if path.exists():
        raise RuntimeError("R12 preflight is single-use")
    payload = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "code_digest": digest(),
               "activation_sha256": hashlib.sha256((state / "activation.json").read_bytes()).hexdigest(),
               "rc22_ids": baseline(state)}
    from c109_guard_access import atomic_json
    atomic_json(path, payload)
