"""Offline R14 lock/watchdog and exact-stop tests; never access Docker."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import c109_r14_preflight as r14
from c109_compose_gate import R14_PROJECT
from c109_r14_safety_prepare import SOURCE, install_private_safety
from c109_r14_writer import (exact_owned_ids, probe_writer_available,
                             require_writer_lease, stop_exact_r14)


CHILD = r'''
import json, os, pathlib, sys, time
from c109_guard_access import atomic_json, marker_path, process_start_ticks
from c109_r14_writer import claim_writer_lease
state, lock_file = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
atomic_json(marker_path(state, "watchdog"), {"pid": os.getpid(),
            "start_ticks": process_start_ticks(os.getpid())})
lease = claim_writer_lease(state, lock_file)
(state / "child-ready").write_text(str(os.getpid()))
while not (state / "child-stop").exists():
    (state / "monitor-heartbeat").write_text(str(time.time()))
    time.sleep(0.05)
lease.close()
'''

WATCHDOG_CHILD = r'''
import os, pathlib, runpy, sys, time, urllib.request
from unittest.mock import patch
import c109_r14_writer
from c109_guard_access import atomic_json, marker_path, process_start_ticks
state = pathlib.Path(sys.argv[1])
atomic_json(marker_path(state, "watchdog"), {"pid": os.getpid(),
            "start_ticks": process_start_ticks(os.getpid())})
original_read = pathlib.Path.read_text
original_sleep = time.sleep
def read(path, *args, **kwargs):
    name = str(path)
    if name == "/proc/vmstat": return "oom_kill 0\n"
    if name == "/proc/meminfo": return "MemAvailable: 6000000 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n"
    if name.startswith("/proc/pressure/"):
        return "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
    return original_read(path, *args, **kwargs)
def sleep(_seconds):
    deadline = time.monotonic() + 5
    while not (state / "child-stop").exists() and time.monotonic() < deadline:
        original_sleep(0.02)
    (state / "monitor-finish").write_text("done")
class Reply:
    status = 200
def forbidden_stop():
    raise RuntimeError("watchdog should not stop any container in GREEN test")
with patch.object(pathlib.Path, "read_text", read), \
     patch.object(time, "sleep", sleep), \
     patch.object(urllib.request, "urlopen", return_value=Reply()), \
     patch.object(c109_r14_writer, "writer_lock_path", return_value=pathlib.Path(sys.argv[2])), \
     patch.object(c109_r14_writer, "stop_exact_r14", side_effect=forbidden_stop):
    runpy.run_path(str(state / "safety.py"), run_name="__main__")
'''


class R14SecurityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        (self.state / "activation.json").write_text(json.dumps({
            "issue": 109, "target": R14_PROJECT, "io_waiver": True}))
        self.lock = self.state / "writer.lock"

    def child(self):
        process = subprocess.Popen([sys.executable, "-c", CHILD, str(self.state), str(self.lock)],
                                   cwd=str(Path(__file__).resolve().parent),
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        def cleanup():
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stderr.close()
        self.addCleanup(cleanup)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if (self.state / "child-ready").exists():
                return process
            if process.poll() is not None:
                self.fail("watchdog subprocess exited before writer lease")
            time.sleep(0.02)
        self.fail("watchdog subprocess did not claim writer lease")

    def actual_watchdog_child(self):
        from datetime import datetime, timedelta, timezone
        data = json.loads((self.state / "activation.json").read_text())
        data["hard_stop_utc"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        (self.state / "activation.json").write_text(json.dumps(data))
        (self.state / "own-containers.json").write_text("{}")
        (self.state / "events-heartbeat").write_text(str(time.time()))
        (self.state / "rc22-heartbeat").write_text(str(time.time()))
        install_private_safety(self.state)
        process = subprocess.Popen([sys.executable, "-c", WATCHDOG_CHILD, str(self.state), str(self.lock)],
                                   cwd=str(Path(__file__).resolve().parent),
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        def cleanup():
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stderr.close()
        self.addCleanup(cleanup)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if (self.state / "writer-lease.json").exists() and (self.state / "monitor-heartbeat").exists():
                return process
            if process.poll() is not None:
                self.fail("versioned watchdog exited before heartbeat")
            time.sleep(0.02)
        self.fail("versioned watchdog did not publish its lease and heartbeat")

    def test_distinct_watchdog_process_owns_writer_while_launcher_is_active(self):
        probe_writer_available(self.lock)  # launcher initial check and release
        process = self.child()             # actual independent process claims it
        require_writer_lease(self.state, self.lock)
        with self.assertRaisesRegex(RuntimeError, "another Docker writer"):
            probe_writer_available(self.lock)
        self.assertTrue((self.state / "monitor-heartbeat").exists())
        (self.state / "child-stop").write_text("stop")
        self.assertEqual(process.wait(timeout=5), 0)
        probe_writer_available(self.lock)
        with self.assertRaises(Exception):
            require_writer_lease(self.state, self.lock)

    def test_other_writer_blocks_watchdog_without_releasing_workload(self):
        with self.lock.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, "another Docker writer"):
                probe_writer_available(self.lock)
            process = subprocess.run([sys.executable, "-c", CHILD, str(self.state), str(self.lock)],
                                     cwd=str(Path(__file__).resolve().parent),
                                     capture_output=True, text=True, timeout=5)
            self.assertNotEqual(process.returncode, 0)
            self.assertFalse((self.state / "writer-lease.json").exists())

    def test_busy_writer_lock_blocks_launcher_before_preflight(self):
        with self.lock.open("a") as stream, \
             patch.object(r14, "preflight") as preflight, \
             patch.object(r14, "start_gated") as release:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, "another Docker writer"):
                r14.main(self.state, lock_file=self.lock)
            preflight.assert_not_called()
            release.assert_not_called()

    def test_real_launcher_sequence_hands_lease_to_distinct_watchdog(self):
        child = []
        def launch(_root):
            child.append(self.child())
        def release(_root):
            require_writer_lease(self.state, self.lock)
        with patch.object(r14, "probe_writer_available", side_effect=probe_writer_available), \
             patch.object(r14, "preflight", side_effect=launch), \
             patch.object(r14, "start_gated", side_effect=release):
            r14.main(self.state, lock_file=self.lock)
        self.assertEqual(len(child), 1)
        require_writer_lease(self.state, self.lock)
        (self.state / "child-stop").write_text("stop")
        self.assertEqual(child[0].wait(timeout=5), 0)

    def test_installed_watchdog_script_runs_in_separate_process_with_mocked_host(self):
        probe_writer_available(self.lock)
        process = self.actual_watchdog_child()
        require_writer_lease(self.state, self.lock)
        self.assertFalse((self.state / "safety-stop.json").exists())
        with self.assertRaisesRegex(RuntimeError, "another Docker writer"):
            probe_writer_available(self.lock)
        (self.state / "child-stop").write_text("stop")
        self.assertEqual(process.wait(timeout=5), 0)
        probe_writer_available(self.lock)

    def test_writer_lease_marker_tampering_fails_closed(self):
        process = self.child()
        marker = self.state / "writer-lease.json"
        payload = json.loads(marker.read_text())
        payload["inode"] += 1
        marker.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "lock file changed"):
            require_writer_lease(self.state, self.lock)
        (self.state / "child-stop").write_text("stop")
        self.assertEqual(process.wait(timeout=5), 0)

    def test_private_watchdog_is_byte_identical_and_rejects_tampering(self):
        install_private_safety(self.state)
        target = self.state / "safety.py"
        self.assertEqual(target.read_bytes(), SOURCE.read_bytes())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        source = SOURCE.read_text()
        for guard in ("CAP_NOT_ENFORCED", "RC22_INDEPENDENT_MONITOR", "PROTECTED_EVENT_MONITOR",
                      "MEMORY_RESERVE", "DISK_RESERVE", "HARD_DEADLINE", "OOM", "UAT_HTTP"):
            self.assertIn(guard, source)
        self.assertIn("stop_exact_r14()", source)
        self.assertNotIn("label=centrochange.mission=C109", source)
        install_private_safety(self.state)  # exact, harmless recheck
        target.write_text("# altered\n")
        with self.assertRaisesRegex(RuntimeError, "differs from verified source"):
            install_private_safety(self.state)

    def test_private_watchdog_rejects_wrong_activation(self):
        (self.state / "activation.json").write_text(json.dumps({"issue": 109, "target": "centrochange-dev", "io_waiver": True}))
        with self.assertRaisesRegex(RuntimeError, "authorization mismatch"):
            install_private_safety(self.state)
        self.assertFalse((self.state / "safety.py").exists())

    def test_private_watchdog_rejects_shared_directory(self):
        self.state.chmod(0o755)
        with self.assertRaisesRegex(RuntimeError, "directory is not private"):
            install_private_safety(self.state)
        self.assertFalse((self.state / "safety.py").exists())

    def test_exact_r14_and_mission_labels_allow_helper_and_service_only(self):
        helper, service = "a" * 64, "b" * 64
        labels = {"com.docker.compose.project": R14_PROJECT, "centrochange.mission": "C109"}
        def run(*args):
            if args[:2] == ("docker", "ps"):
                self.assertIn(f"label=com.docker.compose.project={R14_PROJECT}", args)
                self.assertIn("label=centrochange.mission=C109", args)
                return helper + "\n" + service
            self.assertEqual(args[:4], ("docker", "inspect", "-f", "{{json .Config.Labels}}"))
            return json.dumps(labels)
        actions = []
        ids = stop_exact_r14(run, lambda args, *, timeout: actions.append(args) or 0)
        self.assertEqual(ids, [helper, service])
        self.assertEqual(actions[-1], ["docker", "stop", "--time", "10", helper, service])
        self.assertEqual(len(actions), 3)

    def test_rc22_or_other_project_cannot_be_stopped_even_if_listed(self):
        outsider = "c" * 64
        for labels in ({"com.docker.compose.project": "centrochange-dev", "centrochange.mission": "C109"},
                       {"com.docker.compose.project": R14_PROJECT, "centrochange.mission": "OTHER"}):
            with self.subTest(labels=labels):
                def run(*args):
                    return outsider if args[:2] == ("docker", "ps") else json.dumps(labels)
                actions = []
                with self.assertRaisesRegex(RuntimeError, "ownership mismatch"):
                    stop_exact_r14(run, lambda args, *, timeout: actions.append(args) or 0)
                self.assertEqual(actions, [])

    def test_ambiguous_ids_and_docker_failure_stop_without_action(self):
        identifier = "d" * 64
        for ids in (identifier[:12], identifier + "\n" + identifier):
            with self.subTest(ids=ids):
                actions = []
                with self.assertRaisesRegex(RuntimeError, "ambiguous Docker IDs"):
                    stop_exact_r14(lambda *args: ids, lambda args, *, timeout: actions.append(args) or 0)
                self.assertEqual(actions, [])
        def broken(*args):
            raise RuntimeError("Docker API unavailable")
        with self.assertRaisesRegex(RuntimeError, "Docker API unavailable"):
            exact_owned_ids(broken)

    def test_targeted_stop_failure_is_not_reported_as_success(self):
        identifier = "e" * 64
        def run(*args):
            return identifier if args[:2] == ("docker", "ps") else json.dumps({
                "com.docker.compose.project": R14_PROJECT, "centrochange.mission": "C109"})
        with self.assertRaisesRegex(RuntimeError, "targeted R14 stop failed"):
            stop_exact_r14(run, lambda args, *, timeout: 1 if args[1] == "stop" else 0)


if __name__ == "__main__":
    unittest.main()
