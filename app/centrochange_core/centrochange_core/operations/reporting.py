"""Operational reports use scoped projections; management totals contain no note bodies."""
import csv
from io import StringIO
from html import escape
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import math
import frappe
from frappe.utils import getdate, get_time, cint
from centrochange_core.security.guards import (
    require_manager, require_center, roles, practitioner_for, is_manager, current_rows
)
from centrochange_core.operations.workspace import require_actor, APPOINTMENT_FIELDS

ROME = ZoneInfo('Europe/Rome')


def _now_rome():
    flags = getattr(frappe, 'flags', None)
    clock = None
    if getattr(frappe, 'in_test', False) and getattr(frappe.conf, 'cc_synthetic_dev', 0) == 1 and flags:
        clock = flags.get('cc_test_clock') if isinstance(flags, dict) else getattr(flags, 'cc_test_clock', None)
    if clock:
        if clock.tzinfo is None:
            return clock.replace(tzinfo=ROME)
        return clock.astimezone(ROME)
    return datetime.now(timezone.utc).astimezone(ROME)


def _appointment_datetimes(row):
    """Returns (start_rome, end_rome) localized to Europe/Rome with robust fold/DST handling."""
    app_date = getdate(row.appointment_date)
    app_time = get_time(row.appointment_time)
    start_naive = datetime.combine(app_date, app_time)
    start_rome = start_naive.replace(tzinfo=ROME)
    duration_min = cint(getattr(row, 'duration', 0) or 60)
    end_rome = start_rome + timedelta(minutes=duration_min)
    return start_rome, end_rome


def classify_session(row, now_rome=None):
    """
    Canonical Europe/Rome temporal and operational status oracle:
    - cancelled: status == 'Cancelled'
    - performed: cc_performed or status in ('Closed', 'Completed') or cc_closure_state in ('Closed', 'Auto Locked')
    - future: not cancelled, not performed, end_rome > now_rome
    - to_close: not cancelled, not performed, end_rome <= now_rome
    - paid: cc_paid == 1
    - unpaid: not paid, not cancelled, not future, economic_state not in ('Non Due', 'Waived', 'Package Covered')
    - due: cc_economic_state == 'Due'
    """
    if now_rome is None:
        now_rome = _now_rome()

    status = row.status
    is_cancelled = (status == 'Cancelled')
    is_performed = bool(row.cc_performed) and not is_cancelled

    start_rome, end_rome = _appointment_datetimes(row)
    is_future = False
    is_to_close = False

    if not is_cancelled and not is_performed:
        if end_rome > now_rome:
            is_future = True
        else:
            is_to_close = True

    is_paid = bool(row.cc_paid)
    is_unpaid = (not is_paid and not is_cancelled and not is_future
                 and getattr(row, 'cc_economic_state', '') not in ('Non Due', 'Waived', 'Package Covered'))
    is_due = (getattr(row, 'cc_economic_state', '') == 'Due')

    return {
        'cancelled': is_cancelled,
        'performed': is_performed,
        'future': is_future,
        'to_close': is_to_close,
        'paid': is_paid,
        'unpaid': is_unpaid,
        'due': is_due,
        'start_rome': start_rome,
        'end_rome': end_rome
    }


def _matches_kpi(row, kpi, now_rome):
    if not kpi or kpi == 'all':
        return True
    c = classify_session(row, now_rome)
    if kpi == 'performed':
        return c['performed']
    if kpi == 'cancelled':
        return c['cancelled']
    if kpi == 'future':
        return c['future']
    if kpi == 'to_close':
        return c['to_close']
    if kpi == 'operational_paid':
        return c['paid']
    if kpi == 'operational_unpaid':
        return c['unpaid']
    if kpi == 'due':
        return c['due']
    return True


def _filter_scope(center, start, end, practitioner=None):
    require_actor()
    require_center(center)
    start, end = getdate(start), getdate(end)
    if end < start or end - start > timedelta(days=93):
        frappe.throw('Seleziona un intervallo Report di massimo 93 giorni.')
    user_roles = roles()
    if 'CC Professional' in user_roles and not is_manager():
        my_practitioner = practitioner_for(frappe.session.user)
        if not my_practitioner:
            frappe.throw('Nessun profilo professionista collegato a questo account.', frappe.PermissionError)
        if practitioner and practitioner != my_practitioner:
            frappe.throw('Non hai accesso ai dati di altri professionisti.', frappe.PermissionError)
        practitioner = my_practitioner
    elif practitioner in ('', 'all', None):
        practitioner = None
    filters = {'cc_center': center, 'appointment_date': ['between', [start, end]]}
    if practitioner:
        filters['practitioner'] = practitioner
    return filters, start, end, practitioner


