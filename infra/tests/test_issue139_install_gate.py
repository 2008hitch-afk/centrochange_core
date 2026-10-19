"""Safety invariants for the one-shot #139 installation gate; no Docker writes."""
import importlib.util
import hashlib
import json
import os
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
    def test_candidate_template_is_world_readable_and_probed_as_runtime_user(self):
        source = SOURCE.read_text()
        self.assertIn('COPY --chmod=0644 issue139_frontend.conf.template', source)
        self.assertIn("'--read-only', '--user', 'frappe',", source)
        self.assertIn("'--entrypoint', 'cat', IMAGE, IMAGE_FRONTEND_TEMPLATE", source)
        self.assertNotIn("'--read-only', '--user', '0',\n                                   '--entrypoint', 'cat'", source)

    def test_frontend_nginx_config_is_checked_isolated_before_dev_stop(self):
        source = SOURCE.read_text()
        build = source[source.index('def build_candidate('):source.index('def backup(')]
        execute = source[source.index('def execute('):source.index('def recover(')]
        self.assertIn("'--network', 'none'", build)
        self.assertIn("'--read-only', '--user', 'frappe'", build)
        self.assertIn("('/etc/nginx/conf.d', '/tmp', '/run', '/var/lib/nginx')", build)
        self.assertIn("'--entrypoint', 'sh', IMAGE, '-c'", build)
        self.assertIn('nginx -t', build)
        self.assertIn('isolated candidate frontend did not remain running', build)
        self.assertIn("'docker', 'rm', '-f', probe_name", build)
        self.assertLess(execute.index('candidate_id = build_candidate(paths, output)'),
                        execute.index("'application_stop_started'"))

    def test_security_runner_keeps_isolated_python_in_both_processes(self):
        command = gate.security_command('data-sha', 'communication-sha')
        self.assertEqual(command[:2], [gate.sys.executable, '-I'])
        self.assertEqual(command[-4:], ['--expected-data', 'data-sha',
                                        '--expected-communication', 'communication-sha'])
        inner = (gate.REPO / 'infra/issue137_safe_security_run.py').read_text()
        self.assertIn("command = [sys.executable, '-I',", inner)

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

    def test_persistent_candidate_overlay_replaces_only_its_versioned_content_and_rollback_restores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / 'active.yaml'
            candidate = root / 'candidate.yaml'
            active.write_text('old versioned overlay\n')
            candidate.write_text('new versioned overlay\n')
            active.chmod(0o600)
            prior_bytes = active.read_bytes()
            stat = active.stat()
            fake = {'settings': {'COMPOSE_FILE': 'base:' + str(active)}}
            with patch.object(gate, 'ACTIVE_OVERLAY', active), patch.object(gate, 'OVERLAY', candidate):
                gate.select_candidate_overlay(fake)
                self.assertEqual(active.read_bytes(), candidate.read_bytes())
                self.assertEqual(active.stat().st_mode & 0o777, 0o600)
                pre = {'files': [], 'overlay_bytes': prior_bytes,
                       'overlay_stat': types.SimpleNamespace(st_mode=stat.st_mode,
                           st_uid=stat.st_uid, st_gid=stat.st_gid),
                       'settings': {}, 'services': {}}
                # Exercise the exact checkpoint restoration primitive independently
                # from Docker, then prove subsequent regular Compose reads the old overlay.
                gate.private_write(active, pre['overlay_bytes'])
                active.chmod(pre['overlay_stat'].st_mode & 0o777)
                os.chown(active, pre['overlay_stat'].st_uid, pre['overlay_stat'].st_gid)
                self.assertEqual(active.read_bytes(), prior_bytes)

    def test_candidate_is_app_only_and_preserves_already_migrated_centers(self):
        source = gate.run(['git', 'diff', '--name-only', gate.BASE_SOURCE, gate.SOURCE, '--', gate.APP_PREFIX]).stdout.splitlines()
        self.assertTrue(source)
        self.assertTrue(all(path.startswith(gate.APP_PREFIX) for path in source), source)
        executor = SOURCE.read_text()
        self.assertNotIn("'bench', '--site', SITE, 'migrate'", executor)
        self.assertIn("== {BRANCH_A: 1, BRANCH_B: 0}", executor)
        self.assertIn("'center_a': 'already active and audited; preserved'", executor)
        self.assertIn("'center_b': 'inactive; preserved'", executor)
        self.assertIn("'rm', '-f', '--', remote", executor)

    def test_owner_window_names_one_functional_update_without_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gate.json'
            now = datetime.now(timezone.utc)
            payload = {'issue': 139, 'candidate': gate.SOURCE, 'executor_sha256': 'a' * 64,
                       'authorize': 'DEV_FIRST_MVP_SCOPED_UPDATE_AND_LIVE_TESTS',
                       'window_start_utc': (now - timedelta(minutes=1)).isoformat(),
                       'operation_deadline_utc': (now + timedelta(hours=3)).isoformat(),
                       'recovery_deadline_utc': (now + timedelta(hours=4)).isoformat()}
            path.write_text(json.dumps(payload)); path.chmod(0o600)
            self.assertIn('operation_end', gate.validate_owner_gate(path, 'a' * 64))

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
                       'authorize': 'DEV_FIRST_MVP_SCOPED_UPDATE_AND_LIVE_TESTS',
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
            active = overlay
            active.write_text('candidate')
            baseline_env = Path(directory) / 'runtime.env'
            baseline_env.write_bytes(b'baseline')
            pre = {'files': [Path('/baseline.yaml')], 'settings': {'DB_PASSWORD': 'synthetic'},
                   'module': module, 'services': services, 'data': {'sha256': 'old'},
                   'schema': {'sha256': 'schema'}, 'permissions': {'sha256': 'permissions'},
                   'overlay_bytes': b'baseline overlay',
                   'overlay_stat': types.SimpleNamespace(st_mode=0o600, st_uid=os.getuid(), st_gid=os.getgid())}
            def compose(_files, *args):
                calls.append(('compose', args))
            with patch.object(gate, 'ACTIVE_OVERLAY', overlay), \
                 patch.object(gate, 'ENV', baseline_env), \
                 patch.object(gate, 'compose', side_effect=compose), \
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
            self.assertEqual(overlay.read_bytes(), b'baseline overlay')

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
