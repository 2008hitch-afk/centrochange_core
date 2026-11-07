import importlib.util
import json
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

    def test_candidate_sha_must_match_exactly(self):
        sha = 'a' * 40
        info = [{'Id': 'sha256:' + '1' * 64, 'Config': {'Labels': {'centrochange.mode': 'single-stack-full', 'centrochange.source': sha}}}]
        with patch.object(module, 'run_cmd', return_value=json.dumps(info)):
            self.assertEqual(module.verify_candidate_image('image', expected_source_sha=sha, expected_digest='sha256:' + '1' * 64)['source_sha'], sha)
            with self.assertRaises(ValueError):
                module.verify_candidate_image('image', expected_source_sha=sha[:7], expected_digest='sha256:' + '1' * 64)
            with self.assertRaises(ValueError):
                module.verify_candidate_image('image', expected_source_sha=sha[:-1] + 'b', expected_digest='sha256:' + '1' * 64)

    def test_candidate_digest_is_exact_not_substring(self):
        digest = 'sha256:' + '2' * 64
        info = [{'Id': 'sha256:' + '1' * 64, 'RepoDigests': ['repo@' + digest], 'Config': {'Labels': {'centrochange.mode': 'single-stack-full', 'centrochange.source':'a' * 40}}}]
        with patch.object(module, 'run_cmd', return_value=json.dumps(info)):
            module.verify_candidate_image('image', expected_digest=digest, expected_source_sha='a' * 40)
            with self.assertRaises(ValueError):
                module.verify_candidate_image('image', expected_digest=digest[:16], expected_source_sha='a' * 40)

    def test_image_identity_is_mandatory(self):
        with self.assertRaises(ValueError):
            module.verify_candidate_image('image')
