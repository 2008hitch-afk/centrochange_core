"""Fail-closed C109 checkpoint launcher. Never run without a new private activation.

This launcher is intentionally independent of the product runtime. Its first
live run requires a separately approved activation, watchdog and restore plan.
Offline tests inject a fake host and never call Docker.
"""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time

from c109_cgroup_gate import read_snapshot
from c109_gated_start import guard, oom_count, stop_only_ours
from c109_protected_inventory import validate_existing


VOLUMES = (
    "centrochange-c109-c-fit-db-data",
    "centrochange-c109-c-fit-sites",
    "centrochange-c109-c-fit-assets",
    "centrochange-c109-c-fit-redis-cache-data",
    "centrochange-c109-c-fit-redis-queue-data",
)
PROJECT_PREFIX = "centrochange-c109-checkpoint-"
MAX_READ_BPS = 4 * 1024**2  # proposed ceiling; not a proven safe operating rate
MAX_WRITE_BPS = 2 * 1024**2
HELPER_MEMORY = 256 * 1024**2


class CheckpointError(RuntimeError):
    pass


def parse_mount(raw: str) -> tuple[str, str]:
    parts = raw.strip().split()
    if len(parts) != 2 or not re.fullmatch(r"\d+:\d+", parts[1]) or not parts[0].startswith("/dev/"):
        raise CheckpointError("unresolvable block-device mount")
    return parts[0], parts[1]


def parse_io_max(raw: str, device_id: str, read_bps: int, write_bps: int) -> None:
    matches = [line.split() for line in raw.splitlines() if line.startswith(device_id + " ")]
    if len(matches) != 1:
        raise CheckpointError("I/O cap absent or ambiguous on the actual device")
    limits = dict(token.split("=", 1) for token in matches[0][1:] if "=" in token)
    try:
        actual_read, actual_write = int(limits["rbps"]), int(limits["wbps"])
    except (KeyError, ValueError) as exc:
        raise CheckpointError("I/O cap unlimited or malformed") from exc
    if actual_read <= 0 or actual_write <= 0 or actual_read > read_bps or actual_write > write_bps:
        raise CheckpointError("I/O cap exceeds approved rate")


def validate_activation(data: dict, now: dt.datetime) -> None:
    if (data.get("issue"), data.get("status"), data.get("execution_allowed_now")) != (
        109, "OWNER_AUTHORIZED_C109_CHECKPOINT", True
    ):
        raise CheckpointError("new Owner checkpoint authorization absent")
    project = data.get("project", "")
    if not re.fullmatch(PROJECT_PREFIX + r"[a-z0-9-]+", project):
        raise CheckpointError("invalid isolated checkpoint project")
    try:
        start = dt.datetime.fromisoformat(data["start_utc"])
        end = dt.datetime.fromisoformat(data["mutation_end_utc"])
        stop = dt.datetime.fromisoformat(data["hard_stop_utc"])
    except (KeyError, ValueError) as exc:
        raise CheckpointError("invalid activation window") from exc
    if any(item.tzinfo is None for item in (start, end, stop)) or not start <= now < end < stop:
        raise CheckpointError("outside authorized mutation window")
    if (stop - end) < dt.timedelta(hours=3):
        raise CheckpointError("insufficient stop/recovery margin")
    if data.get("volumes") != list(VOLUMES):
        raise CheckpointError("volume inventory or order changed")
    if data.get("source_commit") is None or not re.fullmatch(r"[0-9a-f]{40}", data["source_commit"]):
        raise CheckpointError("source commit not pinned")
    if not data.get("restore_test_authorized"):
        raise CheckpointError("isolated restore test not authorized")
    if not data.get("exclusive_docker_writer"):
        raise CheckpointError("exclusive Docker writer unconfirmed")
    if data.get("read_bps", 0) not in range(256 * 1024, MAX_READ_BPS + 1) or data.get("write_bps", 0) not in range(128 * 1024, MAX_WRITE_BPS + 1):
        raise CheckpointError("invalid I/O rate")
    if not isinstance(data.get("step_timeout_seconds"), int) or not 60 <= data["step_timeout_seconds"] <= 3600:
        raise CheckpointError("invalid per-volume deadline")


