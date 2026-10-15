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
    except (InvalidOperation,ValueError):frappe.throw('Indica un importo economico valido.')
    if not result.is_finite() or result<0 or result>Decimal('1000000000'):frappe.throw('L’importo economico è fuori dai limiti consentiti.')
    return result


def _practitioner(practitioner,center):
    user=frappe.db.get_value('Healthcare Practitioner',practitioner,'user_id',for_update=True)
    if not user or not current_rows('CC Center Membership',{'user':user,'center':center,'active':1},pluck='name'):
        frappe.throw('Il contesto del professionista nella sede non è disponibile.',frappe.PermissionError)


@frappe.whitelist(methods=['POST'])
@atomic
def configure_rule(center,practitioner,service_item,valid_from,basis,value,currency,request_key,reason,valid_to=None):
    lock();require_finance_manager();require_synthetic();_practitioner(practitioner,center)
    value=number(value)
    if basis not in ('Fixed Amount','Percentage') or basis=='Percentage' and value>100:
        frappe.throw('Seleziona una base di compenso supportata.')
    start=frappe.utils.getdate(valid_from);end=frappe.utils.getdate(valid_to) if valid_to else None
    if not valid_from or end and end<start or currency!='EUR' or not request_key or len(request_key)>140:
        frappe.throw('Indica date, valuta e identificativo della regola.')
    item=frappe.get_doc('Item',service_item)
    if item.disabled or item.is_stock_item:frappe.throw('Seleziona un servizio attivo.')
    data=dict(center=center,practitioner=practitioner,service_item=service_item,valid_from=start,valid_to=end,
        basis=basis,value=float(value),currency=currency)
    old=frappe.db.get_value('CC Compensation Rule',{'request_key':request_key},['name','payload_hash'],as_dict=True,for_update=True)
    if old:
        if old.payload_hash!=digest(data):frappe.throw('La regola è già stata registrata con dati diversi.')
        return {'name':old.name,'replay':True}
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Compensation Rule',**data,'request_key':request_key,'payload_hash':digest(data),'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_RULE_CONFIGURED',doc.doctype,doc.name,None,data,reason)
    return {'name':doc.name,'replay':False}


POLICY = 'HC-0005 DECISION-054'


def latest_expectations(center=None):
    rows=current_rows('CC Professional Expectation', {'center':center} if center else {}, fields=['*'])
    latest={}
    for row in sorted(rows,key=lambda r:(r.sequence or 0,r.creation,r.name)):
        latest[row.appointment]=row
    return latest


def threshold(practitioner):
    rows=current_rows('CC Unpaid Threshold',{'practitioner':practitioner},fields=['*'])
    return max(rows,key=lambda r:r.sequence) if rows else None


@frappe.whitelist(methods=['POST'])
@atomic
def configure_threshold(center,practitioner,max_unpaid_sessions_compensated,request_key,reason):
    lock();require_finance_manager();require_synthetic();_practitioner(practitioner,center)
    raw=str(max_unpaid_sessions_compensated)
    if not raw.isascii() or not raw.isdigit() or len(raw)>10 or int(raw)>2147483647:
        frappe.throw('Indica una soglia intera pari o superiore a zero.')
    if not request_key or len(request_key)>140:frappe.throw('Indica un identificativo per la richiesta.')
    data={'center':center,'practitioner':practitioner,'max_unpaid_sessions_compensated':int(raw)}
    old=frappe.db.get_value('CC Unpaid Threshold',{'request_key':request_key},['name','payload_hash'],as_dict=True,for_update=True)
    if old:
        if old.payload_hash!=digest(data):frappe.throw('La soglia è già stata registrata con dati diversi.')
        return {'name':old.name,'replay':True}
    previous=threshold(practitioner)
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Unpaid Threshold',**data,'sequence':(previous.sequence if previous else 0)+1,
            'request_key':request_key,'payload_hash':digest(data),'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_UNPAID_THRESHOLD_CONFIGURED',doc.doctype,doc.name,
        dict(previous) if previous else None,data,reason)
    _reevaluate(center,reason)
    from centrochange_core.finance.admin_queue import _refresh
    _refresh(center,reason)
    return {'name':doc.name,'replay':False}


def patient_paid(source):
    invoices=frappe.db.sql('''select distinct p.name,p.outstanding_amount,p.docstatus,p.is_return
        from `tabSales Invoice` p join `tabSales Invoice Item` i on i.parent=p.name
        join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
        where s.appointment=%s and p.docstatus=1 and p.is_return=0 for update''',(source.appointment,),as_dict=True)
    # Native invoice outstanding is authoritative when present. Operational corrections
    # are current audited facts, not the obsolete paid flag in a retained source snapshot.
    return all(row.outstanding_amount<=0 for row in invoices) if invoices else bool(
        frappe.db.get_value('Patient Appointment',source.appointment,'cc_paid',for_update=True))


