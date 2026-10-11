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
            for role in guard.ROLES:
                guard.marker_path(state, role).write_text(json.dumps({
                    "pid": 123, "start_ticks": 456,
                    "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}))
            with patch.object(guard, "process_start_ticks", return_value=456):
                guard.require_live_guards(state, max_proof_age=30)

    def test_dead_reused_or_stale_scope_fails_closed(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp)
            for role in guard.ROLES:
                guard.marker_path(state, role).write_text(json.dumps({
                    "pid": 123, "start_ticks": 456,
                    "checked_at": "2020-01-01T00:00:00+00:00"}))
            with patch.object(guard, "process_start_ticks", return_value=457):
                with self.assertRaisesRegex(RuntimeError, "not the verified live process"):
                    guard.require_live_guards(state)
            with patch.object(guard, "process_start_ticks", return_value=456):
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    guard.require_live_guards(state, max_proof_age=30)

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