def sha256(path: Path, safety_check, rate_bps: int | None = None, sleeper=time.sleep) -> str:
    digest = hashlib.sha256()
    started = time.monotonic()
    consumed = 0
    with path.open("rb") as stream:
        while block := stream.read(64 * 1024):
            safety_check()
            digest.update(block)
            consumed += len(block)
            if rate_bps:
                remaining = consumed / rate_bps - (time.monotonic() - started)
                if remaining > 0:
                    sleeper(remaining)
    safety_check()
    return digest.hexdigest()


class Host:
    """Small command boundary; fakes replace it for all offline tests."""

    def run(self, *args: str, timeout: int = 30) -> str:
        return subprocess.check_output(args, text=True, timeout=timeout).strip()

    def process(self, args: list[str]):
        return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def snapshot(self, pid: int, container_id: str):
        return read_snapshot(pid, container_id, HELPER_MEMORY)

    def safety(self, state: Path, rc22_ids: list[str], initial_oom: int) -> None:
        guard(state, rc22_ids, initial_oom)

    def oom(self) -> int:
        return oom_count()

    def mountpoints(self) -> list[Path]:
        """Kernel mount table; no traversal of protected Docker volume paths."""
        points = []
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            fields = line.split(" - ", 1)[0].split()
            if len(fields) < 5:
                raise CheckpointError("malformed host mount table")
            points.append(Path(re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), fields[4])))
        return points


def device_for(host: Host, docker_root: Path, output: Path, volumes: tuple[str, ...]) -> tuple[str, str]:
    """Resolve the real parent block device for both Docker and the archive."""
    mountpoints = host.mountpoints()
    roots = [docker_root, output]
    for volume in volumes:
        mountpoint = host.run("docker", "volume", "inspect", "-f", "{{.Mountpoint}}", volume)
        if not mountpoint.startswith(str(docker_root / "volumes") + "/"):
            raise CheckpointError("volume mountpoint outside Docker root")
        volume_path = Path(mountpoint)
        # The local volume directory may be inaccessible to this Unix user.
        # Fail closed if any mount below Docker root changes its filesystem.
        if any(point != docker_root and point.is_relative_to(docker_root)
               and volume_path.is_relative_to(point) for point in mountpoints):
            raise CheckpointError("volume has a nested host mount")
    mounts = [parse_mount(host.run("findmnt", "-n", "-o", "SOURCE,MAJ:MIN", "-T", str(path))) for path in roots]
    if len(set(mounts)) != 1:
        raise CheckpointError("Docker volumes and archive do not share the verified filesystem")
    source, _ = mounts[0]
    parent = host.run("lsblk", "-no", "PKNAME", source).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", parent):
        raise CheckpointError("cannot identify parent block device")
    device = "/dev/" + parent
    info = host.run("lsblk", "-dn", "-o", "MAJ:MIN", device)
    if not re.fullmatch(r"\d+:\d+", info):
        raise CheckpointError("cannot identify I/O cgroup device number")
    return device, info


def create_command(project: str, volume: str, output: Path, image: str, device: str,
                   read_bps: int, write_bps: int) -> list[str]:
    if volume not in VOLUMES:
        raise CheckpointError("unapproved source volume")
    name = project + "-" + volume.removeprefix("centrochange-c109-c-fit-")
    return [
        "docker", "create", "--name", name,
        "--label", f"com.docker.compose.project={project}",
        "--network", "none", "--memory", str(HELPER_MEMORY), "--memory-swap", str(HELPER_MEMORY),
        "--device-read-bps", f"{device}:{read_bps}",
        "--device-write-bps", f"{device}:{write_bps}",
        "--mount", f"type=volume,source={volume},target=/source,readonly",
        "--mount", f"type=bind,source={output},target=/output",
        "--entrypoint", "/bin/sh", image, "-c", "while :; do sleep 1; done",
    ]


