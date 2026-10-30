"""Center-scoped accounting detail and separately authorized Italian print."""
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


def _money(value, currency=None):
    amount = Decimal(str(value or 0)).quantize(Decimal('0.01'))
    integer, decimals = f'{amount:,.2f}'.split('.')
    return f'{integer.replace(",", ".")},{decimals}' + (f' {currency}' if currency else '')


def _number(value):
    return str(value).replace('.', ',') if value is not None else ''


def _party(doc):
    """Use an existing, exact UAT alias when present; never print fixture IDs."""
    kind = 'Customer' if doc.doctype == 'Sales Invoice' or doc.get('party_type') == 'Customer' else 'Supplier'
    identifier = doc.get('customer') if doc.doctype == 'Sales Invoice' else doc.get('supplier') if doc.doctype == 'Purchase Invoice' else doc.get('party')
    if doc.doctype == 'Payment Entry' and not identifier and not doc.get('party_name'):
        return ''
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
    display = (doc.get('customer_name') if kind == 'Customer' else doc.get('supplier_name')) or doc.get('party_name')
    display = str(display or identifier or '').strip()
    if display.startswith(('CC-HTTP-', 'CC-MVP-POS-', 'SYNTHETIC-')):
        return 'Cliente del documento' if kind == 'Customer' else 'Professionista del documento'
    return display or ('Cliente del documento' if kind == 'Customer' else 'Professionista del documento')


def _document(center, doctype, name):
    require_finance(center)
    if doctype not in PRINTABLE:
        frappe.throw('Documento non disponibile in questa vista', frappe.PermissionError)
    doc = frappe.get_doc(doctype, bounded(name, 'Documento'))
    if doc.cc_center != center:
        frappe.throw('Documento non disponibile per questo centro', frappe.PermissionError)
    doc.check_permission('read')
    return doc


def _link(center, doctype, name):
    if not name or doctype not in PRINTABLE:
        return None
    try:
        doc = frappe.get_doc(doctype, name)
        if doc.cc_center == center and doc.has_permission('read'):
            return {'doctype': doctype, 'name': doc.name}
    except (frappe.PermissionError, frappe.DoesNotExistError):
        pass
    return None


def _safe_text(value):
    """Remove HTML and synthetic markers from text projected to the client."""
    import re
    from html import unescape
    plain = unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))
    if frappe.conf.get('cc_synthetic_dev') == 1 and frappe.conf.get('cc_uat_demo') == 1:
        plain = re.sub(r'\b(?:CC-HTTP-[\w-]+|CC-MVP-POS-[\w-]+|SYNTHETIC-[\w-]+)\b', '', plain, flags=re.I)
    return re.sub(r'\s+', ' ', plain).strip()


