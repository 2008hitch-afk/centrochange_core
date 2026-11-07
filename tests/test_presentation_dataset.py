"""Offline regression for the exact client-presentation dataset."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "presentation_verify", ROOT / "infra/verify_presentation_dataset.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class PresentationDatasetTest(unittest.TestCase):
    def test_dataset_is_coherent_without_real_contacts_or_overlaps(self):
        result = mod.verify(mod.load())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual((result["professionals"], result["patients"],
                          result["payers"], result["appointments"]), (4, 18, 17, 35))


if __name__ == "__main__":
    unittest.main()
