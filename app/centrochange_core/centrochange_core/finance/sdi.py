"""Synthetic SdI contract implementation. No provider/PEC/network transport exists."""
from hashlib import sha256
import frappe
from centrochange_core.finance import fiscal,incoming
from centrochange_core.finance.guards import require_finance
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock

OUTCOMES={'Accepted':'ACCEPTED_OR_DELIVERED','Rejected':'REJECTED','Retryable Failure':'FAILED_RETRYABLE','Terminal Failure':'FAILED_TERMINAL'}


class SimulatedSdiAdapter:
    route='SIMULATED'
    def send(self,payload,idempotency_key,outcome):
        if outcome not in OUTCOMES:frappe.throw('Seleziona un esito SdI simulato esplicito.')
        status=OUTCOMES[outcome];protocol='SYNTHETIC-SDI-'+fiscal.digest([idempotency_key,sha256(payload).hexdigest()])[:24]
        return {'status':status,'external_protocol':protocol,'retryable':status=='FAILED_RETRYABLE',
            'error_class':{'REJECTED':'SYNTHETIC_REJECTION','FAILED_RETRYABLE':'SYNTHETIC_TRANSIENT','FAILED_TERMINAL':'SYNTHETIC_TERMINAL'}.get(status),
            'receipt':{'simulated':True,'protocol':protocol,'status':status}}


@frappe.whitelist(methods=['POST'])
@atomic
def prepare(invoice,request_key,reason,corrects=None):
    lock();fiscal.guard();doc=frappe.get_doc('Sales Invoice',invoice,for_update=True);require_finance(doc.cc_center,True)
    if doc.docstatus!=1 or doc.cc_fiscal_profile!='SYNTHETIC_UNVERIFIED':frappe.throw('Seleziona una fattura paziente demo contabilizzata.')
    if not request_key or len(request_key)>160:frappe.throw('Indica un identificativo valido per la richiesta fiscale.')
    files=frappe.get_all('File',filters={'attached_to_doctype':'Sales Invoice','attached_to_name':invoice,'is_private':1},fields=['name','file_name','creation'])
    files=[f for f in files if f.file_name.endswith('.xml')]
    if not files:frappe.throw('Manca il file XML nativo della fattura elettronica; non viene creato un documento fittizio.')
    file=frappe.get_doc('File',max(files,key=lambda f:(f.creation,f.name)).name)
    payload=file.get_content();payload=payload.encode('utf-8') if isinstance(payload,str) else payload
    digest=sha256(payload).hexdigest()
    if corrects:
        previous=fiscal.transaction(corrects,True)
        if previous.domain!='SDI' or previous.direction!='OUTBOUND' or previous.center!=doc.cc_center or previous.status not in ('REJECTED','FAILED_TERMINAL'):
            frappe.throw('La correzione richiede un originale rifiutato o definitivo nella stessa sede.')
        if not (doc.amended_from==previous.reference_name or doc.return_against==previous.reference_name):
            frappe.throw('La correzione richiede una rettifica nativa o una nota di credito supportata.')
    snapshot={'invoice':invoice,'payload_hash':digest,'corrects':corrects,'profile':'SYNTHETIC_UNVERIFIED'}
    key=fiscal.digest(['SDI','OUTBOUND',doc.cc_center,request_key]);version=fiscal.digest(['SDI','OUTBOUND',invoice,digest])
    old=fiscal.replay(key,fiscal.digest(snapshot),version,doc.cc_center)
    if old:return fiscal.result(old,True)
    retained=fiscal.retain({'center':doc.cc_center,'domain':'SDI','direction':'OUTBOUND','reference_doctype':'Sales Invoice','reference_name':invoice,
        'document_version':digest,'payload_hash':digest,'input_snapshot':serialize(snapshot),'request_key':key,'request_hash':fiscal.digest(snapshot),
        'version_key':version,'status':'PREPARED','corrects':corrects},payload,reason)
    return fiscal.result(retained)


@frappe.whitelist(methods=['POST'])
@atomic
def intake(center,external_message_id,xml,reason):
    lock();fiscal.guard();require_finance(center,True)
    if not external_message_id or not external_message_id.startswith('SYNTHETIC-') or len(external_message_id)>160:
        frappe.throw('Indica un identificativo sintetico valido per il messaggio ricevuto.')
    if not isinstance(xml,str) or len(xml.encode('utf-8'))>1024*1024:frappe.throw('Il file XML deve essere presente e rispettare i limiti previsti.')
    raw=xml.encode('utf-8');payload_hash=sha256(raw).hexdigest()
    key=fiscal.digest(['SDI','INBOUND',external_message_id]);snapshot={'center':center,'message':external_message_id,'payload_hash':payload_hash}
    old=fiscal.replay(key,fiscal.digest(snapshot),key,center)
    if old:return {**fiscal.result(old,True),'incoming_source':old.reference_name}
    source=incoming.intake(center,xml,reason)['name']
    doc=fiscal.retain({'center':center,'domain':'SDI','direction':'INBOUND','reference_doctype':'CC Incoming Invoice','reference_name':source,
        'document_version':payload_hash,'payload_hash':payload_hash,'input_snapshot':serialize(snapshot),'request_key':key,'request_hash':fiscal.digest(snapshot),
        'version_key':key,'external_message_id':external_message_id,'status':'ACCEPTED_OR_DELIVERED'},raw,reason)
    append('SDI_SIMULATED_INBOUND_RETAINED',doc.doctype,doc.name,None,{'source':source,'message':external_message_id,'simulated':True},reason)
    return {**fiscal.result(doc),'incoming_source':source,'incoming_state':frappe.db.get_value('CC Incoming Invoice',source,'state')}


