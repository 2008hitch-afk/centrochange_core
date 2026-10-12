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
from c109_compose_gate import KINDS, PROJECT, RETRY_PROJECT, FINAL_PROJECT, DEMO_PROJECT, LIGHT_QA_PROJECT, IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT
from c109_guard_access import require_live_guards
from c109_io_gate import (IOGateError, resolve_device, verify_cgroup,
                          verify_compose_config, verify_host_config)
from c109_protected_inventory import validate_existing
from c109_rc22_identity import verify as verify_rc22
from c109_r12_contract import require_attestation
from c109_r13_contract import require_attestation as require_r13_attestation
from c109_r12_writer import require_writer_lease, stop_exact_r12
from c109_r13_writer import require_writer_lease as require_r13_writer_lease, stop_exact_r13


ORDER = ["c-fit-db", "c-fit-redis-cache", "c-fit-redis-queue", "c-fit-backend",
         "c-fit-websocket", "c-fit-queue-long", "c-fit-scheduler", "c-fit-frontend"]
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


def guard(state, initial_oom):
    require_live_guards(state)
    target = json.loads((state / "activation.json").read_text()).get("target")
    if target == R12_PROJECT:
        require_writer_lease(state)
    if target == R13_PROJECT:
        require_r13_writer_lease(state)
    if (state / "safety-stop.json").exists() or (state / "protected-event-alert.json").exists():
        raise RuntimeError("host watchdog/protected event alert")
    for name in ("events-heartbeat", "monitor-heartbeat"):
        p = state / name
        if not p.exists() or time.time() - float(p.read_text()) > 12:
            raise RuntimeError(f"monitor heartbeat stale: {name}")
    if oom_count() != initial_oom or mem_available() < 768 * 1024**2:
        raise RuntimeError("OOM or host memory reserve")
    activation = json.loads((state / "activation.json").read_text())
    io_waiver = activation.get("target") in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT) and activation.get("io_waiver") is True
    if psi_full("memory") >= 1 or (not io_waiver and psi_full("io") >= 1):
        raise RuntimeError("host PSI full")
    if io_waiver or activation.get("target") == R13_PROJECT:
        from c109_rc22_monitor import require_rc22_monitor
        require_rc22_monitor(state)
    if os.statvfs("/").f_bavail * os.statvfs("/").f_frsize < 4 * 1024**3:
        raise RuntimeError("disk reserve")
    verify_rc22(state, run)
    if urllib.request.urlopen("http://127.0.0.1:8082/api/method/ping", timeout=5).status != 200:
        raise RuntimeError("RC22 HTTP changed")


def inspect(container):
    parts = run("docker", "inspect", "-f", "{{.Id}} {{.State.Pid}} {{.State.Running}} {{.HostConfig.Memory}} {{.HostConfig.MemorySwap}}", container).split()
    return {"id": parts[0], "pid": int(parts[1]), "running": parts[2] == "true",
            "memory": int(parts[3]), "swap": int(parts[4])}


def stop_only_ours(state, project):
    if project == R12_PROJECT:
        stop_exact_r12(run)
    elif project == R13_PROJECT:
        stop_exact_r13(run)
    else:
        ids = run("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={project}").split()
        if ids:
            subprocess.run(["docker", "stop", "--time", "10", *ids], timeout=60, check=True,
                           stdout=subprocess.DEVNULL)
    (state / "monitor-finish").write_text(now().isoformat())


