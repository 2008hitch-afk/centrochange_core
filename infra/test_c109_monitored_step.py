import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from c109_compose_gate import FINAL_UI_PROJECT
from c109_monitored_step import TestCommandFailed, main


class FailedTestHandling(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        state = self.root / "app-run"
        state.mkdir()
        now = dt.datetime.now(dt.timezone.utc)
        (state / "activation.json").write_text(json.dumps({
            "target": FINAL_UI_PROJECT,
            "start_utc": (now - dt.timedelta(minutes=1)).isoformat(),
            "mutation_end_utc": (now + dt.timedelta(minutes=1)).isoformat(),
        }))
        self.command = ["docker", "exec", FINAL_UI_PROJECT + "-qa", "false"]

    @staticmethod
    def fake_process(*args, **kwargs):
        class Process:
            returncode = 1

            def poll(self):
                return self.returncode
        return Process()

    def test_failed_assertion_preserves_lab_only_in_explicit_test_mode(self):
        with patch("c109_monitored_step.run", return_value="\n".join(str(i) * 12 for i in range(1, 10))), \
             patch("c109_monitored_step.oom_count", return_value=7), \
             patch("c109_monitored_step.guard"), \
             patch("c109_monitored_step.subprocess.Popen", side_effect=self.fake_process), \
             patch("c109_monitored_step.stop_only_ours") as stop:
            with self.assertRaises(TestCommandFailed):
                main(self.root, 5, self.command, test_command=True)
            stop.assert_not_called()
            assert (self.root / "app-run" / "test-failures.jsonl").is_file()
            with self.assertRaisesRegex(RuntimeError, "bounded Docker step exited"):
                main(self.root, 5, self.command)
            stop.assert_called_once()

    def test_test_mode_rejects_nonlocal_target(self):
        with self.assertRaisesRegex(RuntimeError, "this activation"):
            main(self.root, 5, ["docker", "exec", "centrochange-dev-backend-1", "false"], test_command=True)

    def test_guard_trip_stops_lab_even_in_test_mode(self):
        with patch("c109_monitored_step.run", return_value="\n".join(str(i) * 12 for i in range(1, 10))), \
             patch("c109_monitored_step.oom_count", return_value=7), \
             patch("c109_monitored_step.guard", side_effect=[None, RuntimeError("RC22 alert")]), \
             patch("c109_monitored_step.subprocess.Popen", side_effect=self.fake_process), \
             patch("c109_monitored_step.stop_only_ours") as stop:
            with self.assertRaisesRegex(RuntimeError, "RC22 alert"):
                main(self.root, 5, self.command, test_command=True)
            stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