@frappe.whitelist(methods=['POST'])
@atomic
def queue(name,attempt_key,outcome,reason):
    lock();doc=fiscal.transaction(name,True)
    if doc.domain!='SDI' or doc.direction!='OUTBOUND' or outcome not in OUTCOMES or not attempt_key or len(attempt_key)>160:
        frappe.throw('Seleziona un tentativo SdI simulato in uscita supportato.')
    key=fiscal.digest([name,attempt_key]);fingerprint=fiscal.digest([name,outcome,doc.payload_hash])
    old=frappe.db.get_value('CC Fiscal Attempt',{'attempt_key':key},['name','request_hash'],as_dict=True,for_update=True)
    if old:
        if old.request_hash!=fingerprint:frappe.throw('Il tentativo fiscale è già stato usato con dati diversi.')
        return fiscal.result(doc,True)
    if doc.status=='QUEUED':
        if doc.pending_attempt_key!=key or doc.pending_outcome!=outcome:frappe.throw('Un altro tentativo fiscale è già in coda.')
        return fiscal.result(doc,True)
    if doc.status not in ('PREPARED','FAILED_RETRYABLE') or doc.attempt_count>=fiscal.MAX_ATTEMPTS:
        frappe.throw('Stato o limite dei tentativi non consentono un nuovo tentativo simulato.')
    before={'status':doc.status,'attempt_count':doc.attempt_count}
    with internal_write('cc_fiscal_write'):
        doc.status='QUEUED';doc.pending_attempt_key=key;doc.pending_outcome=outcome;doc.pending_actor=frappe.session.user;doc.retryable=0;doc.save(ignore_permissions=True)
    append('SDI_SIMULATED_QUEUED',doc.doctype,doc.name,before,{'status':doc.status,'attempt_key':key},reason)
    frappe.enqueue('centrochange_core.finance.sdi.dispatch',queue='short',enqueue_after_commit=True,name=doc.name)
    return fiscal.result(doc)


@atomic
def dispatch(name):
    previous=frappe.session.user
    try:
        from centrochange_core.operations.install import AUTOMATION_USER
        frappe.set_user(AUTOMATION_USER);lock();fiscal.guard()
        doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=True)
        if doc.domain!='SDI' or doc.direction!='OUTBOUND' or doc.status!='QUEUED':return {'replay':True}
        file=frappe.get_doc('File',doc.payload_file);payload=file.get_content();payload=payload.encode('utf-8') if isinstance(payload,str) else payload
        if not file.is_private or sha256(payload).hexdigest()!=doc.payload_hash:frappe.throw('La verifica di integrità del documento fiscale conservato non è riuscita.')
        response=SimulatedSdiAdapter().send(payload,doc.pending_attempt_key,doc.pending_outcome)
        count=doc.attempt_count+1;status=response['status']
        if count>=fiscal.MAX_ATTEMPTS and response['retryable']:
            status='FAILED_TERMINAL';response.update(status=status,retryable=False,error_class='SYNTHETIC_RETRY_EXHAUSTED');response['receipt']['status']=status
        with internal_write('cc_operation_write'):
            attempt=frappe.get_doc({'doctype':'CC Fiscal Attempt','transaction':doc.name,'center':doc.center,'sequence':count,
                'attempt_key':doc.pending_attempt_key,'request_hash':fiscal.digest([doc.name,doc.pending_outcome,doc.payload_hash]),'payload_hash':doc.payload_hash,
                'route':'SIMULATED','status':status,'state_history_json':serialize(['QUEUED','SENT',status]),'external_protocol':response['external_protocol'],
                'retryable':int(response['retryable']),'error_class':response['error_class'],'receipt_json':serialize(response['receipt']),
                'origin_actor':doc.pending_actor,
                'processed_by':AUTOMATION_USER}).insert(ignore_permissions=True)
        with internal_write('cc_fiscal_write'):
            doc.status=status;doc.attempt_count=count;doc.external_protocol=response['external_protocol'];doc.retryable=int(response['retryable']);doc.error_class=response['error_class'];doc.pending_attempt_key=None;doc.pending_outcome=None;doc.pending_actor=None;doc.save(ignore_permissions=True)
        append('SDI_SIMULATED_RESULT',doc.doctype,doc.name,{'status':'QUEUED'},{'status':status,'attempt':attempt.name,'simulated':True},'Synthetic provider-neutral SdI worker result')
        return fiscal.result(doc)
    finally:frappe.set_user(previous)


def catch_up():
    fiscal.guard()
    from centrochange_core.security.guards import current_rows
    for name in current_rows('CC Fiscal Transaction',{'domain':'SDI','direction':'OUTBOUND','status':'QUEUED'},pluck='name'):
        frappe.enqueue('centrochange_core.finance.sdi.dispatch',queue='short',enqueue_after_commit=True,name=name)
