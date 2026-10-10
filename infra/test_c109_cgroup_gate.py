"""Offline negative tests for the C109 PID/cgroup gate. No Docker required."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from c109_cgroup_gate import CgroupGateError, InertBootstrapObservation, read_snapshot


CONTAINER = "a" * 64
LIMIT = 512 * 1024 * 1024


class GateTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.proc = root / "proc"
        self.cgroup = root / "cgroup"
        self.target = self.cgroup / "system.slice" / f"docker-{CONTAINER}.scope"
        self.target.mkdir(parents=True)
        (self.proc / "123").mkdir(parents=True)
        (self.proc / "123" / "cgroup").write_text(f"0::/system.slice/docker-{CONTAINER}.scope\n")
        (self.cgroup / "system.slice" / "memory.max").write_text("max\n")
        (self.target / "memory.max").write_text(str(LIMIT))
        (self.target / "memory.swap.max").write_text("0\n")
        (self.target / "memory.current").write_text("4096\n")
        (self.target / "memory.events").write_text("oom 0\noom_kill 0\n")
        (self.target / "cgroup.events").write_text("populated 1\n")

    def snapshot(self):
        return read_snapshot(123, CONTAINER, LIMIT, proc_root=self.proc, cgroup_root=self.cgroup)

    def test_root_without_memory_max_is_valid(self):
        result = self.snapshot()
        self.assertEqual(result.memory_max, LIMIT)
        self.assertEqual(result.swap_max, 0)
        self.assertEqual(result.ancestor_memory_max, (None, None, LIMIT))

    def test_missing_pid_fails_closed(self):
        (self.proc / "123" / "cgroup").unlink()
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_wrong_scope_fails_closed(self):
        (self.proc / "123" / "cgroup").write_text("0::/system.slice/docker-" + "b" * 64 + ".scope\n")
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_max_fails_closed(self):
        (self.target / "memory.max").write_text("max\n")
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_swap_fails_closed(self):
        (self.target / "memory.swap.max").write_text("1\n")
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_oom_fails_closed(self):
        (self.target / "memory.events").write_text("oom 1\noom_kill 0\n")
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_unpopulated_fails_closed(self):
        (self.target / "cgroup.events").write_text("populated 0\n")
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_missing_ancestor_fails_closed(self):
        (self.cgroup / "system.slice" / "memory.max").unlink()
        with self.assertRaises(CgroupGateError):
            self.snapshot()

    def test_inert_max_then_cap(self):
        observer = InertBootstrapObservation(LIMIT)
        self.assertEqual(observer.observe(False, "max", "max", 0), "EMPTY")
        self.assertEqual(observer.observe(True, "max", "max", 100), "INERT_WAIT")
        self.assertEqual(observer.observe(True, str(LIMIT), "0", 900_000_000), "CAPPED")

    def test_inert_max_persistent_fails(self):
        observer = InertBootstrapObservation(LIMIT)
        observer.observe(True, "max", "max", 100)
        with self.assertRaises(CgroupGateError):
            observer.observe(True, "max", "max", 2_000_000_100)

    def test_cap_regression_fails_immediately(self):
        observer = InertBootstrapObservation(LIMIT)
        observer.observe(True, str(LIMIT), "0", 100)
        with self.assertRaises(CgroupGateError):
            observer.observe(True, "max", "max", 101)


if __name__ == "__main__":
    unittest.main()
