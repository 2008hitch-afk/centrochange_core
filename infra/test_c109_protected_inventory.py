"""Offline contract tests for C109 protected Docker event identities."""

import json
import unittest

from c109_protected_inventory import records, validate_existing


class ProtectedInventoryTest(unittest.TestCase):
    def test_accepts_complete_unique_ids(self):
        first, second = "a" * 64, "b" * 64
        self.assertEqual(records(first + "\n" + second + "\n"), [{"id": first}, {"id": second}])

    def test_rejects_short_ids(self):
        with self.assertRaises(ValueError):
            records("a" * 12)

    def test_rejects_empty_and_duplicates(self):
        for raw in ("", "a" * 64 + "\n" + "a" * 64):
            with self.assertRaises(ValueError):
                records(raw)

    def test_existing_inventory_must_match_full_live_ids(self):
        first, second = "a" * 64, "b" * 64
        validate_existing(json.dumps([{"id": first}, {"id": second}]), first + "\n" + second)
        for bad in (json.dumps([{"id": first[:12]}, {"id": second}]),
                    json.dumps([{"id": first}]),
                    json.dumps([{"id": first}, {"id": first}])):
            with self.assertRaises(ValueError):
                validate_existing(bad, first + "\n" + second)


if __name__ == "__main__":
    unittest.main()
