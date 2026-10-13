"""Offline checks for the privileged executor. No Docker or DEV writes."""
import importlib.util
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
    def test_atomic_env_change_and_exact_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            env = Path(folder) / 'runtime.env'
            original = b'SITE_NAME=centrochange.local\nCC_UAT_IMAGE=centrochange-single:old\nSECRET=private\n'
            env.write_bytes(original)
            env.chmod(0o600)
            before = env.stat()
            with patch.object(deploy, 'ENV', env):
                deploy.replace_env_image(deploy.NEW_TAG, original, before)
                changed = env.read_bytes()
                self.assertIn(b'CC_UAT_IMAGE=' + deploy.NEW_TAG.encode(), changed)
                self.assertIn(b'SECRET=private', changed)
                self.assertEqual(env.stat().st_mode & 0o777, 0o600)
                deploy.restore_env(original, before)
                self.assertEqual(env.read_bytes(), original)

    def test_checkpoint_requires_all_compose_and_env_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder)
            for name in deploy.COMPOSE_NAMES:
                (checkpoint / name).write_bytes((deploy.COMPOSE_DIR / name).read_bytes())
            (checkpoint / 'runtime.env.sha256').write_text(deploy.ORIGINAL_ENV_SHA + '  runtime.env\n')
            checkpoint.chmod(0o700)
            with patch.object(deploy, 'CHECKPOINT', checkpoint):
                deploy.checkpoint_preflight(deploy.ORIGINAL_ENV_SHA, owner_uid=os.getuid())
                (checkpoint / deploy.COMPOSE_NAMES[0]).write_text('drift')
                with self.assertRaises(deploy.Stop):
                    deploy.checkpoint_preflight(deploy.ORIGINAL_ENV_SHA, owner_uid=os.getuid())


if __name__ == '__main__':
    unittest.main()
