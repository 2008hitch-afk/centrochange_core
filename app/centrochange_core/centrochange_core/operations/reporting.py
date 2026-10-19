"""Operational reports use scoped projections; management totals contain no note bodies."""
import csv
from io import StringIO
from html import escape
from collections import defaultdict
import frappe
from centrochange_core.security.guards import require_manager
from centrochange_core.operations.workspace import agenda


@frappe.whitelist()
def summary(center,start,end):
    data=agenda(center,start,end)
    totals=defaultdict(lambda:{'sessions':0,'due':0,'performed':0,'operational_paid':0,'due_snapshot_amount':0})
    for row in data['appointments']:
        bucket=totals[row.cc_currency_snapshot or 'UNSET']
        bucket['sessions']+=1
        bucket['performed']+=int(bool(row.cc_performed))
        bucket['operational_paid']+=int(bool(row.cc_paid))
        if row.cc_economic_state=='Due':
            bucket['due']+=1
            bucket['due_snapshot_amount']+=row.cc_price_snapshot or 0
    return {'currencies':dict(totals),'truncated':data['truncated']}


@frappe.whitelist()
def dashboard(center,start,end):
    require_manager()
    # Explicit aggregate-only endpoint. No Patient/notes/body/customer contact joins.
    return summary(center,start,end)


def safe_cell(value):
    value=str(value if value is not None else '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r','\n')) else value


@frappe.whitelist()
def export_csv(center,start,end):
    data=agenda(center,start,end)
    if data['truncated']:
        frappe.throw('Riduci l’intervallo prima di esportare: i risultati non vengono omessi senza avviso.')
    fields=['appointment_date','appointment_time','patient_name','practitioner_name','cc_service_label','duration',
        'cc_closure_state','cc_economic_state','cc_paid','cc_price_snapshot','cc_currency_snapshot']
    columns=['Data','Ora','Paziente','Professionista','Servizio','Durata (minuti)',
        'Stato seduta','Stato economico','Pagamento registrato','Prezzo snapshot','Valuta']
    output=StringIO(newline='')
    writer=csv.writer(output)
    writer.writerow(columns)
    for row in data['appointments']:
        values=[row.get(field) for field in fields]
        values[0]=frappe.utils.formatdate(values[0],'dd/MM/yyyy') if values[0] else ''
        values[1]=str(values[1])[:5] if values[1] else ''
        writer.writerow([safe_cell(value) for value in values])
    frappe.response.update({'type':'download','filename':'centrochange-agenda.csv','filecontent':output.getvalue(),
        'content_type':'text/csv; charset=utf-8'})


@frappe.whitelist()
def print_session(appointment):
    from centrochange_core.operations.workspace import APPOINTMENT_FIELDS,require_actor
    require_actor()
    doc=frappe.get_doc('Patient Appointment',appointment)
    doc.check_permission('read')
    # Presentation only; native read guard/document facts above remain canonical.
    import re
    def display_name(value, professional=False):
        match=re.match(r'^CC-HTTP-[A-Za-z0-9]+\s+(.+)$',value or '')
        if not match:return value
        suffix=match.group(1)
        return {'a':'Alfa','b':'Beta','c':'Gamma'}.get(suffix,suffix) if professional else suffix
    closure={'Pending':'Da chiudere','Closed':'Chiusa','Auto Locked':'Bloccata','Reopened':'Riaperta'}
    economy={'Due':'Dovuta','Non Due':'Non dovuta','Package Covered':'Coperta da pacchetto','Waived':'Rinuncia economica'}
    rows=[('Paziente',display_name(doc.patient_name)),('Data',frappe.utils.formatdate(doc.appointment_date,'dd/MM/yyyy')),('Ora',doc.appointment_time),
        ('Professionista',display_name(doc.practitioner_name,True)),('Servizio',display_name(doc.cc_service_label)),('Durata (minuti)',doc.duration),
        ('Stato',closure.get(doc.cc_closure_state,doc.cc_closure_state)),('Economia operativa',economy.get(doc.cc_economic_state,doc.cc_economic_state))]
    body=''.join('<tr><th>'+escape(label)+'</th><td>'+escape(str(value or ''))+'</td></tr>' for label,value in rows)
    return '<!doctype html><html lang="it"><meta charset="utf-8"><title>Riepilogo seduta</title><link rel="stylesheet" href="/assets/centrochange_core/vendor/tabler-core-1.6.1/tabler.min.css"><link rel="stylesheet" href="/assets/centrochange_core/css/ui_v1.css"><h1>Centro Change — Riepilogo seduta</h1><table class="table table-vcenter">'+body+'</table></html>'