def _projection(doc, center):
    data = {'doctype': doc.doctype, 'name': doc.name, 'docstatus': doc.docstatus,
            'posting_date': str(doc.posting_date) if doc.get('posting_date') else None,
            'party': _party(doc), 'currency': doc.get('currency'),
            'can_print': bool(doc.docstatus == 1 and doc.has_permission('print'))}
    if doc.doctype in ('Sales Invoice', 'Purchase Invoice'):
        data.update({'due_date': str(doc.get('due_date')) if doc.get('due_date') else None,
                     'status': doc.get('status'), 'party_currency': doc.get('party_account_currency'),
                     'address': _safe_text(doc.get('address_display')), 'tax_id': _safe_text(doc.get('tax_id')),
                     'company_address': _safe_text(doc.get('company_address_display')), 'company_tax_id': _safe_text(doc.get('company_tax_id')),
                     'items': [{'description': _safe_text(row.get('description') or row.get('item_name')),
                                'item_name': _safe_text(row.get('item_name')),
                                'qty': row.get('qty'), 'uom': {'Nos': 'unità', 'Services': 'servizi'}.get(row.get('uom'), _safe_text(row.get('uom'))),
                                'rate': row.get('rate'), 'discount_percentage': row.get('discount_percentage'),
                                'discount_amount': row.get('discount_amount'), 'amount': row.get('amount')}
                               for row in doc.get('items') or []],
                     'taxes': [{'description': _safe_text(row.get('description')),
                                'rate': row.get('rate'), 'tax_amount': row.get('tax_amount')}
                               for row in doc.get('taxes') or []],
                     'net_total': doc.get('net_total'), 'total_taxes_and_charges': doc.get('total_taxes_and_charges'),
                     'discount_amount': doc.get('discount_amount'), 'additional_discount_percentage': doc.get('additional_discount_percentage'),
                     'grand_total': doc.get('grand_total'), 'outstanding_amount': doc.get('outstanding_amount'),
                     'links': []})
        for field in ('return_against', 'amended_from'):
            link = _link(center, doc.doctype, doc.get(field))
            if link:
                data['links'].append({'kind': field, **link})
    else:
        paid_currency = doc.get('paid_from_account_currency')
        received_currency = doc.get('paid_to_account_currency')
        party_currency = paid_currency if doc.get('payment_type') == 'Receive' else received_currency if doc.get('payment_type') == 'Pay' else None
        data.update({'payment_type': doc.get('payment_type'), 'mode_of_payment': _safe_text(doc.get('mode_of_payment')),
                     'paid_currency': paid_currency, 'received_currency': received_currency, 'party_currency': party_currency,
                     'reference_no': _safe_text(doc.get('reference_no')),
                     'reference_date': str(doc.get('reference_date')) if doc.get('reference_date') else None,
                     'paid_amount': doc.get('paid_amount'), 'received_amount': doc.get('received_amount'),
                     'unallocated_amount': doc.get('unallocated_amount'), 'references': []})
        for row in doc.get('references') or []:
            link = _link(center, row.get('reference_doctype'), row.get('reference_name'))
            if link:
                data['references'].append({**link, 'allocated_amount': row.get('allocated_amount')})
    return data


@frappe.whitelist(methods=['GET'])
def detail(center, doctype, name):
    """Full read-only document without granting print or leaking linked centers."""
    return _projection(_document(center, doctype, name), center)


