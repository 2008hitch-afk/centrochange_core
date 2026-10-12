"""Offline negative and positive checks for C109 pre-release I/O enforcement."""

import tempfile
from pathlib import Path
import unittest

from c109_io_gate import (IOGateError, READ_BPS, WRITE_BPS, io_max_values,
                          verify_cgroup, verify_compose_config, verify_host_config,
                          verify_io_max)


CID = "a" * 64
CGROUP = "/system.slice/docker-" + CID + ".scope"


class C109IOGateTest(unittest.TestCase):
    def test_live_io_max_exact_device_and_finite_limits(self):
        verify_io_max(f"8:0 rbps={READ_BPS} wbps={WRITE_BPS} riops=max wiops=max", "8:0")
        self.assertEqual(io_max_values("8:0 rbps=1024 wbps=512", "8:0"), (1024, 512))
        for raw in ("", "8:1 rbps=1024 wbps=512", "8:0 rbps=max wbps=512",
                    f"8:0 rbps={READ_BPS+1} wbps={WRITE_BPS}",
                    "8:0 rbps=0 wbps=512", "8:0 rbps=1024 wbps=512\n8:0 rbps=1024 wbps=512"):
            with self.subTest(raw=raw), self.assertRaises(IOGateError):
                verify_io_max(raw, "8:0")

    def test_hostconfig_and_compose_normalized_values(self):
        host = {"BlkioDeviceReadBps": [{"Path": "/dev/sda", "Rate": READ_BPS}],
                "BlkioDeviceWriteBps": [{"Path": "/dev/sda", "Rate": WRITE_BPS}]}
        verify_host_config(host, "/dev/sda")
        compose = {"device_read_bps": [{"Path": "/dev/sda", "Rate": str(READ_BPS)}],
                   "device_write_bps": [{"Path": "/dev/sda", "Rate": str(WRITE_BPS)}]}
        verify_compose_config(compose, "/dev/sda")
        for changed in (
            {**host, "BlkioDeviceReadBps": []},
            {**host, "BlkioDeviceWriteBps": [{"Path": "/dev/sdb", "Rate": WRITE_BPS}]},
            {**host, "BlkioDeviceReadBps": [{"Path": "/dev/sda", "Rate": READ_BPS+1}]},
        ):
            with self.subTest(changed=changed), self.assertRaises(IOGateError):
                verify_host_config(changed, "/dev/sda")
        for changed in ({}, {**compose, "device_write_bps": []},
                        {**compose, "device_read_bps": [{"Path": "/dev/sdb", "Rate": str(READ_BPS)}]}):
            with self.subTest(changed=changed), self.assertRaises(IOGateError):
                verify_compose_config(changed, "/dev/sda")

    def test_only_exact_docker_pid_scope_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / CGROUP.lstrip("/")
            path.mkdir(parents=True)
            (path / "io.max").write_text(f"8:0 rbps={READ_BPS} wbps={WRITE_BPS}\n")
            verify_cgroup(CGROUP, "8:0", Path(temp))
            for wrong in ("/", "/system.slice/docker-"+"b"*64+".scope",
                          "/system.slice/docker-"+CID+".scope/../other"):
                with self.subTest(wrong=wrong), self.assertRaises(IOGateError):
                    verify_cgroup(wrong, "8:0", Path(temp))
            (path / "io.max").write_text("8:0 rbps=max wbps=max\n")
            with self.assertRaises(IOGateError):
                verify_cgroup(CGROUP, "8:0", Path(temp))


if __name__ == "__main__":
    unittest.main()
