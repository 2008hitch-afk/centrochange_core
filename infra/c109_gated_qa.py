"""Start one inert, 512 MiB C109 QA process; never launch Chromium here.

The host verifies the real cgroup before a separate test command can be run.
Only the synthetic isolated project is eligible; the marker is single-use.
"""

import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time

from c109_cgroup_gate import CgroupGateError, read_snapshot
from c109_gated_start import guard, inspect, oom_count, run, stop_only_ours
from c109_compose_gate import R10_PROJECT


QA_IMAGE = "sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3"
QA_NAME = "centrochange-c109-gated-r10-qa"
PROJECT = R10_PROJECT
LIMIT = 512 * 1024**2


def main(root: Path):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("target"), activation.get("status")) != (PROJECT, "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP"):
        raise RuntimeError("wrong activation")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("mutation window expired")
    if not (state / "app-bootstrap-green").exists() or (state / "qa-attempted").exists():
        raise RuntimeError("application gate missing or QA already attempted")
    if run("docker", "ps", "-aq", "--filter", f"name=^{QA_NAME}$"):
        raise RuntimeError("QA name already exists")
    app_ids = run("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}").split()
    if len(app_ids) != 8:
        raise RuntimeError("application service count changed")
    rc22 = sorted(run("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=centrochange-dev").split())
    if len(rc22) != 9:
        raise RuntimeError("RC22 service count changed")
    initial_oom = oom_count()
    guard(state, rc22, initial_oom)
    frontend = run("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}",
                   "--filter", "label=com.docker.compose.service=c-fit-frontend").split()
    if len(frontend) != 1:
        raise RuntimeError("frontend identity changed")
    fixture = Path("/home/empv26/.local/state/centrochange-c109/qa-fixture.json")
    if not fixture.is_file():
        raise RuntimeError("private synthetic fixture missing")
    results = state / "qa-results"
    results.mkdir(exist_ok=False)
    (state / "qa-attempted").write_text(dt.datetime.now(dt.timezone.utc).isoformat())
    container = None
    try:
        container = run("docker", "create", "--name", QA_NAME,
                        "--label", "centrochange.mission=C109", "--label", "centrochange.phase=lab",
                        "--label", f"com.docker.compose.project={PROJECT}",
                        "--memory", "512m", "--memory-swap", "512m",
                        "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
                        "--network", f"container:{frontend[0]}",
                        "--mount", f"type=bind,source={fixture},target=/qa-fixture.json,readonly",
                        "--mount", f"type=bind,source={results},target=/qa-results",
                        "--mount", "type=bind,source=/home/empv26/.local/state/centrochange-c109/qa-smoke.cjs,target=/qa/qa-smoke.cjs,readonly",
                        "--mount", f"type=bind,source={root / 'qa-tests'},target=/qa/tests,readonly",
                        "--entrypoint", "sleep", QA_IMAGE, "infinity", timeout=30)
        row = inspect(container)
        if row["running"] or row["memory"] != LIMIT or row["swap"] != LIMIT:
            raise RuntimeError("QA HostConfig cap mismatch")
        host_config = json.loads(run("docker", "inspect", "-f", "{{json .HostConfig}}", container))
        if host_config.get("BlkioDeviceReadBps") or host_config.get("BlkioDeviceWriteBps"):
            raise RuntimeError("r7 QA unexpectedly I/O capped")
        guard(state, rc22, initial_oom)
        run("docker", "start", container)
        first = None
        seen = None
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            guard(state, rc22, initial_oom)
            row = inspect(container)
            if not row["running"] or row["pid"] <= 0:
                raise RuntimeError("QA inert process exited")
            try:
                snapshot = read_snapshot(row["pid"], container, LIMIT)
                if first is None:
                    first = snapshot
                    seen = time.monotonic()
                elif snapshot.inode != first.inode:
                    raise RuntimeError("QA cgroup inode changed")
                if time.monotonic() - seen >= 0.2:
                    (state / "qa-ready.json").write_text(json.dumps({
                        "container": container, "pid": row["pid"], "inode": snapshot.inode,
                        "memory_max": snapshot.memory_max, "swap_max": snapshot.swap_max,
                        "verified_utc": dt.datetime.now(dt.timezone.utc).isoformat()
                    }, indent=2))
                    return
            except CgroupGateError as exc:
                if first is not None or (isinstance(exc, CgroupGateError)
                                         and str(exc) not in ("memory.max is max", "swap.max is max")):
                    raise RuntimeError(f"QA cap invalid: {exc}") from exc
            time.sleep(0.01)
        raise RuntimeError("QA cap did not stabilize before deadline")
    except BaseException:
        if container:
            subprocess.run(["docker", "stop", "--time", "10", container],
                           timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_gated_qa.py PRIVATE_ACTIVATION_ROOT")
    root = Path(sys.argv[1])
    try:
        main(root)
    except BaseException:
        state = root / "app-run"
        try:
            activation = json.loads((state / "activation.json").read_text())
            if activation.get("target") == PROJECT and (state / "app-bootstrap-green").exists():
                stop_only_ours(state, PROJECT)
        except (OSError, ValueError):
            pass
        raise
