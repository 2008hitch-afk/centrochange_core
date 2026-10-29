"""Center-scoped, compact Italian preview of confirmed native finance documents."""
from decimal import Decimal
from html import escape

import frappe
from frappe.utils import getdate

from centrochange_core.finance.guards import require_finance
from centrochange_core.scoped_api import bounded

PRINTABLE = ('Sales Invoice', 'Purchase Invoice', 'Payment Entry')
FORMAT = 'Centro Change'


def _date(value):
    return getdate(value).strftime('%d/%m/%Y') if value else '—'


def _money(value, currency='EUR'):
    amount = Decimal(str(value or 0)).quantize(Decimal('0.01'))
    integer, decimals = f'{amount:,.2f}'.split('.')
    return f'{integer.replace(",", ".")},{decimals} {escape(str(currency or "EUR"))}'


def _party(doc):
    """Use an existing, exact UAT alias when present; never print fixture IDs."""
    kind = 'Customer' if doc.doctype == 'Sales Invoice' or doc.get('party_type') == 'Customer' else 'Supplier'
    identifier = doc.get('customer') if doc.doctype == 'Sales Invoice' else doc.get('supplier') if doc.doctype == 'Purchase Invoice' else doc.get('party')
    if frappe.conf.get('cc_synthetic_dev') == 1 and frappe.conf.get('cc_uat_demo') == 1:
        from centrochange_core.uat.display import _manifest
        manifest = _manifest()
        if manifest:
            if kind == 'Customer':
                owners = [frappe.db.get_value('Patient', name, 'customer') for name in manifest['fixture']['patients']]
                if identifier in owners:
                    return f'Cliente {owners.index(identifier) + 1}'
            else:
                owners = [frappe.db.get_value('Healthcare Practitioner', name, 'supplier') for name in manifest['fixture']['practitioners']]
                if identifier in owners:
                    return f'Professionista {owners.index(identifier) + 1}'
    display = doc.get('customer_name') if kind == 'Customer' else doc.get('supplier_name') or doc.get('party_name')
    display = str(display or identifier or '').strip()
    if display.startswith(('CC-HTTP-', 'CC-MVP-POS-', 'SYNTHETIC-')):
        return 'Cliente del documento' if kind == 'Customer' else 'Professionista del documento'
    return display or ('Cliente del documento' if kind == 'Customer' else 'Professionista del documento')


def _html(doc):
    if doc.doctype == 'Sales Invoice':
        title = 'Fattura paziente'
        rows = [('Data documento', _date(doc.posting_date)), ('Scadenza', _date(doc.due_date)),
                ('Cliente', _party(doc)), ('Totale', _money(doc.grand_total, doc.currency)),
                ('Residuo', _money(doc.outstanding_amount, doc.currency))]
    elif doc.doctype == 'Purchase Invoice':
        title = 'Fattura professionista'
        rows = [('Data documento', _date(doc.posting_date)), ('Scadenza', _date(doc.due_date)),
                ('Professionista', _party(doc)), ('Totale', _money(doc.grand_total, doc.currency)),
                ('Residuo', _money(doc.outstanding_amount, doc.currency))]
    else:
        title = 'Pagamento'
        amount = doc.received_amount if doc.payment_type == 'Receive' else doc.paid_amount
        rows = [('Data pagamento', _date(doc.posting_date)), ('Soggetto', _party(doc)),
                ('Operazione', 'Incasso' if doc.payment_type == 'Receive' else 'Pagamento'),
                ('Importo', _money(amount, doc.get('paid_to_account_currency') or doc.get('paid_from_account_currency') or 'EUR'))]
    body = ''.join(f'<tr><th scope="row">{escape(label)}</th><td>{value if label in ("Totale", "Residuo", "Importo") else escape(value)}</td></tr>' for label, value in rows)
    number = escape(str(doc.name))
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><title>{title} {number}</title>
<style>@page{{size:A4;margin:13mm}}*{{box-sizing:border-box}}body{{font:11pt/1.45 Arial,sans-serif;color:#203047;margin:0}}
main{{max-width:175mm;margin:0 auto}}header{{border-bottom:2px solid #2379ba;padding:0 0 10mm;margin-bottom:8mm}}
.brand{{font-size:10pt;font-weight:700;letter-spacing:.08em;color:#2379ba}}h1{{font-size:19pt;margin:4mm 0 2mm}}
.number{{color:#526277;font-size:10pt}}table{{width:100%;border-collapse:collapse;margin-top:6mm}}th,td{{padding:3mm 2mm;border-bottom:1px solid #dce4ed;text-align:left;vertical-align:top}}th{{width:42%;font-weight:600;color:#526277}}
footer{{margin-top:10mm;border-top:1px solid #dce4ed;padding-top:4mm;font-size:9pt;color:#526277}}
@media print{{body{{print-color-adjust:exact}}main{{break-inside:avoid}}}}</style></head>
<body><main><header><div class="brand">CENTRO CHANGE</div><h1>{title}</h1><div class="number">Documento {number} · Confermato</div></header>
<table><tbody>{body}</tbody></table><footer>Riepilogo del documento confermato. I dati contabili ufficiali restano nel gestionale.</footer></main></body></html>'''


@frappe.whitelist(methods=['GET'])
def preview(center, doctype, name, print_format=FORMAT):
    require_finance(center)
    if doctype not in PRINTABLE or print_format != FORMAT:
        frappe.throw('Formato di stampa non disponibile in questa vista', frappe.PermissionError)
    name = bounded(name, 'Documento')
    doc = frappe.get_doc(doctype, name)
    if doc.cc_center != center:
        frappe.throw('Documento non disponibile per questo centro', frappe.PermissionError)
    doc.check_permission('read')
    doc.check_permission('print')
    # Respect Frappe's native cancellation boundary without changing Print Settings.
    if doc.docstatus != 1:
        frappe.throw('L’anteprima è disponibile solo per documenti confermati.', frappe.PermissionError)
    return {'doctype': doctype, 'name': name, 'format': FORMAT, 'html': _html(doc)}
