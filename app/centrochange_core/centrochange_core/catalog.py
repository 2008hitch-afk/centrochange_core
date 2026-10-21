"""Narrow Centro Change catalog projections and manager-only master updates."""
import frappe
from centrochange_core.scoped_api import bounded, create, deny_extra, manager, mutate, page

FIELDS = {
    'CC Center Service': ['name', 'center', 'appointment_type', 'enabled', 'modified'],
    'Appointment Type': ['name', 'appointment_type', 'default_duration', 'cc_service_item', 'cc_first_meeting', 'modified'],
    'Item': ['name', 'item_name', 'item_group', 'stock_uom', 'is_stock_item', 'is_sales_item', 'disabled', 'modified'],
    'Item Price': ['name', 'item_code', 'price_list', 'currency', 'price_list_rate', 'valid_from', 'valid_upto', 'uom', 'modified'],
    'CC Package Template': ['name', 'title', 'service_item', 'units', 'enabled', 'modified'],
}


def _scope(center):
    manager(center)
    services = frappe.get_list('CC Center Service', filters={'center': center}, fields=['name', 'appointment_type'], page_length=501)
    if len(services) > 500:
        frappe.throw('Catalogo troppo ampio per la proiezione corrente')
    types = [row.appointment_type for row in services]
    items = frappe.get_all('Appointment Type', filters={'name': ['in', types or ['']]}, pluck='cc_service_item')
    price_list = frappe.db.get_value('Branch', center, 'cc_price_list')
    return {'services': [row.name for row in services], 'types': types,
            'items': [item for item in items if item], 'price_list': price_list}


def _check(center, kind, doc):
    scope = _scope(center)
    if kind == 'CC Center Service':
        allowed = doc.center == center
    elif kind == 'Appointment Type':
        allowed = doc.name in scope['types']
    elif kind == 'Item':
        allowed = doc.name in scope['items']
    elif kind == 'Item Price':
        allowed = doc.item_code in scope['items'] and doc.price_list == scope['price_list']
    else:
        allowed = doc.service_item in scope['items']
    if not allowed:
        frappe.throw('Scheda non disponibile per questo centro', frappe.PermissionError)
    return scope


def _exclusive(center, kind, doc):
    _check(center, kind, doc)
    if kind == 'Appointment Type':
        linked = frappe.get_all('CC Center Service', filters={'appointment_type': doc.name}, pluck='center')
    elif kind == 'Item':
        profiles = frappe.get_all('Appointment Type', filters={'cc_service_item': doc.name}, pluck='name')
        linked = frappe.get_all('CC Center Service', filters={'appointment_type': ['in', profiles or ['']]}, pluck='center')
    else:
        linked = [center]
    if set(linked) - {center}:
        frappe.throw('Master condiviso con altro centro: modifica bloccata', frappe.PermissionError)


def _enabled_snapshot(center, doc):
    if doc.enabled:
        from centrochange_core.scheduling.booking import snapshot
        snapshot(doc.appointment_type, center)


@frappe.whitelist(methods=['GET'])
def records(center, kind, limit=50, offset=0):
    if kind not in FIELDS:
        frappe.throw('Archivio non autorizzato', frappe.PermissionError)
    limit, offset = page(limit, offset)
    scope = _scope(center)
    if kind == 'CC Center Service':
        filters = {'center': center}
    elif kind == 'Appointment Type':
        filters = {'name': ['in', scope['types'] or ['']]}
    elif kind == 'Item':
        filters = {'name': ['in', scope['items'] or ['']]}
    elif kind == 'Item Price':
        filters = {'item_code': ['in', scope['items'] or ['']], 'price_list': scope['price_list'] or '',
                   'customer': ['is', 'not set'], 'supplier': ['is', 'not set'], 'batch_no': ['is', 'not set']}
    else:
        filters = {'service_item': ['in', scope['items'] or ['']]}
    rows = frappe.get_list(kind, filters=filters, fields=FIELDS[kind], order_by='modified desc',
                           start=offset, page_length=limit + 1)
    return {'rows': rows[:limit], 'has_more': len(rows) > limit}


@frappe.whitelist(methods=['GET'])
def detail(center, kind, name):
    if kind not in FIELDS:
        frappe.throw('Archivio non autorizzato', frappe.PermissionError)
    doc = frappe.get_doc(kind, bounded(name, 'Scheda'))
    doc.check_permission('read')
    _check(center, kind, doc)
    if kind == 'Item Price':
        item = frappe.get_doc('Item', doc.item_code)
        if doc.customer or doc.supplier or doc.batch_no or (doc.uom and doc.uom != item.stock_uom):
            frappe.throw('Tariffa fuori perimetro', frappe.PermissionError)
    return {field: doc.get(field) for field in FIELDS[kind]}


