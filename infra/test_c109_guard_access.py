"""Offline and read-only tests for the C109 Docker guard scope gate."""

import datetime as dt
import json
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import c109_guard_access as guard


class DockerGuardAccessTest(unittest.TestCase):
    def proof(self, pid=123, ticks=456, seconds_ago=0):
        return {"pid": pid, "start_ticks": ticks, "uid": os.getuid(),
                "euid": os.geteuid(), "egid": os.getegid(), "groups": [1], "socket_gid": 1,
                "docker_host": "unix:///var/run/docker.sock", "docker_context": "default",
                "checked_at": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=seconds_ago)).isoformat()}

    def heartbeats(self, state, seconds_ago=0):
        for name in ("events-heartbeat", "monitor-heartbeat", "rc22-heartbeat"):
            (state / name).write_text(str(__import__("time").time() - seconds_ago))

    def test_event_stream_failure_is_not_green(self):
        fake_socket = type("Socket", (), {"stat": lambda self: type("Info", (), {
            "st_mode": stat.S_IFSOCK | 0o660, "st_gid": 986})()})()
        replies = ["default", "unix:///var/run/docker.sock", "29.8.2", ""]
        with patch.object(guard, "SOCKET", fake_socket), \
             patch.object(guard.os, "getgroups", return_value=[986]), \
             patch.object(guard, "command", side_effect=replies), \
             patch.object(guard.subprocess, "run", return_value=type("Exit", (), {"returncode": 1})()), \
             patch.dict(os.environ, {"DOCKER_HOST": "unix:///var/run/docker.sock", "DOCKER_CONTEXT": "default"}):
            with self.assertRaisesRegex(RuntimeError, "event stream unavailable"):
                guard.check_access("events")

    def test_rejects_other_docker_host_before_api_call(self):
        with patch.dict("os.environ", {"DOCKER_HOST": "tcp://127.0.0.1:2375"}):
            with patch.object(guard, "command") as command:
                with self.assertRaisesRegex(RuntimeError, "endpoint override"):
                    guard.check_access("watchdog")
                command.assert_not_called()

    def test_rejects_other_context_before_api_call(self):
        with patch.dict("os.environ", {"DOCKER_CONTEXT": "remote"}):
            with patch.object(guard, "command") as command:
                with self.assertRaisesRegex(RuntimeError, "context override"):
                    guard.check_access("events")
                command.assert_not_called()

    def test_rejects_unknown_role(self):
        with self.assertRaises(ValueError):
            guard.check_access("application")

    def test_live_markers_accept_matching_pid_and_start_time(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            for role in guard.ROLES:
                guard.atomic_json(guard.marker_path(state, role), self.proof())
            with patch.object(guard, "process_start_ticks", return_value=456):
                guard.require_live_guards(state, max_proof_age=30)

    def test_dead_reused_or_stale_scope_fails_closed(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            for role in guard.ROLES:
                guard.atomic_json(guard.marker_path(state, role), self.proof(seconds_ago=100))
            with patch.object(guard, "process_start_ticks", return_value=457):
                with self.assertRaisesRegex(RuntimeError, "not the verified live process"):
                    guard.require_live_guards(state)
            with patch.object(guard, "process_start_ticks", return_value=456):
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    guard.require_live_guards(state, max_proof_age=30)

    def test_long_preparation_with_multiple_real_renewals(self):
        """A simulated 72-second preparation remains green without raising the 30s cap."""
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            tick = 1000.0
            def at(value):
                return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()
            previous = self.proof(pid=os.getpid(), ticks=456)
            previous["checked_at"] = at(tick)
            guard.atomic_json(guard.marker_path(state, "events"), previous)
            with patch.object(guard, "process_start_ticks", return_value=456), \
                 patch.object(guard.time, "time", return_value=tick + 8), \
                 patch.object(guard, "require_heartbeat"), \
                 patch.object(guard, "check_access") as access:
                for step in range(1, 10):
                    clock = tick + step * 8
                    access.return_value = {**previous, "checked_at": at(clock)}
                    with patch.object(guard.time, "time", return_value=clock):
                        previous = guard.renew_once(state, "events", previous)
                        self.assertLessEqual(guard.proof_age(previous), 30)
                self.assertEqual(access.call_count, 9)
                self.assertEqual(previous["pid"], os.getpid())

    def test_refresh_requires_actual_docker_access_and_does_not_publish_on_failure(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            previous = self.proof(pid=os.getpid())
            guard.atomic_json(guard.marker_path(state, "watchdog"), previous)
            with patch.object(guard, "process_start_ticks", return_value=456), \
                 patch.object(guard, "check_access", side_effect=RuntimeError("Docker API unavailable")):
                with self.assertRaisesRegex(RuntimeError, "Docker API unavailable"):
                    guard.renew_once(state, "watchdog", previous)
            self.assertEqual(json.loads(guard.marker_path(state, "watchdog").read_text()), previous)

    def test_refresh_rejects_stale_marker_reused_pid_or_tampering(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            previous = self.proof(pid=os.getpid(), seconds_ago=31)
            guard.atomic_json(guard.marker_path(state, "events"), previous)
            with patch.object(guard, "process_start_ticks", return_value=456), \
                 patch.object(guard, "check_access") as access:
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    guard.renew_once(state, "events", previous)
                access.assert_not_called()
            previous = self.proof(pid=os.getpid())
            guard.atomic_json(guard.marker_path(state, "events"), previous)
            with patch.object(guard, "process_start_ticks", return_value=457):
                with self.assertRaisesRegex(RuntimeError, "identity changed"):
                    guard.renew_once(state, "events", previous)
            guard.atomic_json(guard.marker_path(state, "events"), {**previous, "socket_gid": 2})
            with self.assertRaisesRegex(RuntimeError, "changed outside"):
                guard.renew_once(state, "events", previous)

    def test_missing_heartbeat_or_monitor_exit_fails_closed(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            previous = self.proof(pid=os.getpid())
            guard.atomic_json(guard.marker_path(state, "events"), previous)
            with patch.object(guard, "process_start_ticks", return_value=456):
                with self.assertRaisesRegex(RuntimeError, "heartbeat missing"):
                    guard.renew_once(state, "events", previous)
            self.heartbeats(state, seconds_ago=60)
            with self.assertRaisesRegex(RuntimeError, "heartbeat stale"):
                guard.require_heartbeat(state, "events")

    def test_context_change_and_failed_docker_probe_do_not_renew(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            previous = self.proof(pid=os.getpid())
            guard.atomic_json(guard.marker_path(state, "rc22"), previous)
            with patch.object(guard, "process_start_ticks", return_value=456), \
                 patch.object(guard, "check_access", return_value={**previous, "docker_context": "remote",
                    "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}):
                with self.assertRaisesRegex(RuntimeError, "context changed"):
                    guard.renew_once(state, "rc22", previous)
            self.assertEqual(json.loads(guard.marker_path(state, "rc22").read_text()), previous)
            with patch.dict(os.environ, {"DOCKER_HOST": "tcp://127.0.0.1:2375"}):
                with self.assertRaisesRegex(RuntimeError, "endpoint override"):
                    guard.check_access("rc22")

    def test_alert_and_expired_proof_cannot_bypass_gate(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            for role in guard.ROLES:
                guard.atomic_json(guard.marker_path(state, role), self.proof(seconds_ago=31))
            with patch.object(guard, "process_start_ticks", return_value=456):
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    guard.require_live_guards(state)
                with self.assertRaisesRegex(ValueError, "cannot be extended"):
                    guard.require_live_guards(state, max_proof_age=300)
                guard.atomic_json(state / "guard-access-alert.json", {"role": "events"})
                with self.assertRaisesRegex(RuntimeError, "renewal failed"):
                    guard.require_live_guards(state)

    def test_failed_renewal_emits_alert_and_stops_only_target(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / "activation.json").write_text(json.dumps({"target": guard.R11_PROJECT}))
            with patch.object(guard, "renew_once", side_effect=RuntimeError("API unavailable")), \
                 patch.object(guard.time, "sleep"), \
                 patch("c109_gated_start.stop_only_ours") as stop, \
                 patch.object(guard.os, "_exit", side_effect=RuntimeError("process exited")):
                with self.assertRaisesRegex(RuntimeError, "process exited"):
                    guard.renewal_loop(state, "events", self.proof())
            self.assertEqual(json.loads((state / "guard-access-alert.json").read_text())["role"], "events")
            stop.assert_called_once_with(state, guard.R11_PROJECT)

    def test_marker_must_be_private_regular_file(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            for role in guard.ROLES:
                guard.atomic_json(guard.marker_path(state, role), self.proof())
            guard.marker_path(state, "events").chmod(0o644)
            with self.assertRaisesRegex(RuntimeError, "not private"):
                guard.require_live_guards(state)

    def test_serve_uses_same_process_for_guard_and_renewal(self):
        for role in guard.ROLES:
            with self.subTest(role=role), TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "app-run").mkdir()
                initial = self.proof(pid=os.getpid())
                with patch.object(guard, "check_access", return_value=initial), \
                     patch.object(guard.threading, "Thread") as thread, \
                     patch.object(guard.runpy, "run_path") as run_path:
                    guard.serve(role, root)
                thread.assert_called_once()
                self.assertEqual(thread.call_args.kwargs["args"], (root / "app-run", role, initial))
                thread.return_value.start.assert_called_once()
                run_path.assert_called_once()
                self.assertEqual(run_path.call_args.kwargs, {"run_name": "__main__"})
                self.assertEqual(json.loads(guard.marker_path(root / "app-run", role).read_text()), initial)

    def test_r11_gate_requires_independent_rc22_scope(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.heartbeats(state)
            (state / "activation.json").write_text(json.dumps({"target": guard.R11_PROJECT}))
            for role in ("events", "watchdog", "expiry"):
                guard.atomic_json(guard.marker_path(state, role), self.proof())
            with patch.object(guard, "process_start_ticks", return_value=456):
                with self.assertRaises(FileNotFoundError):
                    guard.require_live_guards(state)
                guard.atomic_json(guard.marker_path(state, "rc22"), self.proof())
                guard.require_live_guards(state)

    def test_guard_script_and_proof_share_actual_process_id(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "app-run"
            state.mkdir()
            (state / "protected-events.py").write_text(
                "import os\nfrom pathlib import Path\nPath(__file__).with_name('executed-pid').write_text(str(os.getpid()))\n")
            initial = self.proof(pid=os.getpid())
            with patch.object(guard, "check_access", return_value=initial), \
                 patch.object(guard.threading, "Thread"):
                guard.serve("events", root)
            self.assertEqual(int((state / "executed-pid").read_text()), initial["pid"])

    def test_consumed_activation_cannot_launch_scopes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "app-run"
            state.mkdir()
            (state / "activation.json").write_text(json.dumps({
                "issue": 109, "target": "centrochange-c109-gated-r6",
                "status": "OWNER_AUTHORIZED_C_UNIFIED_BOOTSTRAP",
                "hard_stop_utc": "2099-01-01T00:00:00+00:00"}))
            (state / "app-attempted").write_text("used")
            with patch.object(guard, "scope_probe") as probe:
                with self.assertRaisesRegex(RuntimeError, "already attempted"):
                    guard.launch_scopes(root)
                probe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