def verify_helper(host: Host, container_id: str, device: str, device_id: str,
                  read_bps: int, write_bps: int, volume: str, output: Path, project: str):
    info = json.loads(host.run("docker", "inspect", container_id))[0]
    if info["Id"] != container_id or not info["State"]["Running"] or info["State"]["Pid"] <= 0:
        raise CheckpointError("helper PID/container mismatch")
    config = info["HostConfig"]
    if info.get("Config", {}).get("Labels", {}).get("com.docker.compose.project") != project:
        raise CheckpointError("helper project label mismatch")
    if config["Memory"] != HELPER_MEMORY or config["MemorySwap"] != HELPER_MEMORY or config["NetworkMode"] != "none":
        raise CheckpointError("helper RAM/swap/network cap mismatch")
    for key, limit in (("BlkioDeviceReadBps", read_bps), ("BlkioDeviceWriteBps", write_bps)):
        rows = config.get(key) or []
        if len(rows) != 1 or rows[0]["Path"] != device or rows[0]["Rate"] > limit or rows[0]["Rate"] <= 0:
            raise CheckpointError("Docker HostConfig I/O cap mismatch")
    mounts = info["Mounts"]
    if len(mounts) != 2 or not any(m["Destination"] == "/source" and m["RW"] is False
                                   and m["Type"] == "volume" and m["Name"] == volume for m in mounts):
        raise CheckpointError("helper source must be a single read-only C109 volume")
    if not any(m["Destination"] == "/output" and m["Type"] == "bind"
               and m["Source"] == str(output) for m in mounts):
        raise CheckpointError("helper output bind mount absent")
    snap = host.snapshot(info["State"]["Pid"], container_id)
    if snap.memory_current > HELPER_MEMORY:
        raise CheckpointError("helper memory exceeds cap")
    path = Path("/sys/fs/cgroup") / snap.relative_path.lstrip("/")
    parse_io_max(host.run("cat", str(path / "io.max")), device_id, read_bps, write_bps)
    return snap


def monitored(host: Host, command: list[str], safety_check, deadline: float) -> None:
    process = host.process(command)
    try:
        while process.poll() is None:
            safety_check()
            if time.monotonic() >= deadline:
                raise CheckpointError("checkpoint step deadline")
            host.sleep(0.25)
        safety_check()
        if process.returncode:
            raise CheckpointError("checkpoint command failed")
    except BaseException:
        if process.poll() is None:
            process.terminate()
        raise


def validate_tar(archive: Path, safety_check) -> None:
    if archive.stat().st_size < 1024 or archive.stat().st_size % 512:
        raise CheckpointError("truncated tar archive")
    with archive.open("rb") as stream:
        stream.seek(-1024, os.SEEK_END)
        if stream.read(1024) != b"\0" * 1024:
            raise CheckpointError("tar end-of-archive marker absent")
    try:
        safety_check()
        with tarfile.open(archive, "r:") as stream:
            count = 0
            for member in stream:
                safety_check()
                count += 1
                path = Path(member.name)
                if path.is_absolute() or ".." in path.parts or member.isdev():
                    raise CheckpointError("unsafe archive member")
                if (member.issym() or member.islnk()) and (Path(member.linkname).is_absolute() or ".." in Path(member.linkname).parts):
                    raise CheckpointError("unsafe archive link")
            if not count:
                raise CheckpointError("empty tar archive")
        safety_check()
    except (tarfile.TarError, EOFError) as exc:
        raise CheckpointError("invalid tar archive") from exc


