"""Single R12 entrypoint: verify, guard, clone resources, gate, then release."""

import datetime as dt
import json
from pathlib import Path
import sys
import time

from c109_compose_gate import R12_PROJECT
from c109_guard_access import ROLES, launch_scopes, marker_path, require_live_guards
from c109_gated_start import main as start_gated, precreate_gate, run
from c109_gated_start import stop_only_ours
from c109_r12_contract import attest, digest
from c109_r12_resources import prepare as prepare_resources
from c109_r12_safety_prepare import install_private_safety
from c109_r12_writer import probe_writer_available, require_writer_lease
from c109_rc22_identity import verify as verify_rc22
from c109_protected_inventory import validate_existing


IMAGE = "sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00"
REVISION = "e2fd728ecf6acdb0e0ab26379820df6905dd5521"


def preflight(root, *, launch=launch_scopes, sleep=time.sleep, host_run=run,
              gate=precreate_gate, prepare=prepare_resources):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime.fromisoformat(activation["start_utc"])
    mutation_end = dt.datetime.fromisoformat(activation["mutation_end_utc"])
    hard_stop = dt.datetime.fromisoformat(activation["hard_stop_utc"])
    if (activation.get("target") != R12_PROJECT or activation.get("issue") != 109
            or activation.get("status") != "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP"
            or activation.get("workload_release_allowed") is not True
            or activation.get("image_manifest") != IMAGE
            or activation.get("source_commit") != REVISION
            or activation.get("exclusive_docker_writer") is not True
            or activation.get("io_waiver") is not True
            or not all(t.tzinfo for t in (start, mutation_end, hard_stop))
            or not start <= now < mutation_end
            or not mutation_end < hard_stop
            or hard_stop - mutation_end < dt.timedelta(hours=1)
            or mutation_end - start > dt.timedelta(hours=6)):
        raise RuntimeError("R12 authorization, pin or recovery window invalid")
    digest()
    repository = str(Path(__file__).resolve().parent.parent)
    if (host_run("git", "-C", repository, "rev-parse", "HEAD") != activation.get("harness_commit")
            or host_run("git", "-C", repository, "status", "--porcelain")):
        raise RuntimeError("R12 harness HEAD or worktree differs from authorized revision")
    if host_run("docker", "image", "inspect", "-f", "{{.Id}}", IMAGE) != IMAGE:
        raise RuntimeError("R12 immutable application image missing")
    if host_run("docker", "image", "inspect", "-f", "{{index .Config.Labels \"org.opencontainers.image.revision\"}}", IMAGE) != REVISION:
        raise RuntimeError("R12 application image revision mismatch")
    if (state / "r12-preflight-attestation.json").exists():
        raise RuntimeError("R12 preflight already attempted")
    verify_rc22(state, host_run)
    validate_existing((state / "protected-before.json").read_text(),
                      host_run("docker", "ps", "-aq", "--no-trunc"))
    install_private_safety(state)
    launch(root)
    require_live_guards(state, max_proof_age=30)
    require_writer_lease(state)
    first = {role: json.loads(marker_path(state, role).read_text())["checked_at"] for role in ROLES}
    # This intentional 34-second preparation probe makes renewal observable.
    # The expiry scope remains active; no workload is released during the wait.
    deadline = time.monotonic() + 34
    while time.monotonic() < deadline:
        require_live_guards(state, max_proof_age=30)
        require_writer_lease(state)
        sleep(min(2, deadline - time.monotonic()))
    require_live_guards(state, max_proof_age=30)
    require_writer_lease(state)
    for role in ROLES:
        if json.loads(marker_path(state, role).read_text())["checked_at"] <= first[role]:
            raise RuntimeError(f"R12 {role} Docker proof did not renew")
    # The same four guards continue running through the serial, capped copy.
    # A partial preparation is single-use and cannot be resumed automatically.
    prepare(root, image=IMAGE)
    gate(root, attested=False)
    attest(root)
    # Same gate as the real launcher, now requiring the verified attestation.
    gate(root)


def main(root, *, lock_file=None):
    # Probe exclusivity before launching; the independent watchdog then takes
    # and retains this same writer lease. No Docker mutation precedes its proof.
    probe_writer_available(lock_file)
    try:
        preflight(root)
        start_gated(root)
    except BaseException:
        # A failed gate consumes this activation and ends all four scopes.
        stop_only_ours(root / "app-run", R12_PROJECT)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_r12_preflight.py PRIVATE_ACTIVATION_ROOT")
    main(Path(sys.argv[1]))
