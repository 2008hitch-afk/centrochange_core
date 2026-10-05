"""Scoped cross-domain projections; totals drill into native accounting documents."""
from collections import defaultdict
from datetime import timedelta
from io import StringIO
import csv
import frappe
from centrochange_core.security.guards import current_rows,is_manager,centers,roles
from centrochange_core.finance.guards import require_finance,allowed
from centrochange_core.finance import professional_economics,admin_queue
from centrochange_core.operations.reporting import safe_cell


def _interval(start,end):
    a,b=frappe.utils.getdate(start),frappe.utils.getdate(end)
    if not start or not end or b<a or (b-a).days>366:frappe.throw('Choose a date interval of at most 366 days')
    return a,b


def _bounded(doctype,filters,fields):
    rows=current_rows(doctype,filters,fields=fields)
    if len(rows)>500:frappe.throw('Narrow the report filters; more than 500 composing records')
    return rows


@frappe.whitelist(methods=['GET'])
def summary(center,start,end,customer=None,practitioner=None):
    require_finance(center);start,end=_interval(start,end)
    base={'cc_center':center,'posting_date':['between',[start,end]],'docstatus':1}
    if customer:
        from centrochange_core.finance.permissions import master_names
        if not is_manager() and customer not in master_names('Customer'):frappe.throw('Customer scope denied',frappe.PermissionError)
        if practitioner:frappe.throw('Choose a customer or a professional projection separately')
    supplier=None
    if practitioner:
        users=current_rows('CC Center Membership',{'center':center},pluck='user')
        if practitioner not in current_rows('Healthcare Practitioner',{'user_id':['in',users or ['']]},pluck='name'):
            frappe.throw('Professional report context denied',frappe.PermissionError)
        supplier=frappe.db.get_value('Healthcare Practitioner',practitioner,'supplier')
    sales=_bounded('Sales Invoice',{**base,**({'customer':customer} if customer else {})},['name','posting_date','customer','currency','net_total','grand_total','outstanding_amount','is_return','return_against','amended_from'])
    if practitioner:
        # A fiscal invoice may compose several professionals. No invented allocation of its open balance.
        sales=[]
    purchases=[] if customer else _bounded('Purchase Invoice',{**base,**({'supplier':supplier or ''} if practitioner else {})},['name','posting_date','supplier','currency','net_total','grand_total','outstanding_amount','is_return','return_against','amended_from','cc_incoming_source'])
    payments=_bounded('Payment Entry',{**base,**({'party_type':'Customer','party':customer} if customer else {'party_type':'Supplier','party':supplier or ''} if practitioner else {})},['name','posting_date','party_type','party','payment_type','paid_amount','received_amount','paid_from_account_currency','paid_to_account_currency'])
    session_filters={'cc_center':center,'appointment_date':['between',[start,end]]}
    if practitioner:session_filters['practitioner']=practitioner
    sessions=_bounded('Patient Appointment',session_filters,['name','appointment_date','patient','practitioner','cc_service_label','cc_closure_state','cc_economic_state','cc_performed','cc_paid','cc_price_snapshot','cc_currency_snapshot'])
    if customer:
        patients=set(current_rows('Patient',{'customer':customer},pluck='name'));sessions=[r for r in sessions if r.patient in patients]
    currencies={r.currency for r in sales+purchases}
    if currencies-{'EUR'}:frappe.throw('Separate currency reporting is required before combining these documents')
    expected_rows=_bounded('CC Professional Expectation',{'center':center},['name','appointment','practitioner','source','state','amount','amount_known','currency','creation','sequence'])
    session_ids={r.name for r in sessions};latest={}
    for row in sorted(expected_rows,key=lambda r:(r.sequence or 0,r.creation,r.name)):
        if row.appointment in session_ids:latest[row.appointment]=row
    # Performed sessions without an expectation are visible unknowns, never silently absent zero cost.
    performed={r.name for r in sessions if r.cc_performed}
    unknown=sum(r.state!='OK' for r in latest.values())+len(performed-set(latest))
    known=sum(r.amount for r in latest.values() if r.state=='OK')
    collected=sum((r.received_amount if r.payment_type=='Receive' else -r.paid_amount if r.payment_type=='Pay' else 0) for r in payments if r.party_type=='Customer')
    supplier_paid=sum((r.paid_amount if r.payment_type=='Pay' else -r.received_amount if r.payment_type=='Receive' else 0) for r in payments if r.party_type=='Supplier')
    totals={'revenue_net':sum(r.net_total for r in sales),'billed_gross':sum(r.grand_total for r in sales),
        'receivable_outstanding':sum(r.outstanding_amount for r in sales),'collected':collected,
        'purchase_net':sum(r.net_total for r in purchases),'payable_outstanding':sum(r.outstanding_amount for r in purchases),
        'supplier_paid':supplier_paid,'sessions':len(sessions),'performed':len(performed),'known_expected_compensation':known,
        'expected_compensation':None if unknown else known,'unresolved_expectations':unknown,'indicative_margin':None}
    return {'center':center,'start':start,'end':end,'currency':'EUR','totals':totals,'sales_invoices':sales,'purchase_invoices':purchases,
        'payments':payments,'sessions':sessions,'expectations':list(latest.values()),'exceptions':admin_queue.list_items(center),
        'scope_note':'Posting dates for accounting; session dates for operations. Customer totals include the shared fiscal payer. Supplier invoices are fiscal-supplier totals; no inferred allocation to individual professionals. Margin policy remains undefined.'}


