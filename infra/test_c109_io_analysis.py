"""Negative cases prevent false attribution or a weakened PSI threshold."""

import unittest

from c109_io_analysis import analyze


def sample(time, host, read=0, local=0):
    return {"time": time, "io_psi": {"full": host}, "psi": {"full": 0},
            "available": 5 * 1024**3, "oom": 7,
            "probes": [{"name": "/lab-c-fit-db-1", "io_stat": f"8:0 rbytes={read} wbytes=0\n",
                        "local_io_psi": f"full avg10={local:.2f} avg60=0 total=0\n"}]}


class IoAnalysisTest(unittest.TestCase):
    def test_crossing_keeps_conservative_limit_and_uncertainty(self):
        result = analyze([sample(1, .99), sample(2, 1.36, 4096, .0)])
        self.assertEqual(result["threshold"], 1.0)
        self.assertEqual(len(result["crossings"]), 1)
        self.assertEqual(result["crossings"][0]["observed"][0]["read_delta"], 4096)
        self.assertIn("UNPROVEN", result["attribution"])

    def test_no_crossing_is_not_failure(self):
        self.assertEqual(analyze([sample(1, 0), sample(2, .99)])["crossings"], [])

    def test_incomplete_samples_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze([sample(1, 0)])


if __name__ == "__main__":
    unittest.main()
