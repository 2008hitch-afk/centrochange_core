"""Pin single candidate, cache lifecycle and no Agenda source changes."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('issue134_italian_gate',
                                              ROOT / 'infra/issue134_italian_install.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
gate = module.gate


class InstallerTests(unittest.TestCase):
    def test_exact_base_and_candidate(self):
        self.assertEqual(gate.BASE_SOURCE, 'cc763958c234c9cbcc8cb46ce9f57533e47410ba')
        self.assertEqual(gate.BASE_IMAGE,
                         'sha256:17380aa9aed4ee287d8c46ed1d851fe94ef42aa6586f3b9f379e0b8aff3f3602')
        self.assertEqual(gate.SOURCE, '0e6299d8a5507cc5d7dde46336870c0cd6667718')
        self.assertEqual(gate.OVERLAY.read_text().count('image: '+gate.IMAGE), 6)
        self.assertEqual(gate.ACTIVE_OVERLAY_SHA,
                         gate.file_sha(ROOT / 'infra/compose.issue75_native_ux.yaml'))

    def test_only_localization_app_files_change(self):
        paths = gate.changed_files()
        self.assertEqual(len(paths), 8)
        self.assertTrue(any(path.endswith('/translations/it.csv') for path in paths))
        self.assertFalse(any('cc_unified_desk' in path or path.endswith('/workspace.js') or
                             path.endswith('/workspace.css') for path in paths))

    def test_cache_is_refreshed_after_activation_and_rollback(self):
        class Probe:
            calls = []
            def backend_python(self, source):
                self.calls.append(source)
                return 'CC_ITALIAN_CACHE=PASS CC_ITALIAN_ROLLBACK_CACHE=PASS'
        probe = Probe()
        module.refresh_translation_cache(probe, 'Professione')
        self.assertIn('clear_cache()', probe.calls[0])
        self.assertIn("assert actual == 'Professione'", probe.calls[0])
        original_restore = module._restore_services
        original_old_probe = gate.old_probe
        try:
            module._restore_services = lambda *args, **kwargs: 'restored'
            gate.old_probe = lambda: probe
            self.assertEqual(module.restore_services(None, None, None), 'restored')
            self.assertIn('clear_cache()', probe.calls[1])
        finally:
            module._restore_services = original_restore
            gate.old_probe = original_old_probe


if __name__ == '__main__':
    unittest.main()
