"""The next localization candidate cannot inherit an old Owner gate."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'infra/issue134_cumulative_install.py'
spec = importlib.util.spec_from_file_location('cc134_cumulative', SOURCE)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class CumulativeInstallTests(unittest.TestCase):
    def test_baseline_and_six_service_overlay(self):
        self.assertEqual(installer.gate.BASE_SOURCE,
                         '1b7ffc465ff699de163f9536ab04d4dde4da54e3')
        self.assertEqual(installer.gate.BASE_IMAGE,
                         'sha256:d7315cb85d3d51ed6510b9d0f6f1b9b2be639cb2d637f67a57790136f5e55257')
        import yaml
        value = yaml.safe_load(installer.gate.OVERLAY.read_text())
        self.assertEqual(set(value['services']), set(installer.gate.APP))
        self.assertEqual({v['image'] for v in value['services'].values()}, {installer.gate.IMAGE})
        self.assertFalse(any('ports' in v or 'volumes' in v for v in value['services'].values()))

    def test_old_gate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'gate.json'
            value = {'issue':134, 'candidate':installer.gate.SOURCE,
                     'executor_sha256':'a'*64,
                     'authorize':'ISSUE134_FINAL_ONE_CUMULATIVE_DEV_UPDATE',
                     'window_start_utc':'2026-10-20T14:00:00Z',
                     'operation_deadline_utc':'2026-10-20T18:00:00Z',
                     'recovery_deadline_utc':'2026-10-20T19:00:00Z'}
            path.write_text(json.dumps(value)); path.chmod(0o600)
            with self.assertRaises(installer.gate.Stop):
                installer.validate_owner_gate(path, 'a'*64)

    def test_hook_cache_probe_is_scoped_and_fail_closed(self):
        seen=[]
        module=SimpleNamespace(backend_python=lambda code: seen.append(code) or 'CC_LOCALE_HOOK_CACHE=PASS')
        installer.refresh_hook_cache(module, verify_candidate=True)
        self.assertIn('frappe.client_cache.delete_value("app_hooks")', seen[0])
        self.assertIn('assert "centrochange_core.operations.website_brand.client_time_format" in hooks', seen[0])
        self.assertNotIn('frappe.db.commit()', seen[0])
        with self.assertRaises(installer.gate.Stop):
            installer.refresh_hook_cache(SimpleNamespace(backend_python=lambda _: ''),
                                         verify_candidate=True)

    def test_refresh_runs_after_source_probe_and_rollback(self):
        calls=[]
        module=SimpleNamespace(backend_python=lambda _: calls.append('refresh') or 'CC_LOCALE_HOOK_CACHE=PASS')
        with patch.object(installer, '_source_probe', side_effect=lambda *args: calls.append('source')):
            installer.source_probe(module, [])
        self.assertEqual(calls, ['source', 'refresh'])
        calls.clear()
        with patch.object(installer, '_restore_services', side_effect=lambda *args,**kwargs: calls.append('rollback')):
            with patch.object(installer.gate, 'old_probe', return_value=module):
                installer.restore_services()
        self.assertEqual(calls, ['rollback', 'refresh'])


if __name__ == '__main__': unittest.main()
