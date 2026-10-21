"""Offline failure checks for the complete image/source parity gate."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('full_stack_gate', ROOT / 'infra/verify_full_single_stack.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class FullStackPackageTests(unittest.TestCase):
    def test_approved_backend_and_premium_files_are_exact(self):
        manifest = gate.source_manifest(ROOT)
        gate.check_source(ROOT, manifest)
        self.assertIn('centrochange_core/finance/receivables.py', manifest['files'])
        self.assertIn('centrochange_core/catalog.py', manifest['files'])
        self.assertIn('centrochange_core/hooks.py', manifest['reviewed_backend_deltas'])

    def test_changed_manifest_is_rejected(self):
        manifest = gate.source_manifest(ROOT)
        manifest['files']['centrochange_core/catalog.py'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            gate.check_source(ROOT, manifest)

    def test_missing_image_file_is_rejected(self):
        manifest = gate.source_manifest(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'missing/drifted'):
                gate.check_image(Path(tmp), manifest)


if __name__ == '__main__':
    unittest.main()
