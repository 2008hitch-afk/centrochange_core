"""Regression checks for EMPV v1.1 brownfield adoption (Issue #199).

No network, browser, server, customer data or runtime deployment is required.
These checks validate structure and provenance, not that UX/UAT was executed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "handoff-analyst", "solution-architect", "product-art-director",
    "ux-prototyping", "data-model-review", "vertical-slice-engineer",
    "qa-validation", "premium-ui-reviewer", "security-review", "release-engineer"
}
EXISTING_SKILLS = {"centrochange-premium-ui", "ui-ux-pro-max"}


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class EmpvBrownfieldAdoptionTests(unittest.TestCase):
    def test_canonical_upstream_pinned_files_are_exact(self):
        manifest = json.loads((ROOT / "factory/source.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["sop_version"], "1.1")
        self.assertEqual(manifest["upstream_repository"], "empv26/empv-ai-software-factory")
        self.assertEqual(
            manifest["upstream_commit"],
            "02818f47606bffdeea4d4fda49c6bb12e0e739f4"
        )
        self.assertEqual(len(manifest["files"]), 20)
        for path, source in manifest["files"].items():
            with self.subTest(path=path):
                f = ROOT / path
                self.assertTrue(f.is_file(), path)
                self.assertEqual(git_blob_sha(f.read_bytes()), source["blob_sha"])
                self.assertTrue(source["origin"])

    def test_project_goals_use_real_handoff_without_fabricated_authorization(self):
        contract = json.loads((ROOT / "factory/contract.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / "factory/state.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], state["sop_version"])
        self.assertEqual(state["project_id"], "CENTROCHANGE-HC-0005")
        self.assertTrue(state["handoff_ref"].startswith("github:"))
        self.assertIsInstance(state["goals"], list)
        cmd = [sys.executable, str(ROOT / "scripts/goal_factory.py")]
        for command in ("status", "validate-project"):
            with self.subTest(command=command):
                result = subprocess.run(
                    cmd + [command, "--root", str(ROOT)],
                    capture_output=True, text=True, timeout=15
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)

    def test_original_and_new_skills_coexist(self):
        for name in SKILLS | EXISTING_SKILLS:
            with self.subTest(skill=name):
                f = ROOT / ".agents" / "skills" / name / "SKILL.md"
                self.assertTrue(f.is_file(), name)
                self.assertTrue(f.read_text(encoding="utf-8").startswith("---\n"))
        self.assertIn("AUDIT-11", (ROOT / "AGENTS.md").read_text())
        self.assertIn("AUDIT-11", (ROOT / "docs/qa/ACTIVE-GOAL-ROUTER.md").read_text())

    def test_feedback_config_is_local_only_and_has_distinct_browser_port(self):
        config_file = ROOT / "factory/dev-feedback.example.json"
        spec = importlib.util.spec_from_file_location(
            "empv_dev_feedback", ROOT / "scripts/dev_feedback.py"
        )
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cwd, cmd, url, suites = module.config_load(
            ROOT, "factory/dev-feedback.example.json"
        )
        self.assertEqual(cwd, ROOT / "frontend/premium")
        self.assertEqual(cmd, ["npm", "run", "dev"])
        self.assertEqual(
            url, "http://127.0.0.1:5182/assets/centrochange_core/premium/"
        )
        self.assertEqual(suites["typecheck"], ["npm", "run", "typecheck"])
        self.assertTrue(any("playwright.feedback.config.ts" in arg for arg in suites["ui"]))
        self.assertTrue(config_file.is_file())

        script = (ROOT / "frontend/premium/playwright.feedback.config.ts").read_text()
        self.assertIn("5183", script)
        self.assertIn("VITE_CC_SYNTHETIC_UI=1", script)
        self.assertIn("reuseExistingServer: false", script)
        standard = (ROOT / "frontend/premium/playwright.config.ts").read_text()
        self.assertIn("5182", standard)

    def test_local_files_are_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text()
        self.assertIn("/factory/dev-feedback.json", ignore)
        self.assertIn("/.factory-runtime/", ignore)
        self.assertTrue((ROOT / "docs/factory/ADOPTION-2026-11-03.md").is_file())


if __name__ == "__main__":
    unittest.main()