def unpaid_pair(src):
    rows=current_rows('Patient Appointment',{'patient':src.patient,'practitioner':src.practitioner,'cc_performed':1},
        fields=['name','appointment_date','appointment_time','cc_paid'])
    unpaid=[]
    for row in sorted(rows,key=lambda r:(frappe.utils.getdate(r.appointment_date),frappe.utils.get_time(r.appointment_time),r.name)):
        if not patient_paid(frappe._dict(appointment=row.name)):unpaid.append(row.name)
    return unpaid


def _capture(src,reason,rule=None,override=False):
    previous=latest_expectations(src.center).get(src.appointment)
    snapshot={};problem=None;amount=None;paid=patient_paid(src)
    config=threshold(src.practitioner);unpaid=unpaid_pair(src)
    rank=unpaid.index(src.appointment)+1 if src.appointment in unpaid else 0
    visible=set(current_rows('Patient Appointment',{'cc_center':src.center,'name':['in',unpaid or ['']]},pluck='name'))
    scoped_unpaid=[name for name in unpaid if name in visible]
    performed=frappe.db.get_value('Patient Appointment',src.appointment,'cc_performed',for_update=True)
    # A manual exception persists for this source session; it never changes unpaid facts.
    override=bool(override or previous and previous.manual_override)
    if rule:
        doc=frappe.get_doc('CC Compensation Rule',rule,for_update=True)
        if (doc.center,doc.practitioner,doc.service_item,doc.currency)!=(src.center,src.practitioner,src.service_item,src.currency):
            frappe.throw('La regola di compenso non corrisponde alla seduta selezionata.')
        if not doc.valid_from<=frappe.utils.getdate(src.session_date) or doc.valid_to and doc.valid_to<frappe.utils.getdate(src.session_date):
            frappe.throw('La regola non è valida nella data della seduta.')
        snapshot={k:doc.get(k) for k in ('name','valid_from','valid_to','basis','value','currency')}
    else:problem='Compensation Rule Unset'
    if not performed:problem='Eligibility Requires Review'
    elif not config:problem='Professional Unpaid Threshold Missing'
    suspended=bool(not problem and not paid and rank>config.max_unpaid_sessions_compensated and not override)
    if not problem and not suspended:
        amount=float((number(snapshot['value']) if snapshot['basis']=='Fixed Amount' else number(src.price)*number(snapshot['value'])/100).quantize(Decimal('.01')))
    data={'center':src.center,'source':src.name,'appointment':src.appointment,'patient':src.patient,
        'practitioner':src.practitioner,'supplier':src.supplier,'rule':rule,'rule_snapshot':serialize(snapshot),
        'policy_snapshot':POLICY,'paid_snapshot':int(paid),'state':'REVIEW' if problem else 'SUSPENDED' if suspended else 'OK',
        'problem':problem or ('Unpaid Threshold Exceeded' if suspended else None),'amount_known':int(amount is not None),'amount':amount,'currency':src.currency,
        'threshold_config':config.name if config else None,'threshold_snapshot':config.max_unpaid_sessions_compensated if config else 0,
        'threshold_configured':int(bool(config)),'unpaid_count':len(unpaid),'unpaid_rank':rank,
        'unpaid_sessions_json':serialize(scoped_unpaid),'manual_override':int(override)}
    facts={k:data[k] for k in ('source','patient','practitioner','paid_snapshot','threshold_config','threshold_configured','threshold_snapshot','unpaid_count','unpaid_rank','unpaid_sessions_json','state','rule_snapshot')}
    data['original_facts']=previous.original_facts if previous and previous.original_facts else serialize(facts)
    # Compare only with the latest state. Returning a retained old snapshot would make
    # reversal/recapture fail to become the current state.
    def stored(k):
        return None if k=='amount' and not previous.amount_known else previous.get(k)
    if previous and all(stored(k)==v or stored(k) in (None,'') and v in (None,'') for k,v in data.items()):
        return {'name':previous.name,'replay':True,'state':data['state'],'amount':amount}
    data['sequence']=(previous.sequence if previous else 0)+1
    data['previous_expectation']=previous.name if previous else None
    key=digest(data)
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Professional Expectation',**data,'snapshot_hash':key,'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PROFESSIONAL_EXPECTATION_OVERRIDDEN' if override and not (previous and previous.manual_override) else 'PROFESSIONAL_EXPECTATION_CAPTURED',
        doc.doctype,doc.name,dict(previous) if previous else None,{**data,'snapshot_hash':key},reason)
    return {'name':doc.name,'replay':False,'state':data['state'],'amount':amount}


