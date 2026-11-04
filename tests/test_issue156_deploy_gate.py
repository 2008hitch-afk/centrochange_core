import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('deploy_candidate', Path(__file__).resolve().parents[1] / 'infra' / 'deploy_candidate_dev.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DeployGateTests(unittest.TestCase):
    def test_uncoordinated_version_switch_fails_before_docker(self):
        with patch.object(module, 'run_cmd') as run:
            with self.assertRaisesRegex(RuntimeError, 'guardia di rilascio'):
                module.deploy('unverified-image')
            run.assert_not_called()
