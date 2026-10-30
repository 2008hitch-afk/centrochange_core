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


class FakeRow(dict):
    __getattr__ = dict.__getitem__


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
        if not self.has_permission(permission):
            raise Denied(permission)

    def has_permission(self, permission):
        return permission in self.permissions

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
        self.operational_center = True
        self.locked = 0
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = Denied
        self.frappe.session = types.SimpleNamespace(user='manager@example.invalid')
        self.frappe.local = types.SimpleNamespace(request=None)
        self.frappe.db = self.db
        self.frappe.conf = {'cc_synthetic_dev': 0, 'cc_uat_demo': 0}
        self.frappe.throw = lambda message, exc=Invalid: (_ for _ in ()).throw(exc(message))
        self.frappe.get_doc = lambda doctype, name=None, **kwargs: self.db.doc if not isinstance(doctype, dict) else FakeDoc(doctype['doctype'], 'DRAFT', **{k: v for k, v in doctype.items() if k != 'doctype'})
        self.frappe.parse_json = json.loads
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.get_list = lambda doctype, **kwargs: [FakeRow(name='PAY-A', cc_center='A')]
        self.frappe.get_print = lambda *args, **kwargs: '<html><body>Prova sintetica</body></html>'
        self.frappe.utils = types.SimpleNamespace(validate_email_address=lambda value: '@' in value)
        self.audit = types.ModuleType('centrochange_core.security.audit')
        self.audit.atomic = lambda fn: fn
        self.audit.serialize = lambda value: json.dumps(value, sort_keys=True, default=str, separators=(',', ':'))
        self.audit.append = lambda event, doctype, name, before, after, reason: self.db.events.append((event, before, after))
        self.guards = types.ModuleType('centrochange_core.security.guards')
        self.guards.require_manager = lambda: None if self.role_allowed else self.frappe.throw('ruolo negato', Denied)
        self.guards.require_center = lambda center: None if center == 'A' else self.frappe.throw('centro negato', Denied)
        self.guards.require_operational_center = lambda center: None if center == 'A' and self.operational_center else self.frappe.throw('centro inattivo', Denied)
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
        finance_guards = types.ModuleType('centrochange_core.finance.guards')
        finance_guards.require_finance = lambda center: self.guards.require_center(center)
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: date.fromisoformat(value) if isinstance(value, str) else value
        self.extra_modules = patch.dict(sys.modules, {'centrochange_core.finance.guards': finance_guards, 'frappe.utils': utils})
        self.extra_modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.finance.documents', ROOT / 'finance/documents.py')
        self.documents = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.documents
        spec.loader.exec_module(self.documents)

    def tearDown(self):
        self.extra_modules.stop()
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

    def test_frappe_rpc_marker_does_not_open_mass_assignment(self):
        method = 'centrochange_core.catalog.item_save'
        self.frappe.local.request = types.SimpleNamespace(path='/api/method/' + method, method='POST')
        self.api.deny_extra({'cmd': method})
        for extra in ({'cmd': method, 'disabled': 0}, {'cmd': 'centrochange_core.catalog.other'},
                      {'cmd': method, 'customer': 'CROSS'}):
            with self.assertRaises(Denied):
                self.api.deny_extra(extra)
        self.frappe.local.request.method = 'GET'
        with self.assertRaises(Denied):
            self.api.deny_extra({'cmd': method})
        self.frappe.local.request.method = 'POST'
        self.frappe.local.request.path = '/api/method/centrochange_core.catalog.other'
        with self.assertRaises(Denied):
            self.api.deny_extra({'cmd': method})
        self.frappe.local.request = None
        with self.assertRaises(Denied):
            self.api.deny_extra({'cmd': method})

    def test_authorized_empty_patient_result_does_not_expand_scope(self):
        self.role_allowed = False  # Finance-like center member, no patient contexts.
        self.guards.patient_contexts = lambda: set()
        calls = []
        def get_all(doctype, **kwargs):
            calls.append((doctype, kwargs))
            if doctype == 'CC Patient Assignment':
                return ['PAT-A']
            return []
        self.frappe.get_all = get_all
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        result = profiles.patients('A')
        self.assertEqual(result, {'rows': [], 'has_more': False})
        patient_query = next(kwargs for doctype, kwargs in calls if doctype == 'Patient')
        self.assertEqual(patient_query['filters']['name'], ['in', ['']])

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
                              received_amount=50, unallocated_amount=0, mode_of_payment='Contanti', docstatus=1,
                              paid_from_account_currency='EUR', paid_to_account_currency='EUR',
                              reference_no='CC-HTTP-UAT0000001 <rif>&')
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
            preview = documents.preview('A', 'Payment Entry', 'PAY-A')
            self.assertTrue(documents.detail('A', 'Payment Entry', 'PAY-A')['can_print'])
            self.assertEqual(preview['format'], 'Centro Change')
            self.assertIn('Pagamento', preview['html'])
            self.assertIn('50,00 EUR', preview['html'])
            self.assertIn('21/10/2026', preview['html'])
            self.assertEqual(documents.detail('A', 'Payment Entry', 'PAY-A')['reference_no'], 'CC-HTTP-UAT0000001 <rif>&')
            self.assertIn('Riferimento operazione', preview['html'])
            self.assertIn('CC-HTTP-UAT0000001 &lt;rif&gt;&amp;', preview['html'])
            self.assertNotIn('mode_of_payment', preview['html'])
            self.db.doc.fields['paid_from_account_currency'] = 'USD'
            mixed = documents.preview('A', 'Payment Entry', 'PAY-A')['html']
            self.assertIn('50,00 USD', mixed)
            self.assertIn('50,00 EUR', mixed)
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A', 'Formato non approvato')
            self.db.doc.fields['docstatus'] = 2
            self.assertFalse(documents.detail('A', 'Payment Entry', 'PAY-A')['can_print'])
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A')
            self.db.doc.fields['docstatus'] = 1
            self.db.doc.fields['references'] = [types.SimpleNamespace(reference_doctype='Sales Invoice', reference_name='INV-B', allocated_amount=50)]
            original_get_doc = self.frappe.get_doc
            self.frappe.get_doc = lambda doctype, name=None, **kwargs: FakeDoc('Sales Invoice', 'INV-B', cc_center='B') if doctype == 'Sales Invoice' else original_get_doc(doctype, name, **kwargs)
            with self.assertRaises(Denied):
                payments.detail('A', 'PAY-A')
            self.frappe.get_doc = original_get_doc
            self.db.doc.fields['references'] = []
            self.db.doc.permissions.remove('print')
            self.assertFalse(documents.detail('A', 'Payment Entry', 'PAY-A')['can_print'])
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A')
            self.db.doc.permissions.remove('read')
            with self.assertRaises(Denied):
                documents.detail('A', 'Payment Entry', 'PAY-A')
            self.db.doc.permissions.add('read')
            self.db.doc.permissions.add('print')
            self.db.doc.fields['cc_center'] = 'B'
            with self.assertRaises(Denied):
                documents.preview('A', 'Payment Entry', 'PAY-A')
            with self.assertRaises(Denied):
                documents.preview('A', 'Patient', 'PAY-A')

    def test_finance_document_invoice_read_print_and_escape(self):
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: date.fromisoformat(value)
        guards = types.ModuleType('centrochange_core.finance.guards')
        guards.require_finance = lambda center: None if center == 'A' and self.role_allowed else self.frappe.throw('finanza negata', Denied)
        item = FakeDoc('Sales Invoice Item', 'I', item_name='Visita <x>', description='Servizio &amp; assistenza', qty=2, uom='ora', rate=40, discount_percentage=10, discount_amount=4, amount=72)
        tax = FakeDoc('Sales Taxes and Charges', 'T', description='IVA', rate=22, tax_amount=15.84)
        self.db.doc = FakeDoc('Sales Invoice', 'INV-A', cc_center='A', docstatus=1, posting_date='2026-10-21', due_date='2026-11-01', customer='C-1', customer_name='Cliente <prova>', currency='EUR', items=[item], taxes=[tax], net_total=72, total_taxes_and_charges=15.84, discount_amount=0, grand_total=87.84, outstanding_amount=87.84)
        with patch.dict(sys.modules, {'frappe.utils': utils, 'centrochange_core.finance': types.ModuleType('centrochange_core.finance'), 'centrochange_core.finance.guards': guards}):
            spec = importlib.util.spec_from_file_location('centrochange_core.finance.documents', ROOT / 'finance/documents.py')
            documents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(documents)
            detail = documents.detail('A', 'Sales Invoice', 'INV-A')
            self.assertEqual(detail['items'][0]['qty'], 2)
            self.assertEqual(detail['taxes'][0]['tax_amount'], 15.84)
            html = documents.preview('A', 'Sales Invoice', 'INV-A')['html']
            self.assertIn('87,84 EUR', html)
            self.assertIn('Servizio &amp; assistenza', html)
            self.assertNotIn('Cliente <prova>', html)
            self.assertIn('10%', html)
            self.frappe.conf.update({'cc_synthetic_dev': 1, 'cc_uat_demo': 1})
            self.assertEqual(documents._safe_text('CC-HTTP-UAT0000001 Session'), 'Seduta')
            self.assertEqual(documents._safe_text('SYNTHETIC DEV tax input only'), '')
            self.frappe.conf.update({'cc_synthetic_dev': 0, 'cc_uat_demo': 0})
            self.assertEqual(documents._safe_text('Session'), 'Session')
            self.db.doc.fields['docstatus'] = 2
            self.assertEqual(documents.detail('A', 'Sales Invoice', 'INV-A')['items'][0]['amount'], 72)
            with self.assertRaises(Denied):
                documents.preview('A', 'Sales Invoice', 'INV-A')
            self.role_allowed = False
            with self.assertRaises(Denied):
                documents.detail('A', 'Sales Invoice', 'INV-A')

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

    def test_profile_optional_nulls_are_preserved(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        self.db.doc = FakeDoc('Patient', 'PAT-A', first_name='Persona', last_name=None, email=None)
        profiles.patient_save('A', 'PAT-A', 'Nuovo', None, None, 'v1', 'K-NULL', 'motivo')
        self.assertIsNone(self.db.doc.get('last_name'))
        self.assertIsNone(self.db.doc.get('email'))
        self.db.doc = FakeDoc('Healthcare Practitioner', 'PRO-A', user_id='pro@example.invalid', first_name='Persona', last_name=None)
        profiles.practitioner_save('A', 'PRO-A', 'Nuovo', None, 'v1', 'K-NULL-PRO', 'motivo')
        self.assertIsNone(self.db.doc.get('last_name'))

    def test_practitioner_search_is_server_scoped_and_bounded(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        observed = {}
        def listing(doctype, **kwargs):
            observed.update(kwargs)
            return [types.SimpleNamespace(name='PRO-A')]
        self.frappe.get_list = listing
        self.frappe.get_all = lambda doctype, **kwargs: ['pro@example.invalid']
        result = profiles.practitioners('A', 20, 0, 'Rossi')
        self.assertEqual(result['rows'][0].name, 'PRO-A')
        self.assertEqual(observed['filters']['user_id'], ['in', ['pro@example.invalid']])
        self.assertEqual(observed['page_length'], 21)
        self.assertEqual(observed['or_filters']['first_name'], ['like', '%Rossi%'])
        with self.assertRaises(Invalid):
            profiles.practitioners('A', 20, 0, 'x' * 101)

    def test_practitioner_detail_rejects_inactive_center(self):
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.profiles', ROOT / 'operations/profiles.py')
        profiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profiles)
        self.db.doc = FakeDoc('Healthcare Practitioner', 'PRO-A', user_id='pro@example.invalid', status='Active')
        self.operational_center = False
        with self.assertRaises(Denied):
            profiles.practitioner_detail('A', 'PRO-A')


if __name__ == '__main__':
    unittest.main()