@frappe.whitelist()
def summary(center, start, end, practitioner=None):
    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    rows = frappe.get_list('Patient Appointment', filters=filters, fields=APPOINTMENT_FIELDS,
                           order_by='appointment_date,appointment_time,name', page_length=0)
    totals = defaultdict(lambda: {
        'sessions': 0, 'performed': 0, 'cancelled': 0, 'future': 0, 'to_close': 0,
        'operational_paid': 0, 'operational_unpaid': 0, 'due': 0, 'due_snapshot_amount': 0
    })
    now_rome = _now_rome()
    for row in rows:
        bucket = totals[row.cc_currency_snapshot or 'UNSET']
        bucket['sessions'] += 1
        c = classify_session(row, now_rome)
        if c['performed']:
            bucket['performed'] += 1
        if c['cancelled']:
            bucket['cancelled'] += 1
        if c['future']:
            bucket['future'] += 1
        if c['to_close']:
            bucket['to_close'] += 1
        if c['paid']:
            bucket['operational_paid'] += 1
        if c['unpaid']:
            bucket['operational_unpaid'] += 1
        if c['due']:
            bucket['due'] += 1
            bucket['due_snapshot_amount'] += (row.cc_price_snapshot or 0)
    return {
        'currencies': dict(totals),
        'practitioner': practitioner,
        'total_appointments': len(rows),
        'truncated': False
    }


@frappe.whitelist()
def sessions(center, start, end, practitioner=None, kpi='all', page=1, page_length=50, order_by='appointment_date asc, appointment_time asc, name asc'):
    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    rows = frappe.get_list('Patient Appointment', filters=filters, fields=APPOINTMENT_FIELDS,
                           order_by=order_by or 'appointment_date asc, appointment_time asc, name asc', page_length=0)
    now_rome = _now_rome()
    filtered = [row for row in rows if _matches_kpi(row, kpi, now_rome)]
    total = len(filtered)

    page = max(1, cint(page) or 1)
    page_length = cint(page_length)
    if page_length <= 0:
        paged = filtered
        total_pages = 1
    else:
        total_pages = max(1, math.ceil(total / page_length))
        offset = (page - 1) * page_length
        paged = filtered[offset : offset + page_length]

    patient_ids = list({row.patient for row in paged if row.patient})
    patient_query = frappe.get_list if is_manager() else frappe.get_all
    names = {row.name: row for row in patient_query('Patient',
        filters={'name': ['in', patient_ids or ['']]},
        fields=['name', 'first_name', 'last_name'], page_length=len(patient_ids) or 1)}

    app_ids = [row.name for row in paged]
    settlements = current_rows('CC Settlement', {'appointment': ['in', app_ids or ['']]},
                               fields=['appointment', 'mode_of_payment', 'sequence'],
                               order_by='sequence desc') if app_ids else []
    modes = {}
    for s in settlements:
        if s.appointment not in modes:
            modes[s.appointment] = s.mode_of_payment

    for row in paged:
        row.appointment_time = str(get_time(row.appointment_time))
        identity = names.get(row.patient)
        row.patient_first_name = identity.first_name if identity else None
        row.patient_last_name = identity.last_name if identity else None
        row.mode_of_payment = modes.get(row.name) or ''
        c = classify_session(row, now_rome)
        row.cc_classified_future = c['future']
        row.cc_classified_to_close = c['to_close']
        row.cc_classified_unpaid = c['unpaid']

    return {
        'appointments': paged,
        'total': total,
        'page': page,
        'page_length': page_length,
        'total_pages': total_pages,
        'kpi': kpi or 'all',
        'practitioner': practitioner,
        'truncated': False
    }


@frappe.whitelist()
def dashboard(center, start, end):
    require_manager()
    return summary(center, start, end)


def safe_cell(value):
    value = str(value if value is not None else '')
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value


