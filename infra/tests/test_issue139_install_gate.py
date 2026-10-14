"""Safety invariants for the one-shot #139 installation gate; no Docker writes."""
import importlib.util
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'issue139_install_gate.py'
spec = importlib.util.spec_from_file_location('issue139_gate_test', SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class InstallationGateTests(unittest.TestCase):
    def test_versioned_realtime_proxy_keeps_public_origin_and_internal_auth_route(self):
        template = gate.FRONTEND_TEMPLATE.read_text()
        for allowed in ('"centrochange.local:8082" 1;',
                        '"127.0.0.1:8082" 2;',
                        '"http://centrochange.local:8082" 1;',
                        '"http://127.0.0.1:8082" 2;',
                        '"1:0" 1;', '"1:1" 1;', '"2:0" 1;', '"2:2" 1;'):
            self.assertIn(allowed, template)
        self.assertIn('if ($cc_realtime_public_origin_valid = 0) { return 403; }', template)
        self.assertIn('proxy_set_header Origin http://${FRAPPE_SITE_NAME_HEADER}:${NGINX_LISTEN_PORT};', template)
        self.assertIn('proxy_set_header Host ${FRAPPE_SITE_NAME_HEADER};', template)
        self.assertNotIn('proxy_set_header Origin $proxy_x_forwarded_proto://${FRAPPE_SITE_NAME_HEADER};', template)
        overlay = gate.OVERLAY.read_text()
        self.assertEqual(overlay.count('image: '+gate.IMAGE), 6)
        self.assertNotIn('issue139-candidate', overlay)

    def test_only_six_app_images_and_frontend_alias_may_change(self):
        services = {name: {'image': 'old', 'networks': {'centrochange-dev-net': None}}
                    for name in gate.APP + gate.TECH}
        baseline = {'name': 'centrochange-dev', 'volumes': {'sites': {}},
                    'services': services}
        candidate = json.loads(json.dumps(baseline))
        for name in gate.APP:
            candidate['services'][name]['image'] = gate.IMAGE
        candidate['services']['frontend']['networks']['centrochange-dev-net'] = {
            'aliases': ['centrochange.local']}
        gate.compare_compose(baseline, candidate)
        candidate['services']['redis-cache']['image'] = 'changed'
        with self.assertRaisesRegex(gate.Stop, 'redis-cache'):
            gate.compare_compose(baseline, candidate)

    def test_candidate_env_append_is_exact_and_rollback_restores_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / 'runtime.env'
            old_overlay = root / 'old.yaml'
            new_overlay = root / 'new.yaml'
            original = f'COMPOSE_FILE=base:{old_overlay}\nSECRET=unchanged\n'.encode()
            current.write_bytes(original)
            current.chmod(0o600)
            stat = current.stat()
            with patch.object(gate, 'ENV', current), patch.object(gate, 'BASE_OVERLAY', old_overlay), \
                 patch.object(gate, 'ACTIVE_OVERLAY', new_overlay):
                gate.change_env_for_candidate(original)
                self.assertEqual(current.read_bytes().count(str(new_overlay).encode()), 1)
                self.assertIn(b'SECRET=unchanged', current.read_bytes())
                gate.restore_env(original, stat)
                self.assertEqual(current.read_bytes(), original)

    def test_execution_rejects_unmatched_owner_gate_before_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gate.json'
            path.write_text(json.dumps({'issue': 139, 'authorize': 'anything'}))
            path.chmod(0o600)
            with patch.object(gate, 'static_gate', return_value=['one']), \
                 patch.object(gate, 'preflight') as preflight:
                with self.assertRaisesRegex(gate.Stop, 'Owner gate'):
                    gate.execute('0' * 64, path)
                preflight.assert_not_called()

    def test_dry_run_cannot_select_execute(self):
        # The CLI modes are exclusive; a copied command cannot silently deploy.
        with patch('sys.argv', ['gate', '--dry-run', '--execute']):
            with self.assertRaisesRegex(gate.Stop, 'exactly one mode'):
                gate.main()

    def test_owner_window_rejects_excess_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gate.json'
            now = datetime.now(timezone.utc)
            payload = {'issue': 139, 'candidate': gate.SOURCE, 'executor_sha256': '0' * 64,
                       'authorize': 'ONE_DEV_INSTALL_WITH_MIGRATION_AND_W5',
                       'window_start_utc': (now - timedelta(minutes=1)).isoformat(),
                       'operation_deadline_utc': (now + timedelta(hours=5)).isoformat(),
                       'recovery_deadline_utc': (now + timedelta(hours=6)).isoformat()}
            path.write_text(json.dumps(payload))
            path.chmod(0o600)
            with self.assertRaisesRegex(gate.Stop, 'exceeds'):
                gate.validate_owner_gate(path, '0' * 64)

    def test_recovery_restores_database_before_reopening_frontend(self):
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory) / 'candidate.yaml'
            overlay.write_text('candidate')
            calls = []
            services = {name: {'image': name + '-old'} for name in gate.APP + gate.TECH}
            module = types.SimpleNamespace(
                http_ready=lambda: calls.append('http'),
                snapshot=lambda: services,
                runtime_fingerprint=lambda: {'sha256': 'old'},
                hooks=lambda: ['guard'], GUARDS=['guard'])
            pre = {'files': [Path('/baseline.yaml')], 'settings': {'DB_PASSWORD': 'synthetic'},
                   'module': module, 'services': services, 'data': {'sha256': 'old'},
                   'schema': {'sha256': 'schema'}, 'permissions': {'sha256': 'permissions'}}
            def compose(_files, *args):
                calls.append(('compose', args))
            with patch.object(gate, 'ACTIVE_OVERLAY', overlay), \
                 patch.object(gate, 'compose', side_effect=compose), \
                 patch.object(gate, 'restore_env', side_effect=lambda *_: calls.append('env')), \
                 patch.object(gate, 'restore_backup', side_effect=lambda *_: calls.append('db')), \
                 patch.object(gate, 'schema_fingerprint', return_value=pre['schema']), \
                 patch.object(gate, 'permission_fingerprint', return_value=pre['permissions']):
                gate.restore_services(pre, b'baseline', types.SimpleNamespace(st_mode=0o600,
                                      st_uid=1000, st_gid=1000), data_backup={'db': 'synthetic'},
                                      output=Path(directory))
            database = calls.index('db')
            reopen = next(i for i, call in enumerate(calls) if isinstance(call, tuple)
                          and 'frontend' in call[1] and 'up' in call[1])
            self.assertLess(database, reopen)
            self.assertEqual(calls.count('db'), 1)

    def test_restore_backup_uses_pinned_unix_identity_and_both_real_chown_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'backup.key').write_text('synthetic')
            content = b'synthetic encrypted backup plaintext'
            manifest = {}
            for kind in ('db', 'public', 'private', 'config'):
                filename = f'{kind}.gpg'
                (output / filename).write_bytes(b'encrypted-placeholder')
                manifest[kind] = {'file': filename, 'sha256': hashlib.sha256(content).hexdigest()}
            calls = []

            def command(args, **kwargs):
                calls.append(args)
                if args[-3:] == ['id', '-u', 'frappe']:
                    return types.SimpleNamespace(stdout='1000\n', returncode=0)
                if args[-3:] == ['id', '-g', 'frappe']:
                    return types.SimpleNamespace(stdout='0\n', returncode=0)
                if args[-3:] == ['getent', 'group', 'root']:
                    return types.SimpleNamespace(stdout='root:x:0:\n', returncode=0)
                if args[-3:] == ['getent', 'group', 'frappe']:
                    return types.SimpleNamespace(stdout='', returncode=2)
                return types.SimpleNamespace(stdout='', returncode=0)

            with patch.object(gate, 'run', side_effect=command), \
                 patch.object(gate, 'run_bytes', return_value=content):
                gate.restore_backup(output, manifest, 'synthetic-root-password')
            ownership = [args for args in calls if 'chown' in args]
            self.assertEqual(len(ownership), 5)
            self.assertTrue(all(args[-2] == 'frappe:root' for args in ownership))
            self.assertTrue(any(args[-1].endswith('/site_config.json') for args in ownership))
            self.assertFalse(any('frappe:frappe' in args for args in ownership))

    def test_restore_backup_stops_before_copy_when_unix_identity_drifts(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []

            def command(args, **kwargs):
                calls.append(args)
                if args[-3:] == ['id', '-u', 'frappe']:
                    return types.SimpleNamespace(stdout='1001\n', returncode=0)
                return types.SimpleNamespace(stdout='0\n', returncode=0)

            with patch.object(gate, 'run', side_effect=command), \
                 patch.object(gate, 'run_bytes') as decrypt:
                with self.assertRaisesRegex(gate.Stop, 'Unix identity drift'):
                    gate.restore_backup(Path(directory), {}, 'synthetic')
                decrypt.assert_not_called()
            self.assertFalse(any('cp' in args for args in calls))


if __name__ == '__main__':
    unittest.main()
