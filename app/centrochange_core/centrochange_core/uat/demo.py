"""Private, guarded, persistent UAT fixtures. No method in this module is whitelisted.

Historical fixtures run normal services under a process-local synthetic clock;
no lifecycle/authorization validation is skipped and no upstream is patched.
Native serial IDs, passwords and timestamps are intentionally not deterministic.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import fcntl
import json
import os
import frappe
from centrochange_core.security import dev_acceptance as fixtures

TAG = 'CC-HTTP-UAT0000001'
VERSION = 'goal02-demo-v1'
ANCHOR = '2026-10-05'


def guard():
    if (frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1
            or frappe.conf.get('cc_uat_demo') != 1):
        frappe.throw('Explicit synthetic DEV UAT Administrator required', frappe.PermissionError)


def directory():
    path = Path(frappe.get_site_path('private', 'uat'))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


@contextmanager
def exclusive():
    guard()
    with (directory() / 'demo.lock').open('a') as stream:
        os.chmod(stream.name, 0o600)
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def read():
    data = json.loads((directory() / 'demo.json').read_text())
    if data['version'] != VERSION or data['fixture']['tag'] != TAG:
        frappe.throw('UAT manifest version differs; do not reset automatically')
    return data


def write(data):
    path = directory() / 'demo.tmp'
    with path.open('w') as stream:
        os.chmod(path, 0o600)
        json.dump(data, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    path.replace(directory() / 'demo.json')


class HistoricalClock(datetime):
    @classmethod
    def now(cls, tz=None):
        from zoneinfo import ZoneInfo
        instant = datetime(2026, 9, 21, 8, tzinfo=ZoneInfo('Europe/Rome'))
        return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)


@fixtures.synthetic_test
def seed():
    with exclusive():
        if (directory() / 'demo.json').exists():
            data = read()
            # Never overwrite client actions on a retry. Validation is explicit.
            if not all(frappe.db.exists('User', u['name']) for u in data['fixture']['users'].values()):
                frappe.throw('Incomplete UAT seed; explicit owned-fixture reset required')
            return {'status': 'PASS', 'version': VERSION, 'replay': True}
        if frappe.db.exists('User', TAG.lower() + '-a@example.invalid'):
            frappe.throw('Owned UAT rows without manifest; explicit reset required')
        previous_clock = frappe.flags.get('cc_test_clock')
        try:
            data = _seed()
            # Persist recovery ownership before commit; interrupted seeds require reset.
            write(data)
            frappe.db.commit()
            return {'status': 'PASS', 'version': VERSION, 'replay': False}
        except Exception:
            frappe.db.rollback()
            (directory() / 'demo.json').unlink(missing_ok=True)
            raise
        finally:
            frappe.flags.cc_test_clock = previous_clock
            frappe.set_user('Administrator')


def _seed():
    from centrochange_core.security.lifecycle import set_assignment
    from centrochange_core.scheduling.availability import set_schedule
    from centrochange_core.scheduling.booking import book
    from centrochange_core.operations import lifecycle, packages
    from centrochange_core.finance import bridge, collections, receivables, banking, incoming, professional_economics as economics, sdi, ts, admin_queue
    from centrochange_core.finance.dev_profile import setup
    from centrochange_core.finance.incoming_acceptance import xml
    email_count = frappe.db.count('Email Queue')
    fixture = fixtures.create_http(scheduling=True, operations=True, finance_users=True, fixture_tag=TAG, commit=False)
    center, other = fixture['centers']
    prac, prac2 = fixture['practitioners']
    profile = fixture['catalog']['Appointment Type'][0]
    item = fixture['catalog']['Item'][0]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for professional in (prac, prac2):
        schedule = set_schedule(professional, center, [{'day': day, 'from_time': '09:00:00', 'to_time': '17:00:00'} for day in days], TAG)['name']
        if schedule not in fixture['catalog']['Practitioner Schedule']:
            fixture['catalog']['Practitioner Schedule'].append(schedule)
    bridge.map_center(center, TAG)
    supplier = bridge.map_practitioner(prac, center, TAG)['supplier']
    bridge.map_practitioner(prac2, center, TAG)
    patients = {'Alfa': fixture['patients'][0], 'Altro centro': fixture['patients'][1]}
    for label in ('Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Theta'):
        name = frappe.get_doc({'doctype': 'Patient', 'first_name': TAG + ' ' + label,
            'sex': 'Female', 'uid': TAG + '-' + label.upper(), 'invite_user': 0}).insert(ignore_permissions=True).name
        fixture['patients'].append(name)
        patients[label] = name
        set_assignment(name, center, prac2 if label == 'Zeta' else prac, 1, TAG)
    for label, patient in patients.items():
        if label == 'Altro centro':
            continue
        customer = bridge.map_patient(patient, center, TAG)['customer']
        setup(customer)
        if label == 'Theta':
            from zoneinfo import ZoneInfo
            frappe.flags.cc_test_clock = datetime(2026, 9, 21, 8, tzinfo=ZoneInfo('Europe/Rome'))
        collections.agree(patient, center, 'Specific Date', TAG, due_date='2026-09-30' if label == 'Theta' else '2026-10-31')
        frappe.flags.cc_test_clock = None
    rule = economics.configure_rule(center, prac, item, '2020-01-01', 'Fixed Amount', 40, 'EUR', TAG + '-rule', TAG)['name']
    economics.configure_threshold(center, prac, 1, TAG + '-threshold', TAG)
    appointments, sources = {}, {}
    # Historical synthetic import: validated booking at a past reference instant,
    # then normal closure/cancellation at the appropriate test instant.
    with patch('centrochange_core.scheduling.booking.datetime', HistoricalClock):
        entries = [('Alfa non incassata 1', 'Alfa', '2026-09-28', '09:00:00', 'closed'),
            ('Alfa non incassata 2', 'Alfa', '2026-09-29', '09:00:00', 'closed'),
            ('Beta parzialmente incassata', 'Beta', '2026-09-28', '10:00:00', 'closed'),
            ('Gamma incassata', 'Gamma', '2026-09-28', '11:00:00', 'closed'),
            ('Delta annullata puntuale', 'Delta', '2026-09-30', '12:00:00', 'timely'),
            ('Delta annullata tardiva', 'Delta', '2026-09-30', '13:00:00', 'late'),
            ('Epsilon pacchetto', 'Epsilon', '2026-09-28', '14:00:00', 'package'),
            ('Zeta configurazione mancante', 'Zeta', '2026-09-28', '15:00:00', 'closed'),
            ('Theta insoluto scaduto', 'Theta', '2026-09-29', '10:00:00', 'closed'),
            ('Alfa da prenotare', 'Alfa', '2026-10-12', '09:00:00', 'pending')]
        for label, patient_label, date, time, state in entries:
            frappe.flags.cc_test_clock = None
            professional = prac2 if patient_label == 'Zeta' else prac
            package = None
            if state == 'package':
                package = packages.issue(fixture['catalog']['CC Package Template'][0], patients[patient_label], [center], TAG + '-epsilon-package', TAG)['name']
            appointment = book(patients[patient_label], professional, center, profile, date, time, TAG + '-' + label, TAG, patient_package=package)['name']
            appointments[label] = appointment
            start = lifecycle.start_utc(frappe.get_doc('Patient Appointment', appointment))
            if state in ('closed', 'package'):
                frappe.flags.cc_test_clock = start + timedelta(hours=1)
                lifecycle.close(appointment, 0, TAG)
            elif state in ('timely', 'late'):
                frappe.flags.cc_test_clock = start - timedelta(hours=48 if state == 'timely' else 47)
                lifecycle.cancel(appointment, TAG)
            sources[label] = bridge.capture(appointment, TAG)['name']
    frappe.flags.cc_test_clock = None
    invoices = {}
    for label in ('Beta parzialmente incassata', 'Gamma incassata', 'Theta insoluto scaduto'):
        invoice = receivables.draft([sources[label]], '2026-09-29' if label.startswith('Theta') else ANCHOR,
            '2026-09-30' if label.startswith('Theta') else '2026-10-31', TAG + '-' + label + '-invoice', TAG)['name']
        receivables.submit(invoice, TAG)
        if not label.startswith('Theta'):
            receivables.pay(invoice, 40 if label.startswith('Beta') else 100, ANCHOR, TAG + '-' + label + '-receipt', TAG)
        invoices[label] = invoice
    draft_invoice = receivables.draft([sources['Alfa non incassata 1']], ANCHOR, '2026-10-31', TAG + '-draft', TAG)['name']
    invoices['Alfa bozza'] = draft_invoice
    banking.configure_bank(center, TAG)
    movements = banking.import_movements(center, [{'external_id': TAG + '-MATCH', 'date': ANCHOR, 'deposit': 60,
        'customer': frappe.db.get_value('Sales Invoice', invoices['Beta parzialmente incassata'], 'customer'),
        'reference': invoices['Beta parzialmente incassata'], 'description': 'SYNTHETIC UAT saldo Beta'},
        {'external_id': TAG + '-UNMATCHED', 'date': ANCHOR, 'deposit': 999, 'description': 'SYNTHETIC UAT senza riferimento'}], TAG)['movements']
    issuer = 'SYNTHETIC-' + TAG
    frappe.db.set_value('Supplier', supplier, 'tax_id', issuer)
    frappe.db.set_value('Item', item, 'is_purchase_item', 1)
    payable_source = incoming.intake(center, xml(issuer, TAG + '-EXPENSE'), TAG)['name']
    incoming.bind_supplier(payable_source, supplier, TAG)
    company = frappe.db.get_value('Branch', center, 'cc_company')
    expense = frappe.db.get_value('Company', company, 'default_expense_account')
    payable = incoming.draft(payable_source, [item], expense, ANCHOR, '2026-10-31', TAG + '-purchase', TAG)['name']
    incoming.submit(payable, TAG)
    invalid = incoming.intake(center, '<synthetic-invalid', TAG)['name']
    for label, source in sources.items():
        if label not in ('Delta annullata puntuale', 'Delta annullata tardiva', 'Alfa da prenotare'):
            economics.capture(source, TAG, rule if not label.startswith('Zeta') else None)
    economics.reevaluate(center, TAG)
    sd = sdi.prepare(invoices['Gamma incassata'], TAG + '-sdi', TAG)['name']
    sdi.queue(sd, TAG + '-sdi-attempt', 'Accepted', TAG)
    pending = ts.prepare(sources['Beta parzialmente incassata'], invoices['Beta parzialmente incassata'], TAG + '-ts-pending', TAG)['name']
    review = ts.review_inputs(sources['Gamma incassata'], invoices['Gamma incassata'], 'No Opposition', 'SYNTHETIC_ELIGIBLE', TAG + '-ts-input', TAG, expense_amount=100, expense_code='SYNTHETIC_HEALTH')['name']
    ready = ts.prepare(sources['Gamma incassata'], invoices['Gamma incassata'], TAG + '-ts-ready', TAG, input_review=review)['name']
    ts.queue(ready, TAG + '-ts-attempt', 'Accepted', TAG)
    admin_queue.refresh(center, TAG)
    frappe.db.set_value('Patient', patients['Theta'], 'email', TAG.lower() + '-theta@example.invalid')
    collections.refresh(patients['Theta'], center, TAG)
    assert frappe.db.count('Email Queue') == email_count, 'UAT preparation must not queue external email'
    return {'version': VERSION, 'anchor': ANCHOR, 'fixture': fixture, 'patients': patients,
        'appointments': appointments, 'sources': sources, 'invoices': invoices, 'bank': [r['name'] for r in movements],
        'incoming': {'classified': payable_source, 'invalid': invalid, 'payable': payable},
        'fiscal': {'SdI accepted': sd, 'TS pending': pending, 'TS accepted': ready}, 'rule': rule}


def inspect():
    guard()
    data = read()
    # Secrets are never included in this public-to-operator summary.
    return {key: data[key] for key in ('version', 'anchor', 'patients', 'appointments', 'sources', 'invoices', 'bank', 'incoming', 'fiscal')}


def credentials():
    """Only host harness may capture this into a 0600 file outside the repository."""
    guard()
    return read()['fixture']


def validate():
    guard()
    from centrochange_core.finance import professional_economics as economics, banking, collections
    data = read()
    fixture = data['fixture']
    checks = []
    assert len(fixture['users']) == 7 and len(fixture['patients']) == 8
    for user in fixture['users'].values():
        assert user['name'].endswith('@example.invalid') and frappe.db.get_value('User', user['name'], 'enabled')
    for name in data['appointments'].values():
        assert frappe.db.get_value('Patient Appointment', name, 'cc_price_snapshot') == 100
        assert frappe.db.get_value('Patient Appointment', name, 'duration') == 60
        assert str(frappe.db.get_value('Patient Appointment', name, 'cc_booking_date')) == '2026-09-21'
    checks.append('seven synthetic enabled users, eight patients, two centers and two professionals')
    assert frappe.db.get_value('Patient Appointment', data['appointments']['Delta annullata puntuale'], 'cc_late_cancellation') == 0
    assert frappe.db.get_value('Patient Appointment', data['appointments']['Delta annullata tardiva'], 'cc_late_cancellation') == 1
    assert frappe.db.get_value('Patient Appointment', data['appointments']['Epsilon pacchetto'], 'cc_economic_state') == 'Package Covered'
    checks.append('exactly 48h timely, 47h late, package-covered history')
    amounts = {label: float(frappe.db.get_value('Sales Invoice', name, 'outstanding_amount')) for label, name in data['invoices'].items() if not label.startswith('Alfa')}
    assert amounts == {'Beta parzialmente incassata': 60.0, 'Gamma incassata': 0.0, 'Theta insoluto scaduto': 100.0}
    assert frappe.db.get_value('Sales Invoice', data['invoices']['Alfa bozza'], 'docstatus') == 0
    assert not frappe.db.count('GL Entry', {'voucher_no': data['invoices']['Alfa bozza']})
    assert frappe.db.get_value('Purchase Invoice', data['incoming']['payable'], 'outstanding_amount') == 100
    checks.append('native submitted patient balances 60/0, unposted draft and supplier balance 100')
    assert collections.position(data['patients']['Theta'], fixture['centers'][0])['blocked']
    assert frappe.db.get_value('CC Payment Notice', {'patient': data['patients']['Theta']}, 'email_state') == 'SIMULATED'
    checks.append('overdue native patient debt blocks subsequent session; internal/local email trace only')
    rows = economics.latest_expectations(fixture['centers'][0])
    states = {label: rows[name].state for label, name in data['appointments'].items() if name in rows}
    assert states['Alfa non incassata 1'] == 'OK' and states['Alfa non incassata 2'] == 'SUSPENDED'
    assert states['Zeta configurazione mancante'] == 'REVIEW'
    checks.append('approved N1 pair ranking and explicit missing configuration REVIEW')
    assert banking.candidates(data['bank'][0])['state'] == 'Candidate'
    assert banking.candidates(data['bank'][1])['state'] == 'Unmatched'
    assert frappe.db.get_value('CC Incoming Invoice', data['incoming']['invalid'], 'state') == 'Invalid Source'
    checks.append('native bank matching/unmatched and invalid retained XML exception')
    statuses = {label: frappe.db.get_value('CC Fiscal Transaction', name, 'status') for label, name in data['fiscal'].items()}
    for name in data['fiscal'].values():
        assert frappe.db.get_value('CC Fiscal Transaction', name, 'route') == 'SIMULATED'
        assert frappe.db.get_value('CC Fiscal Transaction', name, 'configuration_ref') == 'SYNTHETIC_UNVERIFIED'
    if statuses != {'SdI accepted': 'ACCEPTED_OR_DELIVERED', 'TS pending': 'ELIGIBILITY_PENDING', 'TS accepted': 'ACCEPTED'}:
        return {'status': 'PARTIAL', 'waiting_for_workers': statuses}
    checks.append('actual queued workers completed SdI/TS pure simulations; TS pending remains explicit')
    assert frappe.db.count('CC Audit Event', {'reason': TAG}) > 30
    assert frappe.db.count('CC Admin Exception', {'center': fixture['centers'][0], 'state': ['!=', 'Closed']}) > 0
    checks.append('audit history and actionable administrative exceptions retained')
    normalized = {'version': VERSION, 'anchor': ANCHOR, 'roles': sorted(fixture['users']), 'patients': sorted(data['patients']),
        'appointment_states': {label: {field: str(frappe.db.get_value('Patient Appointment', name, field)) for field in
            ('appointment_date', 'appointment_time', 'cc_booking_date', 'cc_price_snapshot', 'duration', 'cc_economic_state', 'cc_performed', 'cc_late_cancellation')} for label, name in data['appointments'].items()},
        'receivables': amounts, 'payable': 100, 'expectations': states, 'fiscal': statuses}
    digest = sha256(json.dumps(normalized, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'status': 'PASS', 'version': VERSION, 'semantic_sha256': digest, 'checks': checks, 'normalized': normalized}


def reset():
    """Exact tagged ownership only; waits for tracked User contact and fiscal jobs."""
    with exclusive():
        users = frappe.get_all('User', filters={'email': ['like', TAG.lower() + '-%@example.invalid']}, pluck='name')
        if fixtures.pending_contacts(users)['pending']:
            frappe.throw('Owned contact jobs pending; wait before reset')
        centers = frappe.get_all('Branch', filters={'branch': ['like', TAG + ' %']}, pluck='name')
        active = frappe.db.count('CC Fiscal Transaction', {'center': ['in', centers or ['']], 'status': 'SUBMITTED'})
        if active:
            frappe.throw('Owned fiscal jobs pending; wait before reset')
        result = fixtures.recover_http(TAG)
        (directory() / 'demo.json').unlink(missing_ok=True)
        return result
