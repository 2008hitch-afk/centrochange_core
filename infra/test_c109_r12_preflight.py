"""Offline end-to-end test of the exact R12 gate, with host/Docker faked."""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import c109_guard_access as access
import c109_gated_start as start
import c109_r12_preflight as r12
import c109_r12_resources as resources
from c109_gated_start import EXPECTED_MAX, ORDER


class FakeProcess:
    def __init__(self, output="", fail=False):
        self.output = output
        self.returncode = None
        self.remaining = 2
        self.fail = fail

    def poll(self):
        if self.remaining:
            self.remaining -= 1
            return None
        self.returncode = 1 if self.fail else 0
        return self.returncode

    def communicate(self, timeout=None):
        return self.output, ""

    def terminate(self):
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode


class FakeResourceHost:
    """Stateful Docker boundary: the real resource module performs the sequence."""

    def __init__(self, test):
        self.test = test
        self.calls = []
        self.volumes = {resources.SOURCE_PREFIX + suffix for suffix in resources.SUFFIXES}
        self.networks = set()
        self.helpers = {}
        self.next_id = 100
        self.missing_source = False
        self.bad_digest = False
        self.bad_cap = False
        self.copy_failure = False
        self.long_copy = False
        self.active_source = False
        self.bad_network = False
        self.extra_mount = False

    def run(self, *args, **kwargs):
        self.calls.append(args)
        if args[:3] == ("docker", "volume", "ls"):
            values = self.volumes.copy()
            if self.missing_source:
                values.remove(resources.SOURCE_PREFIX + resources.SUFFIXES[0])
            return "\n".join(sorted(values))
        if args[:3] == ("docker", "network", "ls"):
            return "\n".join(sorted(self.networks))
        if args[:3] == ("docker", "ps", "-q") and "--no-trunc" in args and any(str(x).startswith("volume=") for x in args):
            users = [ident for ident, item in self.helpers.items() if item["running"]]
            if self.active_source:
                users.append("a" * 64)
            return "\n".join(users)
        if args[:3] in (("docker", "ps", "-aq"), ("docker", "ps", "-q")):
            if self.active_source and any(str(x).startswith("volume=") for x in args):
                return "a" * 64
            return ""
        if args[:3] == ("docker", "network", "create"):
            name = args[-1]
            self.networks.add(name)
            return "a" * 64
        if args[:3] == ("docker", "volume", "create"):
            self.volumes.add(args[-1])
            return args[-1]
        if args[:3] == ("docker", "network", "inspect"):
            name = args[-1]
            return json.dumps([{"Name": name, "Driver": "bridge", "Internal":
                                (name == resources.NETWORKS[0][0]) and not self.bad_network, "Containers": {},
                                "Labels": {"com.docker.compose.project": r12.R12_PROJECT}}])
        if args[:3] == ("docker", "volume", "inspect"):
            name = args[-1]
            return json.dumps([{"Name": name, "Driver": "local", "Mountpoint": "/docker/" + name,
                                "Labels": {"com.docker.compose.project": r12.R12_PROJECT,
                                           "centrochange.mission": "C109"}}])
        if args[:2] == ("docker", "create"):
            self.next_id += 1
            ident = format(self.next_id, "064x")
            mounts = [x for x in args if isinstance(x, str) and x.startswith("type=volume,")]
            self.helpers[ident] = {"source": mounts[0].split("source=")[1].split(",")[0],
                                   "dest": mounts[1].split("source=")[1].split(",")[0],
                                   "running": False}
            return ident
        if args[:2] == ("docker", "start"):
            self.helpers[args[-1]]["running"] = True
            return args[-1]
        if args[:2] == ("docker", "stop"):
            self.helpers[args[-1]]["running"] = False
            return args[-1]
        if args[:2] == ("docker", "rm"):
            self.helpers.pop(args[-1])
            return args[-1]
        if args[:2] == ("docker", "inspect"):
            ident = args[-1]
            item = self.helpers[ident]
            mounts = [{"Destination": "/source", "Name": item["source"],
                       "RW": False, "Type": "volume"},
                      {"Destination": "/dest", "Name": item["dest"],
                       "RW": True, "Type": "volume"},
                      {"Destination": "/home/frappe/frappe-bench/logs",
                       "RW": True, "Type": "tmpfs"},
                      {"Destination": "/home/frappe/frappe-bench/sites",
                       "RW": True, "Type": "tmpfs"}]
            if self.extra_mount:
                mounts.append({"Destination": "/unexpected", "RW": True, "Type": "volume"})
            return json.dumps([{"Id": ident, "State": {"Running": item["running"], "Pid": 1234},
                                "Config": {"User": "0:0", "Labels": {"com.docker.compose.project": r12.R12_PROJECT}},
                                "HostConfig": {"Memory": resources.MEMORY - int(self.bad_cap),
                                               "MemorySwap": resources.MEMORY, "NetworkMode": "none"},
                                "Mounts": mounts}])
        raise AssertionError(f"unexpected resource command {args}")

    def process(self, args):
        self.calls.append(tuple(args))
        if "cp" in args:
            result = FakeProcess(fail=self.copy_failure)
            result.remaining = 150 if self.long_copy else 2
            return result
        if "python3" in args:
            return FakeProcess("b" * 64 if self.bad_digest and args[-1] == "/dest" else "a" * 64)
        raise AssertionError(args)

    def sleep(self, seconds):
        self.test.sleep(seconds)

    def snapshot(self, pid, container_id):
        return SimpleNamespace(pid=pid, inode=42, memory_current=1024)

    def safety(self, state, initial_oom):
        start.guard(state, initial_oom)


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
                       "volumes": {f"v{i}": {"name": resources.DEST_PREFIX + suffix}
                                   for i, suffix in enumerate(resources.SUFFIXES)},
                       "networks": {f"n{i}": {"name": name}
                                    for i, (name, _) in enumerate(resources.NETWORKS)}}
        self.write_config()
        (self.state / "compose-final-private.json").write_text("{}")
        (self.root / "compose-gated.override.json").write_text("{}")
        self.calls = []
        self.resource_host = FakeResourceHost(self)

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
             patch.object(start.urllib.request, "urlopen", return_value=Reply()), \
             patch.object(resources, "oom_count", return_value=7):
            r12.preflight(self.root, launch=self.launch, sleep=self.sleep, host_run=self.host,
                          prepare=lambda root, image: resources.prepare(root, host=self.resource_host, image=image))

    def test_green_sequence_reaches_exact_precreation_gate(self):
        self.exercise()
        self.assertTrue((self.state / "r12-preflight-attestation.json").is_file())
        self.assertFalse((self.state / "app-attempted").exists())
        self.assertGreaterEqual(min(self.renewals.values()), 3)
        self.assertEqual(len([c for c in self.resource_host.calls if c[:2] == ("docker", "create")]), 5)
        self.assertFalse(any("up" in call for call in self.calls))
        self.assertEqual(len(json.loads((self.state / "r12-resource-integrity.json").read_text())), 5)
        self.assertIn(("docker", "ps", "-q", "--no-trunc", "--filter",
                       "label=com.docker.compose.project=centrochange-dev"), self.calls)

    def test_long_serial_copy_keeps_all_four_guards_renewing(self):
        self.resource_host.long_copy = True
        self.exercise()
        self.assertGreater(self.clock[0] - dt.datetime.fromisoformat(self.activation["start_utc"]).timestamp(), 60)
        self.assertGreaterEqual(min(self.renewals.values()), 5)

    def test_incomplete_copy_stops_before_application(self):
        self.resource_host.copy_failure = True
        with self.assertRaisesRegex(RuntimeError, "volume operation failed"):
            self.exercise()
        self.assertTrue((self.state / "r12-resources-attempted").exists())
        self.assertFalse((self.state / "r12-resource-integrity.json").exists())
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_integrity_error_stops_before_application(self):
        self.resource_host.bad_digest = True
        with self.assertRaisesRegex(RuntimeError, "integrity mismatch"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_helper_cap_violation_stops_before_copy(self):
        self.resource_host.bad_cap = True
        with self.assertRaisesRegex(RuntimeError, "cap mismatch"):
            self.exercise()
        self.assertFalse(any("exec" in call for call in self.resource_host.calls))

    def test_unexpected_helper_mount_stops_before_copy(self):
        self.resource_host.extra_mount = True
        with self.assertRaisesRegex(RuntimeError, "helper identity or cap mismatch"):
            self.exercise()
        self.assertFalse(any("exec" in call for call in self.resource_host.calls))

    def test_preexisting_destination_stops_without_creation(self):
        self.resource_host.volumes.add(resources.DEST_PREFIX + resources.SUFFIXES[0])
        with self.assertRaisesRegex(RuntimeError, "already exist"):
            self.exercise()
        self.assertFalse(any("create" in call for call in self.resource_host.calls))

    def test_active_source_stops_without_creation(self):
        self.resource_host.active_source = True
        with self.assertRaisesRegex(RuntimeError, "mounted by a running container"):
            self.exercise()
        self.assertFalse(any("create" in call for call in self.resource_host.calls))

    def test_network_isolation_mismatch_stops_before_volume_copy(self):
        self.resource_host.bad_network = True
        with self.assertRaisesRegex(RuntimeError, "network isolation mismatch"):
            self.exercise()
        self.assertFalse(any(c[:3] == ("docker", "volume", "create") for c in self.resource_host.calls))

    def test_guard_loss_during_copy_stops(self):
        original = self.resource_host.sleep
        def loss(seconds):
            original(seconds)
            if any("exec" in call for call in self.resource_host.calls):
                (self.state / "safety-stop.json").write_text("{}")
        self.resource_host.sleep = loss
        with self.assertRaisesRegex(RuntimeError, "watchdog"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_docker_access_loss_during_copy_stops(self):
        original = self.resource_host.sleep
        def loss(seconds):
            original(seconds)
            if any("exec" in call for call in self.resource_host.calls):
                access.atomic_json(self.state / "guard-access-alert.json", {"reason": "Docker API unavailable"})
        self.resource_host.sleep = loss
        with self.assertRaisesRegex(RuntimeError, "guard renewal failed"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

    def test_rc22_identity_change_during_copy_stops(self):
        original = self.resource_host.sleep
        def change(seconds):
            original(seconds)
            if any("exec" in call for call in self.resource_host.calls):
                self.live_ids[0] = format(99, "064x")
        self.resource_host.sleep = change
        with self.assertRaisesRegex(RuntimeError, "RC22 container identity changed"):
            self.exercise()
        self.assertFalse((self.state / "r12-preflight-attestation.json").exists())

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
                # Independent activation snapshots; a real failed preparation
                # remains single-use and cannot be retried.
                (self.state / "r12-resources-attempted").unlink(missing_ok=True)
                self.resource_host.volumes = {resources.SOURCE_PREFIX + s for s in resources.SUFFIXES}
                self.resource_host.networks.clear()
                self.clock[0] = dt.datetime.now(dt.timezone.utc).timestamp()
                self.tick[0] = 100.0
                if change == "memory":
                    self.config["services"][ORDER[0]]["mem_limit"] -= 1
                elif change == "swap":
                    self.config["services"][ORDER[0]]["memswap_limit"] += 1
                else:
                    self.config["networks"]["n0"]["name"] = "centrochange-dev_default"
                self.write_config()
                with self.assertRaisesRegex(RuntimeError, "budget|RAM/swap|network mapping"):
                    self.exercise()
                self.config["services"][ORDER[0]]["mem_limit"] = EXPECTED_MAX[ORDER[0]]
                self.config["services"][ORDER[0]]["memswap_limit"] = EXPECTED_MAX[ORDER[0]]
                self.config["networks"]["n0"]["name"] = resources.NETWORKS[0][0]

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
        self.resource_host.missing_source = True
        with self.assertRaisesRegex(RuntimeError, "source volume missing"):
            self.exercise()
        self.resource_host.missing_source = False
        original = self.host
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