def verify_manifest(output: Path, safety_check=lambda: None, rate_bps: int | None = None,
                    candidate: bool = False, deep: bool = True) -> None:
    """Offline archive validation; RESTORE_VERIFIED is a separate gate.

    The runtime candidate uses deep=False only after each volume has already
    passed one paced hash and tar check. Offline review always uses deep=True.
    """
    manifest_name = "manifest.partial.json" if candidate else "manifest.json"
    if any(output.glob("*.partial")) or (not candidate and (output / "manifest.partial.json").exists()):
        raise CheckpointError("interrupted archive or manifest present")
    records = json.loads((output / manifest_name).read_text())
    if not isinstance(records, list) or [r.get("volume") for r in records] != list(VOLUMES):
        raise CheckpointError("incomplete or unordered volume manifest")
    if {p.name for p in output.iterdir()} != {manifest_name} | {v + ".tar" for v in VOLUMES}:
        raise CheckpointError("unexpected or missing archive files")
    for record in records:
        safety_check()
        archive = output / (record["volume"] + ".tar")
        if record.get("archive") != archive.name or record.get("bytes") != archive.stat().st_size:
            raise CheckpointError("archive metadata mismatch")
        if deep:
            if sha256(archive, safety_check, rate_bps) != record.get("sha256"):
                raise CheckpointError("archive checksum mismatch")
            validate_tar(archive, safety_check)


