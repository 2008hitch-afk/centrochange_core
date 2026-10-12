"""R13 Docker writer lease and exact, fail-closed stop ownership.

The watchdog holds the writer lease. The launcher probes it before launch and
requires the watchdog's live lease before every Docker mutation.
"""

import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from c109_compose_gate import R13_PROJECT
from c109_guard_access import atomic_json, marker_path, process_start_ticks


FULL_ID = re.compile(r"[0-9a-f]{64}\Z")
MISSION = "C109"


def writer_lock_path():
    return Path(f"/run/user/{os.getuid()}/centrochange-docker-writer.lock")


def probe_writer_available(lock_file=None):
    """Readiness probe only; releases before the watchdog claims the lease."""
    path = lock_file or writer_lock_path()
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another Docker writer holds the C109 lock") from exc
        fcntl.flock(stream, fcntl.LOCK_UN)


def claim_writer_lease(state, lock_file=None):
    """Called inside the watchdog process; the returned descriptor stays open."""
    activation = json.loads((state / "activation.json").read_text())
    if activation.get("target") != R13_PROJECT or activation.get("issue") != 109:
        raise RuntimeError("wrong R13 writer activation")
    marker = state / "writer-lease.json"
    if marker.exists():
        raise RuntimeError("R13 writer lease already claimed")
    path = lock_file or writer_lock_path()
    stream = path.open("a")
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        info = os.fstat(stream.fileno())
        atomic_json(marker, {"pid": os.getpid(), "start_ticks": process_start_ticks(os.getpid()),
                             "device": info.st_dev, "inode": info.st_ino})
        return stream
    except BaseException:
        stream.close()
        raise


def require_writer_lease(state, lock_file=None):
    """Require live watchdog identity and a still-held, unchanged writer lock."""
    path = state / "writer-lease.json"
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600):
        raise RuntimeError("R13 writer lease marker is not private")
    lease = json.loads(path.read_text())
    watchdog = json.loads(marker_path(state, "watchdog").read_text())
    if (lease.get("pid") != watchdog.get("pid") or lease.get("start_ticks") != watchdog.get("start_ticks")
            or lease["start_ticks"] != process_start_ticks(lease["pid"])):
        raise RuntimeError("R13 writer lease is not owned by live watchdog")
    with (lock_file or writer_lock_path()).open("a") as stream:
        current = os.fstat(stream.fileno())
        if (current.st_dev, current.st_ino) != (lease.get("device"), lease.get("inode")):
            raise RuntimeError("R13 writer lock file changed")
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        else:
            fcntl.flock(stream, fcntl.LOCK_UN)
            raise RuntimeError("R13 watchdog no longer holds Docker writer lock")


def exact_owned_ids(run=None):
    """Require both labels and independently inspect every full container ID."""
    if run is None:
        def run(*args):
            return subprocess.check_output(args, text=True, timeout=10, stderr=subprocess.DEVNULL).strip()
    ids = run("docker", "ps", "-q", "--no-trunc", "--filter",
              f"label=com.docker.compose.project={R13_PROJECT}", "--filter", f"label=centrochange.mission={MISSION}").split()
    if len(ids) != len(set(ids)) or any(not FULL_ID.fullmatch(item) for item in ids):
        raise RuntimeError("R13 stop inventory has ambiguous Docker IDs")
    for container_id in ids:
        labels = json.loads(run("docker", "inspect", "-f", "{{json .Config.Labels}}", container_id))
        if (labels.get("com.docker.compose.project") != R13_PROJECT
                or labels.get("centrochange.mission") != MISSION):
            raise RuntimeError("R13 stop ownership mismatch")
    return ids


def stop_exact_r13(run=None, execute=None):
    """Stop only independently verified R13/C109 IDs, including copy helpers."""
    ids = exact_owned_ids(run)
    if execute is None:
        def execute(args, *, timeout):
            return subprocess.run(args, timeout=timeout, check=False,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    for container_id in ids:
        # A paused C109 container must be made stoppable; only validated IDs
        # reach this point. Unpause may harmlessly fail for an unpaused one.
        execute(["docker", "unpause", container_id], timeout=15)
    if ids and execute(["docker", "stop", "--time", "10", *ids], timeout=60):
        raise RuntimeError("targeted R13 stop failed")
    return ids
