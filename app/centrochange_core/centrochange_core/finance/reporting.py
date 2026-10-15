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
    if not start or not end or b<a or (b-a).days>366:frappe.throw('Seleziona un intervallo di massimo 366 giorni.')
    return a,b


def _bounded(doctype,filters,fields):
    rows=current_rows(doctype,filters,fields=fields)
    if len(rows)>500:frappe.throw('Riduci i filtri del report: ci sono oltre 500 record.')
    return rows


@frappe.whitelist(methods=['GET'])
def summary(center,start,end,customer=None,practitioner=None):
    require_finance(center);start,end=_interval(start,end)
    base={'cc_center':center,'posting_date':['between',[start,end]],'docstatus':1}
    if customer:
        from centrochange_core.finance.permissions import master_names
        if not is_manager() and customer not in master_names('Customer'):frappe.throw('Non hai accesso ai dati di questo cliente.',frappe.PermissionError)
        if practitioner:frappe.throw('Consulta separatamente il report cliente o professionista.')
    supplier=None
    if practitioner:
        users=current_rows('CC Center Membership',{'center':center},pluck='user')
        if practitioner not in current_rows('Healthcare Practitioner',{'user_id':['in',users or ['']]},pluck='name'):
            frappe.throw('Non hai accesso al report di questo professionista.',frappe.PermissionError)
        supplier=frappe.db.get_value('Healthcare Practitioner',practitioner,'supplier')
    sales=_bounded('Sales Invoice',{**base,**({'customer':customer} if customer else {})},['name','posting_date','customer','currency','net_total','grand_total','outstanding_amount','is_return','return_against','amended_from'])
    if practitioner:
        # A fiscal invoice may compose several professionals. No invented allocation of its open balance.
        sales=[]
    purchases=[] if customer else _bounded('Purchase Invoice',{**base,**({'supplier':supplier or ''} if practitioner else {})},['name','posting_date','supplier','status','docstatus','currency','net_total','grand_total','outstanding_amount','is_return','return_against','amended_from','cc_incoming_source'])
    payments=_bounded('Payment Entry',{**base,**({'party_type':'Customer','party':customer} if customer else {'party_type':'Supplier','party':supplier or ''} if practitioner else {})},['name','posting_date','party_type','party','payment_type','mode_of_payment','paid_amount','received_amount','paid_from_account_currency','paid_to_account_currency'])
    session_filters={'cc_center':center,'appointment_date':['between',[start,end]]}
    if practitioner:session_filters['practitioner']=practitioner
    sessions=_bounded('Patient Appointment',session_filters,['name','appointment_date','appointment_time','status','duration','patient','practitioner','cc_service_label','cc_closure_state','cc_economic_state','cc_performed','cc_paid','cc_price_snapshot','cc_currency_snapshot'])
    if customer:
        patients=set(current_rows('Patient',{'customer':customer},pluck='name'));sessions=[r for r in sessions if r.patient in patients]
    currencies={r.currency for r in sales+purchases}
    if currencies-{'EUR'}:frappe.throw('I documenti in valute diverse richiedono report separati.')
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
    writer.writerow(['Tipo documento','Numero documento','Data registrazione','Soggetto','Valuta','Imponibile','Totale','Residuo','Metodo di pagamento'])
    def date_it(value):
        return frappe.utils.formatdate(value,'dd/MM/yyyy') if value else ''
    for key,kind,subject in [('sales_invoices','Sales Invoice','customer'),('purchase_invoices','Purchase Invoice','supplier')]:
        for row in data[key]:writer.writerow([safe_cell(v) for v in [kind,row.name,date_it(row.posting_date),row[subject],row.currency,row.net_total,row.grand_total,row.outstanding_amount,'']])
    for row in data['payments']:writer.writerow([safe_cell(v) for v in ['Pagamento',row.name,date_it(row.posting_date),row.party,'EUR','',row.paid_amount,'',row.mode_of_payment]])
    frappe.response.update({'type':'download','filename':'centrochange-finance.csv','filecontent':output.getvalue(),'content_type':'text/csv; charset=utf-8'})


