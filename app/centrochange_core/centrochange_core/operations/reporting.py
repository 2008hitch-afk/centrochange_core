"""Operational reports use scoped projections; management totals contain no note bodies."""
import csv
from io import StringIO
from html import escape
from collections import defaultdict
from datetime import timedelta
import frappe
from frappe.utils import getdate, get_time, cint
from centrochange_core.security.guards import (
    require_manager, require_center, roles, practitioner_for, is_manager, current_rows
)
from centrochange_core.operations.workspace import require_actor, APPOINTMENT_FIELDS


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


def _matches_kpi(row, kpi, today):
    if not kpi or kpi == 'all':
        return True
    if kpi == 'performed':
        return bool(row.cc_performed)
    if kpi == 'cancelled':
        return row.status == 'Cancelled'
    if kpi == 'future':
        return row.status not in ('Cancelled', 'Closed') and not row.cc_performed and getdate(row.appointment_date) >= today
    if kpi == 'to_close':
        return row.status != 'Cancelled' and not row.cc_performed and getdate(row.appointment_date) <= today
    if kpi == 'operational_paid':
        return bool(row.cc_paid)
    if kpi == 'operational_unpaid':
        return (not row.cc_paid and (bool(row.cc_performed) or row.cc_closure_state in ('Closed', 'Auto Locked'))
                and row.status != 'Cancelled' and row.cc_economic_state != 'Non Due')
    if kpi == 'due':
        return row.cc_economic_state == 'Due'
    return True


@frappe.whitelist()
def summary(center, start, end, practitioner=None):
    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    rows = frappe.get_list('Patient Appointment', filters=filters, fields=APPOINTMENT_FIELDS,
                           order_by='appointment_date,appointment_time,name', page_length=0)
    totals = defaultdict(lambda: {
        'sessions': 0, 'performed': 0, 'cancelled': 0, 'future': 0, 'to_close': 0,
        'operational_paid': 0, 'operational_unpaid': 0, 'due': 0, 'due_snapshot_amount': 0
    })
    today = getdate(frappe.utils.today())
    for row in rows:
        bucket = totals[row.cc_currency_snapshot or 'UNSET']
        bucket['sessions'] += 1
        if row.cc_performed:
            bucket['performed'] += 1
        if row.status == 'Cancelled':
            bucket['cancelled'] += 1
        if row.status not in ('Cancelled', 'Closed') and not row.cc_performed and getdate(row.appointment_date) >= today:
            bucket['future'] += 1
        if row.status != 'Cancelled' and not row.cc_performed and getdate(row.appointment_date) <= today:
            bucket['to_close'] += 1
        if row.cc_paid:
            bucket['operational_paid'] += 1
        if not row.cc_paid and (bool(row.cc_performed) or row.cc_closure_state in ('Closed', 'Auto Locked')) and row.status != 'Cancelled' and row.cc_economic_state != 'Non Due':
            bucket['operational_unpaid'] += 1
        if row.cc_economic_state == 'Due':
            bucket['due'] += 1
            bucket['due_snapshot_amount'] += (row.cc_price_snapshot or 0)
    return {
        'currencies': dict(totals),
        'practitioner': practitioner,
        'total_appointments': len(rows),
        'truncated': False
    }


@frappe.whitelist()
def sessions(center, start, end, practitioner=None, kpi='all'):
    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    rows = frappe.get_list('Patient Appointment', filters=filters, fields=APPOINTMENT_FIELDS,
                           order_by='appointment_date,appointment_time,name', page_length=0)
    today = getdate(frappe.utils.today())
    filtered = [row for row in rows if _matches_kpi(row, kpi, today)]

    patient_ids = list({row.patient for row in filtered if row.patient})
    patient_query = frappe.get_list if is_manager() else frappe.get_all
    names = {row.name: row for row in patient_query('Patient',
        filters={'name': ['in', patient_ids or ['']]},
        fields=['name', 'first_name', 'last_name'], page_length=len(patient_ids) or 1)}

    app_ids = [row.name for row in filtered]
    settlements = current_rows('CC Settlement', {'appointment': ['in', app_ids or ['']]},
                               fields=['appointment', 'mode_of_payment', 'sequence'],
                               order_by='sequence desc') if app_ids else []
    modes = {}
    for s in settlements:
        if s.appointment not in modes:
            modes[s.appointment] = s.mode_of_payment

    for row in filtered:
        row.appointment_time = str(get_time(row.appointment_time))
        identity = names.get(row.patient)
        row.patient_first_name = identity.first_name if identity else None
        row.patient_last_name = identity.last_name if identity else None
        row.mode_of_payment = modes.get(row.name) or ''

    return {
        'appointments': filtered,
        'total': len(filtered),
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
    data = sessions(center, start, end, practitioner, kpi)
    output = StringIO(newline='')
    writer = csv.writer(output)
    columns = ['Data', 'Ora', 'Paziente', 'Professionista', 'Servizio', 'Durata (minuti)',
               'Stato seduta', 'Stato economico', 'Pagamento registrato', 'Metodo di pagamento',
               'Prezzo snapshot', 'Valuta']
    writer.writerow(columns)
    closure = {'Pending': 'Da chiudere', 'Closed': 'Chiusa', 'Auto Locked': 'Bloccata', 'Reopened': 'Riaperta'}
    economy = {'Due': 'Dovuta', 'Non Due': 'Non dovuta', 'Package Covered': 'Coperta da pacchetto', 'Waived': 'Rinuncia economica'}
    for row in data['appointments']:
        values = [
            frappe.utils.formatdate(row.get('appointment_date'), 'dd/MM/yyyy') if row.get('appointment_date') else '',
            str(row.get('appointment_time') or '')[:5],
            row.get('patient_name') or '',
            row.get('practitioner_name') or '',
            row.get('cc_service_label') or '',
            row.get('duration') or '',
            closure.get(row.get('cc_closure_state'), row.get('cc_closure_state') or ''),
            economy.get(row.get('cc_economic_state'), row.get('cc_economic_state') or ''),
            'Sì' if row.get('cc_paid') else 'No',
            row.get('mode_of_payment') or '',
            row.get('cc_price_snapshot') if row.get('cc_price_snapshot') is not None else '',
            row.get('cc_currency_snapshot') or 'EUR'
        ]
        writer.writerow([safe_cell(value) for value in values])
    filename = f"centrochange-report-{practitioner or 'centro'}.csv"
    frappe.response.update({
        'type': 'download',
        'filename': filename,
        'filecontent': output.getvalue(),
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
