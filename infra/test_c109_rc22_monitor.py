import unittest
from unittest.mock import patch

import c109_rc22_monitor as m


class MonitorTest(unittest.TestCase):
    def test_healthy_and_transient_slow(self):
        expected = ["a"] * 9
        for latency in (0.1, 1.1, 0.1):
            alert, count = m.verdict(expected, expected, 200, latency, 0)
            self.assertIsNone(alert)
            self.assertLess(count, 2)

    def test_sustained_and_hard_latency(self):
        expected = ["a"] * 9
        slow = 0
        for _ in range(2):
            alert, slow = m.verdict(expected, expected, 200, 1.2, slow)
            self.assertIsNone(alert)
        self.assertEqual(m.verdict(expected, expected, 200, 1.2, slow)[0],
                         "RC22_SUSTAINED_LATENCY")
        self.assertEqual(m.verdict(expected, expected, 200, 3.0, 0)[0],
                         "RC22_HARD_LATENCY")

    def test_http_and_identity_fail_closed(self):
        expected = ["a"] * 9
        self.assertEqual(m.verdict(expected, expected, None, 0, 0)[0], "RC22_HTTP")
        self.assertEqual(m.verdict(expected, ["b"], 200, 0, 0)[0], "RC22_CONTAINER_IDENTITY")

    def test_targeted_stop_only_exact_r7_label(self):
        calls = []
        def fake_check(args, **kwargs):
            calls.append(args)
            return ["c109-only"]
        def fake_run(args, **kwargs):
            calls.append(args)
            return type("Result", (), {"returncode": 0})()
        with patch.object(m, "c109_ids", lambda project=m.IO_WAIVER_PROJECT: fake_check(
                ["docker", "ps", "-q", "--no-trunc", "--filter",
                 f"label=com.docker.compose.project={project}"])):
            m.stop_c109(fake_run)
        self.assertEqual(calls[-1], ["docker", "stop", "--time", "10", "c109-only"])
        self.assertIn("centrochange-c109-gated-r7", calls[0][-1])
        calls.clear()
        with patch.object(m, "c109_ids", lambda project=m.IO_WAIVER_PROJECT: fake_check(
                ["docker", "ps", "-q", "--no-trunc", "--filter",
                 f"label=com.docker.compose.project={project}"])):
            m.stop_c109(fake_run, project=m.FINAL_UI_PROJECT)
        self.assertIn("centrochange-c109-gated-r8", calls[0][-1])