def _run_checkpoint_locked(root: Path, host: Host | None = None) -> None:
    """Future authorized entrypoint. No effect when authorization is absent."""
    host = host or Host()
    state = root / "app-run"
    data = json.loads((state / "checkpoint-activation.json").read_text())
    validate_activation(data, dt.datetime.now(dt.timezone.utc))
    if (state / "checkpoint-attempted").exists():
        raise CheckpointError("checkpoint activation already consumed")
    output = Path(data["output_dir"])
    if not output.is_absolute() or not output.is_dir() or output.stat().st_mode & 0o077:
        raise CheckpointError("private output directory missing or permissions too broad")
    if any(output.iterdir()):
        raise CheckpointError("output directory is not empty; no duplicate or partial overwrite")
    docker_root = Path(host.run("docker", "info", "-f", "{{.DockerRootDir}}"))
    if output.resolve().is_relative_to(docker_root.resolve()) or not output.resolve().is_relative_to(Path.home() / ".local/state"):
        raise CheckpointError("archive must be private and outside Docker volumes")
    device, device_id = device_for(host, docker_root, output, VOLUMES)
    image = data.get("helper_image", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image) or not host.run("docker", "image", "inspect", "-f", "{{.Id}}", image) == image:
        raise CheckpointError("helper image not already pinned and local")
    repository = Path(__file__).resolve().parent.parent
    if host.run("git", "-C", str(repository), "rev-parse", "HEAD") != data["source_commit"]:
        raise CheckpointError("source HEAD differs from authorized checkpoint activation")
    rc22 = sorted(host.run("docker", "ps", "-q", "--no-trunc", "--filter", "label=com.docker.compose.project=centrochange-dev").split())
    if len(rc22) != 9 or any(not re.fullmatch(r"[0-9a-f]{64}", item) for item in rc22):
        raise CheckpointError("RC22 identity baseline invalid")
    initial_oom = host.oom()
    validate_existing((state / "protected-before.json").read_text(),
                      host.run("docker", "ps", "-aq", "--no-trunc"))
    def check():
        if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(data["mutation_end_utc"]):
            raise CheckpointError("mutation window expired")
        host.safety(state, rc22, initial_oom)
    check()
    if host.run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={data['project']}"):
        raise CheckpointError("checkpoint project already exists")
    if host.run("docker", "ps", "-q", "--filter", "label=centrochange.mission=C109"):
        raise CheckpointError("another C109 workload is running")
    (state / "checkpoint-attempted").write_text(dt.datetime.now(dt.timezone.utc).isoformat())
    manifest = []
    for volume in VOLUMES:
        check()
        if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(data["mutation_end_utc"]):
            raise CheckpointError("mutation window expired")
        partial = output / (volume + ".tar.partial")
        final = output / (volume + ".tar")
        container_id = None
        try:
            container_id = host.run(*create_command(data["project"], volume, output, image, device,
                                                     data["read_bps"], data["write_bps"]))
            if not re.fullmatch(r"[0-9a-f]{64}", container_id):
                raise CheckpointError("Docker returned invalid helper ID")
            host.run("docker", "start", container_id)
            first = verify_helper(host, container_id, device, device_id, data["read_bps"], data["write_bps"], volume, output, data["project"])
            host.sleep(0.2)
            check()
            second = verify_helper(host, container_id, device, device_id, data["read_bps"], data["write_bps"], volume, output, data["project"])
            if (first.pid, first.inode) != (second.pid, second.inode):
                raise CheckpointError("helper cgroup changed before release")
            last_cap_check = time.monotonic()

            def check_during_copy():
                nonlocal last_cap_check
                check()
                raw_io_max = host.run("cat", str(Path("/sys/fs/cgroup") / first.relative_path.lstrip("/") / "io.max"))
                parse_io_max(raw_io_max, device_id, data["read_bps"], data["write_bps"])
                if time.monotonic() - last_cap_check >= 1:
                    current = verify_helper(host, container_id, device, device_id,
                                            data["read_bps"], data["write_bps"], volume, output, data["project"])
                    if (current.pid, current.inode) != (first.pid, first.inode):
                        raise CheckpointError("helper cgroup changed during checkpoint")
                    last_cap_check = time.monotonic()

            # First source read occurs only after both cgroup observations.
            monitored(host, ["docker", "exec", container_id, "tar", "-C", "/source", "-cf",
                             "/output/" + partial.name, "."], check_during_copy,
                      time.monotonic() + data["step_timeout_seconds"])
            check()
            if not partial.is_file() or partial.stat().st_size == 0:
                raise CheckpointError("empty or missing archive")
            checksum = sha256(partial, check_during_copy, data["read_bps"], host.sleep)
            validate_tar(partial, check_during_copy)
            check()
            # Flush the archive in the same capped helper cgroup. Do not issue
            # a host-side filesystem-wide sync on the shared RC22 device.
            monitored(host, ["docker", "exec", container_id, "sync", "/output/" + partial.name],
                      check_during_copy, time.monotonic() + data["step_timeout_seconds"])
            os.replace(partial, final)
            manifest.append({"volume": volume, "archive": final.name, "bytes": final.stat().st_size,
                             "sha256": checksum, "device": device_id, "helper_image": image})
            (output / "manifest.partial.json").write_text(json.dumps(manifest, indent=2) + "\n")
            host.run("docker", "stop", "--time", "10", container_id)
            check()
            # No automatic retry or speed increase. Allow PSI avg10 to settle.
            for _ in range(3):
                host.sleep(5)
                check()
        except BaseException:
            if container_id:
                stop_only_ours(state, data["project"])
            raise
    check()
    verify_manifest(output, check, data["read_bps"], candidate=True, deep=False)
    os.replace(output / "manifest.partial.json", output / "manifest.json")


def run_checkpoint(root: Path, host: Host | None = None, lock_file: Path | None = None) -> None:
    """Hold the same exclusive Docker-writer lock used by earlier C109 runs."""
    lock_file = lock_file or Path(f"/run/user/{os.getuid()}/centrochange-docker-writer.lock")
    try:
        with lock_file.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _run_checkpoint_locked(root, host)
    except BlockingIOError as exc:
        raise CheckpointError("another Docker writer holds the exclusive lock") from exc


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_checkpoint_launcher.py PRIVATE_ACTIVATION_ROOT")
    run_checkpoint(Path(sys.argv[1]))
