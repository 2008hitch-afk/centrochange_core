"""Read-only host PID/cgroup verification for isolated Mission C bootstrap.

This module is a diagnostic gate, not a replacement for the host watchdog.
Only an inert PID1 may be observed before this gate returns a verified snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import time


class CgroupGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Snapshot:
    sampled_ns: int
    pid: int
    relative_path: str
    inode: int
    memory_max: int
    swap_max: int
    memory_current: int
    ancestor_memory_max: tuple[int | None, ...]
    oom: int
    oom_kill: int


def _required(path: Path) -> str:
    try:
        return path.read_text().strip()
    except (FileNotFoundError, PermissionError) as exc:
        raise CgroupGateError(f"missing or unreadable cgroup file: {path.name}") from exc


def _number(value: str, field: str) -> int:
    if value == "max":
        raise CgroupGateError(f"{field} is max")
    try:
        number = int(value)
    except ValueError as exc:
        raise CgroupGateError(f"invalid {field}") from exc
    if number < 0:
        raise CgroupGateError(f"negative {field}")
    return number


def read_snapshot(
    pid: int,
    container_id: str,
    expected_memory: int,
    *,
    proc_root: Path = Path("/proc"),
    cgroup_root: Path = Path("/sys/fs/cgroup"),
) -> Snapshot:
    """Require the exact systemd scope of a live host PID and exact RAM/swap caps.

    The cgroup v2 root may lack memory.max. Missing root files are represented by
    None, while missing target-scope files fail closed.
    """
    if pid <= 0 or not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise CgroupGateError("invalid PID or container ID")
    if expected_memory <= 0:
        raise CgroupGateError("invalid expected cap")
    raw = _required(proc_root / str(pid) / "cgroup")
    entries = [line[3:] for line in raw.splitlines() if line.startswith("0::")]
    if len(entries) != 1:
        raise CgroupGateError("missing or ambiguous cgroup v2 entry")
    relative = entries[0]
    expected = f"/system.slice/docker-{container_id}.scope"
    if relative != expected:
        raise CgroupGateError("PID cgroup does not match Docker container scope")
    parts = PurePosixPath(relative).parts[1:]
    directories = [cgroup_root]
    for part in parts:
        directories.append(directories[-1] / part)
    target = directories[-1]
    if not target.is_dir():
        raise CgroupGateError("PID cgroup path absent on host")
    if "populated 1" not in _required(target / "cgroup.events"):
        raise CgroupGateError("PID cgroup not populated")
    memory = _number(_required(target / "memory.max"), "memory.max")
    swap = _number(_required(target / "memory.swap.max"), "memory.swap.max")
    if memory != expected_memory or swap != 0:
        raise CgroupGateError("RAM/swap cap mismatch")
    limits = []
    for directory in directories:
        path = directory / "memory.max"
        if not path.exists():
            if directory != cgroup_root:
                raise CgroupGateError("ancestor memory.max missing")
            limits.append(None)
        else:
            value = _required(path)
            limits.append(None if value == "max" else _number(value, "ancestor memory.max"))
    events = {}
    for line in _required(target / "memory.events").splitlines():
        key, _, value = line.partition(" ")
        events[key] = _number(value.strip(), "memory.events")
    if events.get("oom", 0) or events.get("oom_kill", 0):
        raise CgroupGateError("cgroup OOM event")
    return Snapshot(
        sampled_ns=time.time_ns(),
        pid=pid,
        relative_path=relative,
        inode=target.stat().st_ino,
        memory_max=memory,
        swap_max=swap,
        memory_current=_number(_required(target / "memory.current"), "memory.current"),
        ancestor_memory_max=tuple(limits),
        oom=events.get("oom", 0),
        oom_kill=events.get("oom_kill", 0),
    )
