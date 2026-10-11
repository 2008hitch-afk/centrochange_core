"""Offline-only tests; never invoke Docker or read a C109 volume."""

import datetime as dt
import fcntl
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

from c109_checkpoint_launcher import (
    CheckpointError, HELPER_MEMORY, VOLUMES, create_command, device_for,
    monitored, parse_io_max, parse_mount, validate_activation, verify_helper,
    verify_manifest,
)


NOW = dt.datetime(2026, 10, 11, 12, 0, tzinfo=dt.timezone.utc)
CID = "a" * 64


def activation():
    return {
        "issue": 109, "status": "OWNER_AUTHORIZED_C109_CHECKPOINT", "execution_allowed_now": True,
        "project": "centrochange-c109-checkpoint-r4", "start_utc": (NOW-dt.timedelta(minutes=1)).isoformat(),
        "mutation_end_utc": (NOW+dt.timedelta(hours=2)).isoformat(),
        "hard_stop_utc": (NOW+dt.timedelta(hours=5)).isoformat(),
        "volumes": list(VOLUMES), "source_commit": "b"*40, "restore_test_authorized": True,
        "exclusive_docker_writer": True, "read_bps": 2*1024**2, "write_bps": 1024**2,
        "step_timeout_seconds": 3600,
    }


class FakeProcess:
    def __init__(self, finished=False):
        self.returncode = 0 if finished else None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15


class FakeHost:
    def __init__(self, output="/private/checkpoint", wrong_mount=False, wrong_cap=False, nested_mount=False):
        self.output = output
        self.wrong_mount = wrong_mount
        self.wrong_cap = wrong_cap
        self.nested_mount = nested_mount

    def mountpoints(self):
        return [Path("/"), Path("/var/lib/docker/volumes/" + VOLUMES[0])] if self.nested_mount else [Path("/")]

    def run(self, *args, **kwargs):
        if args[:3] == ("docker", "volume", "inspect"):
            return "/var/lib/docker/volumes/" + args[-1] + "/_data"
        if args[0] == "findmnt":
            return "/dev/sdb1 8:17" if self.wrong_mount and args[-1] == self.output else "/dev/sda1 8:1"
        if args[0] == "lsblk":
            return "sda" if "PKNAME" in args else "8:0"
        if args[:2] == ("docker", "inspect"):
            return json.dumps([{
                "Id": CID, "State": {"Running": True, "Pid": 123},
                "Config": {"Labels": {"com.docker.compose.project": "centrochange-c109-checkpoint-r4"}},
                "HostConfig": {
                    "Memory": HELPER_MEMORY, "MemorySwap": HELPER_MEMORY, "NetworkMode": "none",
                    "BlkioDeviceReadBps": [{"Path": "/dev/sda", "Rate": 2*1024**2}],
                    "BlkioDeviceWriteBps": [{"Path": "/dev/sda", "Rate": 1024**2}],
                },
                "Mounts": [
                    {"Destination": "/source", "RW": False, "Type": "volume", "Name": VOLUMES[0]},
                    {"Destination": "/output", "Type": "bind", "Source": self.output},
                ],
            }])
        if args[0] == "cat":
            return "8:0 rbps=4194304 wbps=1048576" if self.wrong_cap else "8:0 rbps=2097152 wbps=1048576"
        raise AssertionError(args)

    def snapshot(self, pid, container_id):
        assert pid == 123 and container_id == CID
        return type("Snap", (), {"pid": pid, "inode": 99,
                                 "memory_current": 1024,
                                 "relative_path": "/system.slice/docker-" + CID + ".scope"})()


