"""Single-use, inert C109 cgroup diagnostic. No application workload or cleanup.

Run only with an Owner-authorized activation JSON in a private state directory.
The historical R3 watchdog is copied byte-for-byte and started before Docker start.
"""

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading
import time
import urllib.request


IMAGE = "centrochange-g2d-browser:e85fce588de6-pw1582"
IMAGE_ID = "sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3"
NAME = "centrochange-c109-diag01"
LIMIT = 512 * 1024 * 1024
SOURCE = pathlib.Path("/home/empv26/.local/state/centrochange-c109/recovery-20261010-r3")


def cmd(*args):
    return subprocess.check_output(args, text=True, timeout=20).strip()


def one(path):
    return pathlib.Path(path).read_text().strip()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def heartbeat_ok(path):
    return path.exists() and time.time() - float(one(path)) < 10


def ping():
    return urllib.request.urlopen("http://127.0.0.1:8082/api/method/ping", timeout=5).status


def mem_available():
    return int(next(line.split()[1] for line in open("/proc/meminfo") if line.startswith("MemAvailable:"))) * 1024


def oom_count():
    return int(next(line.split()[1] for line in open("/proc/vmstat") if line.startswith("oom_kill ")))


def psi(kind):
    return {line.split()[0]: {p.split("=")[0]: float(p.split("=")[1]) for p in line.split()[1:]} for line in open(f"/proc/pressure/{kind}")}


def rc22():
    ids = cmd("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=centrochange-dev").split()
    return sorted(ids)


def running_c109():
    return cmd("docker", "ps", "-q", "--filter", "label=centrochange.mission=C109").split()


def inspect(container):
    fields = cmd("docker", "inspect", "-f", "{{.State.Pid}} {{.State.Running}} {{.HostConfig.Memory}} {{.HostConfig.MemorySwap}} {{.State.StartedAt}}", container).split()
    return {"pid": int(fields[0]), "running": fields[1] == "true", "memory": int(fields[2]), "swap": int(fields[3]), "started_at": fields[4]}


