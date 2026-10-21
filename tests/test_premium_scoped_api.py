"""Offline contract tests. Fake Frappe isolates service logic; never a live-backend PASS."""
import importlib.util
import json
from datetime import date
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core'


class Denied(Exception):
    pass


class Invalid(Exception):
    pass


class FakeDoc:
    def __init__(self, doctype='Item', name='ITEM-A', **fields):
        self.doctype, self.name, self.modified = doctype, name, 'v1'
        self.fields = {'item_name': 'Prima visita', **fields}
        self.writes = 0
        self.permissions = {'read', 'write', 'create', 'print'}

    def get(self, field):
        return getattr(self, field, self.fields.get(field))

    def __getattr__(self, field):
        if field in self.fields:
            return self.fields[field]
        raise AttributeError(field)

    def set(self, field, value):
        self.fields[field] = value

    def check_permission(self, permission):
        if permission not in self.permissions:
            raise Denied(permission)

    def save(self):
        self.writes += 1
        self.modified = 'v2'

    def insert(self):
        self.writes += 1
        self.name = 'NEW-1'
        return self


class FakeDB:
    def __init__(self):
        self.events = []
        self.doc = FakeDoc()

    def exists(self, doctype, name):
        if doctype == 'Branch':
            return name == 'A'
        if doctype == 'CC Patient Assignment':
            return isinstance(name, dict) and name.get('center') == 'A' and name.get('patient') == 'PAT-A'
        if doctype == 'CC Center Membership':
            return isinstance(name, dict) and name.get('center') == 'A' and name.get('user') == 'pro@example.invalid'
        return False

    def get_values(self, doctype, filters, fieldname=None, as_dict=False, for_update=False):
        self.last_filters = filters
        return [types.SimpleNamespace(before_state=json.dumps(before, sort_keys=True), after_state=json.dumps(after, sort_keys=True))
                for event, before, after in self.events if event == filters['event_type'] and filters['before_state'][1].strip('%') in json.dumps(before)]


