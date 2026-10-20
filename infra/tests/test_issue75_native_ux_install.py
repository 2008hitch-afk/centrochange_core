"""Issue #75 installer pins the current Agenda, app delta and rollback base."""
import hashlib
import importlib.util
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / 'infra/issue75_native_ux_install.py'
spec = importlib.util.spec_from_file_location('issue75_native_install', WRAPPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
gate = module.gate

class NativeUxInstallTests(unittest.TestCase):
    def test_only_native_presentation_files_change(self):
        paths = gate.changed_files()
        self.assertEqual(len(paths), 7)
        self.assertTrue(all('/public/' in path for path in paths))
        self.assertFalse(any('cc_unified_desk' in path or 'agenda' in path.lower() for path in paths))

    def test_agenda_baseline_is_exact_and_unmodified(self):
        source = 'app/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.css'
        for commit in (gate.BASE_SOURCE, gate.SOURCE):
            contents = subprocess.check_output(['git','show',f'{commit}:{source}'],cwd=ROOT)
            self.assertEqual(hashlib.sha256(contents).hexdigest(), gate.AGENDA_CSS_SHA)

    def test_recoverability_pins(self):
        self.assertEqual(gate.BASE_TAG, 'centrochange-single:client-demo-cf0eff7')
        self.assertEqual(gate.BASE_IMAGE, 'sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834')
        self.assertEqual(gate.OVERLAY.read_text().count('image: '+gate.IMAGE), 6)
        self.assertEqual(gate.ACTIVE_OVERLAY_SHA, gate.file_sha(ROOT/'infra/compose.client_demo.yaml'))

if __name__ == '__main__':
    unittest.main()