def precreate_gate(root, *, attested=True):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if activation["issue"] != 109 or activation["status"] != "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP":
        raise RuntimeError("wrong activation")
    if activation.get("workload_release_allowed") is not True:
        raise RuntimeError("application workload release is not active")
    project = activation.get("target")
    if project not in (PROJECT, RETRY_PROJECT, FINAL_PROJECT, DEMO_PROJECT, LIGHT_QA_PROJECT, IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT):
        raise RuntimeError("unapproved isolated project")
    if project == R12_PROJECT and attested:
        require_attestation(root)
    if project == R13_PROJECT and attested:
        require_r13_attestation(root)
    if now() < dt.datetime.fromisoformat(activation["start_utc"]):
        raise RuntimeError("activation window has not opened")
    if now() >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("mutation window expired")
    if (state / "app-attempted").exists():
        raise RuntimeError("app bootstrap attempt already consumed")
    if set(ORDER) != set(KINDS):
        raise RuntimeError("service inventory changed")
    verify_rc22(state, run)
    initial_oom = oom_count()
    require_live_guards(state, max_proof_age=30)
    validate_existing((state / "protected-before.json").read_text(), run("docker", "ps", "-aq", "--no-trunc"))
    guard(state, initial_oom)
    if run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={project}"):
        raise RuntimeError("gated project already exists")
    if run("docker", "ps", "-q", "--filter", "label=centrochange.mission=C109"):
        raise RuntimeError("other C109 workload running")
    io_device = io_device_id = None
    if project == IO_CAPPED_PROJECT:
        io_device, io_device_id = resolve_device(state)
        if (activation.get("io_device"), activation.get("io_device_id")) != (io_device, io_device_id):
            raise RuntimeError("authorized I/O device differs from live device")
    base = state / "compose-final-private.json"
    override = root / "compose-gated.override.json"
    if not base.is_file() or not override.is_file():
        raise RuntimeError("private R12 Compose input missing")
    config = json.loads((state / "compose-final.merged-private.json").read_text())
    if config["name"] != project or sum(int(s["mem_limit"]) for s in config["services"].values()) != 2 * 1024**3:
        raise RuntimeError("resource budget mismatch")
    if set(config["services"]) != set(ORDER):
        raise RuntimeError("gated service set changed")
    if (len(config.get("volumes", {})), len(config.get("networks", {}))) != (5, 2):
        raise RuntimeError("C109 volume/network inventory changed")
    for kind in ("volumes", "networks"):
        for item in config.get(kind, {}).values():
            if not isinstance(item, dict) or not item.get("name", "").startswith("centrochange-c109-"):
                raise RuntimeError(f"non-isolated C109 {kind} resource")
    normalized = json.loads(run("docker", "compose", "--env-file",
        "/home/empv26/.local/state/centrochange-c109/runtime.env", "-f", str(base),
        "-f", str(override), "--project-name", project, "config", "--format", "json"))
    if normalized != config:
        raise RuntimeError("C109 Compose inputs differ from approved merged config")
    for kind in ("volumes", "networks"):
        docker_kind = "volume" if kind == "volumes" else "network"
        for item in config[kind].values():
            name = item["name"]
            if run("docker", docker_kind, "inspect", "-f", "{{.Name}}", name) != name:
                raise RuntimeError(f"C109 isolated {kind} resource missing or changed")
    for service, expected in EXPECTED_MAX.items():
        item = config["services"][service]
        if project in (R12_PROJECT, R13_PROJECT) and item.get("labels", {}).get("centrochange.mission") != "C109":
            raise RuntimeError(f"R12 service lacks exact stop ownership: {service}")
        if int(item["mem_limit"]) != expected or int(item["memswap_limit"]) != expected:
            raise RuntimeError(f"service RAM/swap cap changed: {service}")
        if item.get("entrypoint") != ["/bin/sh", "/opt/cc-bootstrap.sh", KINDS[service]]:
            raise RuntimeError(f"inert PID1 gate missing: {service}")
        if project == IO_CAPPED_PROJECT:
            verify_compose_config(item.get("blkio_config") or {}, io_device)
        if project in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT) and item.get("blkio_config"):
            raise RuntimeError("I/O waiver project still has artificial I/O cap")
    return state, activation, project, base, override


