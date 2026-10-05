"""Explicit rule snapshots and native received-invoice comparison; no payout ledger."""
from decimal import Decimal,InvalidOperation
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,is_manager,centers,names_condition
from centrochange_core.finance.guards import allowed,require_finance,require_finance_manager,require_synthetic
from centrochange_core.operations.integrity import immutable as protected


def digest(value):return sha256(serialize(value).encode()).hexdigest()


def number(value):
    try: result=Decimal(str(value))
    except (InvalidOperation,ValueError):frappe.throw('An explicit finite economic amount is required')
    if not result.is_finite() or result<0 or result>Decimal('1000000000'):frappe.throw('Economic amount is out of range')
    return result


def _practitioner(practitioner,center):
    user=frappe.db.get_value('Healthcare Practitioner',practitioner,'user_id',for_update=True)
    if not user or not current_rows('CC Center Membership',{'user':user,'center':center,'active':1},pluck='name'):
        frappe.throw('Professional center context is unavailable',frappe.PermissionError)


@frappe.whitelist(methods=['POST'])
@atomic
def configure_rule(center,practitioner,service_item,valid_from,basis,value,currency,request_key,reason,valid_to=None):
    lock();require_finance_manager();require_synthetic();_practitioner(practitioner,center)
    value=number(value)
    if basis not in ('Fixed Amount','Percentage') or basis=='Percentage' and value>100:
        frappe.throw('Choose an explicit supported compensation basis')
    start=frappe.utils.getdate(valid_from);end=frappe.utils.getdate(valid_to) if valid_to else None
    if not valid_from or end and end<start or currency!='EUR' or not request_key or len(request_key)>140:
        frappe.throw('Explicit rule dates currency and request key are required')
    item=frappe.get_doc('Item',service_item)
    if item.disabled or item.is_stock_item:frappe.throw('An enabled service item is required')
    data=dict(center=center,practitioner=practitioner,service_item=service_item,valid_from=start,valid_to=end,
        basis=basis,value=float(value),currency=currency)
    old=frappe.db.get_value('CC Compensation Rule',{'request_key':request_key},['name','payload_hash'],as_dict=True,for_update=True)
    if old:
        if old.payload_hash!=digest(data):frappe.throw('Rule replay differs from the recorded request')
        return {'name':old.name,'replay':True}
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Compensation Rule',**data,'request_key':request_key,'payload_hash':digest(data),'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_RULE_CONFIGURED',doc.doctype,doc.name,None,data,reason)
    return {'name':doc.name,'replay':False}


def patient_paid(source):
    invoices=frappe.db.sql('''select distinct p.name,p.outstanding_amount,p.docstatus,p.is_return
        from `tabSales Invoice` p join `tabSales Invoice Item` i on i.parent=p.name
        join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
        where s.appointment=%s and p.docstatus=1 and p.is_return=0 for update''',(source.appointment,),as_dict=True)
    return all(row.outstanding_amount<=0 for row in invoices) if invoices else bool(source.operational_paid)


@frappe.whitelist(methods=['POST'])
@atomic
def capture(source,reason,rule=None):
    lock();require_synthetic()
    src=frappe.get_doc('CC Economic Source Link',source,for_update=True);require_finance(src.center,True)
    snapshot={};problem=None;amount=None;paid=patient_paid(src)
    policy=frappe.db.get_single_value('CC Finance Settings','unpaid_compensation_policy') or 'UNSET'
    if rule:
        doc=frappe.get_doc('CC Compensation Rule',rule,for_update=True)
        if (doc.center,doc.practitioner,doc.service_item,doc.currency)!=(src.center,src.practitioner,src.service_item,src.currency):
            frappe.throw('Explicit compensation rule and source context differ')
        if not doc.valid_from<=frappe.utils.getdate(src.session_date) or doc.valid_to and doc.valid_to<frappe.utils.getdate(src.session_date):
            frappe.throw('Rule is not valid for the source session date')
        snapshot={k:doc.get(k) for k in ('name','valid_from','valid_to','basis','value','currency')}
    else:problem='Compensation Rule Unset'
    if not src.performed:problem='Eligibility Requires Review'
    elif not paid and policy=='UNSET':problem='Unpaid Compensation Policy Unset'
    elif policy not in ('UNSET','Earn When Performed','Earn When Patient Paid'):problem='Unknown Compensation Policy'
    if not problem:
        amount=0 if not paid and policy=='Earn When Patient Paid' else float((number(snapshot['value']) if snapshot['basis']=='Fixed Amount' else number(src.price)*number(snapshot['value'])/100).quantize(Decimal('.01')))
    data={'center':src.center,'source':src.name,'appointment':src.appointment,'practitioner':src.practitioner,'supplier':src.supplier,
        'rule':rule,'rule_snapshot':serialize(snapshot),'policy_snapshot':policy,'paid_snapshot':int(paid),'state':'REVIEW' if problem else 'OK',
        'problem':problem,'amount_known':int(amount is not None),'amount':amount,'currency':src.currency}
    key=digest(data);old=frappe.db.get_value('CC Professional Expectation',{'snapshot_hash':key},for_update=True)
    if old:return {'name':old,'replay':True,'state':data['state'],'amount':amount}
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Professional Expectation',**data,'snapshot_hash':key,'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_EXPECTATION_CAPTURED',doc.doctype,doc.name,None,{'source':source,'state':doc.state,'snapshot_hash':key},reason)
    return {'name':doc.name,'replay':False,'state':data['state'],'amount':amount}