def cgroup_of_pid(pid):
    if pid <= 0:
        return None
    for line in pathlib.Path(f"/proc/{pid}/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            return line[3:]
    return None


def hierarchy(cg):
    root = pathlib.Path("/sys/fs/cgroup")
    parts = pathlib.PurePosixPath(cg).parts[1:]
    paths = [root]
    for part in parts:
        paths.append(paths[-1] / part)
    return [{"path": str(path), "inode": path.stat().st_ino,
             "memory_max": one(path / "memory.max"), "swap_max": one(path / "memory.swap.max")}
            for path in paths]


def probe(container, records, stop, error):
    expected = f"/system.slice/docker-{container}.scope"
    host_path = pathlib.Path("/sys/fs/cgroup") / expected.lstrip("/")
    last = None
    started = time.monotonic()
    while not stop.is_set() and time.monotonic() - started < 12:
        stamp = now()
        if host_path.exists():
            try:
                populated = "populated 1" in one(host_path / "cgroup.events")
                cap = one(host_path / "memory.max")
                swap = one(host_path / "memory.swap.max")
                inode = host_path.stat().st_ino
                item = {"time": stamp, "path": expected, "inode": inode,
                        "populated": populated, "memory_max": cap, "swap_max": swap}
                state_key = (populated, cap, swap, inode)
                if state_key != last:
                    records.append(item)
                    last = state_key
                if populated and (cap != str(LIMIT) or swap != "0"):
                    error.append("CAP_NOT_ENFORCED_EARLY_SAMPLE")
                    stop.set()
                    return
            except FileNotFoundError:
                pass
        time.sleep(0.002)


def main(run):
    activation = json.loads((run / "activation.json").read_text())
    if activation["issue"] != 122 or activation["status"] != "OWNER_AUTHORIZED_SINGLE_PROBE":
        raise RuntimeError("activation not authorized")
    if dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(activation["start_utc"]):
        raise RuntimeError("activation not started")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("mutation window expired")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["hard_stop_utc"]):
        raise RuntimeError("activation expired")
    if (run / "attempted").exists():
        raise RuntimeError("single attempt already consumed; no retry")
    if cmd("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}") != IMAGE_ID:
        raise RuntimeError("image mismatch")
    if running_c109() or cmd("docker", "ps", "-aq", "--filter", f"name=^{NAME}$"):
        raise RuntimeError("C109 already running or diagnostic name reused")
    before = {"time": now(), "rc22": rc22(), "http": ping(), "oom": oom_count(),
              "memory_available": mem_available(), "memory_psi": psi("memory"), "io_psi": psi("io"),
              "disk_available": os.statvfs("/").f_bavail * os.statvfs("/").f_frsize,
              "container_count": len(cmd("docker", "ps", "-aq").split()),
              "volume_count": len(cmd("docker", "volume", "ls", "-q").split())}
    if len(before["rc22"]) != 9 or before["http"] != 200 or before["oom"] != 7:
        raise RuntimeError("protected baseline mismatch")
    if before["memory_available"] < 3 * 1024**3 or before["disk_available"] < 4 * 1024**3:
        raise RuntimeError("resource reserve")
    if before["memory_psi"]["full"]["avg10"] >= 1 or before["io_psi"]["full"]["avg10"] >= 1:
        raise RuntimeError("pressure preflight")
    (run / "preflight.json").write_text(json.dumps(before, indent=2))
    # The marker is written before the only Docker create. A failure still consumes the attempt.
    (run / "attempted").write_text(now())
    container = None
    monitors = []
    stop = threading.Event()
    records = []
    errors = []
    try:
        container = cmd("docker", "create", "--name", NAME,
                        "--label", "centrochange.mission=C109", "--label", "centrochange.phase=lab",
                        "--label", "centrochange.heavy=false", "--network", "none", "--read-only",
                        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "32",
                        "--memory", str(LIMIT), "--memory-swap", str(LIMIT),
                        "--entrypoint", "/bin/sh", IMAGE, "-c", "sleep 300")
        configured = inspect(container)
        if configured["memory"] != LIMIT or configured["swap"] != LIMIT or configured["running"]:
            raise RuntimeError("Docker HostConfig mismatch before start")
        protected = [dict(id=cid) for cid in cmd("docker", "ps", "-aq").split() if cid != container]
        (run / "protected-before.json").write_text(json.dumps(protected))
        (run / "own-containers.json").write_text(json.dumps({container: {"name": "/" + NAME, "heavy": False, "phase": "lab"}}))
        (run / "events-heartbeat").write_text(str(time.time()))
        for name in ("safety.py", "protected-events.py"):
            shutil.copyfile(SOURCE / name, run / name)
        (run / "source-hashes.json").write_text(json.dumps({name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in ("safety.py", "protected-events.py")}))
        for name in ("protected-events.py", "safety.py"):
            log = open(run / (name + ".log"), "w")
            monitors.append((subprocess.Popen([sys.executable, str(run / name)], cwd=run, stdout=log, stderr=log), log))
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if heartbeat_ok(run / "events-heartbeat") and heartbeat_ok(run / "monitor-heartbeat"):
                break
            if any(process.poll() is not None for process, _ in monitors):
                raise RuntimeError("watchdog failed before start")
            time.sleep(0.1)
        else:
            raise RuntimeError("watchdog not ready")
        if (run / "safety-stop.json").exists() or (run / "protected-event-alert.json").exists():
            raise RuntimeError("watchdog alert before start")
        thread = threading.Thread(target=probe, args=(container, records, stop, errors), daemon=True)
        thread.start()
        (run / "start-issued-at").write_text(now())
        cmd("docker", "start", container)
        # No application command is ever released: PID 1 remains the inert sleep.
        state = inspect(container)
        if state["pid"] <= 0 or not state["running"]:
            errors.append("container exited before PID verification")
        else:
            actual = cgroup_of_pid(state["pid"])
            expected = f"/system.slice/docker-{container}.scope"
            (run / "pid-check.json").write_text(json.dumps({"time": now(), "pid": state["pid"],
                "actual_cgroup": actual, "expected_cgroup": expected,
                "hierarchy": hierarchy(actual) if actual else None,
                "host_config_memory": state["memory"], "host_config_swap": state["swap"],
                "docker_started_at": state["started_at"]}, indent=2))
            if actual != expected:
                errors.append("PID_CGROUP_PATH_MISMATCH")
        if not errors and not stop.is_set():
            until = time.monotonic() + 2
            while time.monotonic() < until and not stop.is_set():
                if (run / "safety-stop.json").exists() or (run / "protected-event-alert.json").exists():
                    errors.append("WATCHDOG_ALERT")
                    break
                time.sleep(0.02)
    finally:
        stop.set()
        if container:
            # Stop only this diagnostic container; retain it for forensic inspection.
            if inspect(container)["running"]:
                subprocess.run(["docker", "stop", "--time", "3", container], timeout=15, check=True,
                               stdout=subprocess.DEVNULL)
        (run / "monitor-finish").write_text(now())
        for process, log in monitors:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
            log.close()
        (run / "samples.json").write_text(json.dumps(records, indent=2))
        after = {"time": now(), "rc22": rc22(), "http": ping(), "oom": oom_count(),
                 "memory_available": mem_available(), "memory_psi": psi("memory"), "io_psi": psi("io"),
                 "disk_available": os.statvfs("/").f_bavail * os.statvfs("/").f_frsize,
                 "running_c109": running_c109(), "container_running": inspect(container)["running"] if container else None,
                 "safety_stop": (run / "safety-stop.json").exists(),
                 "protected_alert": (run / "protected-event-alert.json").exists()}
        (run / "result.json").write_text(json.dumps({"before": before, "after": after, "errors": errors,
             "records": len(records), "container": container,
             "protected_unchanged": before["rc22"] == after["rc22"] and after["http"] == 200,
             "oom_unchanged": before["oom"] == after["oom"]}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_diag01_probe.py PRIVATE_RUN_DIR")
    main(pathlib.Path(sys.argv[1]))
