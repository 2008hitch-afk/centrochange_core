"""Offline unit and contract tests for AUDIT-06: Servizi, catalogo, prezzi e disponibilità.
Covers CC-CAP-007, CC-CAP-011, CC-CAP-012, CC-CAP-013, CC-EXT-010.
"""
from datetime import date, time
from decimal import Decimal
import importlib.util
import json
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
    def __init__(self, doctype='Item', name='ITEM-1', db=None, **fields):
        self.doctype = doctype
        self.name = name
        self.db = db
        self.modified = '2026-10-27 10:00:00'
        self.docstatus = fields.get('docstatus', 0)
        self.disabled = fields.get('disabled', 0)
        self.fields = dict(fields)
        self.writes = 0
        self.cancelled = False
        self.permissions = {'read', 'write', 'create', 'cancel'}
        self.flags = types.SimpleNamespace(ignore_permissions=False)

    def get(self, field, default=None):
        return getattr(self, field, self.fields.get(field, default))

    def __getattr__(self, field):
        if field in self.fields:
            return self.fields[field]
        raise AttributeError(field)

    def set(self, field, value):
        self.fields[field] = value

    def check_permission(self, permission):
        if permission not in self.permissions:
            raise Denied(permission)

    def save(self, ignore_permissions=False):
        self.writes += 1
        self.modified = '2026-10-27 10:05:00'

    def insert(self, ignore_permissions=False):
        self.writes += 1
        if not self.name or self.name == 'DRAFT':
            self.name = f"{self.doctype[:3]}-NEW-1"
        if self.db:
            self.db.store.setdefault(self.doctype, {})[self.name] = self
        return self

    def submit(self):
        self.docstatus = 1
        return self

    def cancel(self):
        self.docstatus = 2
        self.cancelled = True
        return self

    def append(self, field, value):
        if field not in self.fields:
            self.fields[field] = []
        self.fields[field].append(types.SimpleNamespace(**value) if isinstance(value, dict) else value)

    def get_doc_before_save(self):
        return getattr(self, '_before_doc', None)


class FakeDB:
    def __init__(self):
        self.events = []
        self.store = {}

    def exists(self, doctype, key):
        if isinstance(key, dict):
            return any(
                all(doc.get(k) == v for k, v in key.items())
                for doc in self.store.get(doctype, {}).values()
            )
        return key in self.store.get(doctype, {})

    def get_value(self, doctype, filters, fieldname=None, for_update=False):
        docs = list(self.store.get(doctype, {}).values())
        if isinstance(filters, dict):
            for doc in docs:
                if all(doc.get(k) == v for k, v in filters.items()):
                    if fieldname:
                        return doc.get(fieldname)
                    return doc.name
        elif isinstance(filters, str):
            doc = self.store.get(doctype, {}).get(filters)
            if doc:
                return doc.get(fieldname) if fieldname else doc.name
        return None

    def get_single_value(self, doctype, fieldname):
        return 'Centro Change S.r.l.'

    def get_values(self, doctype, filters, fieldname=None, as_dict=False, for_update=False):
        results = []
        for entry in self.events:
            event, dt, name, before, after, reason = entry
            if event == filters.get('event_type'):
                like_pattern = filters.get('before_state', [None, ''])[1].strip('%')
                if like_pattern in json.dumps(before):
                    results.append(types.SimpleNamespace(
                        before_state=json.dumps(before, sort_keys=True),
                        after_state=json.dumps(after, sort_keys=True)
                    ))
        return results


