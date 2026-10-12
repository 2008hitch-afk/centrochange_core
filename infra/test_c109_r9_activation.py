"""The r9 project uses the prior I/O waiver only within its own activation."""

import tempfile
import unittest
from pathlib import Path

from c109_compose_gate import R9_PROJECT, override
from c109_r7_safety_prepare import prepare


class R9ActivationTests(unittest.TestCase):
    def test_r9_is_distinct_and_uncapped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gates = root / "gates"
            from c109_compose_gate import KINDS
            for service in KINDS:
                (gates / service).mkdir(parents=True)
            bootstrap = root / "bootstrap.sh"
            bootstrap.write_text("#!/bin/sh\n")
            base = {"name": "centrochange-c109", "services": {
                service: {"mem_limit": 1, "memswap_limit": 1,
                          "command": ["start"]} for service in KINDS},
                    "networks": {"lab": {"name": "centrochange-c109-test"}},
                    "volumes": {"lab": {"name": "centrochange-c109-test"}}}
            result = override(base, gates, bootstrap, R9_PROJECT)
            self.assertEqual(result["name"], R9_PROJECT)
            self.assertTrue(all("blkio_config" not in s for s in result["services"].values()))

    def test_waiver_requires_exact_activation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.py"
            source.write_text("ip=psi('io')\nif ip['full']>=1:errs.append('IO_PSI')\n"
                              "'io_psi':ip\n'OOM' 'MEMORY_RESERVE' 'CAP_NOT_ENFORCED' "
                              "'DISK_RESERVE' 'PROTECTED_EVENT_MONITOR' 'UAT_HTTP'\n")
            activation = {"issue": 109, "target": R9_PROJECT, "io_waiver": True}
            prepare(source, root / "waiver.py", activation)
            self.assertNotIn("if ip['full']>=1", (root / "waiver.py").read_text())
            with self.assertRaises(ValueError):
                prepare(source, root / "denied.py", dict(activation, io_waiver=False))


if __name__ == "__main__":
    unittest.main()
