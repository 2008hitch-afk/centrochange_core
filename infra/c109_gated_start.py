"""Single C-UNIFIED activation: create gated services and release one by one.

Run only with the private, prevalidated Compose files and active historical
watchdog. No retry in the same activation; no UAT or global Docker mutation.
"""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from c109_cgroup_gate import CgroupGateError, read_snapshot
from c109_compose_gate import KINDS


ORDER = ["c-fit-db", "c-fit-redis-cache", "c-fit-redis-queue", "c-fit-backend",
         "c-fit-websocket", "c-fit-queue-long", "c-fit-scheduler", "c-fit-frontend"]
PROJECT = "centrochange-c109-gated"
EXPECTED_MAX = {
    "c-fit-db": 536870912, "c-fit-redis-cache": 67108864,
    "c-fit-redis-queue": 67108864, "c-fit-backend": 671088640,
    "c-fit-websocket": 100663296, "c-fit-queue-long": 402653184,
    "c-fit-scheduler": 268435456, "c-fit-frontend": 33554432,
}


def run(*args, timeout=30):
    return subprocess.check_output(args, text=True, timeout=timeout).strip()


def now():
    return dt.datetime.now(dt.timezone.utc)


def oom_count():
    return int(next(line.split()[1] for line in open("/proc/vmstat") if line.startswith("oom_kill ")))


def mem_available():
    return int(next(line.split()[1] for line in open("/proc/meminfo") if line.startswith("MemAvailable:"))) * 1024


def psi_full(kind):
    return float(next(line.split()[1].split("=")[1] for line in open(f"/proc/pressure/{kind}") if line.startswith("full ")))


def guard(state, rc22_ids, initial_oom):
    if (state / "safety-stop.json").exists() or (state / "protected-event-alert.json").exists():
        raise RuntimeError("host watchdog/protected event alert")
    for name in ("events-heartbeat", "monitor-heartbeat"):
        p = state / name
        if not p.exists() or time.time() - float(p.read_text()) > 12:
            raise RuntimeError(f"monitor heartbeat stale: {name}")
    if oom_count() != initial_oom or mem_available() < 768 * 1024**2:
        raise RuntimeError("OOM or host memory reserve")
    if psi_full("memory") >= 1 or psi_full("io") >= 1:
        raise RuntimeError("host PSI full")
    if os.statvfs("/").f_bavail * os.statvfs("/").f_frsize < 4 * 1024**3:
        raise RuntimeError("disk reserve")
    if sorted(run("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=centrochange-dev").split()) != rc22_ids:
        raise RuntimeError("RC22 container identity changed")
    if urllib.request.urlopen("http://127.0.0.1:8082/api/method/ping", timeout=5).status != 200:
        raise RuntimeError("RC22 HTTP changed")


def inspect(container):
    parts = run("docker", "inspect", "-f", "{{.Id}} {{.State.Pid}} {{.State.Running}} {{.HostConfig.Memory}} {{.HostConfig.MemorySwap}}", container).split()
    return {"id": parts[0], "pid": int(parts[1]), "running": parts[2] == "true",
            "memory": int(parts[3]), "swap": int(parts[4])}


def stop_only_ours(state):
    ids = run("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}").split()
    if ids:
        subprocess.run(["docker", "stop", "--time", "10", *ids], timeout=60, check=True,
                       stdout=subprocess.DEVNULL)
    (state / "monitor-finish").write_text(now().isoformat())


