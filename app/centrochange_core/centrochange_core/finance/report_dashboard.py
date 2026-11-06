"""Scoped operational report; amounts are derived only from receipt allocations."""
import json
import frappe
from centrochange_core.finance.guards import require_finance, require_finance_manager
from centrochange_core.finance.report_operational import summarize
from centrochange_core.operations import reporting
from centrochange_core.security.guards import current_rows

MAX_ROWS = 20000

@frappe.whitelist(methods=['GET'])
def professional(center, start, end, practitioner=None, payment_state='Tutti'):
    require_finance_manager()
    require_finance(center)
    allowed = {'Tutti', 'Saldata', 'Parziale', 'Da incassare', 'Non dovuto', 'Da definire', 'In programma'}
    if payment_state not in allowed:
        frappe.throw('Stato pagamento non valido.')
    first = reporting.sessions(center, start, end, practitioner=practitioner, page=1, page_length=1000)
    if first['total'] > MAX_ROWS:
        frappe.throw('Riduci il periodo: il report supera il limite consentito.')
    period = list(first['appointments'])
    for page in range(2, first['total_pages'] + 1):
        period.extend(reporting.sessions(center, start, end, practitioner=practitioner, page=page, page_length=1000)['appointments'])
    # All receipts, including those for older sessions, are needed to compute
    # cash by receipt date and current balances by appointment date separately.
    receipts = current_rows('CC Operational Receipt', {'center': center}, fields=['patient', 'receipt_date', 'allocations'])
    if len(receipts) > MAX_ROWS:
        frappe.throw('Il registro richiede una ricerca più limitata.')
    by_name = {row['name']: dict(row) for row in period}
    scoped_receipts = []
    for receipt in receipts:
        try:
            entries = json.loads(receipt.allocations)
            if not isinstance(entries, list):
                raise ValueError()
            selected = []
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get('appointment'):
                    raise ValueError()
                name = entry['appointment']
                row = by_name.get(name)
                if row is None:
                    row = frappe.db.get_value('Patient Appointment', name,
                        ['name', 'patient', 'cc_center', 'practitioner', 'cc_price_snapshot', 'cc_currency_snapshot', 'cc_economic_state', 'cc_paid'], as_dict=True)
                if not row or row.get('patient') != receipt.patient or row.get('cc_center') != center:
                    raise ValueError()
                if practitioner and row.get('practitioner') != practitioner:
                    continue
                by_name[name] = dict(row)
                selected.append(entry)
            if selected:
                scoped_receipts.append({'receipt_date': receipt.receipt_date, 'allocations': selected})
        except (TypeError, ValueError, KeyError):
            frappe.throw('Il registro incassi richiede una riconciliazione prima del report.')
    try:
        projection = summarize(list(by_name.values()), scoped_receipts, start, end)
    except (TypeError, ValueError, KeyError):
        frappe.throw('Il registro incassi richiede una riconciliazione prima del report.')
    payments = projection['sessions']
    filtered = []
    for row in period:
        state = payments[row['name']]
        if payment_state == 'Tutti' or state['state'] == payment_state:
            filtered.append({**dict(row), 'operational_payment': state})
    cash = sum(value['period_cash_cents'] for value in payments.values()
               if payment_state == 'Tutti' or value['state'] == payment_state)
    remaining = [row['operational_payment']['remaining_cents'] for row in filtered]
    return {'appointments': filtered, 'total': len(filtered), 'cash_cents': cash,
            'remaining_cents': None if any(value is None for value in remaining) else sum(remaining),
            'payment_state': payment_state, 'start': start, 'end': end}

@frappe.whitelist(methods=['GET'])
def professional_export(center, start, end, practitioner=None, payment_state='Tutti'):
    import csv
    from io import StringIO
    data = professional(center, start, end, practitioner, payment_state)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Data', 'Ora', 'Paziente', 'Professionista', 'Servizio', 'Esito', 'Pagamento', 'Tariffa EUR', 'Residuo EUR'])
    for row in data['appointments']:
        pay = row['operational_payment']
        outcome = 'Svolta' if row.get('cc_performed') else 'Annullata' if row.get('status') == 'Cancelled' else 'Non svolta' if row.get('cc_closure_state') == 'Closed' else 'Esito da registrare' if row.get('cc_classified_to_close') else 'In programma'
        values = [row.get('appointment_date'), row.get('appointment_time'), row.get('patient_name'), row.get('practitioner_name'), row.get('cc_service_label'), outcome, pay['state'], row.get('cc_price_snapshot'), '' if pay['remaining_cents'] is None else f"{pay['remaining_cents'] / 100:.2f}"]
        writer.writerow([reporting.safe_cell(value) for value in values])
    frappe.response.update({'type': 'download', 'filename': 'report-professionista.csv', 'filecontent': output.getvalue(), 'content_type': 'text/csv; charset=utf-8'})
