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
        self.roles = {
            'manager': ['CC Manager'],
            'secretariat': ['CC Secretariat'],
            'professional': ['CC Professional'],
            'finance': ['CC Finance'],
            'accountant': ['CC Accountant'],
            'mixed': ['CC Manager', 'System Manager'],
            'tech': ['System Manager'],
        }
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
        self.assertEqual(self.module.client_home('mixed'), '/premium')
        self.assertIsNone(self.module.client_home('tech'))
        self.assertIsNone(self.module.client_home('Administrator'))
        self.assertIsNone(self.module.client_home('Guest'))
        self.frappe.local.request = SimpleNamespace(method='GET', path='/app/cc-unified-desk')
        with self.assertRaises(Redirect):
            self.module.redirect_legacy_operational_routes()
        self.assertEqual(self.frappe.local.flags.redirect_location, '/premium')

    def test_all_client_roles_and_desk_aliases(self):
        self.frappe.conf['cc_premium_primary'] = 1
        paths = (
            '/app', '/app/cc-unified-desk', '/app/patient',
            '/desk', '/desk/cc-unified-desk',
            '/desk/centrochange_core/cc-unified-desk', '/desk/patient',
            '/centrochange', '/finanza', '/professionista',
        )
        for user in ('manager', 'secretariat', 'professional', 'finance',
                     'accountant', 'mixed'):
            self.frappe.session.user = user
            self.assertEqual(self.module.client_home(), '/premium')
            for path in paths:
                for method in ('GET', 'HEAD'):
                    with self.subTest(user=user, path=path, method=method):
                        self.frappe.local.flags.redirect_location = None
                        self.frappe.local.request = SimpleNamespace(method=method, path=path)
                        with self.assertRaises(Redirect):
                            self.module.redirect_legacy_operational_routes()
                        self.assertEqual(self.frappe.local.flags.redirect_location, '/premium')

    def test_technical_and_guest_routes_preserved(self):
        self.frappe.conf['cc_premium_primary'] = 1
        for user in ('tech', 'Administrator', 'Guest'):
            self.frappe.session.user = user
            for path in ('/app/cc-unified-desk', '/desk/cc-unified-desk', '/desk/patient'):
                with self.subTest(user=user, path=path):
                    self.frappe.local.flags.redirect_location = None
                    self.frappe.local.request = SimpleNamespace(method='GET', path=path)
                    self.module.redirect_legacy_operational_routes()
                    self.assertIsNone(self.frappe.local.flags.redirect_location)

    def test_post_api_login_and_premium_are_not_redirected(self):
        self.frappe.conf['cc_premium_primary'] = 1
        for method, path in (
            ('POST', '/desk/cc-unified-desk'), ('POST', '/app/cc-unified-desk'),
            ('GET', '/api/method/frappe.auth.get_logged_user'),
            ('POST', '/api/method/centrochange_core.catalog.records'),
            ('GET', '/login'), ('GET', '/premium'), ('GET', '/premium/primo-incontro'),
            ('GET', '/assets/centrochange_core/premium/app.js'),
        ):
            with self.subTest(method=method, path=path):
                self.frappe.local.flags.redirect_location = None
                self.frappe.local.request = SimpleNamespace(method=method, path=path)
                self.module.redirect_legacy_operational_routes()
                self.assertIsNone(self.frappe.local.flags.redirect_location)

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
