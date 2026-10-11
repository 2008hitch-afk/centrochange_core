"""Offline end-to-end test of the exact R12 gate, with host/Docker faked."""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import c109_guard_access as access
import c109_gated_start as start
import c109_r12_preflight as r12
from c109_gated_start import EXPECTED_MAX, ORDER


class IntegratedR12Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "app-run"
        self.state.mkdir()
        self.ids = [format(i, "064x") for i in range(1, 10)]
        self.live_ids = self.ids[:]
        self.clock = [dt.datetime.now(dt.timezone.utc).timestamp()]
        self.tick = [100.0]
        self.renewals = {role: 0 for role in access.ROLES}
        now = dt.datetime.now(dt.timezone.utc)
        self.activation = {"issue": 109, "target": r12.R12_PROJECT,
                           "status": "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP",
                           "workload_release_allowed": True, "exclusive_docker_writer": True,
                           "image_manifest": r12.IMAGE, "source_commit": r12.REVISION,
                           "harness_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                           "io_waiver": True, "start_utc": (now - dt.timedelta(minutes=1)).isoformat(),
                           "mutation_end_utc": (now + dt.timedelta(hours=5)).isoformat(),
                           "hard_stop_utc": (now + dt.timedelta(hours=6)).isoformat()}
        self.write_activation()
        (self.state / "rc22-before.json").write_text(json.dumps({"ids": self.ids}))
        (self.state / "protected-before.json").write_text(json.dumps([{"id": i} for i in self.ids]))
        services = {name: {"mem_limit": size, "memswap_limit": size,
                           "entrypoint": ["/bin/sh", "/opt/cc-bootstrap.sh", start.KINDS[name]]}
                    for name, size in EXPECTED_MAX.items()}
        self.config = {"name": r12.R12_PROJECT, "services": services,
                       "volumes": {f"v{i}": {"name": f"centrochange-c109-r12-v{i}"} for i in range(5)},
                       "networks": {f"n{i}": {"name": f"centrochange-c109-r12-n{i}"} for i in range(2)}}
        self.write_config()
        (self.state / "compose-final-private.json").write_text("{}")
        (self.root / "compose-gated.override.json").write_text("{}")
        self.calls = []

    def write_activation(self):
        (self.state / "activation.json").write_text(json.dumps(self.activation))

    def write_config(self):
        (self.state / "compose-final.merged-private.json").write_text(json.dumps(self.config))

    def proof(self, role):
        return {"pid": os.getpid(), "start_ticks": 456, "uid": os.getuid(),
                "euid": os.geteuid(), "egid": os.getegid(), "groups": [1],
                "socket_gid": 1, "docker_host": "unix:///var/run/docker.sock",
                "docker_context": "default",
                "checked_at": dt.datetime.fromtimestamp(self.clock[0], dt.timezone.utc).isoformat()}

    def heartbeats(self):
        for name in ("events-heartbeat", "monitor-heartbeat", "rc22-heartbeat"):
            (self.state / name).write_text(str(self.clock[0]))

    def launch(self, root):
        self.assertEqual(root, self.root)
        self.heartbeats()
        for role in access.ROLES:
            access.atomic_json(access.marker_path(self.state, role), self.proof(role))

    def sleep(self, seconds):
        self.clock[0] += seconds
        self.tick[0] += seconds
        self.heartbeats()
        if int(self.tick[0]) % 8 == 0:
            for role in access.ROLES:
                path = access.marker_path(self.state, role)
                previous = json.loads(path.read_text())
                with patch.object(access, "check_access", return_value=self.proof(role)):
                    access.renew_once(self.state, role, previous)
                self.renewals[role] += 1

    def host(self, *args, **kwargs):
        self.calls.append(args)
        if args[:4] == ("docker", "image", "inspect", "-f"):
            return r12.IMAGE if args[4] == "{{.Id}}" else r12.REVISION
        if args[:5] == ("docker", "ps", "-q", "--no-trunc", "--filter"):
            return "\n".join(self.live_ids)
        if args[:4] == ("docker", "ps", "-aq", "--no-trunc"):
            return "\n".join(self.ids)
        if args[:3] in (("docker", "ps", "-aq"), ("docker", "ps", "-q")):
            return ""
        if args[:2] == ("docker", "compose") and args[-3:] == ("config", "--format", "json"):
            return json.dumps(self.config)
        if args[:3] == ("git", "-C", str(Path(r12.__file__).resolve().parent.parent)):
            return self.activation["harness_commit"] if args[-2:] == ("rev-parse", "HEAD") else ""
        if args[:2] in (("docker", "volume"), ("docker", "network")) and args[2] == "inspect":
            return args[-1]
        raise AssertionError(f"unexpected host command {args}")

    def exercise(self):
        class Reply:
            status = 200
        with patch.object(access, "process_start_ticks", return_value=456), \
             patch.object(access.time, "time", side_effect=lambda: self.clock[0]), \
             patch.object(access.time, "monotonic", side_effect=lambda: self.tick[0]), \
             patch.object(start, "run", side_effect=self.host), \
             patch.object(start, "oom_count", return_value=7), \
             patch.object(start, "mem_available", return_value=5 * 1024**3), \
             patch.object(start, "psi_full", return_value=0.0), \
             patch.object(start.urllib.request, "urlopen", return_value=Reply()):
            r12.preflight(self.root, launch=self.launch, sleep=self.sleep, host_run=self.host)

    def test_green_sequence_reaches_exact_precreation_gate(self):
        self.exercise()
        self.assertTrue((self.state / "r12-preflight-attestation.json").is_file())
        self.assertFalse((self.state / "app-attempted").exists())
        self.assertGreaterEqual(min(self.renewals.values()), 3)
        self.assertFalse(any("create" in call or "up" in call for call in self.calls))
        self.assertIn(("docker", "ps", "-q", "--no-trunc", "--filter",
                       "label=com.docker.compose.project=centrochange-dev"), self.calls)

    def test_real_identity_change_stops(self):
        self.live_ids[0] = format(99, "064x")
        with self.assertRaisesRegex(RuntimeError, "RC22 container identity changed"):
            self.exercise()
        self.assertFalse((self.state / "app-attempted").exists())

    def test_short_duplicate_missing_or_extra_identity_stops(self):
        for value in ([i[:12] for i in self.ids], self.ids[:8],
                      self.ids + [format(99, "064x")], self.ids[:8] + [self.ids[0]]):
            with self.subTest(value=value), self.assertRaisesRegex(RuntimeError, "complete Docker IDs"):
                self.live_ids = value
                self.exercise()

    def test_baseline_divergence_stops(self):
        (self.state / "rc22-before.json").write_text(json.dumps({"ids": self.ids[:8] + [format(99, "064x")]}))
        with self.assertRaisesRegex(RuntimeError, "RC22 container identity changed"):
            self.exercise()

    def test_swap_memory_and_isolation_fail_closed(self):
        for change in ("memory", "swap", "network"):
            with self.subTest(change=change):
                if change == "memory":
                    self.config["services"][ORDER[0]]["mem_limit"] -= 1
                elif change == "swap":
                    self.config["services"][ORDER[0]]["memswap_limit"] += 1
                else:
                    self.config["networks"]["n0"]["name"] = "centrochange-dev_default"
                self.write_config()
                with self.assertRaisesRegex(RuntimeError, "budget|RAM/swap|non-isolated"):
                    self.exercise()
                self.config["services"][ORDER[0]]["mem_limit"] = EXPECTED_MAX[ORDER[0]]
                self.config["services"][ORDER[0]]["memswap_limit"] = EXPECTED_MAX[ORDER[0]]
                self.config["networks"]["n0"]["name"] = "centrochange-c109-r12-n0"

    def test_missing_config_and_expiry_stop(self):
        (self.state / "compose-final.merged-private.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.exercise()
        self.write_config()
        self.activation["mutation_end_utc"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
        self.write_activation()
        with self.assertRaisesRegex(RuntimeError, "window invalid"):
            self.exercise()

    def test_wrong_image_and_missing_compose_inputs_stop(self):
        def wrong_image(*args, **kwargs):
            if args[:4] == ("docker", "image", "inspect", "-f"):
                return "sha256:" + "0" * 64
            return self.host(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, "immutable application image missing"):
            r12.preflight(self.root, launch=self.launch, sleep=self.sleep, host_run=wrong_image)
        (self.state / "compose-final-private.json").unlink()
        with self.assertRaisesRegex(RuntimeError, "Compose input missing"):
            self.exercise()

    def test_missing_isolated_volume_and_wrong_harness_revision_stop(self):
        original = self.host
        def missing_volume(*args, **kwargs):
            if args[:3] == ("docker", "volume", "inspect"):
                return "unexpected-volume"
            return original(*args, **kwargs)
        self.host = missing_volume
        with self.assertRaisesRegex(RuntimeError, "isolated volumes resource"):
            self.exercise()
        self.host = original
        self.activation["harness_commit"] = "0" * 40
        self.write_activation()
        # A fake host that returns the real revision must reject the changed authorization.
        def actual_git(*args, **kwargs):
            if args[:2] == ("git", "-C") and args[-2:] == ("rev-parse", "HEAD"):
                return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            return original(*args, **kwargs)
        with self.assertRaisesRegex(RuntimeError, "harness HEAD"):
            r12.preflight(self.root, launch=self.launch, sleep=self.sleep, host_run=actual_git)

    def test_protected_inventory_mismatch_and_safety_alert_stop(self):
        (self.state / "protected-before.json").write_text(json.dumps([{"id": i} for i in self.ids[:8]]))
        with self.assertRaisesRegex(ValueError, "protected inventory"):
            self.exercise()
        (self.state / "protected-before.json").write_text(json.dumps([{"id": i} for i in self.ids]))
        (self.state / "safety-stop.json").write_text("{}")
        with self.assertRaisesRegex(RuntimeError, "watchdog"):
            self.exercise()

    def test_failed_docker_access_is_not_renewed(self):
        def broken(seconds):
            self.clock[0] += seconds
            self.tick[0] += seconds
            self.heartbeats()
            if int(self.tick[0]) % 8 == 0:
                role = "events"
                path = access.marker_path(self.state, role)
                previous = json.loads(path.read_text())
                with patch.object(access, "check_access", side_effect=RuntimeError("Docker API unavailable")):
                    access.renew_once(self.state, role, previous)
        self.sleep = broken
        with self.assertRaisesRegex(RuntimeError, "Docker API unavailable"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_stale_proof_after_long_preparation_stops(self):
        def no_renew(seconds):
            self.clock[0] += seconds
            self.tick[0] += seconds
            self.heartbeats()
        self.sleep = no_renew
        with self.assertRaisesRegex(RuntimeError, "proof is stale"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_reused_process_missing_heartbeat_and_alert_stop(self):
        variants = ("process", "heartbeat", "alert")
        for variant in variants:
            with self.subTest(variant=variant):
                original_launch = self.launch
                def launch(root):
                    original_launch(root)
                    if variant == "process":
                        marker = access.marker_path(self.state, "events")
                        data = json.loads(marker.read_text())
                        data["start_ticks"] = 999
                        access.atomic_json(marker, data)
                    elif variant == "heartbeat":
                        (self.state / "events-heartbeat").unlink()
                    else:
                        (self.state / "guard-access-alert.json").write_text("{}")
                self.launch = launch
                try:
                    with self.assertRaises(RuntimeError):
                        self.exercise()
                    self.assertFalse((self.state / "r12-preflight-attestation.json").exists())
                finally:
                    self.launch = original_launch
                    (self.state / "guard-access-alert.json").unlink(missing_ok=True)

    def test_attestation_rejects_tampering_or_stale_marker(self):
        self.exercise()
        from c109_r12_contract import require_attestation
        self.activation["io_waiver"] = False
        self.write_activation()
        with self.assertRaisesRegex(RuntimeError, "attestation"):
            require_attestation(self.root)

    def test_unverified_code_manifest_stops_before_guard_launch(self):
        import c109_r12_contract as contract
        wrong = self.root / "wrong-verified.json"
        wrong.write_text("{}")
        with patch.object(contract, "MANIFEST", wrong):
            with self.assertRaisesRegex(RuntimeError, "differs from offline-verified"):
                self.exercise()
        self.assertFalse(access.marker_path(self.state, "events").exists())

    def test_launcher_stops_target_only_on_preflight_failure(self):
        with patch.object(r12, "preflight", side_effect=RuntimeError("guard failed")), \
             patch.object(r12, "start_gated") as start_workload, \
             patch.object(r12, "stop_only_ours") as stop_target:
            with self.assertRaisesRegex(RuntimeError, "guard failed"):
                r12.main(self.root, lock_file=self.root / "writer.lock")
            start_workload.assert_not_called()
            stop_target.assert_called_once_with(self.state, r12.R12_PROJECT)


if __name__ == "__main__":
    unittest.main()