class CheckpointLauncherTest(unittest.TestCase):
    def test_activation_positive_and_fail_closed_gates(self):
        validate_activation(activation(), NOW)
        for key, value in (
            ("execution_allowed_now", False), ("restore_test_authorized", False),
            ("exclusive_docker_writer", False), ("read_bps", 5*1024**2),
            ("write_bps", 0), ("project", "centrochange-dev"),
            ("volumes", list(reversed(VOLUMES))), ("step_timeout_seconds", 0),
        ):
            changed = activation()
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(CheckpointError):
                validate_activation(changed, NOW)
        with self.assertRaises(CheckpointError):
            validate_activation(activation(), NOW+dt.timedelta(hours=3))

    def test_device_discovery_and_mismatch(self):
        self.assertEqual(parse_mount("/dev/sda1 8:1"), ("/dev/sda1", "8:1"))
        self.assertEqual(device_for(FakeHost(), Path("/var/lib/docker"), Path("/private/checkpoint"), VOLUMES),
                         ("/dev/sda", "8:0"))
        with self.assertRaises(CheckpointError):
            device_for(FakeHost(wrong_mount=True), Path("/var/lib/docker"), Path("/private/checkpoint"), VOLUMES)
        with self.assertRaisesRegex(CheckpointError, "nested"):
            device_for(FakeHost(nested_mount=True), Path("/var/lib/docker"), Path("/private/checkpoint"), VOLUMES)
        with self.assertRaises(CheckpointError):
            parse_mount("overlay 0:1")

    def test_io_cap_exact_scope_and_negative_cases(self):
        parse_io_max("8:0 rbps=2097152 wbps=1048576", "8:0", 2097152, 1048576)
        for raw in ("8:1 rbps=2097152 wbps=1048576", "8:0 rbps=max wbps=1048576",
                    "8:0 rbps=4194304 wbps=1048576", "8:0 rbps=2097152 wbps=1048576\n8:0 rbps=1 wbps=1"):
            with self.subTest(raw=raw), self.assertRaises(CheckpointError):
                parse_io_max(raw, "8:0", 2097152, 1048576)
        verify_helper(FakeHost(), CID, "/dev/sda", "8:0", 2097152, 1048576,
                      VOLUMES[0], Path("/private/checkpoint"), "centrochange-c109-checkpoint-r4")
        with self.assertRaises(CheckpointError):
            verify_helper(FakeHost(wrong_cap=True), CID, "/dev/sda", "8:0", 2097152, 1048576,
                          VOLUMES[0], Path("/private/checkpoint"), "centrochange-c109-checkpoint-r4")
        with self.assertRaises(CheckpointError):
            verify_helper(FakeHost(), CID, "/dev/sda", "8:0", 2097152, 1048576,
                          VOLUMES[1], Path("/private/checkpoint"), "centrochange-c109-checkpoint-r4")

    def test_one_read_only_volume_per_helper(self):
        command = create_command("centrochange-c109-checkpoint-r4", VOLUMES[0],
                                 Path("/private/checkpoint"), "sha256:"+"b"*64,
                                 "/dev/sda", 2097152, 1048576)
        self.assertEqual(sum("type=volume" in word for word in command), 1)
        self.assertIn(f"type=volume,source={VOLUMES[0]},target=/source,readonly", command)
        self.assertIn("none", command)
        self.assertIn("/dev/sda:2097152", command)
        with self.assertRaises(CheckpointError):
            create_command("x", "centrochange-dev-sites", Path("/tmp"), "sha256:"+"b"*64,
                           "/dev/sda", 1, 1)

    def test_guard_trip_terminates_in_flight_step(self):
        process = FakeProcess()
        host = type("Host", (), {"process": lambda self, cmd: process,
                                 "sleep": lambda self, delay: None})()
        with self.assertRaisesRegex(CheckpointError, "PSI"):
            monitored(host, ["synthetic-only"], lambda: (_ for _ in ()).throw(CheckpointError("PSI")),
                      999999999999.0)
        self.assertTrue(process.terminated)

    def test_existing_watchdog_guard_preserves_psi_oom_and_rc22_stops(self):
        from c109_gated_start import guard

        class Reply:
            status = 200

        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            for name in ("events-heartbeat", "monitor-heartbeat"):
                (state / name).write_text(str(time.time()))
            ids = [str(i)*64 for i in range(1, 10)]
            with patch("c109_gated_start.oom_count", return_value=7), \
                 patch("c109_gated_start.mem_available", return_value=5*1024**3), \
                 patch("c109_gated_start.psi_full", return_value=0.0), \
                 patch("c109_gated_start.run", return_value="\n".join(ids)), \
                 patch("c109_gated_start.urllib.request.urlopen", return_value=Reply()):
                guard(state, sorted(ids), 7)
            with patch("c109_gated_start.oom_count", return_value=8):
                with self.assertRaisesRegex(RuntimeError, "OOM"):
                    guard(state, sorted(ids), 7)
            with patch("c109_gated_start.oom_count", return_value=7), \
                 patch("c109_gated_start.mem_available", return_value=5*1024**3), \
                 patch("c109_gated_start.psi_full", side_effect=lambda kind: 1.0 if kind == "io" else 0.0):
                with self.assertRaisesRegex(RuntimeError, "PSI"):
                    guard(state, sorted(ids), 7)
            with patch("c109_gated_start.oom_count", return_value=7), \
                 patch("c109_gated_start.mem_available", return_value=5*1024**3), \
                 patch("c109_gated_start.psi_full", return_value=0.0), \
                 patch("c109_gated_start.run", return_value="\n".join(ids[:-1])):
                with self.assertRaisesRegex(RuntimeError, "RC22"):
                    guard(state, sorted(ids), 7)

    def test_complete_manifest_and_interrupted_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            records = []
            for volume in VOLUMES:
                archive = output / (volume + ".tar")
                with tarfile.open(archive, "w") as stream:
                    contents = b"synthetic fixture only"
                    info = tarfile.TarInfo("./fixture.txt")
                    info.size = len(contents)
                    stream.addfile(info, io.BytesIO(contents))
                records.append({"volume": volume, "archive": archive.name,
                                "bytes": archive.stat().st_size,
                                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()})
            (output / "manifest.json").write_text(json.dumps(records))
            verify_manifest(output)
            partial = output / (VOLUMES[0] + ".tar.partial")
            partial.write_bytes(b"interrupted")
            with self.assertRaisesRegex(CheckpointError, "interrupted"):
                verify_manifest(output)
            partial.unlink()
            archive = output / (VOLUMES[0] + ".tar")
            archive.write_bytes(archive.read_bytes()[:-1024] + b"X" * 1024)
            records[0]["bytes"] = archive.stat().st_size
            records[0]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            (output / "manifest.json").write_text(json.dumps(records))
            with self.assertRaisesRegex(CheckpointError, "end-of-archive"):
                verify_manifest(output)

    def test_no_activation_means_no_runtime_call(self):
        with tempfile.TemporaryDirectory(dir=Path.home() / ".local/state") as temp:
            root = Path(temp)
            (root / "app-run").mkdir()
            (root / "app-run" / "checkpoint-activation.json").write_text(json.dumps({"execution_allowed_now": False}))
            from c109_checkpoint_launcher import run_checkpoint
            host = type("NoDocker", (), {"run": lambda self, *args, **kw: self.fail()})()
            with self.assertRaises(CheckpointError):
                run_checkpoint(root, host, root / "writer.lock")

    def test_full_offline_orchestration_and_interrupted_copy(self):
        from c109_checkpoint_launcher import run_checkpoint

        class OrchestrationHost:
            def __init__(self, output, fail_copy=False):
                self.output = output
                self.fail_copy = fail_copy
                self.bad_cap = False
                self.commands = []
                self.safety_calls = 0

            def run(self, *args, **kwargs):
                self.commands.append(args)
                if args[:2] == ("docker", "info"):
                    return "/var/lib/docker"
                if args[:3] == ("docker", "image", "inspect"):
                    return "sha256:" + "c" * 64
                if args[0] == "git":
                    return "b" * 40
                if args[:3] == ("docker", "ps", "-q") and "centrochange-dev" in args[-1]:
                    return "\n".join(str(i) * 64 for i in range(1, 10))
                if args[:4] == ("docker", "ps", "-aq", "--no-trunc"):
                    return "\n".join(str(i) * 64 for i in range(1, 10))
                if args[:2] == ("docker", "ps"):
                    return ""
                if args[:2] == ("docker", "create"):
                    return CID
                if args[:2] in (("docker", "start"), ("docker", "stop")):
                    return ""
                if args[0] == "cat":
                    return "8:0 rbps=max wbps=1048576" if self.bad_cap else "8:0 rbps=2097152 wbps=1048576"
                raise AssertionError(args)

            def process(self, args):
                self.commands.append(tuple(args))
                if args[:2] == ["docker", "exec"] and args[3] == "tar":
                    volume = Path(args[-2]).name.removesuffix(".tar.partial")
                    archive = self.output / (volume + ".tar.partial")
                    with tarfile.open(archive, "w") as stream:
                        content = b"synthetic only"
                        info = tarfile.TarInfo("./record")
                        info.size = len(content)
                        stream.addfile(info, io.BytesIO(content))
                return FakeProcess(finished=True)

            def sleep(self, seconds):
                pass

            def safety(self, state, rc22, initial_oom):
                self.safety_calls += 1

            def oom(self):
                return 7

        with tempfile.TemporaryDirectory(dir=Path.home() / ".local/state") as temp:
            root = Path(temp)
            state = root / "app-run"
            state.mkdir()
            output = root / "output"
            output.mkdir(mode=0o700)
            data = activation()
            current = dt.datetime.now(dt.timezone.utc)
            data.update({"start_utc": (current-dt.timedelta(minutes=1)).isoformat(),
                         "mutation_end_utc": (current+dt.timedelta(hours=2)).isoformat(),
                         "hard_stop_utc": (current+dt.timedelta(hours=5)).isoformat(),
                         "output_dir": str(output), "helper_image": "sha256:"+"c"*64})
            (state / "checkpoint-activation.json").write_text(json.dumps(data))
            (state / "protected-before.json").write_text(json.dumps([{"id": str(i)*64} for i in range(1, 10)]))
            host = OrchestrationHost(output)
            snap = type("Snap", (), {"pid": 123, "inode": 99,
                                     "relative_path": "/system.slice/docker-" + CID + ".scope"})()
            with patch("c109_checkpoint_launcher.device_for", return_value=("/dev/sda", "8:0")), \
                 patch("c109_checkpoint_launcher.verify_helper", return_value=snap):
                run_checkpoint(root, host, root / "writer.lock")
            verify_manifest(output)
            self.assertEqual(len([c for c in host.commands if c[:2] == ("docker", "create")]), 5)
            self.assertGreater(host.safety_calls, 10)

        with tempfile.TemporaryDirectory(dir=Path.home() / ".local/state") as temp:
            root = Path(temp)
            state = root / "app-run"
            state.mkdir()
            output = root / "output"
            output.mkdir(mode=0o700)
            data["output_dir"] = str(output)
            (state / "checkpoint-activation.json").write_text(json.dumps(data))
            (state / "protected-before.json").write_text(json.dumps([{"id": str(i)*64} for i in range(1, 10)]))
            host = OrchestrationHost(output)
            stopped = []

            def interrupt(*args, **kwargs):
                (output / (VOLUMES[0] + ".tar.partial")).write_bytes(b"interrupted")
                raise CheckpointError("PSI guard trip")

            with patch("c109_checkpoint_launcher.device_for", return_value=("/dev/sda", "8:0")), \
                 patch("c109_checkpoint_launcher.verify_helper", return_value=snap), \
                 patch("c109_checkpoint_launcher.monitored", side_effect=interrupt), \
                 patch("c109_checkpoint_launcher.stop_only_ours", side_effect=lambda *args: stopped.append(args)):
                with self.assertRaisesRegex(CheckpointError, "PSI guard trip"):
                    run_checkpoint(root, host, root / "writer.lock")
            self.assertEqual(len(stopped), 1)
            self.assertTrue((output / (VOLUMES[0] + ".tar.partial")).exists())
            self.assertFalse((output / "manifest.json").exists())
            with self.assertRaises(CheckpointError):
                run_checkpoint(root, host, root / "writer.lock")  # consumed activation: no retry

        with tempfile.TemporaryDirectory(dir=Path.home() / ".local/state") as temp:
            root = Path(temp)
            state = root / "app-run"
            state.mkdir()
            output = root / "output"
            output.mkdir(mode=0o700)
            data["output_dir"] = str(output)
            (state / "checkpoint-activation.json").write_text(json.dumps(data))
            (state / "protected-before.json").write_text(json.dumps([{"id": str(i)*64} for i in range(1, 10)]))
            host = OrchestrationHost(output)
            host.bad_cap = True
            stopped = []
            with patch("c109_checkpoint_launcher.device_for", return_value=("/dev/sda", "8:0")), \
                 patch("c109_checkpoint_launcher.verify_helper", return_value=snap), \
                 patch("c109_checkpoint_launcher.stop_only_ours", side_effect=lambda *args: stopped.append(args)):
                with self.assertRaisesRegex(CheckpointError, "unlimited"):
                    run_checkpoint(root, host, root / "writer.lock")
            self.assertEqual(len(stopped), 1)
            self.assertFalse((output / "manifest.json").exists())

    def test_exclusive_writer_lock_blocks_before_docker(self):
        from c109_checkpoint_launcher import run_checkpoint
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock_path = root / "writer.lock"
            with lock_path.open("a") as held:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                host = type("NoDocker", (), {"run": lambda self, *args, **kw: self.fail()})()
                with self.assertRaisesRegex(CheckpointError, "exclusive lock"):
                    run_checkpoint(root, host, lock_path)


if __name__ == "__main__":
    unittest.main()
