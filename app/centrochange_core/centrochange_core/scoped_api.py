"""Shared boundary for the premium UI's narrow, audited master mutations."""
from hashlib import sha256
import json

import frappe
from centrochange_core.security.audit import append, atomic, serialize
from centrochange_core.security.guards import require_center, require_manager
from centrochange_core.security.lifecycle import lock


def bounded(text, label, limit=140, required=True):
    value = str(text or '').strip()
    if len(value) > limit or (required and not value):
        frappe.throw(f'{label}: valore obbligatorio o troppo lungo')
    return value


def page(limit=50, offset=0):
    try:
        limit, offset = int(limit), int(offset)
    except (TypeError, ValueError):
        frappe.throw('Paginazione non valida')
    if not 1 <= limit <= 100 or not 0 <= offset <= 10000:
        frappe.throw('Paginazione fuori limite')
    return limit, offset


def exact_fields(values, allowed):
    if isinstance(values, str):
        values = frappe.parse_json(values)
    if not isinstance(values, dict) or not values or set(values) - set(allowed):
        frappe.throw('Campi non autorizzati', frappe.PermissionError)
    return values


def deny_extra(extra):
    if not extra:
        return
    request = getattr(frappe.local, 'request', None)
    cmd = extra.get('cmd')
    # Frappe v16 injects its RPC route into form_dict before calling a
    # whitelisted function with **kwargs. Accept only that exact framework
    # marker; every client-supplied business field remains rejected.
    if (set(extra) == {'cmd'} and isinstance(cmd, str) and request
            and request.method == 'POST' and request.path == '/api/method/' + cmd):
        return
    frappe.throw('Campi non autorizzati', frappe.PermissionError)


def manager(center):
    require_manager()
    require_center(center)
    if not frappe.db.exists('Branch', center):
        frappe.throw('Centro inesistente', frappe.PermissionError)


def replay_key(operation, key):
    key = bounded(key, 'Chiave richiesta', 140)
    return sha256(serialize([frappe.session.user, operation, key]).encode()).hexdigest()


def mutate(operation, center, doctype, name, values, allowed, expected_version, request_key, reason, validate=None, after_save=None):
    """Update only a pinned field set. Role lock serializes audit-based replay checks.

    No new schema or permission bypass. Same key + different payload is rejected.
    Native save and append-only audit remain in one savepoint/transaction.
    """
    @atomic
    def run():
        manager(center)
        lock()
        data = exact_fields(values, allowed)
        reason_text = bounded(reason, 'Motivo', 500)
        digest = replay_key(operation, request_key)
        fingerprint = sha256(serialize([center, doctype, name, data, expected_version]).encode()).hexdigest()
        events = frappe.db.get_values('CC Audit Event',
            {'event_type': 'PREMIUM_MASTER_UPDATED', 'actor': frappe.session.user,
             'before_state': ['like', '%' + digest + '%']},
            fieldname=['before_state', 'after_state'], as_dict=True, for_update=True)
        for event in events:
            before = json.loads(event.before_state)
            if before.get('request_key_hash') == digest:
                if before.get('fingerprint') != fingerprint:
                    frappe.throw('Chiave richiesta già usata con dati diversi')
                result = json.loads(event.after_state)['result']
                current = frappe.get_doc(doctype, result['name'])
                current.check_permission('read')
                if validate:
                    validate(current)
                return {**result, 'replay': True}
        doc = frappe.get_doc(doctype, name, for_update=True)
        doc.check_permission('write')
        if validate:
            validate(doc)
        if not expected_version or str(doc.modified) != str(expected_version):
            frappe.throw('Scheda modificata da un altro utente. Ricarica e riprova.')
        # Audit the changed field names and value digests, not patient identifiers/PII.
        before = {field: sha256(serialize(doc.get(field)).encode()).hexdigest() for field in data}
        for field, value in data.items():
            doc.set(field, value)
        doc.save()
        if after_save:
            after_save(doc)
        result = {'name': doc.name, 'modified': str(doc.modified)}
        append('PREMIUM_MASTER_UPDATED', doctype, doc.name,
               {'request_key_hash': digest, 'fingerprint': fingerprint, 'before': before},
               {'result': result}, reason_text)
        return {**result, 'replay': False}
    return run()


def create(operation, center, doctype, values, allowed, request_key, reason, validate=None, after_insert=None, replay_guard=None):
    """Native insert with the same serialized, audit-backed replay boundary."""
    @atomic
    def run():
        manager(center)
        lock()
        data = exact_fields(values, allowed)
        reason_text = bounded(reason, 'Motivo', 500)
        digest = replay_key(operation, request_key)
        fingerprint = sha256(serialize([center, doctype, data]).encode()).hexdigest()
        events = frappe.db.get_values('CC Audit Event',
            {'event_type': 'PREMIUM_MASTER_CREATED', 'actor': frappe.session.user,
             'before_state': ['like', '%' + digest + '%']},
            fieldname=['before_state', 'after_state'], as_dict=True, for_update=True)
        for event in events:
            before = json.loads(event.before_state)
            if before.get('request_key_hash') == digest:
                if before.get('fingerprint') != fingerprint:
                    frappe.throw('Chiave richiesta già usata con dati diversi')
                result = json.loads(event.after_state)['result']
                existing = frappe.get_doc(doctype, result['name'])
                existing.check_permission('read')
                if replay_guard:
                    replay_guard(existing)
                return {**result, 'replay': True}
        if validate:
            validate(data)
        doc = frappe.get_doc({'doctype': doctype, **data})
        doc.check_permission('create')
        doc.insert()
        if after_insert:
            after_insert(doc)
        result = {'name': doc.name, 'modified': str(doc.modified)}
        append('PREMIUM_MASTER_CREATED', doctype, doc.name,
               {'request_key_hash': digest, 'fingerprint': fingerprint}, {'result': result}, reason_text)
        return {**result, 'replay': False}
    return run()
