"""Offline tests for the isolated C109 two-phase Compose override."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from c109_compose_gate import KINDS, PROJECT, RETRY_PROJECT, override


class ComposeGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.gates = root / "gates"
        for name in KINDS:
            (self.gates / name).mkdir(parents=True)
        self.script = root / "bootstrap.sh"
        self.script.write_text("#!/bin/sh\nexit 1\n")
        self.base = {
            "name": "centrochange-c109",
            "services": {name: {"mem_limit": "128m", "memswap_limit": "128m"} for name in KINDS},
            "volumes": {"site": {"name": "centrochange-c109-site"}},
            "networks": {"lab": {"name": "centrochange-c109-net"}},
        }
        self.base["services"]["c-fit-db"]["command"] = ["--innodb-buffer-pool-size=64M"]
        self.base["services"]["c-fit-frontend"]["command"] = ["nginx-entrypoint.sh"]
        self.base["services"]["c-fit-queue-long"]["command"] = ["bench", "worker"]
        self.base["services"]["c-fit-scheduler"]["command"] = ["bench", "schedule"]
        self.base["services"]["c-fit-websocket"]["command"] = ["node", "socketio.js"]

    def test_all_services_are_gated_with_external_lab_resources(self):
        result = override(self.base, self.gates, self.script)
        self.assertEqual(result["name"], PROJECT)
        self.assertEqual(set(result["services"]), set(KINDS))
        self.assertTrue(all(row["entrypoint"][1] == "/opt/cc-bootstrap.sh" for row in result["services"].values()))
        self.assertTrue(all(len(row["volumes"]) == 2 and all(v["read_only"] for v in row["volumes"])
                            for row in result["services"].values()))
        self.assertEqual(result["volumes"]["site"], {"external": True, "name": "centrochange-c109-site"})
        self.assertEqual(result["services"]["c-fit-backend"]["command"], ["start.sh"])
        self.assertEqual(result["services"]["c-fit-redis-cache"]["command"], ["redis-server"])
        self.assertEqual(result["services"]["c-fit-redis-queue"]["command"], ["redis-server"])

    def test_unexpected_service_fails_closed(self):
        self.base["services"]["unreviewed"] = {"mem_limit": "1m", "memswap_limit": "1m"}
        with self.assertRaises(ValueError):
            override(self.base, self.gates, self.script)

    def test_swap_mismatch_fails_closed(self):
        self.base["services"]["c-fit-db"]["memswap_limit"] = "256m"
        with self.assertRaises(ValueError):
            override(self.base, self.gates, self.script)

    def test_non_lab_resource_fails_closed(self):
        self.base["volumes"]["site"]["name"] = "centrochange-dev-sites"
        with self.assertRaises(ValueError):
            override(self.base, self.gates, self.script)

    def test_distinct_recovery_activation_project(self):
        result = override(self.base, self.gates, self.script, RETRY_PROJECT)
        self.assertEqual(result["name"], RETRY_PROJECT)
        with self.assertRaises(ValueError):
            override(self.base, self.gates, self.script, "centrochange-dev")


if __name__ == "__main__":
    unittest.main()
