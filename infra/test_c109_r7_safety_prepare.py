import tempfile
import unittest
from pathlib import Path

from c109_r7_safety_prepare import prepare


class PrepareTest(unittest.TestCase):
    def test_rejects_wrong_activation(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            with self.assertRaises(ValueError):
                prepare(p / "missing", p / "out", {"target": "other"})

    def test_rejects_missing_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            (p / "source").write_text("ip=psi('io')\nif ip['full']>=1:errs.append('IO_PSI')\n")
            with self.assertRaises(ValueError):
                prepare(p / "source", p / "out",
                        {"target": "centrochange-c109-gated-r7", "io_waiver": True, "issue": 109})
