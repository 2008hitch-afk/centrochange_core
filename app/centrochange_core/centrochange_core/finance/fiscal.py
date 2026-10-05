"""Provider-neutral retained transactions and append-only normalized attempts."""
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,is_manager,centers,names_condition
from centrochange_core.finance.guards import allowed,require_finance,require_synthetic
from centrochange_core.operations.integrity import immutable as protected_attempt

RAW=('center','domain','direction','reference_doctype','reference_name','document_version','payload_hash','input_snapshot','configuration_ref','route','request_key','request_hash','version_key','external_message_id','corrects','recorded_by')
MAX_ATTEMPTS=3


def digest(value):return sha256(serialize(value).encode()).hexdigest()


def guard():
    require_synthetic()
    if frappe.utils.cint(frappe.db.get_single_value('CC Finance Settings','simulation_only'))!=1:
        frappe.throw('Only the synthetic SIMULATED fiscal route is authorized',frappe.PermissionError)


def protected(doc,method=None):
    old=doc.get_doc_before_save()
    if method=='on_trash' or not frappe.flags.get('cc_fiscal_write'):
        frappe.throw('Fiscal transactions require audited adapter services',frappe.PermissionError)
    if old and (any(doc.get(k)!=old.get(k) for k in RAW) or old.payload_file and doc.payload_file!=old.payload_file):
        frappe.throw('Fiscal source payload and version identity are immutable',frappe.PermissionError)
    if doc.route!='SIMULATED' or doc.configuration_ref!='SYNTHETIC_UNVERIFIED':
        frappe.throw('Real fiscal transport configuration is not authorized',frappe.PermissionError)


def transaction(name,write=False):
    doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=write);require_finance(doc.center,write);guard();return doc


def retain(data,payload,reason):
    raw=payload.encode('utf-8') if isinstance(payload,str) else payload
    if not raw or len(raw)>1024*1024:frappe.throw('Retained fiscal payload must be bounded nonempty local bytes')
    if sha256(raw).hexdigest()!=data['payload_hash']:frappe.throw('Fiscal payload digest differs')
    with internal_write('cc_fiscal_write'):
        doc=frappe.get_doc({'doctype':'CC Fiscal Transaction',**data,'route':'SIMULATED','configuration_ref':'SYNTHETIC_UNVERIFIED','recorded_by':frappe.session.user}).insert(ignore_permissions=True)
        file=frappe.get_doc({'doctype':'File','file_name':'CC-FISCAL-'+doc.payload_hash+'.payload','attached_to_doctype':doc.doctype,'attached_to_name':doc.name,'is_private':1,'content':raw}).insert(ignore_permissions=True)
        doc.payload_file=file.name;doc.save(ignore_permissions=True)
    append('FISCAL_PAYLOAD_PREPARED',doc.doctype,doc.name,None,{'domain':doc.domain,'direction':doc.direction,'payload_hash':doc.payload_hash,'status':doc.status},reason)
    return doc


def result(doc,replay=False):
    return {'name':doc.name,'domain':doc.domain,'direction':doc.direction,'status':doc.status,'attempt_count':doc.attempt_count,
        'route':doc.route,'retryable':bool(doc.retryable),'error_class':doc.error_class,'external_protocol':doc.external_protocol,
        'payload_hash':doc.payload_hash,'payload_file':doc.payload_file,'replay':replay,'simulated':True}


def replay(request_key,request_hash,version_key,center):
    old=frappe.db.get_value('CC Fiscal Transaction',{'request_key':request_key},['name','center','request_hash'],as_dict=True,for_update=True)
    if old:
        require_finance(old.center,True)
        if old.center!=center or old.request_hash!=request_hash:frappe.throw('Fiscal idempotency key payload differs')
        return frappe.get_doc('CC Fiscal Transaction',old.name,for_update=True)
    name=frappe.db.get_value('CC Fiscal Transaction',{'version_key':version_key},for_update=True)
    if name:
        doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=True)
        if doc.center!=center:frappe.throw('Fiscal message belongs to a different center',frappe.PermissionError)
        require_finance(doc.center,True)
        if doc.request_hash!=request_hash:frappe.throw('Existing fiscal version has a different correction/input context')
        return doc


@frappe.whitelist(methods=['GET'])
def status(name):
    doc=transaction(name)
    return {**result(doc),'attempts':current_rows('CC Fiscal Attempt',{'transaction':doc.name},fields=['name','sequence','status','route','payload_hash','state_history_json','external_protocol','retryable','error_class','receipt_json','origin_actor','processed_by'])}


def names(dt,user=None):
    if not allowed(user):return []
    return current_rows(dt,{} if is_manager(user) else {'center':['in',centers(user) or ['']]},pluck='name')
def transaction_query(user=None):return names_condition('CC Fiscal Transaction',names('CC Fiscal Transaction',user))
def attempt_query(user=None):return names_condition('CC Fiscal Attempt',names('CC Fiscal Attempt',user))
def permission(doc,user=None,ptype=None):return bool(ptype in ('read','select') and doc.name in names(doc.doctype,user))


@frappe.whitelist(methods=['GET'])
def records(center,domain):
    require_finance(center)
    if domain not in ('SDI','TS'):frappe.throw('Unsupported fiscal domain')
    rows=current_rows('CC Fiscal Transaction',{'center':center,'domain':domain},fields=['name','direction','reference_doctype','reference_name','status','attempt_count','retryable','error_class','external_protocol','corrects'])
    if len(rows)>500:frappe.throw('Narrow the fiscal workspace before listing more than 500 records')
    return rows