@frappe.whitelist(methods=['GET'])
def bootstrap(center=None):
    if not allowed():frappe.throw('Non hai accesso alla Finanza.',frappe.PermissionError)
    from centrochange_core.security.guards import operational_centers
    available=operational_centers()
    scopes=current_rows('Branch',{'name':['in',[row.name for row in available] or ['']]},fields=['name','branch','cc_company','cc_cost_center','cc_bank_account'])
    center=center or (scopes[0].name if scopes else None)
    if center and center not in [row.name for row in scopes]:
        frappe.throw('La sede non è disponibile per le operazioni.',frappe.PermissionError)
    if center:require_finance(center)
    from centrochange_core.finance.permissions import master_names
    def masters(dt,fields):
        filters={} if is_manager() else {'name':['in',master_names(dt) or ['']]}
        return _bounded(dt,filters,fields)
    users=current_rows('CC Center Membership',{'center':center,'active':1},pluck='user') if center else []
    practitioners=current_rows('Healthcare Practitioner',{'user_id':['in',users or ['']]},fields=['name','practitioner_name','supplier'])
    assignees=[u for u in users if allowed(u,True)]
    payment_methods=[]
    if center:
        company=next((row.cc_company for row in scopes if row.name==center),None)
        if company:
            for mode in current_rows('Mode of Payment',{'enabled':1},fields=['name','type']):
                matches=current_rows('Mode of Payment Account',{'parent':mode.name,'company':company},fields=['default_account'])
                for mapping in matches:
                    if not mapping.default_account:continue
                    account=frappe.db.get_value('Account',mapping.default_account,['company','account_type','is_group','disabled','account_currency'],as_dict=True)
                    currency=frappe.db.get_value('Company',company,'default_currency')
                    if account and account.company==company and account.account_type in ('Bank','Cash') and not account.is_group and not account.disabled and account.account_currency in (None,'',currency):
                        label=mode.name
                        if mode.name.startswith('CC DEV PROFILE '):
                            label={'Cash':'Contanti','Bank':'Bonifico','General':'Altro metodo'}.get(mode.type,'Metodo di pagamento')
                        payment_methods.append({'name':mode.name,'type':mode.type,'label':label})
                        break
    return {'centers':scopes,'center':center,'can_write':allowed(write=True),'is_manager':is_manager(),
        'customers':masters('Customer',['name','customer_name']),'suppliers':masters('Supplier',['name','supplier_name','tax_id']),
        'accounts':masters('Account',['name','root_type','account_type','is_group','disabled','company']),
        'items':_bounded('Item',{'disabled':0,'is_stock_item':0},['name','item_name','is_purchase_item','is_sales_item']),
        'practitioners':practitioners,'assignees':assignees,'payment_methods':payment_methods,'unpaid_policy':professional_economics.POLICY,
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
    if doctype not in allowed_types:frappe.throw('Il tipo di documento richiesto non è supportato.')
    field='center' if doctype.startswith('CC ') else 'cc_center'
    if doctype=='CC Professional Expectation':
        latest=professional_economics.latest_expectations(center)
        if len(latest)>500:frappe.throw('Riduci i filtri del report: ci sono oltre 500 record.')
        result=[]
        for r in latest.values():
            row={k:r.get(k) for k in allowed_types[doctype]}
            source=frappe.db.get_value('CC Economic Source Link',r.source,['customer','center','session_date'],as_dict=True)
            if source and source.center==center:
                row['appointment_label']=str(source.session_date)+' · '+(frappe.db.get_value('Customer',source.customer,'customer_name') or source.customer)
            result.append(row)
        return result
    return _bounded(doctype,{field:center},allowed_types[doctype])


@frappe.whitelist(methods=['GET'])
def professional_view(center,start,end,practitioner):
    """One bounded period projection; native subject totals are never allocated."""
    require_finance(center)
    # Reuse the existing authorized practitioner selector, including active membership.
    context=bootstrap(center)
    identity=next((r for r in context['practitioners'] if r.name==practitioner),None)
    if not identity:frappe.throw('Non hai accesso al report di questo professionista.',frappe.PermissionError)
    data=summary(center,start,end,practitioner=practitioner)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from frappe.utils import get_time
    now=datetime.now(ZoneInfo('Europe/Rome')).replace(tzinfo=None)
    counts={'sessions':len(data['sessions']),'performed':0,'cancelled':0,'future':0,'pending':0,'closed_not_performed':0,'operational_paid':0,'operational_unpaid':0}
    values=defaultdict(float);sessions=[]
    for row in data['sessions']:
        start_at=datetime.combine(frappe.utils.getdate(row.appointment_date),get_time(row.appointment_time))
        category=('cancelled' if row.status=='Cancelled' else 'performed' if row.cc_performed else 'future' if start_at>now else 'closed_not_performed' if row.cc_closure_state=='Closed' else 'pending')
        counts[category]+=1;counts['operational_paid' if row.cc_paid else 'operational_unpaid']+=1
        values[row.cc_currency_snapshot or 'UNSET']+=float(row.cc_price_snapshot or 0)
        doc=frappe.get_doc('Patient Appointment',row.name)
        can_open=bool(doc.has_permission('read') and (is_manager() or 'CC Secretariat' in roles()))
        source=frappe.db.get_value('CC Economic Source Link',{'appointment':row.name,'center':center},['customer'],as_dict=True)
        label=doc.patient_name if can_open else (frappe.db.get_value('Customer',source.customer,'customer_name') if source and source.customer else 'Paziente non proiettato')
        sessions.append({**dict(row),'appointment_time':str(get_time(row.appointment_time)),'category':category,'patient_label':label,'can_open':can_open})
    sessions.sort(key=lambda r:(str(r['appointment_date']),r['appointment_time'],r['name']))
    expectations=data['expectations']
    if any(r.currency!='EUR' for r in expectations):frappe.throw('Le valute diverse richiedono report separati.')
    unresolved=[r for r in expectations if r.state!='OK']
    missing=[r['name'] for r in sessions if r['cc_performed'] and r['name'] not in {e.appointment for e in expectations}]
    comparisons=[]
    identifiers={r['name'] for r in sessions}
    for row in _bounded('CC Professional Comparison',{'center':center,'practitioner':practitioner},['name','purchase_invoice','expectations_json','expected_known','expected_amount','received_amount','currency','state','problem','creation']):
        refs=frappe.parse_json(row.expectations_json or '[]')
        composed=current_rows('CC Professional Expectation',{'name':['in',refs or ['']]},fields=['name','appointment','center','practitioner','state','amount','amount_known'])
        # Whole canonical comparison only; never split an invoice/comparison across periods.
        if not refs or len(composed)!=len(refs) or any(r.center!=center or r.practitioner!=practitioner or r.appointment not in identifiers for r in composed):continue
        row.pop('expectations_json',None)
        comparisons.append({**dict(row),'expectations':[dict(r) for r in composed],'difference':float(row.expected_amount)-float(row.received_amount) if row.expected_known else None})
    return {'center':center,'practitioner':practitioner,'practitioner_name':identity.practitioner_name,'start':data['start'],'end':data['end'],'counts':counts,'snapshot_values':dict(values),'sessions':sessions,
        'economics':{'currency':'EUR','known_expected':data['totals']['known_expected_compensation'],'expected':data['totals']['expected_compensation'],'suspended':sum(r.state=='SUSPENDED' for r in expectations),'review':sum(r.state not in ('OK','SUSPENDED') for r in expectations)+len(missing),'expectations':[dict(r) for r in expectations],'missing_expectation_sessions':missing,'supplier_invoices':[dict(r) for r in data['purchase_invoices']],'supplier_paid':data['totals']['supplier_paid'],'comparisons':comparisons},
        'scope_note':'Paid/Unpaid is operational, not patient accounting. Snapshot value includes cancelled/non-due sessions. Expected compensation follows session dates. Received invoice/payment follows posting dates and fiscal supplier; no allocation to individual professionals. Comparisons include only whole canonical snapshots whose sessions lie in this period; no inferred comparison or discrepancy total.'}


@frappe.whitelist(methods=['GET'])
def professional_export(center,start,end,practitioner):
    data=professional_view(center,start,end,practitioner);output=StringIO(newline='');writer=csv.writer(output)
    fields=['name','appointment_date','appointment_time','patient_label','cc_service_label','category','cc_price_snapshot','cc_currency_snapshot','cc_economic_state','cc_paid']
    writer.writerow(['Identificativo seduta','Data','Ora','Paziente','Servizio','Stato seduta','Valore snapshot','Valuta','Stato economico','Pagamento registrato'])
    categories={'cancelled':'Annullata','performed':'Svolta','future':'In programma','closed_not_performed':'Chiusa non svolta','pending':'Da completare'}
    economy={'Due':'Dovuta','Non Due':'Non dovuta','Package Covered':'Coperta da pacchetto','Waived':'Rinuncia economica'}
    for row in data['sessions']:
        values=[row.get(field) for field in fields]
        values[1]=frappe.utils.formatdate(values[1],'dd/MM/yyyy') if values[1] else ''
        values[2]=str(values[2])[:5] if values[2] else ''
        values[5]=categories.get(values[5],values[5]);values[8]=economy.get(values[8],values[8]);values[9]='Sì' if values[9] else 'No'
        writer.writerow([safe_cell(value) for value in values])
    frappe.response.update({'type':'download','filename':'centrochange-professional.csv','filecontent':output.getvalue(),'content_type':'text/csv; charset=utf-8'})