def main(root):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if activation["issue"] != 109 or activation["status"] != "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP":
        raise RuntimeError("wrong activation")
    if activation.get("workload_release_allowed") is not True:
        raise RuntimeError("application workload release is not active")
    if now() >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("mutation window expired")
    if (state / "app-attempted").exists():
        raise RuntimeError("app bootstrap attempt already consumed")
    if set(ORDER) != set(KINDS):
        raise RuntimeError("service inventory changed")
    original = sorted(run("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=centrochange-dev").split())
    if len(original) != 9:
        raise RuntimeError("RC22 baseline count changed")
    initial_oom = oom_count()
    guard(state, original, initial_oom)
    if run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}"):
        raise RuntimeError("gated project already exists")
    if run("docker", "ps", "-q", "--filter", "label=centrochange.mission=C109"):
        raise RuntimeError("other C109 workload running")
    base = state / "compose-final-private.json"
    override = root / "compose-gated.override.json"
    config = json.loads((state / "compose-final.merged-private.json").read_text())
    if config["name"] != PROJECT or sum(int(s["mem_limit"]) for s in config["services"].values()) != 2 * 1024**3:
        raise RuntimeError("resource budget mismatch")
    if set(config["services"]) != set(ORDER):
        raise RuntimeError("gated service set changed")
    for service, expected in EXPECTED_MAX.items():
        item = config["services"][service]
        if int(item["mem_limit"]) != expected or int(item["memswap_limit"]) != expected:
            raise RuntimeError(f"service RAM/swap cap changed: {service}")
        if item.get("entrypoint") != ["/bin/sh", "/opt/cc-bootstrap.sh", KINDS[service]]:
            raise RuntimeError(f"inert PID1 gate missing: {service}")
    compose = ["docker", "compose", "--env-file", "/home/empv26/.local/state/centrochange-c109/runtime.env",
               "-f", str(base), "-f", str(override), "--project-name", PROJECT]
    (state / "app-attempted").write_text(now().isoformat())
    records = []
    try:
        with open(state / "compose-create.log", "w") as log:
            subprocess.run(compose + ["up", "--no-start", "--no-build", "--pull", "never"],
                           stdout=log, stderr=log, timeout=120, check=True)
        ids = run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}").split()
        if len(ids) != 8:
            raise RuntimeError("expected exactly eight gated containers")
        for service in ORDER:
            guard(state, original, initial_oom)
            short = run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}",
                        "--filter", f"label=com.docker.compose.service={service}")
            if len(short.split()) != 1:
                raise RuntimeError(f"service count mismatch: {service}")
            container = inspect(short)
            expected = EXPECTED_MAX[service]
            if container["running"] or container["memory"] != expected or container["swap"] != expected:
                raise RuntimeError(f"HostConfig mismatch before start: {service}")
            gate = root / "gates" / service / "release"
            if gate.exists():
                raise RuntimeError(f"stale release gate: {service}")
            start_requested = now().isoformat()
            run("docker", "start", container["id"])
            deadline = time.monotonic() + 2
            first = None
            last = None
            seen_valid = None
            while time.monotonic() < deadline:
                guard(state, original, initial_oom)
                current = inspect(container["id"])
                if not current["running"] or current["pid"] <= 0:
                    raise RuntimeError(f"inert PID exited: {service}")
                try:
                    snapshot = read_snapshot(current["pid"], container["id"], expected)
                    if first is None:
                        first = snapshot
                        seen_valid = time.monotonic()
                    elif snapshot.inode != first.inode:
                        raise RuntimeError(f"cgroup inode changed: {service}")
                    last = snapshot
                    if time.monotonic() - seen_valid >= 0.2:
                        break
                except CgroupGateError as exc:
                    if first is not None or str(exc) not in ("memory.max is max", "swap.max is max"):
                        raise RuntimeError(f"invalid cgroup after start: {service}: {exc}") from exc
                time.sleep(0.01)
            else:
                raise RuntimeError(f"cap did not stabilize before deadline: {service}")
            guard(state, original, initial_oom)
            gate.write_text(container["id"] + "\n")
            records.append({"service": service, "start_requested": start_requested, "released": now().isoformat(),
                            "container": container["id"], "pid": last.pid, "inode": last.inode,
                            "memory_max": last.memory_max, "swap_max": last.swap_max,
                            "ancestor_memory_max": last.ancestor_memory_max})
            (state / "released-services.json").write_text(json.dumps(records, indent=2))
            # Dependency services have native healthchecks; do not start their users
            # until Docker reports healthy. Other services must remain running.
            health_deadline = time.monotonic() + (90 if service in ("c-fit-db", "c-fit-redis-cache", "c-fit-redis-queue") else 15)
            while time.monotonic() < health_deadline:
                guard(state, original, initial_oom)
                status = run("docker", "inspect", "-f", "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", container["id"]).split()
                if status[0] != "running":
                    raise RuntimeError(f"service exited after release: {service}")
                if status[1] in ("healthy", "none"):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError(f"service health timeout: {service}")
        guard(state, original, initial_oom)
        (state / "app-bootstrap-green").write_text(now().isoformat())
    except BaseException:
        stop_only_ours(state)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_gated_start.py PRIVATE_ACTIVATION_ROOT")
    main(Path(sys.argv[1]))
