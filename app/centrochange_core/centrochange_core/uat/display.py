"""Read-only presentation aliases for exact UAT-owned records.

The private manifest is the sole ownership source. Missing or malformed manifests
fail closed: no display aliases are returned and canonical records are unchanged.
"""
import json
from pathlib import Path

import frappe

from centrochange_core.uat.demo import TAG, VERSION


def _manifest():
    if frappe.conf.get('cc_synthetic_dev') != 1 or frappe.conf.get('cc_uat_demo') != 1:
        return None
    path = Path(frappe.get_site_path('private', 'uat', 'demo.json'))
    if path.is_symlink() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get('version') != VERSION:
        return None
    fixture = data.get('fixture')
    if not isinstance(fixture, dict) or fixture.get('tag') != TAG:
        return None
    if not all(isinstance(fixture.get(key), list) for key in ('centers', 'patients', 'practitioners')):
        return None
    if not isinstance(fixture.get('catalog'), dict):
        return None
    if not all(isinstance(data.get(key), dict) for key in ('patients', 'appointments', 'sources', 'invoices', 'incoming', 'fiscal')):
        return None
    if not isinstance(data.get('bank'), list):
        return None
    return data


def _put(result, identifier, label, display=None):
    if identifier:
        result[str(identifier)] = label
    if display and display != identifier:
        result[str(display)] = label


def _readable(doctype, name):
    try:
        return bool(frappe.has_permission(doctype, ptype='read', doc=name))
    except (frappe.PermissionError, frappe.DoesNotExistError):
        return False


def operational_aliases(center, patients, practitioners, services, packages, centers, manager=False):
    data = _manifest()
    if not data:
        return {}
    fixture = data['fixture']
    result = {}
    owned = set(fixture['centers'])
    for row in centers:
        if row.name in owned:
            _put(result, row.name, f'Centro {chr(65 + fixture["centers"].index(row.name))}', row.branch)
    patient_order = fixture['patients']
    for row in patients:
        if row.name in patient_order:
            label = f'Paziente {patient_order.index(row.name) + 1}'
            _put(result, row.name, label, row.patient_name)
    practitioner_order = fixture['practitioners']
    for row in practitioners:
        if row.name in practitioner_order:
            label = f'Professionista {practitioner_order.index(row.name) + 1}'
            _put(result, row.name, label, row.practitioner_name)
    service_order = fixture['catalog'].get('Appointment Type', [])
    for row in services:
        if row['name'] in service_order:
            label = f'Servizio {service_order.index(row["name"]) + 1}'
            _put(result, row['name'], label, row.get('cc_service_label'))
    owned_packages = [data.get('package')] if data.get('package') else []
    for row in packages:
        if row['name'] in owned_packages:
            _put(result, row['name'], f'Pacchetto {owned_packages.index(row["name"]) + 1}', row.get('label'))
    if manager:
        catalog = fixture['catalog']
        for doctype, title, name_field in (('Item', 'Servizio', 'item_name'),
                                           ('Appointment Type', 'Servizio', 'appointment_type'),
                                           ('CC Package Template', 'Pacchetto', 'title'),
                                           ('Item Price', 'Tariffa', None)):
            for index, name in enumerate(catalog.get(doctype, []), 1):
                if _readable(doctype, name):
                    display = frappe.db.get_value(doctype, name, name_field) if name_field else None
                    _put(result, name, f'{title} {index}', display)
        for index, name in enumerate(catalog.get('CC Center Service', []), 1):
            if (frappe.db.get_value('CC Center Service', name, 'center') == center
                    and _readable('CC Center Service', name)):
                _put(result, name, f'Servizio {index}')
    return result


def finance_aliases(center, scopes, customers, suppliers, practitioners, items):
    data = _manifest()
    if not data:
        return {}
    fixture = data['fixture']
    result = {}
    for row in scopes:
        if row.name in fixture['centers']:
            _put(result, row.name, f'Centro {chr(65 + fixture["centers"].index(row.name))}', row.branch)
    patient_order = fixture['patients']
    customer_order = [frappe.db.get_value('Patient', patient, 'customer') for patient in patient_order]
    for row in customers:
        if row.name in customer_order:
            _put(result, row.name, f'Cliente {customer_order.index(row.name) + 1}')
    practitioner_order = fixture['practitioners']
    supplier_order = [frappe.db.get_value('Healthcare Practitioner', practitioner, 'supplier') for practitioner in practitioner_order]
    for row in suppliers:
        if row.name in supplier_order:
            _put(result, row.name, f'Fornitore {supplier_order.index(row.name) + 1}')
    for row in practitioners:
        if row.name in practitioner_order:
            _put(result, row.name, f'Professionista {practitioner_order.index(row.name) + 1}', row.practitioner_name)
    item_order = fixture['catalog'].get('Item', [])
    for row in items:
        if row.name in item_order:
            _put(result, row.name, f'Servizio {item_order.index(row.name) + 1}', row.item_name)
    # Only documents in the exact UAT manifest and in the selected center.
    groups = (('invoices', 'Sales Invoice', 'cc_center', 'Fattura paziente'),
              ('bank', 'Bank Transaction', 'cc_center', 'Movimento bancario'),
              ('fiscal', 'CC Fiscal Transaction', 'center', 'Documento fiscale'))
    for key, doctype, field, title in groups:
        values = data.get(key, {})
        names = list(values.values()) if isinstance(values, dict) else list(values)
        for index, name in enumerate(names, 1):
            if (frappe.db.get_value(doctype, name, field) == center
                    and _readable(doctype, name)):
                _put(result, name, f'{title} {index}')
    for key, doctype, field, title in (('appointments', 'Patient Appointment', 'cc_center', 'Seduta'),
                                       ('sources', 'CC Economic Source Link', 'center', 'Fonte seduta')):
        for index, name in enumerate(data.get(key, {}).values(), 1):
            if (frappe.db.get_value(doctype, name, field) == center
                    and _readable(doctype, name)):
                _put(result, name, f'{title} {index}')
    for index, (label, invoice) in enumerate(data.get('invoices', {}).items(), 1):
        reference = TAG + '-' + label + '-receipt'
        payment = frappe.db.get_value('Payment Entry', {'reference_no': reference, 'cc_center': center}, 'name')
        if (payment and frappe.db.get_value('Sales Invoice', invoice, 'cc_center') == center
                and _readable('Payment Entry', payment)):
            _put(result, payment, f'Pagamento {index}')
    incoming = data.get('incoming', {})
    for index, (kind, name) in enumerate(incoming.items(), 1):
        doctype = 'Purchase Invoice' if kind == 'payable' else 'CC Incoming Invoice'
        field = 'cc_center' if kind == 'payable' else 'center'
        if (frappe.db.get_value(doctype, name, field) == center
                and _readable(doctype, name)):
            _put(result, name, f'{"Fattura professionista" if kind == "payable" else "Documento XML"} {index}')
    return result
