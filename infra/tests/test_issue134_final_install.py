"""Static safety contract for the single Owner-gated final localization update."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'infra/issue134_final_install.py'
spec = importlib.util.spec_from_file_location('cc_final_install', SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class FinalInstallGateTests(unittest.TestCase):
    def test_exact_source_image_and_six_service_overlay(self):
        self.assertEqual(installer.gate.BASE_SOURCE,
                         '0e6299d8a5507cc5d7dde46336870c0cd6667718')
        self.assertEqual(installer.gate.BASE_IMAGE,
                         'sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5')
        self.assertEqual(installer.gate.SOURCE,
                         '6fc6ecacd43fc486f747a99428757be2c6cdbb68')
        self.assertEqual(installer.gate.ACTIVE_OVERLAY_SHA,
                         '8da3285db7b15e01dadb878a0a2fc0d72bd21ee11669ee39e036117bd269cb1f')
        import yaml
        overlay = yaml.safe_load(installer.gate.OVERLAY.read_text())
        self.assertEqual(set(overlay['services']), set(installer.gate.APP))
        self.assertEqual({v['image'] for v in overlay['services'].values()}, {installer.gate.IMAGE})
        self.assertFalse(any('ports' in v or 'volumes' in v for v in overlay['services'].values()))

    def test_only_private_docker_listeners_and_origin_guard_retained(self):
        template = installer.gate.FRONTEND_TEMPLATE.read_text()
        for listener in ('listen ${NGINX_LISTEN_PORT};', 'listen 80;', 'listen 8082;'):
            self.assertEqual(template.count(listener), 1)
        self.assertIn('if ($cc_realtime_public_origin_valid = 0) { return 403; }', template)
        self.assertIn('proxy_set_header Origin http://${FRAPPE_SITE_NAME_HEADER}:${NGINX_LISTEN_PORT};', template)

    def test_old_owner_gate_cannot_authorize_new_candidate(self):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'gate.json'
            value = {'issue': 134, 'candidate': installer.gate.SOURCE,
                     'executor_sha256': 'a' * 64,
                     'authorize': 'ISSUE134_ONE_CUMULATIVE_DEV_UPDATE',
                     'window_start_utc': (now - timedelta(minutes=1)).isoformat(),
                     'operation_deadline_utc': (now + timedelta(hours=3)).isoformat(),
                     'recovery_deadline_utc': (now + timedelta(hours=4)).isoformat()}
            path.write_text(json.dumps(value))
            path.chmod(0o600)
            with self.assertRaises(installer.gate.Stop):
                installer.validate_owner_gate(path, 'a' * 64)
            value['authorize'] = 'ISSUE134_FINAL_ONE_CUMULATIVE_DEV_UPDATE'
            path.write_text(json.dumps(value))
            with patch.object(installer, 'datetime') as mocked:
                mocked.fromisoformat.side_effect = datetime.fromisoformat
                mocked.now.return_value = now
                self.assertEqual(installer.validate_owner_gate(path, 'a' * 64)['operation_end'],
                                 datetime.fromisoformat(value['operation_deadline_utc']))


if __name__ == '__main__':
    unittest.main()
