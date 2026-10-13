"""Static safety checks for the Owner-run controlled installation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('goal02_install', ROOT / 'infra/goal02_install_one_command.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class InstallContract(unittest.TestCase):
    def test_frappe_exec_uses_sites_cwd_and_stream_logging(self):
        # Frappe v16.50 logger.py uses ../logs relative to process cwd.
        bench = Path('/home/frappe/frappe-bench')
        self.assertEqual((bench / '..' / 'logs').resolve(), Path('/home/frappe/logs'))
        self.assertEqual((bench / 'sites' / '..' / 'logs').resolve(), bench / 'logs')
        with patch.object(module, 'run') as call:
            call.return_value.stdout = 'ok'
            self.assertEqual(module.backend_python('print(1)'), 'ok')
        argv = call.call_args.args[0]
        self.assertEqual(argv[argv.index('-w') + 1], str(bench / 'sites'))
        self.assertIn('FRAPPE_STREAM_LOGGING=1', argv)
        self.assertEqual(argv[-1], str(bench / 'env/bin/python'))
        self.assertEqual(call.call_args.kwargs['input'], 'print(1)')

    def test_authorized_application_delta(self):
        names = module.git('diff', '--name-only', module.BASE, module.SOURCE, '--', module.REL).stdout.splitlines()
        self.assertEqual(names, sorted(module.REL + x for x in module.CHANGED))
        self.assertEqual(module.digest(module.git_file(module.SOURCE,module.CSS_FILE)), module.CSS_SHA)
        self.assertNotEqual(module.git('merge-base',module.EXCLUDED,module.SOURCE).stdout.strip(),module.EXCLUDED)

    def test_compose_switch_only_changes_six_images(self):
        old = {'name':'centrochange-dev','networks':{'n':{}},'services':{}}
        for service in module.APP + module.TECH + ('configurator',):
            old['services'][service] = {'image':'old','volumes':['same'],'environment':{'SAFE':'1'}}
        new = {'name':'centrochange-dev','networks':old['networks'],
               'services':{key:dict(value) for key,value in old['services'].items()}}
        for service in module.APP:
            new['services'][service]['image'] = module.TARGET
        module.compare_config(old,new)
        new['services']['db']['image'] = 'changed'
        with self.assertRaises(module.Stop):
            module.compare_config(old,new)

    def test_rollback_requires_original_technical_services(self):
        self.assertIn("all(recovered[s] == before[s] for s in TECH)",
                      (ROOT / 'infra/goal02_install_one_command.py').read_text())
        self.assertIn('runtime_fingerprint() == before_data',
                      (ROOT / 'infra/goal02_install_one_command.py').read_text())


if __name__ == '__main__':
    unittest.main()
