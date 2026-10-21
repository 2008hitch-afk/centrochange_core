"""Static gate regression: missing payload or a divergent pin must fail closed."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('premium_package', ROOT / 'infra/premium_single_stack_package.py')
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class PackageGateTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / PACKAGE.MANIFEST).read_text())

    def test_checked_in_source_matches_manifest_and_dockerfile(self):
        PACKAGE.check_contract(ROOT, self.manifest)

    def test_hash_drift_fails(self):
        self.manifest['files']['catalog.py'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'hash drift'):
            PACKAGE.check_contract(ROOT, self.manifest)

    def test_upstream_pin_drift_fails(self):
        self.manifest['upstream_versions']['frappe'] = '99.0.0'
        with self.assertRaisesRegex(RuntimeError, 'pins changed'):
            PACKAGE.check_contract(ROOT, self.manifest)

    def test_pinned_backend_dependency_drift_fails(self):
        self.manifest['base_dependency_files']['security/guards.py'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'backend dependency hash drift'):
            PACKAGE.check_contract(ROOT, self.manifest)

    def test_missing_image_payload_fails_before_import(self):
        with tempfile.TemporaryDirectory() as path:
            bench = Path(path)
            for name in PACKAGE.BASE_FILES:
                target = bench / PACKAGE.DEST / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(subprocess.check_output(
                    ['git', 'show', f'{PACKAGE.BASE_APP_REVISION}:{PACKAGE.APP / name}'], cwd=ROOT))
            with self.assertRaisesRegex(RuntimeError, 'Image payload missing'):
                PACKAGE.check_image(bench, self.manifest)


if __name__ == '__main__':
    unittest.main()
