"""Run C109 guards in the caller's existing Docker-authorized user scope.

Transient systemd *services* inherit the user manager's stale groups on this
host. A transient --scope inherits the caller's credentials. No group, socket,
Docker daemon, or existing service configuration is changed here.
"""

import datetime as dt
import json
import os
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import tempfile
import threading
import time
from c109_compose_gate import IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT


SOCKET = Path("/var/run/docker.sock")
ROLES = {"events": "protected-events.py", "watchdog": "safety.py",
         "expiry": "c109_demo_expiry.py", "rc22": "c109_rc22_monitor.py"}
PROOF_MAX_AGE = 30
RENEW_INTERVAL = 8


def command(*args, timeout=8):
    return subprocess.check_output(args, text=True, timeout=timeout, stderr=subprocess.PIPE).strip()


def process_start_ticks(pid):
    # /proc/<pid>/stat field 22; the command in parentheses may contain spaces.
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[19])


def check_access(role):
    if role not in ROLES:
        raise ValueError("unknown C109 guard role")
    if os.environ.get("DOCKER_HOST") not in (None, "", "unix:///var/run/docker.sock"):
        raise RuntimeError("unexpected Docker endpoint override")
    if os.environ.get("DOCKER_CONTEXT") not in (None, "", "default"):
        raise RuntimeError("unexpected Docker context override")
    info = SOCKET.stat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_gid not in (*os.getgroups(), os.getegid()):
        raise RuntimeError("Docker socket unavailable to effective groups")
    if command("docker", "context", "show") != "default":
        raise RuntimeError("Docker context is not default")
    if command("docker", "context", "inspect", "default", "--format", "{{.Endpoints.docker.Host}}") != "unix:///var/run/docker.sock":
        raise RuntimeError("Docker context endpoint changed")
    if not command("docker", "version", "--format", "{{.Server.Version}}"):
        raise RuntimeError("Docker API unavailable")
    command("docker", "ps", "-q")
    if role == "events":
        # A live subscription must remain connected until the local timeout.
        result = subprocess.run(["timeout", "2", "docker", "events", "--format", "{{json .}}"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode != 124:
            raise RuntimeError("Docker event stream unavailable")
    return {"pid": os.getpid(), "start_ticks": process_start_ticks(os.getpid()),
            "uid": os.getuid(), "euid": os.geteuid(), "egid": os.getegid(),
            "groups": sorted(set(os.getgroups())),
            "socket_gid": info.st_gid, "docker_host": "unix:///var/run/docker.sock",
            "docker_context": "default", "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}


def marker_path(state, role):
    return state / f"guard-access-{role}.json"


def atomic_json(path, value):
    """Publish only a complete, newly verified proof in the private state dir."""
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def heartbeat_path(state, role):
    if role == "expiry":
        return None
    return state / {"events": "events-heartbeat", "watchdog": "monitor-heartbeat",
                    "rc22": "rc22-heartbeat"}[role]


def require_heartbeat(state, role):
    heartbeat = heartbeat_path(state, role)
    if heartbeat is None:
        return  # Expiry's own renewed proof is its heartbeat.
    try:
        age = time.time() - float(heartbeat.read_text())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"C109 {role} heartbeat missing") from exc
    if age < -2 or age > (8 if role == "rc22" else 12):
        raise RuntimeError(f"C109 {role} heartbeat stale")


def proof_age(proof):
    stamp = dt.datetime.fromisoformat(proof["checked_at"])
    if stamp.utcoffset() is None:
        raise ValueError("guard proof has no timezone")
    return time.time() - stamp.timestamp()


def renew_once(state, role, previous):
    """Called only inside the guard PID; never refresh an unverified marker."""
    if (state / "monitor-finish").exists():
        return previous
    current = json.loads(marker_path(state, role).read_text())
    if current != previous:
        raise RuntimeError(f"C109 {role} guard marker changed outside its process")
    if current["pid"] != os.getpid() or current["start_ticks"] != process_start_ticks(os.getpid()):
        raise RuntimeError(f"C109 {role} guard process identity changed")
    if not -2 <= proof_age(current) <= PROOF_MAX_AGE:
        raise RuntimeError(f"C109 {role} Docker access proof is stale")
    require_heartbeat(state, role)
    refreshed = check_access(role)
    require_heartbeat(state, role)
    for field in ("pid", "start_ticks", "uid", "euid", "egid", "groups", "socket_gid",
                  "docker_host", "docker_context"):
        if refreshed[field] != current[field]:
            raise RuntimeError(f"C109 {role} Docker guard context changed: {field}")
    if proof_age(refreshed) < -2 or refreshed["checked_at"] <= current["checked_at"]:
        raise RuntimeError(f"C109 {role} Docker proof clock did not advance")
    if json.loads(marker_path(state, role).read_text()) != previous:
        raise RuntimeError(f"C109 {role} guard marker changed during verification")
    atomic_json(marker_path(state, role), refreshed)
    return refreshed


def require_live_guards(state, max_proof_age=PROOF_MAX_AGE):
    if max_proof_age is None or max_proof_age > PROOF_MAX_AGE:
        raise ValueError("C109 Docker proof lifetime cannot be extended")
    if (state / "guard-access-alert.json").exists():
        raise RuntimeError("C109 Docker guard renewal failed")
    roles = ("events", "watchdog", "expiry")
    if ((state / "activation.json").exists()
            and json.loads((state / "activation.json").read_text()).get("target") in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT)):
        roles += ("rc22",)
    for role in roles:
        marker_file = marker_path(state, role)
        info = marker_file.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise RuntimeError(f"C109 {role} guard marker is not private and regular")
        marker = json.loads(marker_file.read_text())
        if marker["pid"] <= 0 or marker["start_ticks"] != process_start_ticks(marker["pid"]):
            raise RuntimeError(f"C109 {role} guard is not the verified live process")
        age = proof_age(marker)
        if age < -2 or age > max_proof_age:
            raise RuntimeError(f"C109 {role} Docker access proof is stale")
        require_heartbeat(state, role)


def renewal_loop(state, role, initial):
    proof = initial
    # Stop is observed before every probe; no proof is renewed after monitor-finish.
    while not (state / "monitor-finish").exists():
        time.sleep(RENEW_INTERVAL)
        if (state / "monitor-finish").exists():
            return
        try:
            proof = renew_once(state, role, proof)
            if (state / "guard-scopes.json").exists():
                require_live_guards(state)
        except BaseException as exc:
            try:
                atomic_json(state / "guard-access-alert.json", {"role": role,
                            "reason": type(exc).__name__, "time": dt.datetime.now(dt.timezone.utc).isoformat()})
            finally:
                try:
                    from c109_gated_start import stop_only_ours
                    target = json.loads((state / "activation.json").read_text())["target"]
                    stop_only_ours(state, target)
                finally:
                    os._exit(2)


def serve(role, root):
    state = root / "app-run"
    if marker_path(state, role).exists():
        raise RuntimeError("guard access marker already exists")
    proof = check_access(role)
    atomic_json(marker_path(state, role), proof)
    threading.Thread(target=renewal_loop, args=(state, role, proof), daemon=True,
                     name=f"c109-{role}-docker-proof").start()
    if role == "expiry":
        script, argv = Path(__file__).with_name(ROLES[role]), ["--wait", str(root)]
    elif role == "rc22":
        script, argv = Path(__file__).with_name(ROLES[role]), [str(root)]
    else:
        script, argv = state / ROLES[role], []
    old_argv = sys.argv
    sys.argv = [str(script), *argv]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = old_argv


def scope_probe(role):
    unit = f"centrochange-c109-{role}-access-{os.getpid()}"
    command("systemd-run", "--user", "--scope", "--collect", f"--unit={unit}",
            sys.executable, str(Path(__file__)), "probe", role, timeout=12)


def launch_scopes(root):
    """Start only guard scopes, after proving their actual inherited credentials."""
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("issue") != 109 or activation.get("target") not in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT)
            or activation.get("status") != "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP"):
        raise RuntimeError("wrong C109 demo activation")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["hard_stop_utc"]):
        raise RuntimeError("demo deadline expired")
    if ((state / "app-attempted").exists() or (state / "monitor-finish").exists()
            or any(marker_path(state, role).exists() for role in ROLES)):
        raise RuntimeError("activation or guard launch already attempted")
    roles = ("rc22", "events", "watchdog", "expiry") if activation["target"] in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT) else ("events", "watchdog", "expiry")
    for role in roles:
        scope_probe(role)
    launched = []
    try:
        for role in roles:
            unit = f"centrochange-c109-{role}-{os.getpid()}"
            with open(state / f"{role}-scope.log", "w") as log:
                process = subprocess.Popen(["systemd-run", "--user", "--scope", "--collect",
                                            f"--unit={unit}", sys.executable, str(Path(__file__)),
                                            "serve", role, str(root)], stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=log, start_new_session=True)
            launched.append((unit, process))
            deadline = time.monotonic() + 10
            heartbeat = state / ("events-heartbeat" if role == "events" else "rc22-heartbeat" if role == "rc22" else "monitor-heartbeat")
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"C109 {role} scope exited before readiness")
                if (state / "protected-event-alert.json").exists() or (state / "safety-stop.json").exists():
                    raise RuntimeError("C109 guard tripped before readiness")
                if marker_path(state, role).exists() and (role == "expiry" or
                        (heartbeat.exists() and time.time() - float(heartbeat.read_text()) < 5)):
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError(f"C109 {role} scope not ready")
        require_live_guards(state, max_proof_age=30)
        (state / "guard-scopes.json").write_text(json.dumps([unit for unit, _ in launched]))
    except BaseException:
        for unit, _ in reversed(launched):
            subprocess.run(["systemctl", "--user", "stop", f"{unit}.scope"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "probe":
        check_access(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == "preflight":
        for role in ROLES:
            scope_probe(role)
    elif len(sys.argv) == 3 and sys.argv[1] == "launch":
        launch_scopes(Path(sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[1] == "serve":
        serve(sys.argv[2], Path(sys.argv[3]))
    else:
        raise SystemExit("usage: c109_guard_access.py preflight | launch PRIVATE_ROOT | probe ROLE | serve ROLE PRIVATE_ROOT")