class ScopedApiTest(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        self.role_allowed = True
        self.locked = 0
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = Denied
        self.frappe.session = types.SimpleNamespace(user='manager@example.invalid')
        self.frappe.db = self.db
        self.frappe.throw = lambda message, exc=Invalid: (_ for _ in ()).throw(exc(message))
        self.frappe.get_doc = lambda doctype, name=None, **kwargs: self.db.doc if not isinstance(doctype, dict) else FakeDoc(doctype['doctype'], 'DRAFT', **{k: v for k, v in doctype.items() if k != 'doctype'})
        self.frappe.parse_json = json.loads
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.get_list = lambda doctype, **kwargs: [types.SimpleNamespace(name='PAY-A', cc_center='A')]
        self.frappe.get_print = lambda *args, **kwargs: '<html><body>Prova sintetica</body></html>'
        self.frappe.utils = types.SimpleNamespace(validate_email_address=lambda value: '@' in value)
        self.audit = types.ModuleType('centrochange_core.security.audit')
        self.audit.atomic = lambda fn: fn
        self.audit.serialize = lambda value: json.dumps(value, sort_keys=True, default=str, separators=(',', ':'))
        self.audit.append = lambda event, doctype, name, before, after, reason: self.db.events.append((event, before, after))
        self.guards = types.ModuleType('centrochange_core.security.guards')
        self.guards.require_manager = lambda: None if self.role_allowed else self.frappe.throw('ruolo negato', Denied)
        self.guards.require_center = lambda center: None if center == 'A' else self.frappe.throw('centro negato', Denied)
        self.guards.is_manager = lambda: self.role_allowed
        self.guards.patient_contexts = lambda: {('PAT-A', 'A')}
        self.guards.practitioner_for = lambda: 'PRO-A'
        self.guards.roles = lambda: ['CC Manager'] if self.role_allowed else ['CC Professional']
        self.lifecycle = types.ModuleType('centrochange_core.security.lifecycle')
        self.lifecycle.lock = lambda: setattr(self, 'locked', self.locked + 1)
        modules = {'frappe': self.frappe, 'centrochange_core': types.ModuleType('centrochange_core'),
                   'centrochange_core.security': types.ModuleType('centrochange_core.security'),
                   'centrochange_core.security.audit': self.audit, 'centrochange_core.security.guards': self.guards,
                   'centrochange_core.security.lifecycle': self.lifecycle}
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.scoped_api', ROOT / 'scoped_api.py')
        self.api = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.api
        spec.loader.exec_module(self.api)

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.scoped_api', None)

    def mutate(self, key='K', value='Nuovo nome', version='v1', center='A'):
        return self.api.mutate('item', center, 'Item', 'ITEM-A', {'item_name': value}, ('item_name',), version, key, 'motivo')

    def test_update_and_replay_do_not_duplicate_write_or_audit(self):
        first = self.mutate()
        second = self.mutate()
        self.assertFalse(first['replay'])
        self.assertTrue(second['replay'])
        self.assertEqual(self.db.doc.writes, 1)
        self.assertEqual(len(self.db.events), 1)
        self.assertEqual(self.locked, 2)

    def test_same_key_different_payload_denied(self):
        self.mutate()
        with self.assertRaises(Invalid):
            self.mutate(value='Diverso')
        self.assertEqual(self.db.doc.writes, 1)

    def test_stale_version_denied_without_write(self):
        with self.assertRaises(Invalid):
            self.mutate(version='stale')
        self.assertEqual(self.db.doc.writes, 0)

    def test_role_center_and_native_permission_denials(self):
        self.role_allowed = False
        with self.assertRaises(Denied):
            self.mutate()
        self.role_allowed = True
        with self.assertRaises(Denied):
            self.mutate(center='B')
        self.db.doc.permissions.remove('write')
        with self.assertRaises(Denied):
            self.mutate()
        self.assertEqual(self.db.doc.writes, 0)

    def test_mass_assignment_and_invalid_pagination_denied(self):
        with self.assertRaises(Denied):
            self.api.mutate('item', 'A', 'Item', 'ITEM-A', {'customer': 'CROSS'}, ('item_name',), 'v1', 'K', 'motivo')
        for args in ((0, 0), (101, 0), (50, -1), ('oops', 0)):
            with self.assertRaises(Invalid):
                self.api.page(*args)
        self.assertEqual(self.db.doc.writes, 0)

    def test_create_and_replay(self):
        first = self.api.create('create', 'A', 'Item', {'item_name': 'Nuovo'}, ('item_name',), 'KC', 'motivo')
        second = self.api.create('create', 'A', 'Item', {'item_name': 'Nuovo'}, ('item_name',), 'KC', 'motivo')
        self.assertEqual(first['name'], 'NEW-1')
        self.assertTrue(second['replay'])
        self.assertEqual(len(self.db.events), 1)
        with self.assertRaises(Invalid):
            self.api.create('create', 'A', 'Item', {'item_name': 'Altro'}, ('item_name',), 'KC', 'motivo')

    def test_payment_read_scope_and_print_permission(self):
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: date.fromisoformat(value)
        guards = types.ModuleType('centrochange_core.finance.guards')
        guards.require_finance = lambda center: None if center == 'A' and self.role_allowed else self.frappe.throw('finanza negata', Denied)
        self.db.doc = FakeDoc('Payment Entry', 'PAY-A', cc_center='A', references=[], posting_date='2026-10-21',
                              payment_type='Receive', party_type='Customer', party='C-1', paid_amount=50,
                              received_amount=50, unallocated_amount=0, mode_of_payment='Contanti', docstatus=1)
        with patch.dict(sys.modules, {'frappe.utils': utils, 'centrochange_core.finance': types.ModuleType('centrochange_core.finance'),
                                      'centrochange_core.finance.guards': guards}):
            self.frappe.utils = utils
            spec = importlib.util.spec_from_file_location('centrochange_core.finance.payments', ROOT / 'finance/payments.py')
            payments = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(payments)
            self.assertEqual(payments.records('A', '2026-10-01', '2026-10-21')['rows'][0].name, 'PAY-A')
            self.assertEqual(payments.detail('A', 'PAY-A')['party'], 'C-1')
            with self.assertRaises(Denied):
                payments.detail('B', 'PAY-A')
            with self.assertRaises(Invalid):
                payments.records('A', '2024-01-01', '2026-10-21')
            spec = importlib.util.spec_from_file_location('centrochange_core.finance.documents', ROOT / 'finance/documents.py')
            documents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(documents)
            self.assertIn('Prova sintetica', documents.preview('A', 'Payment Entry', 'PAY-A')['html'])
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A', 'Formato non approvato')
            self.db.doc.fields['references'] = [types.SimpleNamespace(reference_doctype='Sales Invoice', reference_name='INV-B', allocated_amount=50)]
            original_get_doc = self.frappe.get_doc
            self.frappe.get_doc = lambda doctype, name=None, **kwargs: FakeDoc('Sales Invoice', 'INV-B', cc_center='B') if doctype == 'Sales Invoice' else original_get_doc(doctype, name, **kwargs)
            with self.assertRaises(Denied):
                payments.detail('A', 'PAY-A')
            self.frappe.get_doc = original_get_doc
            self.db.doc.fields['references'] = []
            self.db.doc.permissions.remove('print')
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A')
            self.db.doc.permissions.add('print')
            self.db.doc.fields['cc_center'] = 'B'
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A')
            with self.assertRaises(Denied):
                documents.preview('A', 'Patient', 'PAY-A')

    def test_catalog_service_write_and_cross_center_denial(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.catalog', ROOT / 'catalog.py')
        catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(catalog)
        catalog._scope = lambda center: {'services': ['SERV-A'], 'types': ['TYPE-A'], 'items': ['ITEM-A'], 'price_list': 'LIST-A'}
        self.db.doc = FakeDoc('CC Center Service', 'SERV-A', center='A', appointment_type='TYPE-A', enabled=1)
        result = catalog.service_save('A', 'SERV-A', 0, 'v1', 'S1', 'motivo')
        self.assertEqual(result['name'], 'SERV-A')
        self.assertEqual(self.db.doc.get('enabled'), 0)
        self.assertEqual(catalog.service_save('A', 'SERV-A', 0, 'v1', 'S1', 'motivo')['replay'], True)
        with self.assertRaises(Denied):
            catalog.service_save('B', 'SERV-A', 0, 'v2', 'S2', 'motivo')
        with self.assertRaises(Invalid):
            catalog.service_save('A', 'SERV-A', 'wrong', 'v2', 'S3', 'motivo')
        with self.assertRaises(Denied):
            catalog.service_save('A', 'SERV-A', 0, 'v2', 'S4', 'motivo', docstatus=1)
        self.assertEqual(self.db.doc.writes, 1)

    def test_catalog_rejects_unapproved_kind_and_invalid_rate(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.catalog', ROOT / 'catalog.py')
        catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(catalog)
        with self.assertRaises(Denied):
            catalog.records('A', 'Customer')
        for amount in ('NaN', '-1', '12.345', 'garbage'):
            with self.assertRaises(Invalid):
                catalog.price_save('A', 'PRICE-A', amount, 'v1', 'P1', 'motivo')

    def test_profile_updates_preserve_sensitive_links(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        self.db.doc = FakeDoc('Patient', 'PAT-A', first_name='Persona', last_name='Prova', email='a@example.invalid', customer='CUS-A')
        result = profiles.patient_save('A', 'PAT-A', 'Persona nuova', 'Prova', 'b@example.invalid', 'v1', 'K-PAT', 'motivo')
        self.assertEqual(result['name'], 'PAT-A')
        self.assertEqual(self.db.doc.get('customer'), 'CUS-A')
        self.assertEqual(self.db.doc.writes, 1)
        with self.assertRaises(Denied):
            profiles.patient_save('B', 'PAT-A', 'Altro', 'Prova', 'b@example.invalid', 'v2', 'K-B', 'motivo')
        self.db.doc = FakeDoc('Healthcare Practitioner', 'PRO-A', user_id='pro@example.invalid', first_name='Professionista', status='Active', supplier='SUP-A')
        result = profiles.practitioner_save('A', 'PRO-A', 'Nome nuovo', 'Cognome', 'v1', 'K-PRO', 'motivo')
        self.assertEqual(result['name'], 'PRO-A')
        self.assertEqual(self.db.doc.get('status'), 'Active')
        self.assertEqual(self.db.doc.get('supplier'), 'SUP-A')

    def test_profile_unapproved_email_and_professional_write_denied(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        self.db.doc = FakeDoc('Patient', 'PAT-A', first_name='Persona', last_name='Prova', email='a@example.invalid')
        with self.assertRaises(Invalid):
            profiles.patient_save('A', 'PAT-A', 'Persona', 'Prova', 'not-an-email', 'v1', 'K-BAD', 'motivo')
        with self.assertRaises(Denied):
            profiles.patient_save('A', 'PAT-A', 'Persona', 'Prova', 'a@example.invalid', 'v1', 'K-EXTRA', 'motivo', customer='CUS-B')
        self.role_allowed = False
        with self.assertRaises(Denied):
            profiles.patient_save('A', 'PAT-A', 'Persona', 'Prova', 'a@example.invalid', 'v1', 'K-PRO', 'motivo')
        self.assertEqual(self.db.doc.writes, 0)


if __name__ == '__main__':
    unittest.main()
