"""Synthetic-only operational receipts; no posting to the accounting ledger."""
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import frappe
from centrochange_core.finance.guards import patient_context, require_synthetic
from centrochange_core.security.audit import atomic, append, internal_write, serialize
from centrochange_core.security.guards import current_rows
from centrochange_core.security.lifecycle import lock


def cents(value):
    try:
        value = Decimal(str(value))
        if not value.is_finite() or value != value.quantize(Decimal('.01')) or value <= 0:
            raise ValueError()
        return int(value * 100)
    except (ValueError, InvalidOperation, TypeError):
        frappe.throw('Indica un importo positivo con al massimo due decimali.')


def _rows(patient, center):
    return current_rows('CC Operational Receipt', {'patient': patient, 'center': center},
        fields=['name', 'receipt_date', 'mode_of_payment', 'reason', 'actor', 'allocations', 'creation'])


def allocated(patient, center):
    result = {}
    for receipt in _rows(patient, center):
        for item in json.loads(receipt.allocations):
            result[item['appointment']] = result.get(item['appointment'], 0) + item['cents']
    return result


def has_allocation(appointment):
    row = frappe.db.get_value('Patient Appointment', appointment, ['patient', 'cc_center'], as_dict=True)
    return bool(row and allocated(row.patient, row.cc_center).get(appointment))


@frappe.whitelist(methods=['GET'])
def history(patient, center):
    patient_context(patient, center)
    rows = _rows(patient, center)
    return [{**dict(row), 'allocations': json.loads(row.allocations)} for row in rows]


@frappe.whitelist(methods=['POST'])
@atomic
def record(patient, center, receipt_date, mode_of_payment, reason, request_key, allocations):
    lock(); require_synthetic(); patient_context(patient, center, True)
    return _record(patient, center, receipt_date, mode_of_payment, reason, request_key, allocations)


def record_from_authorized_closure(doc, mode_of_payment, reason):
    # Private helper: the lifecycle caller has already enforced appointment,
    # practitioner and center permissions under the same transaction lock.
    return _record(doc.patient, doc.cc_center, frappe.utils.today(), mode_of_payment, reason,
        'legacy-settlement:' + doc.name + ':' + str(int(doc.cc_settlement_revision or 0)+1),
        [{'appointment':doc.name, 'amount':doc.cc_price_snapshot}])


def _record(patient, center, receipt_date, mode_of_payment, reason, request_key, allocations):
    if not reason or not reason.strip() or len(reason) > 2000 or not request_key or len(request_key) > 140:
        frappe.throw('Indica causale e identificativo validi.')
    if not frappe.db.get_value('Mode of Payment', mode_of_payment, 'enabled', for_update=True):
        frappe.throw('Seleziona un metodo di pagamento attivo.')
    date = frappe.utils.getdate(receipt_date)
    if date > frappe.utils.getdate():
        frappe.throw('La data dell’incasso non può essere futura.')
    if isinstance(allocations, str):
        allocations = frappe.parse_json(allocations)
    if not isinstance(allocations, list) or not 1 <= len(allocations) <= 100:
        frappe.throw('Seleziona almeno una seduta.')
    entries = []
    for item in allocations:
        if not isinstance(item, dict) or not item.get('appointment'):
            frappe.throw('Seleziona una seduta valida.')
        entries.append({'appointment': str(item['appointment']), 'cents': cents(item.get('amount'))})
    entries.sort(key=lambda item: item['appointment'])
    if len({item['appointment'] for item in entries}) != len(entries):
        frappe.throw('Ogni seduta può essere selezionata una sola volta.')
    key = sha256((frappe.session.user + '\0' + request_key).encode()).hexdigest()
    fingerprint = sha256(serialize([patient, center, str(date), mode_of_payment, reason, entries]).encode()).hexdigest()
    existing = frappe.db.get_value('CC Operational Receipt', key, 'request_hash', for_update=True)
    if existing:
        if existing != fingerprint:
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return {'name': key, 'replay': True}
    previous = allocated(patient, center)
    complete = []
    for item in entries:
        doc = frappe.get_doc('Patient Appointment', item['appointment'], for_update=True)
        if doc.patient != patient or doc.cc_center != center or doc.cc_economic_state != 'Due' or doc.cc_closure_state not in ('Closed', 'Auto Locked') or doc.cc_paid or doc.cc_currency_snapshot != 'EUR':
            frappe.throw('Una seduta non è disponibile per questo incasso.')
        if frappe.db.sql('''select i.name from `tabSales Invoice Item` i join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus<2 and p.is_return=0 limit 1 for update''', (doc.name,)):
            frappe.throw('La seduta è già collegata a una fattura: verifica la posizione contabile.')
        due = cents(doc.cc_price_snapshot)
        if item['cents'] + previous.get(doc.name, 0) > due:
            frappe.throw('L’incasso supera il residuo della seduta.')
        if item['cents'] + previous.get(doc.name, 0) == due:
            complete.append(doc)
    with internal_write('cc_operation_write'):
        frappe.get_doc({'doctype':'CC Operational Receipt', 'request_key':key, 'request_hash':fingerprint,
            'patient':patient, 'center':center, 'receipt_date':date, 'mode_of_payment':mode_of_payment,
            'reason':reason.strip(), 'actor':frappe.session.user, 'allocations':json.dumps(entries)}).insert(ignore_permissions=True)
    # Keep legacy operational reports consistent only when a session is fully paid.
    # The monetary source remains the receipt; this is the existing binary projection.
    from centrochange_core.operations.lifecycle import _patch
    for doc in complete:
        sequence = int(doc.cc_settlement_revision or 0) + 1
        with internal_write('cc_operation_write'):
            event = frappe.get_doc({'doctype':'CC Settlement', 'appointment':doc.name, 'paid':1,
                'sequence':sequence, 'mode_of_payment':mode_of_payment, 'actor':frappe.session.user,
                'event_time':frappe.utils.now_datetime(), 'reason':reason.strip()}).insert(ignore_permissions=True)
            _patch(doc, {'cc_paid':1, 'cc_settlement_revision':sequence})
        append('OPERATIONAL_SETTLEMENT', doc.doctype, doc.name, None,
            {'paid':1, 'method':mode_of_payment, 'settlement':event.name, 'receipt':key}, reason)
    append('OPERATIONAL_RECEIPT_RECORDED', 'CC Operational Receipt', key, None,
        {'patient':patient, 'center':center, 'allocations':entries, 'mode_of_payment':mode_of_payment}, reason)
    return {'name':key, 'replay':False}

@frappe.whitelist(methods=['GET'])
def center_records(center):
    from centrochange_core.finance.guards import require_finance
    require_finance(center)
    rows = current_rows('CC Operational Receipt', {'center':center},
        fields=['name','patient','receipt_date','mode_of_payment','allocations','creation'])
    result = []
    for row in sorted(rows, key=lambda x: (x.creation, x.name), reverse=True):
        try:
            patient_context(row.patient, center)
        except frappe.PermissionError:
            continue
        result.append({'name':row.name,'patient':row.patient,
            'patient_label':frappe.db.get_value('Patient',row.patient,'patient_name'),
            'receipt_date':row.receipt_date,'mode_of_payment':row.mode_of_payment,
            'amount':sum(a['cents'] for a in json.loads(row.allocations))/100})
    return result
