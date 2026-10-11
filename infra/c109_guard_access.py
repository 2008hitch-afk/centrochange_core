"""Run C109 guards in the caller's existing Docker-authorized user scope.

Transient systemd *services* inherit the user manager's stale groups on this
host. A transient --scope inherits the caller's credentials. No group, socket,
Docker daemon, or existing service configuration is changed here.
"""

import datetime as dt
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from c109_compose_gate import IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT


SOCKET = Path("/var/run/docker.sock")
ROLES = {"events": "protected-events.py", "watchdog": "safety.py",
         "expiry": "c109_demo_expiry.py", "rc22": "c109_rc22_monitor.py"}


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
            "socket_gid": info.st_gid, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}


def marker_path(state, role):
    return state / f"guard-access-{role}.json"


def require_live_guards(state, max_proof_age=None):
    roles = ("events", "watchdog", "expiry")
    if ((state / "activation.json").exists()
            and json.loads((state / "activation.json").read_text()).get("target") in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT)):
        roles += ("rc22",)
    for role in roles:
        marker = json.loads(marker_path(state, role).read_text())
        if marker["pid"] <= 0 or marker["start_ticks"] != process_start_ticks(marker["pid"]):
            raise RuntimeError(f"C109 {role} guard is not the verified live process")
        if max_proof_age is not None and time.time() - dt.datetime.fromisoformat(marker["checked_at"]).timestamp() > max_proof_age:
            raise RuntimeError(f"C109 {role} Docker access proof is stale")


def serve(role, root):
    state = root / "app-run"
    if marker_path(state, role).exists():
        raise RuntimeError("guard access marker already exists")
    proof = check_access(role)
    marker_path(state, role).write_text(json.dumps(proof))
    if role == "expiry":
        os.execv(sys.executable, [sys.executable, str(Path(__file__).with_name(ROLES[role])),
                                   "--wait", str(root)])
    if role == "rc22":
        os.execv(sys.executable, [sys.executable, str(Path(__file__).with_name(ROLES[role])),
                                   str(root)])
    os.execv(sys.executable, [sys.executable, str(state / ROLES[role])])


def scope_probe(role):
    unit = f"centrochange-c109-{role}-access-{os.getpid()}"
    command("systemd-run", "--user", "--scope", "--collect", f"--unit={unit}",
            sys.executable, str(Path(__file__)), "probe", role, timeout=12)


def launch_scopes(root):
    """Start only guard scopes, after proving their actual inherited credentials."""
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("issue") != 109 or activation.get("target") not in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT)
            or activation.get("status") != "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP"):
        raise RuntimeError("wrong C109 demo activation")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["hard_stop_utc"]):
        raise RuntimeError("demo deadline expired")
    if ((state / "app-attempted").exists() or (state / "monitor-finish").exists()
            or any(marker_path(state, role).exists() for role in ROLES)):
        raise RuntimeError("activation or guard launch already attempted")
    roles = ("rc22", "events", "watchdog", "expiry") if activation["target"] in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT) else ("events", "watchdog", "expiry")
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
