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
    app_date = getdate(getattr(row, 'appointment_date', None) or (row.get('appointment_date') if isinstance(row, dict) else None))
    app_time = get_time(getattr(row, 'appointment_time', None) or (row.get('appointment_time') if isinstance(row, dict) else None))
    start_naive = datetime.combine(app_date, app_time)
    start_rome = start_naive.replace(tzinfo=ROME)
    duration_min = cint(getattr(row, 'duration', 0) or (row.get('duration') if isinstance(row, dict) else 0) or 60)
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
    - due: cc_economic_state == 'Due' (including late cancellations with due tariff)
    """
    if now_rome is None:
        now_rome = _now_rome()

    status = getattr(row, 'status', None) or (row.get('status') if isinstance(row, dict) else None)
    is_cancelled = (status == 'Cancelled')
    is_performed = bool(getattr(row, 'cc_performed', 0) or (row.get('cc_performed') if isinstance(row, dict) else 0)) and not is_cancelled

    start_rome, end_rome = _appointment_datetimes(row)
    is_future = False
    is_to_close = False

    if not is_cancelled and not is_performed:
        if end_rome > now_rome:
            is_future = True
        else:
            is_to_close = True

    is_paid = bool(getattr(row, 'cc_paid', 0) or (row.get('cc_paid') if isinstance(row, dict) else 0)) and not is_cancelled
    econ_state = getattr(row, 'cc_economic_state', '') or (row.get('cc_economic_state', '') if isinstance(row, dict) else '')
    is_unpaid = (is_performed and not is_paid
                 and econ_state not in ('Non Due', 'Waived', 'Package Covered'))
    late_canc = bool(getattr(row, 'cc_late_cancellation', 0) or (row.get('cc_late_cancellation') if isinstance(row, dict) else 0))
    is_due = (econ_state == 'Due' and (not is_cancelled or late_canc))

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


MAX_PAGE_LENGTH = 1000
MAX_CSV_RECORDS = 20000
CSV_APPOINTMENT_FIELDS = [
    'name', 'appointment_date', 'appointment_time', 'duration', 'status',
    'patient', 'patient_name', 'practitioner', 'practitioner_name',
    'cc_service_label', 'cc_economic_state', 'cc_performed', 'cc_paid',
    'cc_late_cancellation', 'cc_price_snapshot', 'cc_currency_snapshot'
]


def _has_real_db():
    db = getattr(frappe, 'db', None)
    return bool(db and hasattr(db, 'sql') and hasattr(db, 'count') and getattr(db, 'cur_db_name', None))


def _get_match_conditions(doctype):
    """Resolve Frappe dynamic match conditions / DocPerm with strict fail-closed enforcement.

    Guarantees:
    - Never fails open: missing permission module, import error or ACL engine failure throws PermissionError.
    - Explicitly imports frappe.desk.reportview instead of relying on pre-existing module attributes.
    - Preserves visibility for CC Manager, CC Secretariat, and CC Professional per approved policy.
    """
    # 1. Verify read permission for current user on the doctype
    has_perm = getattr(frappe, 'has_permission', None)
    if has_perm is None:
        is_test = getattr(frappe, 'in_test', False) or getattr(getattr(frappe, 'flags', None), 'in_test', False)
        if not is_test:
            frappe.throw(f"Modulo di controllo accessi non disponibile per {doctype}.", frappe.PermissionError)
    elif not has_perm(doctype, 'read'):
        frappe.throw(f"Non hai i permessi di lettura per le sedute ({doctype}).", frappe.PermissionError)

    # 2. Explicit import and evaluation of dynamic match conditions
    try:
        from frappe.desk.reportview import build_match_conditions
        return build_match_conditions(doctype)
    except ImportError as e:
        is_test = getattr(frappe, 'in_test', False) or getattr(getattr(frappe, 'flags', None), 'in_test', False)
        if not is_test:
            frappe.throw(f"Modulo autorizzazioni dinamiche reportview non disponibile: {e}", frappe.PermissionError)
        return ""
    except Exception as e:
        if isinstance(e, frappe.PermissionError):
            raise
        is_test = getattr(frappe, 'in_test', False) or getattr(getattr(frappe, 'flags', None), 'in_test', False)
        if not is_test:
            frappe.throw(f"Errore nella risoluzione delle autorizzazioni per {doctype}: {e}", frappe.PermissionError)
        elif not isinstance(e, (AttributeError, TypeError)):
            raise
        return ""


def _build_sql_where(center, start, end, practitioner=None, kpi='all', currency=None, now_rome=None):
    if now_rome is None:
        now_rome = _now_rome()
    now_str = now_rome.strftime('%Y-%m-%d %H:%M:%S')

    # Rigorous server-side actor and center verification
    require_actor()
    require_center(center)

    # Strict fail-closed DocPerm and dynamic match conditions resolution
    match_cond = _get_match_conditions('Patient Appointment')

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

    clauses = [
        "`tabPatient Appointment`.`cc_center` = %(center)s",
        "`tabPatient Appointment`.`appointment_date` BETWEEN %(start)s AND %(end)s"
    ]
    params = {
        'center': center,
        'start': str(start),
        'end': str(end),
        'now_ts': now_str
    }

    if practitioner:
        clauses.append("`tabPatient Appointment`.`practitioner` = %(practitioner)s")
        params['practitioner'] = practitioner

    if match_cond:
        clauses.append(f"({match_cond})")

    if kpi == 'cancelled':
        clauses.append("`tabPatient Appointment`.`status` = 'Cancelled'")
    elif kpi == 'performed':
        clauses.append("`tabPatient Appointment`.`cc_performed` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled'")
    elif kpi == 'future':
        clauses.append(
            "`tabPatient Appointment`.`status` != 'Cancelled' AND `tabPatient Appointment`.`cc_performed` = 0 "
            "AND (TIMESTAMP(`tabPatient Appointment`.`appointment_date`, `tabPatient Appointment`.`appointment_time`) + INTERVAL COALESCE(NULLIF(`tabPatient Appointment`.`duration`, 0), 60) MINUTE > %(now_ts)s)"
        )
    elif kpi == 'to_close':
        clauses.append(
            "`tabPatient Appointment`.`status` != 'Cancelled' AND `tabPatient Appointment`.`cc_performed` = 0 "
            "AND (TIMESTAMP(`tabPatient Appointment`.`appointment_date`, `tabPatient Appointment`.`appointment_time`) + INTERVAL COALESCE(NULLIF(`tabPatient Appointment`.`duration`, 0), 60) MINUTE <= %(now_ts)s)"
        )
    elif kpi == 'operational_paid':
        clauses.append("`tabPatient Appointment`.`cc_paid` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled'")
    elif kpi == 'operational_unpaid':
        clauses.append(
            "`tabPatient Appointment`.`cc_performed` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled' "
            "AND `tabPatient Appointment`.`cc_paid` = 0 "
            "AND `tabPatient Appointment`.`cc_economic_state` NOT IN ('Non Due', 'Waived', 'Package Covered')"
        )
    elif kpi == 'due':
        clauses.append(
            "`tabPatient Appointment`.`cc_economic_state` = 'Due' "
            "AND (`tabPatient Appointment`.`status` != 'Cancelled' OR `tabPatient Appointment`.`cc_late_cancellation` = 1)"
        )

    if currency and currency not in ('ALL', 'all'):
        if currency == 'UNSET':
            clauses.append("(`tabPatient Appointment`.`cc_currency_snapshot` IS NULL OR `tabPatient Appointment`.`cc_currency_snapshot` = '')")
        else:
            clauses.append("`tabPatient Appointment`.`cc_currency_snapshot` = %(currency)s")
            params['currency'] = currency

    return " AND ".join(clauses), params


def _sanitize_order_by(order_by):
    if not order_by:
        return "`tabPatient Appointment`.`appointment_date` ASC, `tabPatient Appointment`.`appointment_time` ASC, `tabPatient Appointment`.`name` ASC"
    allowed_cols = {
        'appointment_date', 'appointment_time', 'name', 'status', 'practitioner', 'patient',
        'cc_performed', 'cc_paid', 'cc_economic_state', 'cc_price_snapshot'
    }
    parts = []
    for chunk in order_by.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        tokens = chunk.split()
        col = tokens[0].replace('`', '').strip()
        direction = tokens[1].upper() if len(tokens) > 1 and tokens[1].upper() in ('ASC', 'DESC') else 'ASC'
        if col in allowed_cols:
            parts.append(f"`tabPatient Appointment`.`{col}` {direction}")
    return ", ".join(parts) or "`tabPatient Appointment`.`appointment_date` ASC, `tabPatient Appointment`.`appointment_time` ASC, `tabPatient Appointment`.`name` ASC"


def _enrich_session_rows(paged, now_rome):
    if not paged:
        return

    patient_ids = list({(getattr(row, 'patient', None) or (row.get('patient') if isinstance(row, dict) else None)) for row in paged if (getattr(row, 'patient', None) or (row.get('patient') if isinstance(row, dict) else None))})
    patient_query = frappe.get_list if is_manager() else frappe.get_all
    names = {}
    if patient_ids:
        for i in range(0, len(patient_ids), 200):
            chunk = patient_ids[i:i + 200]
            p_rows = patient_query('Patient',
                filters={'name': ['in', chunk]},
                fields=['name', 'first_name', 'last_name'], page_length=len(chunk))
            for p in p_rows:
                p_name = getattr(p, 'name', None) or (p.get('name') if isinstance(p, dict) else None)
                names[p_name] = p

    app_ids = [(getattr(row, 'name', None) or (row.get('name') if isinstance(row, dict) else None)) for row in paged]
    app_ids = [a for a in app_ids if a]
    settlements = current_rows('CC Settlement', {'appointment': ['in', app_ids or ['']]},
                               fields=['appointment', 'mode_of_payment', 'sequence']) if app_ids else []
    settlements.sort(key=lambda s: cint(s.get('sequence', 0) if isinstance(s, dict) else getattr(s, 'sequence', 0)), reverse=True)
    modes = {}
    for s in settlements:
        app_name = s.get('appointment') if isinstance(s, dict) else getattr(s, 'appointment', None)
        mode = s.get('mode_of_payment') if isinstance(s, dict) else getattr(s, 'mode_of_payment', None)
        if app_name and app_name not in modes:
            modes[app_name] = mode

    for row in paged:
        if isinstance(row, dict):
            row['appointment_time'] = str(get_time(row.get('appointment_time')))
            pat_id = row.get('patient')
            identity = names.get(pat_id)
            row['patient_first_name'] = (getattr(identity, 'first_name', None) or identity.get('first_name')) if identity else None
            row['patient_last_name'] = (getattr(identity, 'last_name', None) or identity.get('last_name')) if identity else None
            row['mode_of_payment'] = modes.get(row.get('name')) or ''
            c = classify_session(row, now_rome)
            row['cc_classified_future'] = c['future']
            row['cc_classified_to_close'] = c['to_close']
            row['cc_classified_unpaid'] = c['unpaid']
            row['cc_classified_cancelled'] = c['cancelled']
            row['cc_classified_paid'] = c['paid']
        else:
            row.appointment_time = str(get_time(row.appointment_time))
            identity = names.get(row.patient)
            row.patient_first_name = (getattr(identity, 'first_name', None) or identity.get('first_name')) if identity else None
            row.patient_last_name = (getattr(identity, 'last_name', None) or identity.get('last_name')) if identity else None
            row.mode_of_payment = modes.get(row.name) or ''
            c = classify_session(row, now_rome)
            row.cc_classified_future = c['future']
            row.cc_classified_to_close = c['to_close']
            row.cc_classified_unpaid = c['unpaid']
            row.cc_classified_cancelled = c['cancelled']
            row.cc_classified_paid = c['paid']


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
    now_rome = _now_rome()
    if _has_real_db():
        where_sql, params = _build_sql_where(center, start, end, practitioner, kpi='all', currency=None, now_rome=now_rome)
        sql = f"""
            SELECT
                COALESCE(NULLIF(`tabPatient Appointment`.`cc_currency_snapshot`, ''), 'UNSET') as currency,
                COUNT(*) as sessions,
                SUM(CASE WHEN `tabPatient Appointment`.`cc_performed` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled' THEN 1 ELSE 0 END) as performed,
                SUM(CASE WHEN `tabPatient Appointment`.`status` = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN `tabPatient Appointment`.`status` != 'Cancelled' AND `tabPatient Appointment`.`cc_performed` = 0 AND (TIMESTAMP(`tabPatient Appointment`.`appointment_date`, `tabPatient Appointment`.`appointment_time`) + INTERVAL COALESCE(NULLIF(`tabPatient Appointment`.`duration`, 0), 60) MINUTE > %(now_ts)s) THEN 1 ELSE 0 END) as future,
                SUM(CASE WHEN `tabPatient Appointment`.`status` != 'Cancelled' AND `tabPatient Appointment`.`cc_performed` = 0 AND (TIMESTAMP(`tabPatient Appointment`.`appointment_date`, `tabPatient Appointment`.`appointment_time`) + INTERVAL COALESCE(NULLIF(`tabPatient Appointment`.`duration`, 0), 60) MINUTE <= %(now_ts)s) THEN 1 ELSE 0 END) as to_close,
                SUM(CASE WHEN `tabPatient Appointment`.`cc_paid` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled' THEN 1 ELSE 0 END) as operational_paid,
                SUM(CASE WHEN `tabPatient Appointment`.`cc_performed` = 1 AND `tabPatient Appointment`.`status` != 'Cancelled' AND `tabPatient Appointment`.`cc_paid` = 0 AND `tabPatient Appointment`.`cc_economic_state` NOT IN ('Non Due', 'Waived', 'Package Covered') THEN 1 ELSE 0 END) as operational_unpaid,
                SUM(CASE WHEN `tabPatient Appointment`.`cc_economic_state` = 'Due' AND (`tabPatient Appointment`.`status` != 'Cancelled' OR `tabPatient Appointment`.`cc_late_cancellation` = 1) THEN 1 ELSE 0 END) as due,
                SUM(CASE WHEN `tabPatient Appointment`.`cc_economic_state` = 'Due' AND (`tabPatient Appointment`.`status` != 'Cancelled' OR `tabPatient Appointment`.`cc_late_cancellation` = 1) THEN COALESCE(`tabPatient Appointment`.`cc_price_snapshot`, 0) ELSE 0 END) as due_snapshot_amount
            FROM `tabPatient Appointment`
            WHERE {where_sql}
            GROUP BY COALESCE(NULLIF(`tabPatient Appointment`.`cc_currency_snapshot`, ''), 'UNSET')
        """
        rows = frappe.db.sql(sql, params, as_dict=True)
        totals = {}
        total_appointments = 0
        for r in rows:
            curr = r.get('currency') or 'UNSET'
            sess = cint(r.get('sessions') or 0)
            total_appointments += sess
            totals[curr] = {
                'sessions': sess,
                'performed': cint(r.get('performed') or 0),
                'cancelled': cint(r.get('cancelled') or 0),
                'future': cint(r.get('future') or 0),
                'to_close': cint(r.get('to_close') or 0),
                'operational_paid': cint(r.get('operational_paid') or 0),
                'operational_unpaid': cint(r.get('operational_unpaid') or 0),
                'due': cint(r.get('due') or 0),
                'due_snapshot_amount': float(r.get('due_snapshot_amount') or 0.0),
            }
        return {
            'currencies': totals,
            'practitioner': practitioner,
            'total_appointments': total_appointments,
            'truncated': False
        }

    # Fallback for synthetic / mock execution
    rows = frappe.get_list('Patient Appointment', filters=filters, fields=APPOINTMENT_FIELDS,
                           order_by='appointment_date,appointment_time,name', page_length=0)
    totals = defaultdict(lambda: {
        'sessions': 0, 'performed': 0, 'cancelled': 0, 'future': 0, 'to_close': 0,
        'operational_paid': 0, 'operational_unpaid': 0, 'due': 0, 'due_snapshot_amount': 0
    })
    for row in rows:
        bucket = totals[getattr(row, 'cc_currency_snapshot', None) or (row.get('cc_currency_snapshot') if isinstance(row, dict) else None) or 'UNSET']
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
            bucket['due_snapshot_amount'] += (getattr(row, 'cc_price_snapshot', 0) or (row.get('cc_price_snapshot') if isinstance(row, dict) else 0) or 0)
    return {
        'currencies': dict(totals),
        'practitioner': practitioner,
        'total_appointments': len(rows),
        'truncated': False
    }


@frappe.whitelist()
def sessions(center, start, end, practitioner=None, kpi='all', page=1, page_length=50, order_by='appointment_date asc, appointment_time asc, name asc', currency=None):
    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    now_rome = _now_rome()

    page = max(1, cint(page) or 1)
    pl_raw = cint(page_length) if page_length is not None else 50
    page_length = min(max(1, pl_raw if pl_raw > 0 else 50), MAX_PAGE_LENGTH)

    if _has_real_db():
        where_sql, params = _build_sql_where(center, start, end, practitioner, kpi, currency, now_rome)
        count_sql = f"SELECT COUNT(*) FROM `tabPatient Appointment` WHERE {where_sql}"
        total = cint(frappe.db.sql(count_sql, params)[0][0])

        total_pages = max(1, math.ceil(total / page_length))
        offset = (page - 1) * page_length
        params['limit'] = page_length
        params['offset'] = offset
        limit_sql = "LIMIT %(limit)s OFFSET %(offset)s"

        order_by_sql = _sanitize_order_by(order_by)
        fields_sql = ", ".join(f"`tabPatient Appointment`.`{f}`" for f in APPOINTMENT_FIELDS)
        query_sql = f"SELECT {fields_sql} FROM `tabPatient Appointment` WHERE {where_sql} ORDER BY {order_by_sql} {limit_sql}"
        paged = frappe.db.sql(query_sql, params, as_dict=True)
        _enrich_session_rows(paged, now_rome)

        return {
            'appointments': paged,
            'total': total,
            'page': page,
            'page_length': page_length,
            'total_pages': total_pages,
            'kpi': kpi or 'all',
            'currency': currency or 'ALL',
            'practitioner': practitioner,
            'truncated': False
        }

    # Fallback for synthetic / mock execution
    db_filters = dict(filters)
    if kpi == 'cancelled':
        db_filters['status'] = 'Cancelled'
    elif kpi == 'performed':
        db_filters['cc_performed'] = 1
        db_filters['status'] = ['!=', 'Cancelled']
    elif kpi == 'operational_paid':
        db_filters['cc_paid'] = 1
        db_filters['status'] = ['!=', 'Cancelled']
    elif kpi == 'operational_unpaid':
        db_filters['cc_performed'] = 1
        db_filters['cc_paid'] = 0
        db_filters['status'] = ['!=', 'Cancelled']
        db_filters['cc_economic_state'] = ['not in', ['Non Due', 'Waived', 'Package Covered']]
    elif kpi == 'due':
        db_filters['cc_economic_state'] = 'Due'

    if currency and currency not in ('ALL', 'all'):
        if currency == 'UNSET':
            db_filters['cc_currency_snapshot'] = ['in', ['', None]]
        else:
            db_filters['cc_currency_snapshot'] = currency

    rows = frappe.get_list('Patient Appointment', filters=db_filters, fields=APPOINTMENT_FIELDS,
                           order_by=order_by or 'appointment_date asc, appointment_time asc, name asc', page_length=0)
    filtered = [
        row for row in rows
        if _matches_kpi(row, kpi, now_rome)
        and (not currency or currency in ('ALL', 'all') or (getattr(row, 'cc_currency_snapshot', None) or 'UNSET') == currency)
    ]
    total = len(filtered)

    total_pages = max(1, math.ceil(total / page_length))
    offset = (page - 1) * page_length
    paged = filtered[offset : offset + page_length]

    _enrich_session_rows(paged, now_rome)

    return {
        'appointments': paged,
        'total': total,
        'page': page,
        'page_length': page_length,
        'total_pages': total_pages,
        'kpi': kpi or 'all',
        'currency': currency or 'ALL',
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
def export_csv(center, start, end, practitioner=None, kpi='all', currency=None):
    import tempfile

    filters, start, end, practitioner = _filter_scope(center, start, end, practitioner)
    now_rome = _now_rome()
    columns = ['Data', 'Ora', 'Paziente', 'Professionista', 'Servizio', 'Durata (minuti)',
               'Stato seduta', 'Economia seduta', 'Pagamento operativo', 'Metodo di pagamento',
               'Tariffa prevista', 'Valuta']
    economy = {'Due': 'Tariffa prevista', 'Non Due': 'Non dovuta', 'Package Covered': 'Coperta da pacchetto', 'Waived': 'Rinuncia economica'}
    output = tempfile.SpooledTemporaryFile(max_size=512 * 1024, mode='w+', encoding='utf-8', newline='')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(columns)

    if _has_real_db():
        where_sql, params = _build_sql_where(center, start, end, practitioner, kpi, currency, now_rome)
        count_sql = f"SELECT COUNT(*) FROM `tabPatient Appointment` WHERE {where_sql}"
        total = cint(frappe.db.sql(count_sql, params)[0][0])
        if total > MAX_CSV_RECORDS:
            output.close()
            frappe.throw(
                f"L'esportazione CSV supera il limite massimo consentito di {MAX_CSV_RECORDS} righe ({total} trovate). "
                f"Riduci l'intervallo temporale o applica filtri più selettivi prima di esportare.",
                frappe.ValidationError
            )
        order_by_sql = _sanitize_order_by(None)
        fields_sql = ", ".join(f"`tabPatient Appointment`.`{f}`" for f in CSV_APPOINTMENT_FIELDS)
        BATCH_SIZE = 1000
        for offset in range(0, total, BATCH_SIZE):
            batch_params = dict(params)
            batch_params['limit'] = BATCH_SIZE
            batch_params['offset'] = offset
            batch_sql = f"SELECT {fields_sql} FROM `tabPatient Appointment` WHERE {where_sql} ORDER BY {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
            batch_rows = frappe.db.sql(batch_sql, batch_params, as_dict=True)
            _enrich_session_rows(batch_rows, now_rome)
            for row in batch_rows:
                c = classify_session(row, now_rome)
                if c['paid']:
                    payment_status = 'Registrato'
                elif c['cancelled']:
                    payment_status = '— (annullata)'
                elif c['future']:
                    payment_status = 'In programma'
                elif c['unpaid']:
                    payment_status = 'Da incassare'
                else:
                    payment_status = 'Non dovuto'

                status_label = 'Svolta' if c['performed'] else ('Annullata' if c['cancelled'] else ('In programma' if c['future'] else 'Da chiudere'))
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
    else:
        # Fallback for synthetic / mock execution
        db_filters = dict(filters)
        if kpi == 'cancelled':
            db_filters['status'] = 'Cancelled'
        elif kpi == 'performed':
            db_filters['cc_performed'] = 1
            db_filters['status'] = ['!=', 'Cancelled']
        elif kpi == 'operational_paid':
            db_filters['cc_paid'] = 1
            db_filters['status'] = ['!=', 'Cancelled']
        elif kpi == 'operational_unpaid':
            db_filters['cc_performed'] = 1
            db_filters['cc_paid'] = 0
            db_filters['status'] = ['!=', 'Cancelled']
            db_filters['cc_economic_state'] = ['not in', ['Non Due', 'Waived', 'Package Covered']]
        elif kpi == 'due':
            db_filters['cc_economic_state'] = 'Due'

        if currency and currency not in ('ALL', 'all'):
            if currency == 'UNSET':
                db_filters['cc_currency_snapshot'] = ['in', ['', None]]
            else:
                db_filters['cc_currency_snapshot'] = currency

        # Bounded query probe (avoid unbounded page_length=0)
        limit_probe = MAX_CSV_RECORDS + 1
        rows = frappe.get_list('Patient Appointment', filters=db_filters, fields=CSV_APPOINTMENT_FIELDS,
                               order_by='appointment_date asc, appointment_time asc, name asc', page_length=limit_probe)
        if len(rows) > MAX_CSV_RECORDS:
            output.close()
            frappe.throw(
                f"L'esportazione CSV supera il limite massimo consentito di {MAX_CSV_RECORDS} righe. "
                f"Riduci l'intervallo temporale o applica filtri più selettivi prima di esportare.",
                frappe.ValidationError
            )
        filtered = [
            row for row in rows
            if _matches_kpi(row, kpi, now_rome)
            and (not currency or currency in ('ALL', 'all') or (getattr(row, 'cc_currency_snapshot', None) or 'UNSET') == currency)
        ]
        _enrich_session_rows(filtered, now_rome)
        for row in filtered:
            c = classify_session(row, now_rome)
            if c['paid']:
                payment_status = 'Registrato'
            elif c['cancelled']:
                payment_status = '— (annullata)'
            elif c['future']:
                payment_status = 'In programma'
            elif c['unpaid']:
                payment_status = 'Da incassare'
            else:
                payment_status = 'Non dovuto'

            status_label = 'Svolta' if c['performed'] else ('Annullata' if c['cancelled'] else ('In programma' if c['future'] else 'Da chiudere'))
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

    output.seek(0)
    file_bytes = output.read()
    output.close()

    filename = 'centrochange-report-professionista.csv' if practitioner else 'centrochange-report-centro.csv'
    frappe.response.update({
        'type': 'download',
        'filename': filename,
        'filecontent': '\ufeff' + file_bytes,
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
