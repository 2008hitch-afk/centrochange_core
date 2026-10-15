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
        frappe.throw('È autorizzata soltanto la simulazione fiscale con dati sintetici.',frappe.PermissionError)


def protected(doc,method=None):
    old=doc.get_doc_before_save()
    if method=='on_trash' or not frappe.flags.get('cc_fiscal_write'):
        frappe.throw('Le operazioni fiscali richiedono i servizi tracciati previsti.',frappe.PermissionError)
    if old and (any(doc.get(k)!=old.get(k) for k in RAW) or old.payload_file and doc.payload_file!=old.payload_file):
        frappe.throw('Documento fiscale originale e identità della versione non possono essere modificati.',frappe.PermissionError)
    if doc.route!='SIMULATED' or doc.configuration_ref!='SYNTHETIC_UNVERIFIED':
        frappe.throw('La configurazione per invii fiscali reali non è autorizzata.',frappe.PermissionError)


def transaction(name,write=False):
    doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=write);require_finance(doc.center,write);guard();return doc


def retain(data,payload,reason):
    raw=payload.encode('utf-8') if isinstance(payload,str) else payload
    if not raw or len(raw)>1024*1024:frappe.throw('Il documento fiscale conservato deve essere locale, non vuoto e nei limiti previsti.')
    if sha256(raw).hexdigest()!=data['payload_hash']:frappe.throw('L’impronta del documento fiscale non corrisponde.')
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
        if old.center!=center or old.request_hash!=request_hash:frappe.throw('La richiesta fiscale è già stata usata con dati diversi.')
        return frappe.get_doc('CC Fiscal Transaction',old.name,for_update=True)
    name=frappe.db.get_value('CC Fiscal Transaction',{'version_key':version_key},for_update=True)
    if name:
        doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=True)
        if doc.center!=center:frappe.throw('Il messaggio fiscale appartiene a un’altra sede.',frappe.PermissionError)
        require_finance(doc.center,True)
        if doc.request_hash!=request_hash:frappe.throw('La versione fiscale esistente ha dati o contesto di correzione diversi.')
        return doc


@frappe.whitelist(methods=['GET'])
def status(name):
    doc=transaction(name)
    attempts=current_rows('CC Fiscal Attempt',{'transaction':doc.name},fields=['name','sequence','status','route','payload_hash','state_history_json','external_protocol','retryable','error_class','receipt_json','origin_actor','processed_by'])
    return {**result(doc),'attempts':sorted(attempts,key=lambda row:(row.sequence,row.name))}


def names(dt,user=None):
    if not allowed(user):return []
    return current_rows(dt,{} if is_manager(user) else {'center':['in',centers(user) or ['']]},pluck='name')
def transaction_query(user=None):return names_condition('CC Fiscal Transaction',names('CC Fiscal Transaction',user))
def attempt_query(user=None):return names_condition('CC Fiscal Attempt',names('CC Fiscal Attempt',user))
def permission(doc,user=None,ptype=None):return bool(ptype in ('read','select') and doc.name in names(doc.doctype,user))


@frappe.whitelist(methods=['GET'])
def records(center,domain):
    require_finance(center)
    if domain not in ('SDI','TS'):frappe.throw('Il tipo di simulazione fiscale non è supportato.')
    rows=current_rows('CC Fiscal Transaction',{'center':center,'domain':domain},fields=['name','direction','reference_doctype','reference_name','status','attempt_count','retryable','error_class','external_protocol','corrects'])
    if len(rows)>500:frappe.throw('Riduci la ricerca fiscale per visualizzare meno di 500 record.')
    for row in rows:
        if row.reference_doctype=='Sales Invoice':
            invoice=frappe.db.get_value('Sales Invoice',row.reference_name,['customer','cc_center'],as_dict=True)
            if invoice and invoice.cc_center==center:
                row.reference_label=row.reference_name+' · '+(frappe.db.get_value('Customer',invoice.customer,'customer_name') or invoice.customer)
        elif row.reference_doctype=='CC Economic Source Link':
            source=frappe.db.get_value('CC Economic Source Link',row.reference_name,['customer','center','session_date'],as_dict=True)
            if source and source.center==center:
                row.reference_label=str(source.session_date)+' · '+(frappe.db.get_value('Customer',source.customer,'customer_name') or source.customer)
    return rows
