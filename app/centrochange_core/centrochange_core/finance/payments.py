"""Read-only, center-scoped Payment Entry projection; no direct allocation API."""
from datetime import timedelta
import frappe
from frappe.utils import getdate
from centrochange_core.finance.guards import require_finance
from centrochange_core.scoped_api import bounded, page

FIELDS = ['name', 'posting_date', 'payment_type', 'party_type', 'party', 'paid_amount',
          'received_amount', 'unallocated_amount', 'mode_of_payment', 'docstatus', 'modified']


@frappe.whitelist(methods=['GET'])
def records(center, start, end, limit=50, offset=0, search=''):
    require_finance(center)
    limit, offset = page(limit, offset)
    search = bounded(search, 'Ricerca', 100, required=False)
    start, end = getdate(start), getdate(end)
    if end < start or end - start > timedelta(days=366):
        frappe.throw('Intervallo pagamenti non valido')
    filters = {'cc_center': center, 'posting_date': ['between', [start, end]]}
    options = {}
    if search:
        needle = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        options['or_filters'] = {'party': ['like', needle], 'name': ['like', needle], 'mode_of_payment': ['like', needle]}
    rows = frappe.get_list('Payment Entry', filters=filters,
                           fields=FIELDS, order_by='posting_date desc,name desc', start=offset, page_length=limit + 1, **options)
    return {'rows': rows[:limit], 'has_more': len(rows) > limit}


@frappe.whitelist(methods=['GET'])
def detail(center, name):
    require_finance(center)
    doc = frappe.get_doc('Payment Entry', bounded(name, 'Pagamento'))
    doc.check_permission('read')
    if doc.cc_center != center:
        frappe.throw('Pagamento non disponibile per questo centro', frappe.PermissionError)
    refs = []
    for row in doc.references[:100]:
        if row.reference_doctype not in ('Sales Invoice', 'Purchase Invoice'):
            continue
        invoice = frappe.get_doc(row.reference_doctype, row.reference_name)
        if invoice.cc_center != center:
            frappe.throw('Documento collegato fuori centro', frappe.PermissionError)
        invoice.check_permission('read')
        refs.append({'doctype': row.reference_doctype, 'name': row.reference_name,
                     'allocated_amount': row.allocated_amount})
    return {**{field: doc.get(field) for field in FIELDS}, 'references': refs,
            'references_truncated': len(doc.references) > 100}
