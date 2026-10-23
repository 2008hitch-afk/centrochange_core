"""The one-UI cutover stays off until the Site flag is explicitly enabled."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = (Path(__file__).resolve().parent.parent / 'app/centrochange_core/centrochange_core'
        / 'operations/client_landing.py')


class Response:
    def __init__(self):
        self.status_code = 200
        self.headers = {}
        self.data = None

    def set_data(self, data):
        self.data = data


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
            utils=SimpleNamespace(cint=lambda value: int(value or 0)),
            get_roles=lambda user: self.roles.get(user, []))
        with patch.dict(sys.modules, {'frappe': self.frappe}):
            spec = importlib.util.spec_from_file_location('cc_primary_test', PATH)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def route(self, method, path):
        response = Response()
        request = SimpleNamespace(method=method, path=path)
        self.module.redirect_legacy_operational_routes(response, request)
        return response

    def test_off_by_default_preserves_current_landing(self):
        self.assertEqual(self.module.client_home(), '/app/cc-unified-desk?cc_view=agenda')
        self.assertEqual(self.route('GET', '/finanza').status_code, 200)

    def test_after_gate_react_is_primary_and_technical_desk_remains(self):
        self.frappe.conf['cc_premium_primary'] = '1'
        self.assertEqual(self.module.client_home(), '/premium')
        self.assertEqual(self.module.client_home('mixed'), '/premium')
        self.assertIsNone(self.module.client_home('tech'))
        self.assertIsNone(self.module.client_home('Administrator'))
        self.assertIsNone(self.module.client_home('Guest'))
        response = self.route('GET', '/app/cc-unified-desk')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/premium')
        self.assertEqual(response.headers['Cache-Control'], 'private, no-store')
        self.assertEqual(response.data, b'')

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
                        response = self.route(method, path)
                        self.assertEqual(response.status_code, 302)
                        self.assertEqual(response.headers['Location'], '/premium')

    def test_technical_and_guest_routes_preserved(self):
        self.frappe.conf['cc_premium_primary'] = 1
        for user in ('tech', 'Administrator', 'Guest'):
            self.frappe.session.user = user
            for path in ('/app/cc-unified-desk', '/desk/cc-unified-desk', '/desk/patient'):
                with self.subTest(user=user, path=path):
                    self.assertEqual(self.route('GET', path).status_code, 200)

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
                self.assertEqual(self.route(method, path).status_code, 200)

    def test_legacy_public_alias_and_api_boundary(self):
        self.frappe.conf['cc_premium_primary'] = 1
        self.frappe.session.user = 'Guest'
        self.assertEqual(self.route('GET', '/primo_incontro').headers['Location'],
                         '/premium-primo-incontro')
        self.frappe.session.user = 'manager'
        self.assertEqual(self.route('POST', '/api/method/centrochange_core.catalog.records').status_code,
                         200)


if __name__ == '__main__':
    unittest.main()