class Audit06ServicesCatalogueAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        self.role_allowed = True
        self.is_manager = True
        self.user_roles = ['CC Manager']
        self.session_user = 'manager@example.invalid'
        self.operational_center = True
        self.current_center = 'CENTRO-A'
        self.locked = 0

        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = Denied
        self.frappe.session = types.SimpleNamespace(user=self.session_user)
        self.frappe.local = types.SimpleNamespace(request=None)
        self.frappe.db = self.db
        self.frappe.flags = {}
        self.frappe.conf = types.SimpleNamespace(get=lambda k: 1)
        self.frappe.throw = lambda message, exc=Invalid: (_ for _ in ()).throw(exc(message))
        self.frappe.generate_hash = lambda length=16: 'HASH123456789012'[:length]
        self.frappe.parse_json = json.loads
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn

        def fake_get_doc(doctype, name=None, for_update=False):
            if isinstance(doctype, dict):
                dt = doctype.get('doctype', 'Unknown')
                dname = doctype.get('name', 'DRAFT')
                doc = FakeDoc(dt, dname, db=self.db, **{k: v for k, v in doctype.items() if k not in ('doctype', 'name')})
                self.db.store.setdefault(dt, {})[dname] = doc
                return doc
            doc = self.db.store.get(doctype, {}).get(name)
            if not doc:
                doc = FakeDoc(doctype, name, db=self.db)
                self.db.store.setdefault(doctype, {})[name] = doc
            return doc

        self.frappe.get_doc = fake_get_doc

        def fake_get_all(doctype, filters=None, pluck=None, fields=None, **kwargs):
            filters = filters or {}
            items = list(self.db.store.get(doctype, {}).values())
            res = []
            for item in items:
                match = True
                for k, v in filters.items():
                    val = item.get(k)
                    if isinstance(v, list) and len(v) == 2 and v[0] == 'in':
                        if val not in v[1]:
                            match = False; break
                    elif isinstance(v, list) and len(v) == 2 and v[0] == '!=':
                        if val == v[1]:
                            match = False; break
                    elif isinstance(v, list) and len(v) == 2 and v[0] == 'is':
                        if v[1] == 'not set' and val is not None:
                            match = False; break
                    elif val != v:
                        match = False; break
                if match:
                    if pluck:
                        res.append(item.get(pluck))
                    elif fields:
                        res.append(types.SimpleNamespace(**{f: item.get(f) for f in fields}))
                    else:
                        res.append(item)
            start = kwargs.get('start', 0)
            page_length = kwargs.get('page_length')
            if page_length is not None:
                return res[start:start + page_length]
            return res

        self.frappe.get_all = fake_get_all
        self.frappe.get_list = fake_get_all

        utils = types.ModuleType('frappe.utils')
        utils.get_time = lambda v: time.fromisoformat(str(v)) if isinstance(v, str) else v
        utils.getdate = lambda v: date.fromisoformat(str(v)) if isinstance(v, str) else v
        utils.flt = lambda v: float(v) if v is not None else 0.0
        self.frappe.utils = utils

        self.audit = types.ModuleType('centrochange_core.security.audit')
        self.audit.atomic = lambda fn: fn
        self.audit.serialize = lambda v: json.dumps(v, sort_keys=True, default=str, separators=(',', ':'))
        self.audit.append = lambda event, doctype, name, before, after, reason: self.db.events.append((event, doctype, name, before, after, reason))

        class InternalWrite:
            def __init__(ctx, flag):
                ctx.flag = flag
            def __enter__(ctx):
                self.frappe.flags[ctx.flag] = True
            def __exit__(ctx, *exc):
                self.frappe.flags.pop(ctx.flag, None)

        self.audit.internal_write = InternalWrite

        self.guards = types.ModuleType('centrochange_core.security.guards')
        self.guards.require_manager = lambda: None if self.is_manager else self.frappe.throw('ruolo negato', Denied)
        self.guards.require_center = lambda center: None if center == self.current_center else self.frappe.throw('centro negato', Denied)
        self.guards.require_operational_center = lambda center: None if center == self.current_center and self.operational_center else self.frappe.throw('centro inattivo', Denied)
        self.guards.require_operations = lambda center: None if center == self.current_center else self.frappe.throw('operazioni negate', Denied)
        self.guards.require_patient = lambda patient: None
        self.guards.is_manager = lambda user=None: self.is_manager
        self.guards.enabled = lambda user=None: True
        self.guards.roles = lambda user=None: self.user_roles
        self.guards.centers = lambda user=None: [self.current_center]
        self.guards.practitioner_for = lambda user=None: 'PRO-1'
        self.guards.patient_contexts = lambda: {('PAT-1', self.current_center)}
        self.guards.current_rows = lambda doctype, filters=None, fields=None, pluck=None: fake_get_all(doctype, filters, pluck, fields)

        self.lifecycle = types.ModuleType('centrochange_core.security.lifecycle')
        self.lifecycle.lock = lambda: setattr(self, 'locked', self.locked + 1)

        collections = types.ModuleType('centrochange_core.finance.collections')
        collections._agreement = lambda patient, center: None
        collections.require_booking = lambda doc: None

        pkgs = types.ModuleType('centrochange_core.operations.packages')
        pkgs.reserve = lambda doc, reason: None

        op_life = types.ModuleType('centrochange_core.operations.lifecycle')
        op_life.start_utc = lambda doc: doc
        op_life.require_mutable = lambda doc: None

        modules = {
            'frappe': self.frappe,
            'frappe.utils': utils,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.audit': self.audit,
            'centrochange_core.security.guards': self.guards,
            'centrochange_core.security.lifecycle': self.lifecycle,
            'centrochange_core.scheduling': types.ModuleType('centrochange_core.scheduling'),
            'centrochange_core.finance': types.ModuleType('centrochange_core.finance'),
            'centrochange_core.finance.collections': collections,
            'centrochange_core.operations': types.ModuleType('centrochange_core.operations'),
            'centrochange_core.operations.packages': pkgs,
            'centrochange_core.operations.lifecycle': op_life,
        }

        self.patcher = patch.dict(sys.modules, modules)
        self.patcher.start()

        # Load scoped_api
        spec = importlib.util.spec_from_file_location('centrochange_core.scoped_api', ROOT / 'scoped_api.py')
        self.scoped_api = importlib.util.module_from_spec(spec)
        sys.modules['centrochange_core.scoped_api'] = self.scoped_api
        spec.loader.exec_module(self.scoped_api)

        # Load catalog
        spec = importlib.util.spec_from_file_location('centrochange_core.catalog', ROOT / 'catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        sys.modules['centrochange_core.catalog'] = self.catalog
        spec.loader.exec_module(self.catalog)

        # Load availability
        spec = importlib.util.spec_from_file_location('centrochange_core.scheduling.availability', ROOT / 'scheduling/availability.py')
        self.availability = importlib.util.module_from_spec(spec)
        sys.modules['centrochange_core.scheduling.availability'] = self.availability
        spec.loader.exec_module(self.availability)

        # Load booking
        spec = importlib.util.spec_from_file_location('centrochange_core.scheduling.booking', ROOT / 'scheduling/booking.py')
        self.booking = importlib.util.module_from_spec(spec)
        sys.modules['centrochange_core.scheduling.booking'] = self.booking
        spec.loader.exec_module(self.booking)

        # Seed initial records in fake db
        self._seed()

    def _seed(self):
        # Branch
        self.db.store['Branch'] = {
            'CENTRO-A': FakeDoc('Branch', 'CENTRO-A', cc_price_list='PL-CENTRO-A'),
            'CENTRO-B': FakeDoc('Branch', 'CENTRO-B', cc_price_list='PL-CENTRO-B'),
        }
        # Price List
        self.db.store['Price List'] = {
            'PL-CENTRO-A': FakeDoc('Price List', 'PL-CENTRO-A', enabled=1, selling=1, currency='EUR'),
            'PL-CENTRO-B': FakeDoc('Price List', 'PL-CENTRO-B', enabled=1, selling=1, currency='EUR'),
        }
        # Item
        self.db.store['Item'] = {
            'ITEM-COLLOQUIO': FakeDoc('Item', 'ITEM-COLLOQUIO', item_name='Colloquio individuale',
                                      stock_uom='Unit', is_stock_item=0, is_sales_item=1, disabled=0),
            'ITEM-VALUTAZIONE': FakeDoc('Item', 'ITEM-VALUTAZIONE', item_name='Valutazione psicodiagnostica',
                                        stock_uom='Unit', is_stock_item=0, is_sales_item=1, disabled=0),
            'ITEM-INATTIVO': FakeDoc('Item', 'ITEM-INATTIVO', item_name='Servizio dismesso',
                                     stock_uom='Unit', is_stock_item=0, is_sales_item=1, disabled=1),
        }
        # Appointment Type
        self.db.store['Appointment Type'] = {
            'AT-COLLOQUIO': FakeDoc('Appointment Type', 'AT-COLLOQUIO', appointment_type='Colloquio individuale',
                                    default_duration=50, cc_service_item='ITEM-COLLOQUIO', allow_booking_for='Practitioner', cc_first_meeting=0),
            'AT-VALUTAZIONE': FakeDoc('Appointment Type', 'AT-VALUTAZIONE', appointment_type='Valutazione psicodiagnostica',
                                      default_duration=60, cc_service_item='ITEM-VALUTAZIONE', allow_booking_for='Practitioner', cc_first_meeting=0),
            'AT-INATTIVO': FakeDoc('Appointment Type', 'AT-INATTIVO', appointment_type='Servizio dismesso',
                                   default_duration=45, cc_service_item='ITEM-INATTIVO', allow_booking_for='Practitioner', cc_first_meeting=0),
        }
        # CC Center Service
        self.db.store['CC Center Service'] = {
            'SRV-A-1': FakeDoc('CC Center Service', 'SRV-A-1', center='CENTRO-A', appointment_type='AT-COLLOQUIO', enabled=1),
            'SRV-A-2': FakeDoc('CC Center Service', 'SRV-A-2', center='CENTRO-A', appointment_type='AT-VALUTAZIONE', enabled=1),
            'SRV-A-3': FakeDoc('CC Center Service', 'SRV-A-3', center='CENTRO-A', appointment_type='AT-INATTIVO', enabled=0),
        }
        # Item Price
        self.db.store['Item Price'] = {
            'PR-A-1': FakeDoc('Item Price', 'PR-A-1', item_code='ITEM-COLLOQUIO', price_list='PL-CENTRO-A',
                              price_list_rate=Decimal('70.00'), currency='EUR', valid_from='2026-01-01', valid_upto=None,
                              customer=None, supplier=None, batch_no=None, uom='Unit'),
            'PR-A-2': FakeDoc('Item Price', 'PR-A-2', item_code='ITEM-VALUTAZIONE', price_list='PL-CENTRO-A',
                              price_list_rate=Decimal('120.00'), currency='EUR', valid_from='2026-01-01', valid_upto=None,
                              customer=None, supplier=None, batch_no=None, uom='Unit'),
        }
        # Healthcare Practitioner
        self.db.store['Healthcare Practitioner'] = {
            'PRO-1': FakeDoc('Healthcare Practitioner', 'PRO-1', status='Active', user_id='pro1@example.invalid',
                             practitioner_name='Dott.ssa Rossi', practitioner_schedules=[]),
            'PRO-2': FakeDoc('Healthcare Practitioner', 'PRO-2', status='Active', user_id='pro2@example.invalid',
                             practitioner_name='Dott. Bianchi', practitioner_schedules=[]),
        }
        # Practitioner Schedule
        self.db.store['Practitioner Schedule'] = {
            'SCHED-PRO-1': FakeDoc('Practitioner Schedule', 'SCHED-PRO-1', cc_practitioner='PRO-1', cc_center='CENTRO-A',
                                   schedule_name='CC-SCHED-1', disabled=0, time_slots=[
                                       types.SimpleNamespace(day='Monday', from_time='09:00:00', to_time='13:00:00'),
                                       types.SimpleNamespace(day='Monday', from_time='14:00:00', to_time='18:00:00'),
                                   ]),
        }
        # CC Patient Assignment
        self.db.store['CC Patient Assignment'] = {
            'ASG-1': FakeDoc('CC Patient Assignment', 'ASG-1', patient='PAT-1', practitioner='PRO-1', center='CENTRO-A', active=1),
        }
        # CC Center Membership
        self.db.store['CC Center Membership'] = {
            'MB-1': FakeDoc('CC Center Membership', 'MB-1', user='pro1@example.invalid', center='CENTRO-A', active=1),
            'MB-2': FakeDoc('CC Center Membership', 'MB-2', user='pro2@example.invalid', center='CENTRO-A', active=1),
        }

    def tearDown(self):
        self.patcher.stop()
        for mod in ('centrochange_core.scoped_api', 'centrochange_core.catalog',
                    'centrochange_core.scheduling.availability', 'centrochange_core.scheduling.booking'):
            sys.modules.pop(mod, None)

    # --------------------------------------------------------------------------
    # CC-CAP-007: Orari ricorrenti e assenze
    # --------------------------------------------------------------------------

    def test_cap007_set_schedule_multi_slot_intra_day_and_audit(self):
        """Demonstrates multi-slot intra-day availability update and SCHEDULE_CHANGED audit event."""
        slots = [
            {'day': 'Monday', 'from_time': '09:00', 'to_time': '13:00'},
            {'day': 'Monday', 'from_time': '14:30', 'to_time': '18:30'},
            {'day': 'Wednesday', 'from_time': '10:00', 'to_time': '16:00'},
        ]
        res = self.availability.set_schedule(
            practitioner='PRO-1',
            center='CENTRO-A',
            time_slots=slots,
            reason='Aggiornamento orario autunno 2026',
            expected_modified='2026-10-27 10:00:00'
        )
        self.assertEqual(res['name'], 'SCHED-PRO-1')
        doc = self.db.store['Practitioner Schedule']['SCHED-PRO-1']
        self.assertEqual(len(doc.time_slots), 3)
        self.assertEqual(doc.time_slots[0]['day'], 'Monday')
        self.assertEqual(doc.time_slots[1]['from_time'], '14:30:00')

        # Check audit event
        events = [e for e in self.db.events if e[0] == 'SCHEDULE_CHANGED']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], 'Practitioner Schedule')
        self.assertEqual(events[0][5], 'Aggiornamento orario autunno 2026')

    def test_cap007_set_schedule_rejects_overlapping_intra_day_slots(self):
        """Demonstrates rejection when time slots on same day overlap."""
        slots = [
            {'day': 'Tuesday', 'from_time': '09:00', 'to_time': '13:00'},
            {'day': 'Tuesday', 'from_time': '12:30', 'to_time': '15:00'},
        ]
        with self.assertRaisesRegex(Invalid, 'Le fasce della disponibilità settimanale si sovrappongono'):
            self.availability.set_schedule('PRO-1', 'CENTRO-A', slots, 'Overlap test')

    def test_cap007_set_schedule_rejects_inverted_time(self):
        """Demonstrates rejection when start time is equal or after end time."""
        slots = [{'day': 'Friday', 'from_time': '17:00', 'to_time': '09:00'}]
        with self.assertRaisesRegex(Invalid, 'L’ora iniziale deve precedere quella finale'):
            self.availability.set_schedule('PRO-1', 'CENTRO-A', slots, 'Inverted test')

    def test_cap007_set_schedule_rejects_stale_concurrency(self):
        """Demonstrates optimistic concurrency control via expected_modified."""
        slots = [{'day': 'Monday', 'from_time': '09:00', 'to_time': '12:00'}]
        with self.assertRaisesRegex(Invalid, 'L’orario è cambiato'):
            self.availability.set_schedule('PRO-1', 'CENTRO-A', slots, 'Stale test', expected_modified='2020-01-01 00:00:00')

    def test_cap007_professional_cannot_mutate_another_practitioner(self):
        """Demonstrates role boundary: CC Professional cannot update or query another practitioner's schedule."""
        self.is_manager = False
        self.user_roles = ['CC Professional']
        self.frappe.session.user = 'pro1@example.invalid'
        slots = [{'day': 'Monday', 'from_time': '09:00', 'to_time': '12:00'}]

        # PRO-1 can update PRO-1
        self.availability.set_schedule('PRO-1', 'CENTRO-A', slots, 'Self update')

        # PRO-1 CANNOT update PRO-2
        with self.assertRaises(Denied):
            self.availability.set_schedule('PRO-2', 'CENTRO-A', slots, 'Cross pro update')

    def test_cap007_create_and_cancel_absence_lifecycle_with_audit_and_idempotency(self):
        """Demonstrates absence creation, idempotency replay, cancellation, and audit logging."""
        # Create absence
        res1 = self.availability.create_absence(
            practitioner='PRO-1',
            center='CENTRO-A',
            start_date='2026-11-05',
            end_date='2026-11-05',
            start_time='09:00:00',
            end_time='13:00:00',
            reason='Ferie programmate'
        )
        abs_name = res1['name']
        self.assertTrue(abs_name)

        # Verify idempotency on identical create_absence
        res2 = self.availability.create_absence(
            practitioner='PRO-1',
            center='CENTRO-A',
            start_date='2026-11-05',
            end_date='2026-11-05',
            start_time='09:00:00',
            end_time='13:00:00',
            reason='Ferie duplicate'
        )
        self.assertEqual(res2['name'], abs_name)

        # Cancel absence
        cancel_res = self.availability.cancel_absence(abs_name, 'Rientro anticipato')
        self.assertEqual(cancel_res['name'], abs_name)
        self.assertFalse(cancel_res['replay'])

        # Cancel again (idempotent replay)
        cancel_res_2 = self.availability.cancel_absence(abs_name, 'Rientro anticipato re-run')
        self.assertTrue(cancel_res_2['replay'])

        # Verify audit entries
        abs_created = [e for e in self.db.events if e[0] == 'ABSENCE_CREATED']
        abs_cancelled = [e for e in self.db.events if e[0] == 'ABSENCE_CANCELLED']
        self.assertEqual(len(abs_created), 1)
        self.assertEqual(len(abs_cancelled), 1)

    # --------------------------------------------------------------------------
    # CC-CAP-011: Catalogo servizi e tipi seduta
    # --------------------------------------------------------------------------

    def test_cap011_catalog_records_scoped_to_center(self):
        """Demonstrates reading CC Center Service and Appointment Type scoped to the center."""
        srv_records = self.catalog.records('CENTRO-A', 'CC Center Service')
        self.assertEqual(len(srv_records['rows']), 3)

        type_records = self.catalog.records('CENTRO-A', 'Appointment Type')
        self.assertEqual(len(type_records['rows']), 3)
        names = [r.name for r in type_records['rows']]
        self.assertIn('AT-COLLOQUIO', names)
        self.assertIn('AT-VALUTAZIONE', names)

    def test_cap011_service_save_toggle_enabled(self):
        """Demonstrates updating service enabled flag with version check and replay protection."""
        res = self.catalog.service_save(
            center='CENTRO-A',
            name='SRV-A-2',
            enabled=0,
            expected_version='2026-10-27 10:00:00',
            request_key='KEY-SRV-TOGGLE',
            reason='Sospensione temporanea'
        )
        self.assertFalse(res['replay'])
        doc = self.db.store['CC Center Service']['SRV-A-2']
        self.assertEqual(doc.enabled, 0)

    def test_cap011_appointment_type_save_validates_duration(self):
        """Demonstrates modifying Appointment Type duration with validation."""
        res = self.catalog.appointment_type_save(
            center='CENTRO-A',
            name='AT-COLLOQUIO',
            default_duration=45,
            expected_version='2026-10-27 10:00:00',
            request_key='KEY-AT-SAVE',
            reason='Riduzione a 45 min'
        )
        self.assertFalse(res['replay'])
        doc = self.db.store['Appointment Type']['AT-COLLOQUIO']
        self.assertEqual(doc.default_duration, 45)

        # Invalid duration rejected
        with self.assertRaisesRegex(Invalid, 'Durata non valida'):
            self.catalog.appointment_type_save(
                center='CENTRO-A',
                name='AT-COLLOQUIO',
                default_duration=-10,
                expected_version='2026-10-27 10:05:00',
                request_key='KEY-AT-INVALID',
                reason='Errato'
            )

    def test_cap011_appointment_type_create_requires_valid_active_item(self):
        """Demonstrates creating new Appointment Type linked to active Item, rejecting disabled item."""
        with self.assertRaisesRegex(Invalid, 'Articolo servizio non attivo'):
            self.catalog.appointment_type_create(
                center='CENTRO-A',
                appointment_type='Seduta Dismessa',
                service_item='ITEM-INATTIVO',
                default_duration=60,
                request_key='KEY-AT-NEW-DIS',
                reason='Test disattivo'
            )

    # --------------------------------------------------------------------------
    # CC-CAP-012: Tariffe per listino centro
    # --------------------------------------------------------------------------

    def test_cap012_item_price_records_and_create(self):
        """Demonstrates reading Item Price scoped to center's price list and creating a future rate."""
        records = self.catalog.records('CENTRO-A', 'Item Price')
        self.assertEqual(len(records['rows']), 2)

        # Create new tariff with future valid_from
        res = self.catalog.price_create(
            center='CENTRO-A',
            item_code='ITEM-COLLOQUIO',
            valid_from='2027-01-01',
            price_list_rate='80.00',
            request_key='KEY-PR-NEW',
            reason='Aggiornamento listino 2027'
        )
        self.assertTrue(res['name'])

        # Duplicate valid_from for same item and price list is rejected
        with self.assertRaisesRegex(Invalid, 'Tariffa già presente per questa decorrenza'):
            self.catalog.price_create(
                center='CENTRO-A',
                item_code='ITEM-COLLOQUIO',
                valid_from='2027-01-01',
                price_list_rate='85.00',
                request_key='KEY-PR-DUP',
                reason='Duplicato'
            )

    def test_cap012_price_save_validates_rate_and_bounds(self):
        """Demonstrates updating price_list_rate with numeric and decimal precision validation."""
        res = self.catalog.price_save(
            center='CENTRO-A',
            name='PR-A-1',
            price_list_rate='75.50',
            expected_version='2026-10-27 10:00:00',
            request_key='KEY-PR-SAVE',
            reason='Adeguamento ISTAT'
        )
        self.assertFalse(res['replay'])
        doc = self.db.store['Item Price']['PR-A-1']
        self.assertEqual(doc.price_list_rate, Decimal('75.50'))

        # Negative rate rejected
        with self.assertRaisesRegex(Invalid, 'Tariffa non valida'):
            self.catalog.price_save(
                center='CENTRO-A',
                name='PR-A-1',
                price_list_rate='-50.00',
                expected_version='2026-10-27 10:05:00',
                request_key='KEY-PR-NEG',
                reason='Negativo'
            )

    # --------------------------------------------------------------------------
    # CC-CAP-013: Snapshot servizio, durata e prezzo alla prenotazione
    # --------------------------------------------------------------------------

    def test_cap013_booking_snapshot_captures_current_tariff_and_duration(self):
        """Demonstrates that booking.snapshot extracts current active tariff and duration for appointment type."""
        snap = self.booking.snapshot('AT-COLLOQUIO', 'CENTRO-A')
        self.assertEqual(snap['cc_service_item'], 'ITEM-COLLOQUIO')
        self.assertEqual(snap['cc_service_label'], 'Colloquio individuale')
        self.assertEqual(snap['cc_price_snapshot'], Decimal('70.00'))
        self.assertEqual(snap['cc_currency_snapshot'], 'EUR')
        self.assertEqual(snap['duration'], 50)
        self.assertEqual(snap['cc_booking_date'], date.today())

    def test_cap013_historical_appointment_preserves_snapshot_on_catalog_update(self):
        """Demonstrates CC-CAP-013: booked appointment snapshot is immutable; catalog updates do not mutate history."""
        # 1. Book an appointment with current catalog (tariff 70.00, duration 50)
        appt = FakeDoc(
            'Patient Appointment',
            'APT-2026-001',
            patient='PAT-1',
            practitioner='PRO-1',
            cc_center='CENTRO-A',
            appointment_type='AT-COLLOQUIO',
            appointment_date='2026-11-10',
            appointment_time='10:00:00',
            duration=50,
            cc_price_snapshot=Decimal('70.00'),
            cc_currency_snapshot='EUR',
            cc_service_item='ITEM-COLLOQUIO',
            cc_service_label='Colloquio individuale',
            cc_booking_key='KEY-APT-HIST',
            cc_booking_date='2026-10-27',
            status='Open'
        )
        self.db.store['Patient Appointment'] = {'APT-2026-001': appt}

        # 2. Manager modifies catalog: changes price to 90.00 and duration to 45
        self.catalog.price_save(
            center='CENTRO-A',
            name='PR-A-1',
            price_list_rate='90.00',
            expected_version='2026-10-27 10:00:00',
            request_key='KEY-PR-UPDATE-2',
            reason='Aumento tariffa'
        )
        self.catalog.appointment_type_save(
            center='CENTRO-A',
            name='AT-COLLOQUIO',
            default_duration=45,
            expected_version='2026-10-27 10:00:00',
            request_key='KEY-AT-UPDATE-2',
            reason='Riduzione durata'
        )

        # 3. Verify existing booked appointment retains its original snapshot
        persisted = self.db.store['Patient Appointment']['APT-2026-001']
        self.assertEqual(persisted.cc_price_snapshot, Decimal('70.00'))
        self.assertEqual(persisted.duration, 50)

        # 4. Verify AppointmentMixin rejects any attempt to mutate snapshot on existing appointment
        class TestAppointment(self.booking.AppointmentMixin):
            def __init__(self, doc):
                self.__dict__.update(doc.__dict__)
                self.fields = dict(doc.fields)
                self._before_doc = FakeDoc(**doc.fields)

            def get(self, k, default=None):
                return self.fields.get(k, default)

            def get_doc_before_save(self):
                return self._before_doc

            def validate(self):
                super().validate()

        self.frappe.flags['cc_appointment_write'] = True
        test_appt = TestAppointment(persisted)
        # Attempt to change price snapshot
        test_appt.fields['cc_price_snapshot'] = Decimal('90.00')
        with self.assertRaisesRegex(Invalid, 'I dati storici della seduta non possono essere modificati: cc_price_snapshot'):
            test_appt.validate()

    # --------------------------------------------------------------------------
    # CC-EXT-010: Editor limitato per Item/Type/Service/Price/Template
    # --------------------------------------------------------------------------

    def test_ext010_deny_extra_fields(self):
        """Demonstrates that unexpected fields are rejected via deny_extra."""
        with self.assertRaises(Denied):
            self.catalog.price_save(
                center='CENTRO-A',
                name='PR-A-1',
                price_list_rate='70.00',
                expected_version='2026-10-27 10:00:00',
                request_key='KEY-EXTRA',
                reason='Prova',
                malicious_field='injected'
            )

    def test_ext010_non_manager_role_denied(self):
        """Demonstrates that non-manager users (e.g. CC Professional or Secretariat) cannot mutate catalog."""
        self.is_manager = False
        self.user_roles = ['CC Secretariat']

        with self.assertRaises(Denied):
            self.catalog.service_save(
                center='CENTRO-A',
                name='SRV-A-1',
                enabled=0,
                expected_version='2026-10-27 10:00:00',
                request_key='KEY-SEC-DENIED',
                reason='Non autorizzato'
            )

    def test_ext010_cross_center_modification_denied(self):
        """Demonstrates that a center manager cannot mutate catalog items belonging to another center."""
        # Attempt to update SRV-A-1 specifying CENTRO-B
        with self.assertRaises(Denied):
            self.catalog.service_save(
                center='CENTRO-B',
                name='SRV-A-1',
                enabled=0,
                expected_version='2026-10-27 10:00:00',
                request_key='KEY-CROSS-DENIED',
                reason='Cross center test'
            )

    def test_ext010_no_standalone_item_create_endpoint_exists(self):
        """Verifies DECISION-063: no item_create endpoint exists in catalog module."""
        self.assertFalse(hasattr(self.catalog, 'item_create'))


if __name__ == '__main__':
    unittest.main()