@frappe.whitelist(methods=['POST'])
@atomic
def compare(purchase_invoice,expectations,reason):
    lock();require_synthetic()
    invoice=frappe.get_doc('Purchase Invoice',purchase_invoice,for_update=True);require_finance(invoice.cc_center,True)
    ids=frappe.parse_json(expectations) if isinstance(expectations,str) else expectations
    if not isinstance(ids,list) or not ids or len(ids)>500 or len(set(ids))!=len(ids):frappe.throw('Choose distinct expected session snapshots')
    if invoice.docstatus!=1 or invoice.is_return:frappe.throw('A submitted ordinary native Purchase Invoice is required')
    rows=[frappe.get_doc('CC Professional Expectation',name,for_update=True) for name in sorted(ids)]
    contexts={(r.center,r.practitioner,r.supplier,r.currency) for r in rows}
    if len(contexts)!=1 or next(iter(contexts))!=(invoice.cc_center,rows[0].practitioner,invoice.supplier,invoice.currency):
        frappe.throw('Expected and received professional context differ',frappe.PermissionError)
    if len({r.appointment for r in rows})!=len(rows):frappe.throw('A session cannot count twice in one comparison')
    known=all(r.state=='OK' for r in rows);expected=sum(number(r.amount) for r in rows) if known else None
    received=number(invoice.net_total)
    data={'center':invoice.cc_center,'practitioner':rows[0].practitioner,'purchase_invoice':invoice.name,
        'expectations_json':serialize(sorted(ids)),'expected_known':int(known),'expected_amount':float(expected) if known else None,'received_amount':float(received),
        'currency':invoice.currency,'state':'OK' if known and expected==received else 'REVIEW',
        'problem':None if known and expected==received else ('Expectation Unresolved' if not known else 'Amount Difference')}
    key=digest(data);old=frappe.db.get_value('CC Professional Comparison',{'snapshot_hash':key},for_update=True)
    if old:return {'name':old,'replay':True,'state':data['state']}
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Professional Comparison',**data,'snapshot_hash':key,'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_INVOICE_COMPARED',doc.doctype,doc.name,None,{'state':doc.state,'snapshot_hash':key},reason)
    return {'name':doc.name,'replay':False,'state':doc.state}


def names(doctype,user=None):
    if not allowed(user):return []
    return current_rows(doctype,{} if is_manager(user) else {'center':['in',centers(user) or ['']]},pluck='name')


def query(doctype,user=None):return names_condition(doctype,names(doctype,user))
def rule_query(user=None):return query('CC Compensation Rule',user)
def expectation_query(user=None):return query('CC Professional Expectation',user)
def comparison_query(user=None):return query('CC Professional Comparison',user)
def permission(doc,user=None,ptype=None):return bool(ptype in ('read','select') and doc.name in names(doc.doctype,user))


@frappe.whitelist(methods=['GET'])
def position(center,practitioner):
    require_finance(center)
    rows=current_rows('CC Professional Expectation',{'center':center,'practitioner':practitioner},fields=['name','appointment','source','state','amount','currency','creation','rule','problem'])
    latest={}
    for row in sorted(rows,key=lambda r:(r.creation,r.name)):latest[row.appointment]=row
    comparisons=current_rows('CC Professional Comparison',{'center':center,'practitioner':practitioner},fields=['name','purchase_invoice','state','expected_amount','received_amount','problem','creation'])
    unknown=any(r.state!='OK' for r in latest.values())
    return {'state':'REVIEW' if unknown else 'OK','known_expected':sum(r.amount for r in latest.values() if r.state=='OK'),
        'expected_amount':None if unknown else sum(r.amount for r in latest.values()),'unresolved_count':sum(r.state!='OK' for r in latest.values()),
        'sessions':list(latest.values()),'comparisons':comparisons,'currency':'EUR'}
