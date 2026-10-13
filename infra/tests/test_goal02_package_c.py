"""Offline GOAL-02 consolidation checks; no Frappe runtime or DEV mutation."""
import ast
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / 'app/centrochange_core/centrochange_core/hooks.py'
BASE = '2f0aa47f51d452a3e711cb838b1dd350611cb6cb'
REQUIRED = {
    'centrochange_core.finance.request_guard.before_request',
    'centrochange_core.security.diagnostics.before_request',
    'centrochange_core.security.api.before_request',
    'centrochange_core.operations.notes.request_guard',
}


class ConsolidationTests(unittest.TestCase):
    def test_before_request_guards_are_retained_once(self):
        tree = ast.parse(HOOKS.read_text())
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == 'before_request'
                               for target in node.targets)]
        self.assertEqual(len(assignments), 1, 'a later reassignment can erase the guards')
        initial = ast.literal_eval(assignments[0].value)
        self.assertEqual(set(initial), REQUIRED)
        appended = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'append' and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'before_request'):
                appended.append(ast.literal_eval(node.args[0]))
        self.assertEqual(len(appended), 2)
        self.assertEqual(len(set(initial + appended)), 6)

    def test_package_changes_do_not_touch_security_or_business_modules(self):
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD'],
                                          cwd=ROOT, text=True).splitlines()
        forbidden = ('/security/', '/finance/', '/scheduling/', '/operations/', '/doctype/')
        app = [name for name in changed if name.startswith('app/')]
        self.assertTrue(app)
        self.assertTrue(all(name.endswith(('.js', '.css')) and not any(part in name for part in forbidden)
                            for name in app), app)
        self.assertNotIn('app/centrochange_core/centrochange_core/hooks.py', changed)

    def test_historical_correction_pr_is_not_an_ancestor(self):
        result = subprocess.run(['git', 'merge-base', '--is-ancestor',
                                 '382042c493dc07db142ce1e1abc2159060444f49', 'HEAD'],
                                cwd=ROOT, check=False)
        self.assertEqual(result.returncode, 1, '#128 must remain outside the candidate')


if __name__ == '__main__':
    unittest.main()
