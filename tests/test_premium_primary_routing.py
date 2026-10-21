"""The one-UI cutover stays off until the Site flag is explicitly enabled."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = (Path(__file__).resolve().parent.parent / 'app/centrochange_core/centrochange_core'
        / 'operations/client_landing.py')


class Redirect(Exception):
    pass


class PrimaryRoutingTests(unittest.TestCase):
    def setUp(self):
        self.roles = {'manager': ['CC Manager'], 'tech': ['CC Manager', 'System Manager']}
        self.frappe = SimpleNamespace(
            conf={}, session=SimpleNamespace(user='manager'),
            local=SimpleNamespace(request=None, flags=SimpleNamespace(redirect_location=None)),
            utils=SimpleNamespace(cint=lambda value: int(value or 0)),
            get_roles=lambda user: self.roles.get(user, []), Redirect=Redirect)
        with patch.dict(sys.modules, {'frappe': self.frappe}):
            spec = importlib.util.spec_from_file_location('cc_primary_test', PATH)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def test_off_by_default_preserves_current_landing(self):
        self.assertEqual(self.module.client_home(), '/app/cc-unified-desk?cc_view=agenda')
        self.frappe.local.request = SimpleNamespace(method='GET', path='/finanza')
        self.module.redirect_legacy_operational_routes()
        self.assertIsNone(self.frappe.local.flags.redirect_location)

    def test_after_gate_react_is_primary_and_technical_desk_remains(self):
        self.frappe.conf['cc_premium_primary'] = '1'
        self.assertEqual(self.module.client_home(), '/premium')
        self.assertEqual(self.module.client_home('tech'), '/app/cc-unified-desk?cc_view=agenda')
        self.frappe.local.request = SimpleNamespace(method='GET', path='/app/cc-unified-desk')
        with self.assertRaises(Redirect):
            self.module.redirect_legacy_operational_routes()
        self.assertEqual(self.frappe.local.flags.redirect_location, '/premium')

    def test_legacy_public_alias_and_api_boundary(self):
        self.frappe.conf['cc_premium_primary'] = 1
        self.frappe.session.user = 'Guest'
        self.frappe.local.request = SimpleNamespace(method='GET', path='/primo_incontro')
        with self.assertRaises(Redirect):
            self.module.redirect_legacy_operational_routes()
        self.assertEqual(self.frappe.local.flags.redirect_location, '/premium-primo-incontro')
        self.frappe.session.user = 'manager'
        self.frappe.local.flags.redirect_location = None
        self.frappe.local.request = SimpleNamespace(method='POST', path='/api/method/centrochange_core.catalog.records')
        self.module.redirect_legacy_operational_routes()
        self.assertIsNone(self.frappe.local.flags.redirect_location)


if __name__ == '__main__':
    unittest.main()
