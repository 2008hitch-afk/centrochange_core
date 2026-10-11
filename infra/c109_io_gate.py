"""Fail-closed block-I/O gate for a future, separately authorized C109 run.

Resolve the host device, then verify Docker HostConfig and the live inert
container cgroup before releasing any application or browser workload.
This module performs no Docker mutation.
"""

from pathlib import Path
import re
import stat
import subprocess


READ_BPS = 4 * 1024**2
WRITE_BPS = 2 * 1024**2
VOLUMES = (
    "centrochange-c109-c-fit-db-data", "centrochange-c109-c-fit-sites",
    "centrochange-c109-c-fit-assets", "centrochange-c109-c-fit-redis-cache-data",
    "centrochange-c109-c-fit-redis-queue-data",
)


class IOGateError(RuntimeError):
    pass


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True, timeout=15).strip()


def resolve_device(state_dir: Path, run=command) -> tuple[str, str]:
    """Require Docker, all C109 volumes and the private state on one filesystem."""
    docker_root = Path(run("docker", "info", "-f", "{{.DockerRootDir}}"))
    if not docker_root.is_absolute() or not state_dir.is_absolute():
        raise IOGateError("Docker/private state path is not absolute")
    mounts = [run("findmnt", "-n", "-o", "SOURCE,MAJ:MIN", "-T", str(path))
              for path in (docker_root, state_dir)]
    # Docker's volume directories are root-owned on this host. Inspect their
    # names without traversing data, then reject any nested host mount.
    mountpoints = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split(" - ", 1)[0].split()
        if len(fields) < 5:
            raise IOGateError("malformed host mount table")
        mountpoints.append(Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), fields[4])))
    for name in VOLUMES:
        path = Path(run("docker", "volume", "inspect", "-f", "{{.Mountpoint}}", name))
        if not path.is_relative_to(docker_root / "volumes"):
            raise IOGateError("C109 volume outside Docker root")
        if any(point != docker_root and point.is_relative_to(docker_root)
               and path.is_relative_to(point) for point in mountpoints):
            raise IOGateError("C109 volume has a nested host mount")
    if len(set(mounts)) != 1:
        raise IOGateError("Docker, C109 volumes and private state use different filesystems")
    parts = mounts[0].split()
    if len(parts) != 2 or not re.fullmatch(r"/dev/[A-Za-z0-9._-]+", parts[0]) or not re.fullmatch(r"\d+:\d+", parts[1]):
        raise IOGateError("host filesystem device is ambiguous")
    parent = run("lsblk", "-no", "PKNAME", parts[0])
    if not re.fullmatch(r"[A-Za-z0-9._-]+", parent):
        raise IOGateError("parent block device is ambiguous")
    device = "/dev/" + parent
    if not stat.S_ISBLK(Path(device).stat().st_mode):
        raise IOGateError("parent device is not a block device")
    device_id = run("lsblk", "-dn", "-o", "MAJ:MIN", device)
    if not re.fullmatch(r"\d+:\d+", device_id):
        raise IOGateError("parent device ID is ambiguous")
    return device, device_id


def io_max_values(raw: str, device_id: str) -> tuple[int, int]:
    matches = [line.split() for line in raw.splitlines() if line.startswith(device_id + " ")]
    if len(matches) != 1:
        raise IOGateError("I/O cap absent or ambiguous on actual device")
    try:
        fields = dict(item.split("=", 1) for item in matches[0][1:])
        values = int(fields["rbps"]), int(fields["wbps"])
    except (ValueError, KeyError) as exc:
        raise IOGateError("I/O cap unlimited or malformed") from exc
    if any(value <= 0 for value in values):
        raise IOGateError("I/O cap is not positive")
    return values


def verify_io_max(raw: str, device_id: str, read_bps: int = READ_BPS,
                  write_bps: int = WRITE_BPS) -> None:
    actual_read, actual_write = io_max_values(raw, device_id)
    if actual_read > read_bps or actual_write > write_bps:
        raise IOGateError("live cgroup I/O cap exceeds profile")


def verify_host_config(config: dict, device: str, read_bps: int = READ_BPS,
                       write_bps: int = WRITE_BPS) -> None:
    for key, maximum in (("BlkioDeviceReadBps", read_bps), ("BlkioDeviceWriteBps", write_bps)):
        rows = config.get(key) or []
        if (len(rows) != 1 or rows[0].get("Path") != device
                or not isinstance(rows[0].get("Rate"), int)
                or not 0 < rows[0]["Rate"] <= maximum):
            raise IOGateError("Docker HostConfig I/O cap mismatch")


def verify_compose_config(config: dict, device: str, read_bps: int = READ_BPS,
                          write_bps: int = WRITE_BPS) -> None:
    """Validate Docker Compose's normalized Path/Rate output, not only input."""
    if set(config) != {"device_read_bps", "device_write_bps"}:
        raise IOGateError("Compose I/O profile missing or unexpected")
    for key, expected in (("device_read_bps", read_bps), ("device_write_bps", write_bps)):
        rows = config.get(key)
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise IOGateError("Compose I/O device cardinality invalid")
        item = rows[0]
        path = item.get("Path", item.get("path"))
        try:
            rate = int(item.get("Rate", item.get("rate")))
        except (ValueError, TypeError) as exc:
            raise IOGateError("Compose I/O rate invalid") from exc
        if path != device or rate != expected:
            raise IOGateError("Compose I/O cap differs from approved profile")


def verify_cgroup(relative_path: str, device_id: str,
                  cgroup_root: Path = Path("/sys/fs/cgroup")) -> None:
    if not re.fullmatch(r"/system\.slice/docker-[0-9a-f]{64}\.scope", relative_path):
        raise IOGateError("unverified cgroup path")
    path = cgroup_root / relative_path.lstrip("/") / "io.max"
    try:
        verify_io_max(path.read_text(), device_id)
    except (OSError, UnicodeError) as exc:
        raise IOGateError("live cgroup I/O cap unreadable") from exc
