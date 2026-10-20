"""Fail-closed topology checks for the temporary #134 rendering clone."""
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'issue134_locale_clone.py'
spec = importlib.util.spec_from_file_location('cc134_clone', SOURCE)
clone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clone)


def config():
    return {'name':clone.PROJECT,
            'networks':{clone.PROJECT+'-net':{}},
            'volumes':{clone.PROJECT+'-sites':{}},
            'services':{'frontend':{'ports':[{'mode':'ingress','target':8080,
                'published':'8082','protocol':'tcp','host_ip':'127.0.0.2'}]},
                'backend':{'image':clone.BASE}}}


class CloneIsolationTests(unittest.TestCase):
    def check(self, value):
        with patch.object(clone, 'run', return_value=SimpleNamespace(stdout=json.dumps(value).encode())):
            return clone.verify_isolation(Path('/private/clone'))

    def test_valid_private_topology(self):
        self.assertEqual(self.check(config())['name'], clone.PROJECT)

    def test_shared_volume_rejected(self):
        value=config(); value['volumes']['centrochange-dev-sites']={}
        with self.assertRaises(RuntimeError): self.check(value)

    def test_shared_network_rejected(self):
        value=config(); value['networks']['centrochange-dev-net']={}
        with self.assertRaises(RuntimeError): self.check(value)

    def test_public_or_dev_listener_rejected(self):
        for address in ('0.0.0.0','127.0.0.1'):
            value=config(); value['services']['frontend']['ports'][0]['host_ip']=address
            with self.assertRaises(RuntimeError): self.check(value)

    def test_dev_service_reference_rejected(self):
        value=config(); value['services']['backend']['image']='centrochange-dev:latest'
        with self.assertRaises(RuntimeError): self.check(value)


if __name__ == '__main__':
    unittest.main()