@frappe.whitelist()
def export_csv(center, start, end, practitioner=None, kpi='all'):
    data = sessions(center, start, end, practitioner, kpi, page=1, page_length=0)
    output = StringIO(newline='')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    columns = ['Data', 'Ora', 'Paziente', 'Professionista', 'Servizio', 'Durata (minuti)',
               'Stato seduta', 'Stato economico', 'Pagamento registrato', 'Metodo di pagamento',
               'Prezzo snapshot', 'Valuta']
    writer.writerow(columns)
    economy = {'Due': 'Dovuta', 'Non Due': 'Non dovuta', 'Package Covered': 'Coperta da pacchetto', 'Waived': 'Rinuncia economica'}
    now_rome = _now_rome()
    for row in data['appointments']:
        c = classify_session(row, now_rome)
        if c['paid']:
            payment_status = 'Sì'
        elif c['cancelled']:
            payment_status = 'Non applicabile (annullata)'
        elif c['future']:
            payment_status = 'In programma'
        elif c['unpaid']:
            payment_status = 'No (non pagata)'
        else:
            payment_status = 'Non dovuto'

        status_label = 'Svolta' if c['performed'] else ('Annullata' if c['cancelled'] else ('In programma' if c['future'] else 'Da completare'))
        values = [
            frappe.utils.formatdate(row.get('appointment_date'), 'dd/MM/yyyy') if row.get('appointment_date') else '',
            str(row.get('appointment_time') or '')[:5],
            row.get('patient_name') or '',
            row.get('practitioner_name') or '',
            row.get('cc_service_label') or '',
            row.get('duration') or '',
            status_label,
            economy.get(row.get('cc_economic_state'), row.get('cc_economic_state') or ''),
            payment_status,
            row.get('mode_of_payment') or '',
            row.get('cc_price_snapshot') if row.get('cc_price_snapshot') is not None else '',
            row.get('cc_currency_snapshot') or 'EUR'
        ]
        writer.writerow([safe_cell(value) for value in values])
    active_practitioner = practitioner or data.get('practitioner')
    filename = 'centrochange-report-professionista.csv' if active_practitioner else 'centrochange-report-centro.csv'
    frappe.response.update({
        'type': 'download',
        'filename': filename,
        'filecontent': '\ufeff' + output.getvalue(),
        'content_type': 'text/csv; charset=utf-8'
    })


@frappe.whitelist()
def print_session(appointment):
    from centrochange_core.operations.workspace import APPOINTMENT_FIELDS, require_actor
    require_actor()
    doc = frappe.get_doc('Patient Appointment', appointment)
    doc.check_permission('read')
    import re
    def display_name(value, professional=False):
        match = re.match(r'^CC-HTTP-[A-Za-z0-9]+\s+(.+)$', value or '')
        if not match: return value
        suffix = match.group(1)
        return {'a': 'Alfa', 'b': 'Beta', 'c': 'Gamma'}.get(suffix, suffix) if professional else suffix
    closure = {'Pending': 'Da chiudere', 'Closed': 'Chiusa', 'Auto Locked': 'Bloccata', 'Reopened': 'Riaperta'}
    economy = {'Due': 'Dovuta', 'Non Due': 'Non dovuta', 'Package Covered': 'Coperta da pacchetto', 'Waived': 'Rinuncia economica'}
    rows = [
        ('Paziente', display_name(doc.patient_name)),
        ('Data', frappe.utils.formatdate(doc.appointment_date, 'dd/MM/yyyy')),
        ('Ora', str(doc.appointment_time or '')[:5]),
        ('Professionista', display_name(doc.practitioner_name, True)),
        ('Servizio', display_name(doc.cc_service_label)),
        ('Durata (minuti)', doc.duration),
        ('Stato', closure.get(doc.cc_closure_state, doc.cc_closure_state)),
        ('Economia operativa', economy.get(doc.cc_economic_state, doc.cc_economic_state))
    ]
    body = ''.join('<tr><th>' + escape(label) + '</th><td>' + escape(str(value or '')) + '</td></tr>' for label, value in rows)
    return '<!doctype html><html lang="it"><meta charset="utf-8"><title>Riepilogo seduta</title><link rel="stylesheet" href="/assets/centrochange_core/vendor/tabler-core-1.6.1/tabler.min.css"><link rel="stylesheet" href="/assets/centrochange_core/css/ui_v1.css"><h1>Centro Change — Riepilogo seduta</h1><table class="table table-vcenter">' + body + '</table></html>'
