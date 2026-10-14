"""No executor rehearsal command may reach shared DEV."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

source = Path(__file__).resolve().parents[1] / 'issue139_rehearsal_scope.py'
spec = importlib.util.spec_from_file_location('issue139_rehearsal_scope', source)
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)
IMAGE = 'centrochange-single:issue139-e2e-unit'


class RehearsalScopeTests(unittest.TestCase):
    def test_exec_and_compose_route_only_to_clone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = root / 'runtime.env'; env.touch()
            base = root / 'compose.yaml'; base.touch()
            routed = scope.scope_command(['docker', 'exec', '-w', '/home/frappe/frappe-bench',
                                            'centrochange-dev-backend-1', 'bench', 'migrate'],
                                           root=root, image=IMAGE)
            self.assertIn('cc139-w5-isolated-backend-1', routed)
            self.assertNotIn('centrochange-dev-backend-1', routed)
            compose = ['docker', 'compose', '--env-file', str(env), '-p', scope.PROJECT,
                       '-f', str(base), 'up', '-d', '--no-deps', 'backend']
            self.assertEqual(scope.scope_command(compose, root=root, image=IMAGE), compose)

    def test_rejects_dev_project_shared_file_and_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for command in (
                ['docker', 'compose', '--env-file', str(root / 'runtime.env'), '-p',
                 'centrochange-dev', '-f', str(root / 'compose.yaml'), 'up', 'backend'],
                ['docker', 'compose', '--env-file', '/home/empv26/.local/state/centrochange-single/runtime.env',
                 '-p', scope.PROJECT, '-f', str(root / 'compose.yaml'), 'up', 'backend'],
                ['docker', 'cp', '/etc/passwd', 'centrochange-dev-backend-1:/tmp/passwd'],
                ['docker', 'volume', 'rm', 'centrochange-dev-sites'],
                ['docker', 'run', '--network=none', '-v', 'centrochange-dev-sites:/sites', IMAGE],
                ['python3', '-c', 'open("/tmp/unsafe", "w").write("x")'],
                ['docker', 'compose', '--env-file', str(root / 'runtime.env'), '-p',
                 scope.PROJECT, '-f', '/tmp/other-project.yaml', 'up', 'backend'],
            ):
                with self.subTest(command=command), self.assertRaises(scope.IsolationError):
                    scope.scope_command(command, root=root, image=IMAGE)

    def test_clone_security_chain_propagates_isolated_python(self):
        gate_source = source.with_name('issue139_install_gate.py')
        runner_source = source.with_name('issue137_safe_security_run.py')
        spec = importlib.util.spec_from_file_location('issue139_test_gate', gate_source)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / 'runtime.env'
            command = gate.security_command('data', 'communications',
                                            isolated_project=scope.PROJECT, env_file=env)
            self.assertEqual(scope.scope_command(command, root=Path(directory), image=IMAGE),
                             command)
            for invalid in (command[:1] + command[2:],
                            command[:-1] + ['/home/empv26/.local/state/centrochange-single/runtime.env'],
                            [sys.executable, '-I', '/tmp/unsafe.py']):
                with self.assertRaises(scope.IsolationError):
                    scope.scope_command(invalid, root=Path(directory), image=IMAGE)
        self.assertEqual(command[1], '-I')
        self.assertEqual(command[-4:], ['--isolated-project', scope.PROJECT,
                                        '--env-file', str(env)])
        runner = runner_source.read_text()
        self.assertIn("command = [sys.executable, '-I'", runner)
        self.assertIn("command += ['--isolated-project', args.isolated_project]", runner)


if __name__ == '__main__':
    unittest.main()