def main(root):
    state, activation, project, base, override = precreate_gate(root)
    initial_oom = oom_count()
    guard(state, initial_oom)
    if project == R12_PROJECT:
        require_attestation(root)
    if project == R13_PROJECT:
        require_r13_attestation(root)
    compose = ["docker", "compose", "--env-file", "/home/empv26/.local/state/centrochange-c109/runtime.env",
               "-f", str(base), "-f", str(override), "--project-name", project]
    (state / "app-attempted").write_text(now().isoformat())
    records = []
    try:
        with open(state / "compose-create.log", "w") as log:
            subprocess.run(compose + ["up", "--no-start", "--no-build", "--pull", "never"],
                           stdout=log, stderr=log, timeout=120, check=True)
        ids = run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={project}").split()
        if len(ids) != 8:
            raise RuntimeError("expected exactly eight gated containers")
        for service in ORDER:
            guard(state, initial_oom)
            short = run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={project}",
                        "--filter", f"label=com.docker.compose.service={service}")
            if len(short.split()) != 1:
                raise RuntimeError(f"service count mismatch: {service}")
            container = inspect(short)
            expected = EXPECTED_MAX[service]
            if container["running"] or container["memory"] != expected or container["swap"] != expected:
                raise RuntimeError(f"HostConfig mismatch before start: {service}")
            if project == IO_CAPPED_PROJECT:
                verify_host_config(json.loads(run("docker", "inspect", "-f", "{{json .HostConfig}}", container["id"])),
                                   io_device)
            if project in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT):
                host_config = json.loads(run("docker", "inspect", "-f", "{{json .HostConfig}}", container["id"]))
                if host_config.get("BlkioDeviceReadBps") or host_config.get("BlkioDeviceWriteBps"):
                    raise RuntimeError(f"r7 HostConfig still I/O capped: {service}")
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
                guard(state, initial_oom)
                current = inspect(container["id"])
                if not current["running"] or current["pid"] <= 0:
                    raise RuntimeError(f"inert PID exited: {service}")
                try:
                    snapshot = read_snapshot(current["pid"], container["id"], expected)
                    if project == IO_CAPPED_PROJECT:
                        verify_cgroup(snapshot.relative_path, io_device_id)
                    if first is None:
                        first = snapshot
                        seen_valid = time.monotonic()
                    elif snapshot.inode != first.inode:
                        raise RuntimeError(f"cgroup inode changed: {service}")
                    last = snapshot
                    if time.monotonic() - seen_valid >= 0.2:
                        break
                except (CgroupGateError, IOGateError) as exc:
                    if first is not None or (isinstance(exc, CgroupGateError)
                                             and str(exc) not in ("memory.max is max", "swap.max is max")):
                        raise RuntimeError(f"invalid cgroup after start: {service}: {exc}") from exc
                time.sleep(0.01)
            else:
                raise RuntimeError(f"cap did not stabilize before deadline: {service}")
            guard(state, initial_oom)
            gate.write_text(container["id"] + "\n")
            records.append({"service": service, "start_requested": start_requested, "released": now().isoformat(),
                            "container": container["id"], "pid": last.pid, "inode": last.inode,
                            "memory_max": last.memory_max, "swap_max": last.swap_max,
                            "ancestor_memory_max": last.ancestor_memory_max})
            (state / "released-services.json").write_text(json.dumps(records, indent=2))
            # Dependency services have native healthchecks; do not start their users
            # until Docker reports healthy. Other services must remain running.
            health_deadline = time.monotonic() + (120 if project == IO_CAPPED_PROJECT else
                                                   90 if service in ("c-fit-db", "c-fit-redis-cache", "c-fit-redis-queue") else 15)
            while time.monotonic() < health_deadline:
                guard(state, initial_oom)
                status = run("docker", "inspect", "-f", "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", container["id"]).split()
                if status[0] != "running":
                    raise RuntimeError(f"service exited after release: {service}")
                if status[1] in ("healthy", "none"):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError(f"service health timeout: {service}")
            if project in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT):
                # Do not overlap the next cold-start read with a previous
                # service's I/O pressure. The host watchdog remains active.
                stable = 0
                settle_deadline = time.monotonic() + (180 if project in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT) else 90)
                while stable < 3:
                    guard(state, initial_oom)
                    threshold = 0.1 if project == R13_PROJECT else 5 if project in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT) else 0.1
                    stable = stable + 1 if psi_full("io") < threshold else 0
                    if time.monotonic() >= settle_deadline:
                        raise RuntimeError("host I/O did not settle before next service")
                    time.sleep(5)
        guard(state, initial_oom)
        (state / "app-bootstrap-green").write_text(now().isoformat())
    except BaseException:
        stop_only_ours(state, project)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_gated_start.py PRIVATE_ACTIVATION_ROOT")
    root = Path(sys.argv[1])
    try:
        main(root)
    except BaseException:
        # The new I/O-capped activation is single-use even when a gate fails
        # before Compose creates its first container.
        state = root / "app-run"
        try:
            activation = json.loads((state / "activation.json").read_text())
            if activation.get("target") in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT) and not (state / "monitor-finish").exists():
                stop_only_ours(state, activation["target"])
        except (OSError, ValueError):
            pass
        raise