@frappe.whitelist(methods=['POST'])
@atomic
def capture(source,reason,rule=None):
    lock();require_synthetic()
    src=frappe.get_doc('CC Economic Source Link',source,for_update=True);require_finance(src.center,True)
    result=_capture(src,reason,rule)
    from centrochange_core.finance.admin_queue import _refresh
    _refresh(src.center,reason)
    return result


def _reevaluate(center,reason):
    results=[]
    for row in latest_expectations(center).values():
        results.append(_capture(frappe.get_doc('CC Economic Source Link',row.source,for_update=True),reason,row.rule))
    return results


@frappe.whitelist(methods=['POST'])
@atomic
def reevaluate(center,reason):
    lock();require_synthetic();require_finance(center,True)
    results=_reevaluate(center,reason)
    from centrochange_core.finance.admin_queue import _refresh
    return {'expectations':results,'queue':_refresh(center,reason)}


@frappe.whitelist(methods=['POST'])
@atomic
def override(expectation,reason):
    lock();require_synthetic();require_finance_manager()
    old=frappe.get_doc('CC Professional Expectation',expectation,for_update=True);require_finance(old.center,True)
    current=latest_expectations(old.center).get(old.appointment)
    if current.manual_override:
        return {'name':current.name,'replay':True,'state':current.state,'amount':current.amount}
    if old.name!=current.name or current.state!='SUSPENDED':frappe.throw('Seleziona il compenso sospeso corrente della seduta.')
    result=_capture(frappe.get_doc('CC Economic Source Link',old.source,for_update=True),reason,old.rule,True)
    from centrochange_core.finance.admin_queue import _refresh
    _refresh(old.center,reason)
    return result


def payment_changed(doc,method=None):
    # Supported native post-submit/cancel hook, after outstanding amounts are updated.
    if not doc.get('cc_center') or not frappe.conf.get('cc_synthetic_dev'):return
    lock();require_synthetic()
    _reevaluate(doc.cc_center,'Native payment/source change: '+doc.doctype+' '+doc.name+' '+str(method))
    from centrochange_core.finance.admin_queue import _refresh
    _refresh(doc.cc_center,'Native payment/source administrative reconciliation')


@frappe.whitelist(methods=['POST'])
@atomic
def compare(purchase_invoice,expectations,reason):
    lock();require_synthetic()
    invoice=frappe.get_doc('Purchase Invoice',purchase_invoice,for_update=True);require_finance(invoice.cc_center,True)
    ids=frappe.parse_json(expectations) if isinstance(expectations,str) else expectations
    if not isinstance(ids,list) or not ids or len(ids)>500 or len(set(ids))!=len(ids):frappe.throw('Seleziona sedute attese distinte.')
    if invoice.docstatus!=1 or invoice.is_return:frappe.throw('Seleziona una fattura fornitore ordinaria e contabilizzata.')
    rows=[frappe.get_doc('CC Professional Expectation',name,for_update=True) for name in sorted(ids)]
    contexts={(r.center,r.practitioner,r.supplier,r.currency) for r in rows}
    if len(contexts)!=1 or next(iter(contexts))!=(invoice.cc_center,rows[0].practitioner,invoice.supplier,invoice.currency):
        frappe.throw('Il contesto del compenso atteso non corrisponde alla fattura ricevuta.',frappe.PermissionError)
    if len({r.appointment for r in rows})!=len(rows):frappe.throw('Una seduta non può comparire due volte nello stesso confronto.')
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
def threshold_query(user=None):return query('CC Unpaid Threshold',user)
def permission(doc,user=None,ptype=None):return bool(ptype in ('read','select') and doc.name in names(doc.doctype,user))


@frappe.whitelist(methods=['GET'])
def position(center,practitioner):
    require_finance(center)
    latest={a:r for a,r in latest_expectations(center).items() if r.practitioner==practitioner}
    comparisons=current_rows('CC Professional Comparison',{'center':center,'practitioner':practitioner},fields=['name','purchase_invoice','state','expected_amount','received_amount','problem','creation'])
    unknown=any(r.state!='OK' for r in latest.values())
    return {'state':'REVIEW' if unknown else 'OK','known_expected':sum(r.amount for r in latest.values() if r.state=='OK'),
        'expected_amount':None if unknown else sum(r.amount for r in latest.values()),'unresolved_count':sum(r.state!='OK' for r in latest.values()),
        'sessions':list(latest.values()),'comparisons':comparisons,'currency':'EUR'}