@frappe.whitelist(methods=['GET'])
def export_csv(center,start,end,customer=None,practitioner=None):
    data=summary(center,start,end,customer,practitioner);output=StringIO(newline='');writer=csv.writer(output)
    writer.writerow(['kind','name','date','subject','currency','net','gross','outstanding'])
    for key,kind,subject in [('sales_invoices','Sales Invoice','customer'),('purchase_invoices','Purchase Invoice','supplier')]:
        for row in data[key]:writer.writerow([safe_cell(v) for v in [kind,row.name,row.posting_date,row[subject],row.currency,row.net_total,row.grand_total,row.outstanding_amount]])
    for row in data['payments']:writer.writerow([safe_cell(v) for v in ['Payment Entry',row.name,row.posting_date,row.party,'EUR','',row.paid_amount,'']])
    frappe.response.update({'type':'download','filename':'centrochange-finance.csv','filecontent':output.getvalue(),'content_type':'text/csv; charset=utf-8'})


@frappe.whitelist(methods=['GET'])
def bootstrap(center=None):
    if not allowed():frappe.throw('Finance workspace access denied',frappe.PermissionError)
    scopes=current_rows('Branch',{} if is_manager() else {'name':['in',centers() or ['']]},fields=['name','branch','cc_company','cc_cost_center','cc_bank_account'])
    center=center or (scopes[0].name if scopes else None)
    if center:require_finance(center)
    from centrochange_core.finance.permissions import master_names
    def masters(dt,fields):
        filters={} if is_manager() else {'name':['in',master_names(dt) or ['']]}
        return _bounded(dt,filters,fields)
    users=current_rows('CC Center Membership',{'center':center,'active':1},pluck='user') if center else []
    practitioners=current_rows('Healthcare Practitioner',{'user_id':['in',users or ['']]},fields=['name','practitioner_name','supplier'])
    assignees=[u for u in users if allowed(u,True)]
    return {'centers':scopes,'center':center,'can_write':allowed(write=True),'is_manager':is_manager(),
        'customers':masters('Customer',['name','customer_name']),'suppliers':masters('Supplier',['name','supplier_name','tax_id']),
        'accounts':masters('Account',['name','root_type','account_type','is_group','disabled','company']),
        'items':_bounded('Item',{'disabled':0,'is_stock_item':0},['name','item_name','is_purchase_item','is_sales_item']),
        'practitioners':practitioners,'assignees':assignees,'unpaid_policy':professional_economics.POLICY,
        'fiscal_verified':bool(frappe.db.get_single_value('CC Finance Settings','fiscal_configuration_verified')),'simulation_only':True}


@frappe.whitelist(methods=['GET'])
def records(center,doctype):
    require_finance(center)
    allowed_types={'CC Incoming Invoice':['name','state','supplier','invoice_number','invoice_date','total','currency','purchase_invoice','problem'],
        'Sales Invoice':['name','docstatus','posting_date','customer','grand_total','outstanding_amount','currency'],
        'Purchase Invoice':['name','docstatus','posting_date','supplier','grand_total','outstanding_amount','currency','cc_incoming_source'],
        'Bank Transaction':['name','docstatus','date','deposit','withdrawal','unallocated_amount','reference_number'],
        'CC Economic Source Link':['name','appointment','session_date','practitioner','patient','price','currency','performed','economic_state'],
        'CC Professional Expectation':['name','appointment','practitioner','state','amount','amount_known','problem','rule']}
    if doctype not in allowed_types:frappe.throw('Unsupported workspace record type')
    field='center' if doctype.startswith('CC ') else 'cc_center'
    if doctype=='CC Professional Expectation':
        latest=professional_economics.latest_expectations(center)
        if len(latest)>500:frappe.throw('Narrow the report filters; more than 500 composing records')
        return [{k:r.get(k) for k in allowed_types[doctype]} for r in latest.values()]
    return _bounded(doctype,{field:center},allowed_types[doctype])