def _html(data):
    title = {'Sales Invoice': 'Fattura paziente', 'Purchase Invoice': 'Fattura professionista', 'Payment Entry': 'Pagamento'}[data['doctype']]
    currency = data['currency']

    def pair(label, value):
        if value is None or value == '':
            return ''
        return f'<div class="pair"><dt>{escape(label)}</dt><dd>{escape(str(value))}</dd></div>'

    def amount(label, value, unit=currency):
        return pair(label, _money(value, unit)) if value is not None else ''

    meta = pair('Numero', data['name']) + pair('Data documento', _date(data['posting_date'])) + pair('Soggetto', data['party'])
    if data['doctype'] != 'Payment Entry':
        meta += pair('Scadenza', _date(data['due_date'])) + pair('Indirizzo', data['address']) + pair('Identificativo fiscale', data['tax_id']) + pair('Indirizzo azienda', data['company_address']) + pair('Identificativo fiscale azienda', data['company_tax_id'])
        rows = ''.join('<tr><td>' + escape(row['item_name'] or row['description']) + ('<br>' + escape(row['description']) if row['description'] and row['description'] != row['item_name'] else '') + '</td><td>' + escape(_number(row['qty'])) + '</td><td>' + escape(row['uom'] or '') + '</td><td>' + (escape(_money(row['rate'], currency)) if row['rate'] is not None else '') + '</td><td>' + (' · '.join(([escape(_number(row['discount_percentage'])) + '%'] if row['discount_percentage'] else []) + ([escape(_money(row['discount_amount'], currency)) + ' per unità'] if row['discount_amount'] else []))) + '</td><td>' + (escape(_money(row['amount'], currency)) if row['amount'] is not None else '') + '</td></tr>' for row in data['items'])
        body = '<h2>Righe del documento</h2><table class="lines"><thead><tr><th>Servizio o articolo</th><th>Qtà</th><th>Unità</th><th>Prezzo</th><th>Sconto</th><th>Importo</th></tr></thead><tbody>' + (rows or '<tr><td colspan="6">Nessuna riga presente</td></tr>') + '</tbody></table>'
        taxes = ''.join(pair(row['description'] or 'Imposta', _money(row['tax_amount'], currency)) for row in data['taxes'] if row['tax_amount'] is not None)
        body += '<h2>Importi</h2><dl class="totals">' + amount('Imponibile', data['net_total']) + amount('Sconto aggiuntivo', data['discount_amount']) + taxes + amount('Imposte e oneri', data['total_taxes_and_charges']) + amount('Totale', data['grand_total']) + amount('Residuo', data['outstanding_amount'], data['party_currency']) + '</dl>'
    else:
        direction = {'Receive': 'Incasso', 'Pay': 'Pagamento', 'Internal Transfer': 'Trasferimento interno'}.get(data['payment_type'], '')
        meta += pair('Operazione', direction) + pair('Metodo', data['mode_of_payment']) + pair('Riferimento', data['reference_no']) + pair('Data riferimento', _date(data['reference_date']))
        body = '<h2>Importi</h2><dl class="totals">' + amount('Importo pagato', data['paid_amount'], data['paid_currency']) + amount('Importo ricevuto', data['received_amount'], data['received_currency']) + amount('Non attribuito', data['unallocated_amount'], data['party_currency']) + '</dl>'
        if data['references']:
            refs = ''.join('<tr><td>' + escape(row['name']) + '</td><td>' + escape(_money(row['allocated_amount'], data['party_currency'])) + '</td></tr>' for row in data['references'])
            body += '<h2>Documenti collegati</h2><table><thead><tr><th>Documento</th><th>Importo attribuito</th></tr></thead><tbody>' + refs + '</tbody></table>'
    number = escape(str(data['name']))
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><title>{title} {number}</title><style>
@page{{size:A4;margin:14mm}}*{{box-sizing:border-box}}body{{font:10pt/1.4 Arial,sans-serif;color:#203047;margin:0}}main{{max-width:180mm;margin:auto}}
header{{border-bottom:2px solid #2379ba;padding-bottom:5mm}}.brand{{font-size:9pt;font-weight:700;letter-spacing:.08em;color:#2379ba}}h1{{font-size:18pt;margin:3mm 0}}.number{{color:#526277}}
h2{{font-size:11pt;margin:7mm 0 2mm}}dl{{display:grid;grid-template-columns:1fr 1fr;gap:2mm 8mm}}.pair{{display:flex;gap:3mm;border-bottom:1px solid #e4eaf0;padding:2mm 0}}dt{{color:#526277;min-width:30mm}}dd{{margin:0;font-weight:600}}
table{{width:100%;border-collapse:collapse;margin-top:2mm}}th,td{{padding:2mm 1mm;border-bottom:1px solid #dce4ed;text-align:left;vertical-align:top}}th{{color:#526277}}.lines th:nth-child(n+2),.lines td:nth-child(n+2){{text-align:right}}
tr,.pair{{break-inside:avoid}}thead{{display:table-header-group}}footer{{margin-top:7mm;border-top:1px solid #dce4ed;padding-top:3mm;font-size:8pt;color:#526277}}@media print{{body{{print-color-adjust:exact}}}}
</style></head><body><main><header><div class="brand">CENTRO CHANGE</div><h1>{title}</h1><div class="number">Documento {number} · Confermato</div></header>
<dl>{meta}</dl>{body}<footer>Documento contabile consultabile. Le intestazioni con data e URL sono impostazioni del browser: disattivale nel dialogo di stampa.</footer></main></body></html>'''


@frappe.whitelist(methods=['GET'])
def preview(center, doctype, name, print_format=FORMAT):
    if print_format != FORMAT:
        frappe.throw('Formato di stampa non disponibile in questa vista', frappe.PermissionError)
    doc = _document(center, doctype, name)
    doc.check_permission('print')
    # Respect Frappe's native cancellation boundary without changing Print Settings.
    if doc.docstatus != 1:
        frappe.throw('L’anteprima è disponibile solo per documenti confermati.', frappe.PermissionError)
    return {'doctype': doctype, 'name': doc.name, 'format': FORMAT, 'html': _html(_projection(doc, center))}
