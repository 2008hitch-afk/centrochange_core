"""Offline checks for the privileged executor. No Docker or DEV writes."""
import importlib.util
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'issue79_one_command.py'
spec = importlib.util.spec_from_file_location('issue79_one_command', SCRIPT)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class ExecutorTests(unittest.TestCase):
    def test_backend_only_persistent_config_and_exact_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            env = root / 'runtime.env'
            override = root / 'compose.issue79.yaml'
            base = root / 'compose.yaml'
            base.write_text('services:\n  backend:\n    image: ${CC_UAT_IMAGE}\n'
                            '  frontend:\n    image: ${CC_UAT_IMAGE}\n'
                            '  websocket:\n    image: ${CC_UAT_IMAGE}\n'
                            '  queue-short:\n    image: ${CC_UAT_IMAGE}\n'
                            '  queue-long:\n    image: ${CC_UAT_IMAGE}\n'
                            '  scheduler:\n    image: ${CC_UAT_IMAGE}\n'
                            '  configurator:\n    image: ${CC_UAT_IMAGE}\n'
                            '  db:\n    image: mariadb:11\n')
            (root / 'compose.issue124.yaml').write_text('services: {}\n')
            (root / 'compose.uat.yaml').write_text('services: {}\n')
            original = b'CC_UAT_IMAGE=centrochange-single:old\nSECRET=private\n'
            env.write_bytes(original)
            env.chmod(0o600)
            before = env.stat()
            with (patch.object(deploy, 'ENV', env), patch.object(deploy, 'STATE', root),
                  patch.object(deploy, 'OVERRIDE', override), patch.object(deploy, 'COMPOSE_DIR', root)):
                baseline = deploy.configured_services(env_file=env)
                proposed = deploy.configured_services(target=True, env_file=env,
                                                       override_file=deploy.OVERRIDE_SOURCE)
                deploy.require_backend_only(baseline, proposed, 'centrochange-single:old')
                unsafe = {name: dict(value) for name, value in proposed.items()}
                unsafe['frontend']['image'] = deploy.NEW_TAG
                with self.assertRaises(deploy.Stop):
                    deploy.require_backend_only(baseline, unsafe, 'centrochange-single:old')
                deploy.persist_override()
                deploy.persist_compose_file(original, before)
                self.assertEqual(deploy.read_env()['CC_UAT_IMAGE'], 'centrochange-single:old')
                self.assertEqual(deploy.read_env()['COMPOSE_FILE'], deploy.compose_files_value())
                self.assertEqual(deploy.configured_services(target=True, env_file=env,
                                                             override_file=override), proposed)
                deploy.require_default_compose(proposed)
                self.assertEqual([s for s in baseline if baseline[s] != proposed[s]], ['backend'])
                changed = env.read_bytes()
                self.assertIn(b'SECRET=private', changed)
                self.assertEqual(env.stat().st_mode & 0o777, 0o600)
                deploy.restore_env(original, before)
                deploy.remove_override()
                self.assertEqual(env.read_bytes(), original)
                self.assertFalse(override.exists())
                self.assertEqual(deploy.configured_services(env_file=env), baseline)

    def test_evidence_directory_must_be_private_before_switch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            root.chmod(0o755)
            with patch.object(deploy, 'STATE', root):
                with self.assertRaises(deploy.Stop):
                    deploy.evidence_preflight('run')

    def test_checkpoint_requires_all_compose_and_env_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            checkpoint = root / 'checkpoint'
            checkpoint.mkdir(mode=0o700)
            compose = root / 'source-compose'
            compose.mkdir(mode=0o700)
            expected = {}
            for index, name in enumerate(deploy.COMPOSE_NAMES):
                content = f'# deterministic checkpoint fixture {index}\n'
                (compose / name).write_text(content)
                (checkpoint / name).write_bytes((compose / name).read_bytes())
                expected[name] = hashlib.sha256(content.encode()).hexdigest()
            (checkpoint / 'runtime.env.sha256').write_text(deploy.ORIGINAL_ENV_SHA + '  runtime.env\n')
            checkpoint.chmod(0o700)
            with patch.object(deploy, 'CHECKPOINT', checkpoint), patch.object(deploy, 'COMPOSE_DIR', compose), \
                 patch.object(deploy, 'COMPOSE_SHA', expected):
                deploy.checkpoint_preflight(deploy.ORIGINAL_ENV_SHA, owner_uid=os.getuid())
                (checkpoint / deploy.COMPOSE_NAMES[0]).write_text('drift')
                with self.assertRaises(deploy.Stop):
                    deploy.checkpoint_preflight(deploy.ORIGINAL_ENV_SHA, owner_uid=os.getuid())


if __name__ == '__main__':
    unittest.main()
