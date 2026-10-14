"""Offline safety tests for the single-key Frappe asset cache gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "issue139_asset_cache_gate.py"
spec = importlib.util.spec_from_file_location("asset_gate", SOURCE)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)

MANIFEST = {
    "desk.bundle.css": "/assets/frappe/dist/css/desk.bundle.NEW.css",
    "erpnext.bundle.css": "/assets/erpnext/dist/css/erpnext.bundle.NEW.css",
    "report.bundle.css": "/assets/frappe/dist/css/report.bundle.NEW.css",
}
OLD = gate.KNOWN_STALE
INTEGRITY = ({"sha256": "synthetic", "communication_sha256": "synthetic"}, [])


class AssetGateTests(unittest.TestCase):
    def test_read_only_probe_never_contains_cache_mutation(self):
        captured = []

        def fake_command(args, *, input_text=None):
            captured.append(input_text)
            return 'CC_ASSET_GATE={"manifest":{},"cache_before":{},"cache_after":{}}'

        with patch.object(gate, "command", side_effect=fake_command):
            gate.probe()
        self.assertIn("if False:", captured[0])
        self.assertNotIn("if True:", captured[0])

    def test_stale_cache_requires_explicit_flag(self):
        state = {"manifest": MANIFEST, "cache_before": OLD, "cache_after": OLD}
        with patch.object(gate, "image_and_scope"), patch.object(gate, "integrity", return_value=INTEGRITY), patch.object(gate, "probe", return_value=state) as probe, \
             patch.object(gate, "check_served_assets"), patch.object(sys, "argv", ["gate"]):
            self.assertEqual(gate.main(), 2)
            probe.assert_called_once_with()

    def test_invalidation_verifies_new_mapping(self):
        before = {"manifest": MANIFEST, "cache_before": OLD, "cache_after": OLD}
        after = {"manifest": MANIFEST, "cache_before": OLD, "cache_after": MANIFEST}
        with patch.object(gate, "image_and_scope"), patch.object(gate, "integrity", return_value=INTEGRITY), patch.object(gate, "probe", side_effect=[before, after]) as probe, \
             patch.object(gate, "check_served_assets"), patch.object(sys, "argv", ["gate", "--invalidate"]):
            self.assertEqual(gate.main(), 0)
            self.assertEqual(probe.call_args_list[-1].args, (True,))

    def test_current_cache_cannot_be_invalidated(self):
        current = {"manifest": MANIFEST, "cache_before": MANIFEST, "cache_after": MANIFEST}
        with patch.object(gate, "image_and_scope"), patch.object(gate, "integrity", return_value=INTEGRITY), patch.object(gate, "probe", return_value=current), \
             patch.object(gate, "check_served_assets"), patch.object(sys, "argv", ["gate", "--invalidate"]):
            with self.assertRaisesRegex(RuntimeError, "already current"):
                gate.main()

    def test_post_invalidation_mismatch_fails(self):
        state = {"manifest": MANIFEST, "cache_before": OLD, "cache_after": OLD}
        with patch.object(gate, "image_and_scope"), patch.object(gate, "integrity", return_value=INTEGRITY), patch.object(gate, "probe", return_value=state), \
             patch.object(gate, "check_served_assets"), patch.object(sys, "argv", ["gate", "--invalidate"]):
            with self.assertRaisesRegex(RuntimeError, "failed verification"):
                gate.main()


if __name__ == "__main__":
    unittest.main()