@frappe.whitelist(methods=['POST'])
def service_save(center, name, enabled, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    try:
        value = int(enabled)
    except (TypeError, ValueError):
        frappe.throw('Stato servizio non valido')
    if value not in (0, 1):
        frappe.throw('Stato servizio non valido')
    return mutate('service', center, 'CC Center Service', name, {'enabled': value},
                  ('enabled',), expected_version, request_key, reason,
                  lambda doc: _check(center, 'CC Center Service', doc),
                  lambda doc: _enabled_snapshot(center, doc))


@frappe.whitelist(methods=['POST'])
def service_create(center, appointment_type, enabled, request_key, reason, **extra):
    deny_extra(extra)
    try:
        enabled = int(enabled)
    except (TypeError, ValueError):
        frappe.throw('Stato servizio non valido')
    if enabled not in (0, 1):
        frappe.throw('Stato servizio non valido')
    appointment_type = bounded(appointment_type, 'Tipo seduta')
    def validate(data):
        profile = frappe.get_doc('Appointment Type', appointment_type)
        profile.check_permission('read')
        if not profile.cc_service_item or not frappe.db.exists('Item', profile.cc_service_item):
            frappe.throw('Tipo seduta senza articolo servizio')
        if frappe.db.exists('CC Center Service', {'center': center, 'appointment_type': appointment_type}):
            frappe.throw('Servizio già presente nel centro')
    return create('service_create', center, 'CC Center Service',
                  {'center': center, 'appointment_type': appointment_type, 'enabled': enabled},
                  ('center', 'appointment_type', 'enabled'), request_key, reason, validate,
                  lambda doc: _enabled_snapshot(center, doc),
                  lambda doc: _check(center, 'CC Center Service', doc))


@frappe.whitelist(methods=['POST'])
def item_save(center, name, item_name, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    return mutate('item', center, 'Item', name, {'item_name': bounded(item_name, 'Nome articolo')},
                  ('item_name',), expected_version, request_key, reason,
                  lambda doc: _exclusive(center, 'Item', doc))


@frappe.whitelist(methods=['POST'])
def appointment_type_save(center, name, default_duration, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    try:
        duration = int(default_duration)
    except (TypeError, ValueError):
        frappe.throw('Durata non valida')
    if duration <= 0:
        frappe.throw('Durata non valida')
    return mutate('appointment_type', center, 'Appointment Type', name,
                  {'default_duration': duration}, ('default_duration',), expected_version, request_key, reason,
                  lambda doc: _exclusive(center, 'Appointment Type', doc))


@frappe.whitelist(methods=['POST'])
def appointment_type_create(center, appointment_type, service_item, default_duration, request_key, reason, **extra):
    deny_extra(extra)
    try:
        duration = int(default_duration)
    except (TypeError, ValueError):
        frappe.throw('Durata non valida')
    if duration <= 0:
        frappe.throw('Durata non valida')
    appointment_type = bounded(appointment_type, 'Tipo seduta')
    service_item = bounded(service_item, 'Articolo servizio')
    def validate(data):
        item = frappe.get_doc('Item', service_item, for_update=True)
        item.check_permission('read')
        _exclusive(center, 'Item', item)
        if item.disabled or item.is_stock_item or not item.is_sales_item:
            frappe.throw('Articolo servizio non attivo')
        if frappe.db.exists('Appointment Type', appointment_type):
            frappe.throw('Tipo seduta già presente')
    return create('appointment_type_create', center, 'Appointment Type',
                  {'appointment_type': appointment_type, 'default_duration': duration,
                   'cc_service_item': service_item, 'allow_booking_for': 'Practitioner', 'cc_first_meeting': 0},
                  ('appointment_type', 'default_duration', 'cc_service_item', 'allow_booking_for', 'cc_first_meeting'),
                  request_key, reason, validate, replay_guard=lambda doc: _exclusive(center, 'Item', frappe.get_doc('Item', doc.cc_service_item)))


@frappe.whitelist(methods=['POST'])
def price_save(center, name, price_list_rate, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    from decimal import Decimal, InvalidOperation
    try:
        rate = Decimal(str(price_list_rate))
    except (InvalidOperation, ValueError):
        frappe.throw('Tariffa non valida')
    if not rate.is_finite() or rate < 0 or rate > 1000000 or rate.as_tuple().exponent < -2:
        frappe.throw('Tariffa non valida')
    def validate(doc):
        scope = _check(center, 'Item Price', doc)
        price_list = frappe.get_doc('Price List', scope['price_list'])
        price_list.check_permission('read')
        item = frappe.get_doc('Item', doc.item_code)
        item.check_permission('read')
        if not price_list.enabled or not price_list.selling or doc.currency != price_list.currency or doc.customer or doc.supplier or doc.batch_no or (doc.uom and doc.uom != item.stock_uom):
            frappe.throw('Listino o tariffa fuori perimetro', frappe.PermissionError)
        if set(frappe.get_all('Branch', filters={'cc_price_list': scope['price_list']}, pluck='name')) - {center}:
            frappe.throw('Listino condiviso con altro centro: modifica bloccata', frappe.PermissionError)
    return mutate('price', center, 'Item Price', name, {'price_list_rate': rate},
                  ('price_list_rate',), expected_version, request_key, reason, validate)


@frappe.whitelist(methods=['POST'])
def price_create(center, item_code, valid_from, price_list_rate, request_key, reason, **extra):
    deny_extra(extra)
    from datetime import date
    from decimal import Decimal, InvalidOperation
    try:
        rate = Decimal(str(price_list_rate))
        date.fromisoformat(str(valid_from))
    except (InvalidOperation, ValueError, TypeError):
        frappe.throw('Tariffa o decorrenza non valida')
    if not rate.is_finite() or rate < 0 or rate > 1000000 or rate.as_tuple().exponent < -2:
        frappe.throw('Tariffa non valida')
    scope = _scope(center)
    item_code = bounded(item_code, 'Articolo')
    if item_code not in scope['items']:
        frappe.throw('Articolo fuori centro', frappe.PermissionError)
    price_list = frappe.get_doc('Price List', scope['price_list'])
    price_list.check_permission('read')
    if not price_list.enabled or not price_list.selling:
        frappe.throw('Listino non attivo', frappe.PermissionError)
    other_centers = frappe.get_all('Branch', filters={'cc_price_list': scope['price_list']}, pluck='name')
    if set(other_centers) - {center}:
        frappe.throw('Listino condiviso con altro centro: modifica bloccata', frappe.PermissionError)
    def validate(data):
        fresh = _scope(center)
        if fresh['price_list'] != scope['price_list'] or item_code not in fresh['items']:
            frappe.throw('Catalogo modificato: ricarica la pagina', frappe.PermissionError)
        if set(frappe.get_all('Branch', filters={'cc_price_list': scope['price_list']}, pluck='name')) - {center}:
            frappe.throw('Listino condiviso con altro centro: modifica bloccata', frappe.PermissionError)
        item = frappe.get_doc('Item', item_code)
        item.check_permission('read')
        if item.disabled or item.is_stock_item or not item.is_sales_item:
            frappe.throw('Articolo servizio non attivo')
        previous = frappe.get_all('Item Price', filters={'item_code': item_code, 'price_list': scope['price_list'], 'valid_from': valid_from},
                                  fields=['name', 'customer', 'supplier', 'batch_no'])
        if any(not row.customer and not row.supplier and not row.batch_no for row in previous):
            frappe.throw('Tariffa già presente per questa decorrenza')
    return create('price_create', center, 'Item Price',
                  {'item_code': item_code, 'price_list': scope['price_list'], 'currency': price_list.currency,
                   'price_list_rate': rate, 'valid_from': valid_from},
                  ('item_code', 'price_list', 'currency', 'price_list_rate', 'valid_from'), request_key, reason, validate,
                  replay_guard=lambda doc: _check(center, 'Item Price', doc))


@frappe.whitelist(methods=['POST'])
def package_template_save(center, name, title, units, enabled, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    try:
        units, enabled = int(units), int(enabled)
    except (TypeError, ValueError):
        frappe.throw('Modello pacchetto non valido')
    if not 1 <= units <= 9999 or enabled not in (0, 1):
        frappe.throw('Modello pacchetto non valido')
    return mutate('package_template', center, 'CC Package Template', name,
                  {'title': bounded(title, 'Nome modello'), 'units': units, 'enabled': enabled},
                  ('title', 'units', 'enabled'), expected_version, request_key, reason,
                  lambda doc: _exclusive(center, 'Item', frappe.get_doc('Item', doc.service_item)))


@frappe.whitelist(methods=['POST'])
def package_template_create(center, title, service_item, units, enabled, request_key, reason, **extra):
    deny_extra(extra)
    try:
        units, enabled = int(units), int(enabled)
    except (TypeError, ValueError):
        frappe.throw('Modello pacchetto non valido')
    if not 1 <= units <= 9999 or enabled not in (0, 1):
        frappe.throw('Modello pacchetto non valido')
    title, service_item = bounded(title, 'Nome modello'), bounded(service_item, 'Articolo servizio')
    def validate(data):
        if service_item not in _scope(center)['items']:
            frappe.throw('Articolo fuori centro', frappe.PermissionError)
        item = frappe.get_doc('Item', service_item)
        item.check_permission('read')
        _exclusive(center, 'Item', item)
        if item.disabled or item.is_stock_item or not item.is_sales_item:
            frappe.throw('Articolo servizio non attivo')
    return create('package_template_create', center, 'CC Package Template',
                  {'title': title, 'service_item': service_item, 'units': units, 'enabled': enabled},
                  ('title', 'service_item', 'units', 'enabled'), request_key, reason, validate,
                  replay_guard=lambda doc: _exclusive(center, 'Item', frappe.get_doc('Item', doc.service_item)))
