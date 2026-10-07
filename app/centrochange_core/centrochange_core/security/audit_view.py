"""Read-only management surface over the existing append-only audit."""
from datetime import timedelta
import frappe
from frappe.utils import getdate, get_datetime
from centrochange_core.security.guards import require_manager


@frappe.whitelist(methods=['GET'])
def events(start, end, event_type=None, reference=None, offset=0):
    require_manager()
    start, end = getdate(start), getdate(end)
    if end < start or end - start > timedelta(days=366):
        frappe.throw('Select an audit interval of at most 367 days')
    offset = int(offset)
    if offset < 0 or offset > 100000:
        frappe.throw('Invalid audit page')
    filters = {'event_time': ['between', [get_datetime(start), get_datetime(end + timedelta(days=1)) - timedelta(microseconds=1)]]}
    if event_type:
        filters['event_type'] = str(event_type)[:140]
    if reference:
        filters['reference_name'] = ['like', '%' + str(reference)[:140] + '%']
    rows = frappe.get_list('CC Audit Event', filters=filters,
        fields=['name', 'event_type', 'actor', 'event_time', 'reference_doctype', 'reference_name', 'reason', 'before_state', 'after_state'],
        order_by='event_time desc,name desc', start=offset, page_length=101)
    return {'events': rows[:100], 'has_more': len(rows) > 100, 'offset': offset}
