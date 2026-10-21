"""Independent synthetic TS expense contract; real fiscal eligibility remains a gate."""
from hashlib import sha256
import frappe
from centrochange_core.finance import fiscal
from centrochange_core.finance.guards import require_finance,require_finance_manager
from centrochange_core.finance.professional_economics import number
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock

OUTCOMES={'Accepted':'ACCEPTED','Rejected':'REJECTED','Correction Required':'CORRECTION_REQUIRED','Retryable Failure':'RETRY_REQUIRED','Terminal Failure':'FAILED_TERMINAL'}


def context(source,invoice,write=True):
    src=frappe.get_doc('CC Economic Source Link',source,for_update=write);require_finance(src.center,write)
    doc=frappe.get_doc('Sales Invoice',invoice,for_update=write)
    if doc.docstatus!=1 or doc.cc_center!=src.center or doc.customer!=src.customer or not any(i.cc_economic_source==source for i in doc.items):
        frappe.throw('La spesa TS richiede una fonte esatta conservata nella fattura contabilizzata.')
    if doc.cc_fiscal_profile!='SYNTHETIC_UNVERIFIED' or doc.currency!='EUR':frappe.throw('Sono ammessi solo dati fiscali demo espliciti e fittizi.')
    return src,doc


@frappe.whitelist(methods=['POST'])
@atomic
def review_inputs(source,invoice,opposition,eligibility,request_key,reason,expense_amount=None,expense_code=None,subject_ref='SYNTHETIC_SUBJECT',transmitter_ref='SYNTHETIC_TRANSMITTER'):
    lock();fiscal.guard();require_finance_manager();src,doc=context(source,invoice)
    if opposition not in ('UNSET','Opposed','No Opposition') or eligibility not in ('UNSET','SYNTHETIC_ELIGIBLE','SYNTHETIC_INELIGIBLE'):
        frappe.throw('Indica esplicitamente opposizione ed eligibilità sintetica.')
    if not request_key or len(request_key)>160 or subject_ref!='SYNTHETIC_SUBJECT' or transmitter_ref!='SYNTHETIC_TRANSMITTER':
        frappe.throw('Sono autorizzati solo soggetto e trasmittente fittizi.')
    amount=number(expense_amount) if expense_amount not in (None,'') else None
    if amount is not None and (amount<=0 or amount>number(doc.grand_total)):
        frappe.throw('L’importo della spesa deve essere positivo e non superare il totale della fattura.')
    if eligibility=='SYNTHETIC_ELIGIBLE' and (amount is None or not expense_code or not expense_code.startswith('SYNTHETIC_') or len(expense_code)>100):
        frappe.throw('L’eligibilità sintetica richiede importo e classificazione fittizia espliciti.')
    data={'center':src.center,'source':src.name,'invoice':doc.name,'patient':src.patient,'opposition':opposition,'eligibility':eligibility,
        'expense_amount':float(amount) if amount is not None else None,'expense_amount_known':int(amount is not None),'expense_code':expense_code,
        'currency':doc.currency,'subject_ref':subject_ref,'transmitter_ref':transmitter_ref}
    key=fiscal.digest(['TS_INPUT',src.center,request_key]);digest=fiscal.digest(data)
    old=frappe.db.get_value('CC TS Input Review',{'request_key':key},['name','payload_hash'],as_dict=True,for_update=True)
    if old:
        if old.payload_hash!=digest:frappe.throw('La richiesta di revisione TS è già stata usata con dati diversi.')
        return {'name':old.name,'replay':True}
    with internal_write('cc_operation_write'):
        review=frappe.get_doc({'doctype':'CC TS Input Review',**data,'request_key':key,'payload_hash':digest,'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('TS_SYNTHETIC_INPUT_REVIEWED',review.doctype,review.name,None,{'source':source,'opposition':opposition,'eligibility':eligibility,'snapshot_hash':digest},reason)
    return {'name':review.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def prepare(source,invoice,request_key,reason,input_review=None,corrects=None):
    lock();fiscal.guard();src,doc=context(source,invoice)
    if not request_key or len(request_key)>160:frappe.throw('Indica un identificativo valido per la richiesta TS.')
    reviewed={'opposition':'UNSET','eligibility':'UNSET','expense_amount':None,'expense_code':None,'subject_ref':'SYNTHETIC_SUBJECT','transmitter_ref':'SYNTHETIC_TRANSMITTER'}
    if input_review:
        review=frappe.get_doc('CC TS Input Review',input_review,for_update=True)
        if (review.center,review.source,review.invoice,review.patient)!=(src.center,source,invoice,src.patient):
            frappe.throw('La revisione TS non corrisponde alla spesa selezionata.',frappe.PermissionError)
        reviewed={k:review.get(k) for k in reviewed};reviewed['expense_amount']=review.expense_amount if review.expense_amount_known else None
    ready=reviewed['eligibility']=='SYNTHETIC_ELIGIBLE' and reviewed['opposition']=='No Opposition' and reviewed['expense_amount'] is not None
    snapshot={'source':source,'appointment':src.appointment,'invoice':invoice,'patient':src.patient,
        'fictional_patient_identifier':'SYNTHETIC-PATIENT-'+fiscal.digest(src.patient)[:20],'currency':doc.currency,
        'native_document_gross':doc.grand_total,'native_document_outstanding':doc.outstanding_amount,'posting_date':str(doc.posting_date),
        'source_historical_price':src.price,'source_session_date':str(src.session_date),'input_review':input_review,
        'commercialista_verified':False,'simulated':True,**reviewed}
    payload=serialize(snapshot).encode('utf-8');digest=sha256(payload).hexdigest()
    if corrects:
        old=fiscal.transaction(corrects,True)
        if old.domain!='TS' or old.center!=src.center or old.reference_name!=source or old.status not in ('ELIGIBILITY_PENDING','REJECTED','CORRECTION_REQUIRED','FAILED_TERMINAL'):
            frappe.throw('La correzione TS richiede la spesa originale non risolta nello stesso contesto.')
        if old.payload_hash==digest:frappe.throw('La correzione TS deve conservare una versione distinta dei dati verificati.')
    key=fiscal.digest(['TS',src.center,request_key]);version=fiscal.digest(['TS',source,invoice,digest])
    fingerprint=fiscal.digest([snapshot,corrects]);old=fiscal.replay(key,fingerprint,version,src.center)
    if old:return fiscal.result(old,True)
    if ready:
        from centrochange_core.security.guards import current_rows
        existing=current_rows('CC Fiscal Transaction',{'domain':'TS','reference_name':source},fields=['name','status','input_snapshot'])
        same_expense=[r for r in existing if frappe.parse_json(r.input_snapshot).get('invoice')==invoice and r.status!='ELIGIBILITY_PENDING']
        if same_expense and not corrects:
            frappe.throw('La spesa ha già una versione TS: usa la catena di correzione verificata.')
        if corrects:
            # A rejected ancestor cannot branch around an already accepted/pending successor.
            blockers=[r for r in same_expense if r.name!=corrects and r.status in ('READY','SUBMITTED','ACCEPTED','RETRY_REQUIRED')]
            if blockers:frappe.throw('La spesa ha già una versione TS successiva attiva o accettata.')
    prepared=fiscal.retain({'center':src.center,'domain':'TS','direction':'OUTBOUND','reference_doctype':'CC Economic Source Link','reference_name':source,
        'document_version':digest,'payload_hash':digest,'input_snapshot':serialize(snapshot),'request_key':key,'request_hash':fingerprint,'version_key':version,
        'status':'READY' if ready else 'ELIGIBILITY_PENDING','error_class':None if ready else 'UNVERIFIED_ELIGIBILITY_OR_OPPOSITION','corrects':corrects},payload,reason)
    return fiscal.result(prepared)


class SimulatedTsAdapter:
    route='SIMULATED'
    def submit(self,payload,idempotency_key,outcome):
        if outcome not in OUTCOMES:frappe.throw('Seleziona un esito TS simulato supportato.')
        status=OUTCOMES[outcome];protocol='SYNTHETIC-TS-'+fiscal.digest([idempotency_key,sha256(payload).hexdigest()])[:24]
        error={'REJECTED':'SYNTHETIC_TS_REJECTION','CORRECTION_REQUIRED':'SYNTHETIC_TS_CORRECTION','RETRY_REQUIRED':'SYNTHETIC_TS_TRANSIENT','FAILED_TERMINAL':'SYNTHETIC_TS_TERMINAL'}.get(status)
        snapshot=frappe.parse_json(payload.decode('utf-8'))
        return {'status':status,'external_protocol':protocol,'retryable':status=='RETRY_REQUIRED','error_class':error,
            'receipt':{'simulated':True,'protocol':protocol,'status':status,'items':[{'source':snapshot['source'],'status':status,'error_class':error}]}}


@frappe.whitelist(methods=['POST'])
@atomic
def queue(name,attempt_key,outcome,reason):
    lock();doc=fiscal.transaction(name,True)
    if doc.domain!='TS' or doc.direction!='OUTBOUND' or outcome not in OUTCOMES or not attempt_key or len(attempt_key)>160:
        frappe.throw('È richiesto un tentativo TS sintetico esplicito.')
    key=fiscal.digest([name,attempt_key]);fingerprint=fiscal.digest([name,outcome,doc.payload_hash])
    old=frappe.db.get_value('CC Fiscal Attempt',{'attempt_key':key},['name','request_hash'],as_dict=True,for_update=True)
    if old:
        if old.request_hash!=fingerprint:frappe.throw('Il tentativo TS è già stato usato con dati diversi.')
        return fiscal.result(doc,True)
    if doc.status=='SUBMITTED':
        if doc.pending_attempt_key!=key or doc.pending_outcome!=outcome:frappe.throw('Un altro tentativo TS è già in attesa.')
        return fiscal.result(doc,True)
    if doc.status not in ('READY','RETRY_REQUIRED') or doc.attempt_count>=fiscal.MAX_ATTEMPTS:
        frappe.throw('Eligibilità, stato o limite dei tentativi non consentono l’invio simulato.')
    before={'status':doc.status,'attempt_count':doc.attempt_count}
    with internal_write('cc_fiscal_write'):
        doc.status='SUBMITTED';doc.pending_attempt_key=key;doc.pending_outcome=outcome;doc.pending_actor=frappe.session.user;doc.retryable=0;doc.save(ignore_permissions=True)
    append('TS_SIMULATED_SUBMITTED',doc.doctype,doc.name,before,{'status':doc.status,'attempt_key':key},reason)
    frappe.enqueue('centrochange_core.finance.ts.dispatch',queue='short',enqueue_after_commit=True,name=doc.name)
    return fiscal.result(doc)


@atomic
def dispatch(name):
    previous=frappe.session.user
    try:
        from centrochange_core.operations.install import AUTOMATION_USER
        frappe.set_user(AUTOMATION_USER);lock();fiscal.guard()
        doc=frappe.get_doc('CC Fiscal Transaction',name,for_update=True)
        if doc.domain!='TS' or doc.direction!='OUTBOUND' or doc.status!='SUBMITTED':return {'replay':True}
        file=frappe.get_doc('File',doc.payload_file);payload=file.get_content();payload=payload.encode('utf-8') if isinstance(payload,str) else payload
        if not file.is_private or sha256(payload).hexdigest()!=doc.payload_hash:frappe.throw('La verifica di integrità dei dati TS conservati non è riuscita.')
        response=SimulatedTsAdapter().submit(payload,doc.pending_attempt_key,doc.pending_outcome)
        count=doc.attempt_count+1;status=response['status']
        if count>=fiscal.MAX_ATTEMPTS and response['retryable']:
            status='FAILED_TERMINAL';response.update(status=status,retryable=False,error_class='SYNTHETIC_TS_RETRY_EXHAUSTED');response['receipt']['status']=status;response['receipt']['items'][0].update(status=status,error_class=response['error_class'])
        with internal_write('cc_operation_write'):
            attempt=frappe.get_doc({'doctype':'CC Fiscal Attempt','transaction':doc.name,'center':doc.center,'sequence':count,
                'attempt_key':doc.pending_attempt_key,'request_hash':fiscal.digest([doc.name,doc.pending_outcome,doc.payload_hash]),'payload_hash':doc.payload_hash,
                'route':'SIMULATED','status':status,'state_history_json':serialize(['READY','SUBMITTED',status]),'external_protocol':response['external_protocol'],
                'retryable':int(response['retryable']),'error_class':response['error_class'],'receipt_json':serialize(response['receipt']),
                'origin_actor':doc.pending_actor,'processed_by':AUTOMATION_USER}).insert(ignore_permissions=True)
        with internal_write('cc_fiscal_write'):
            doc.status=status;doc.attempt_count=count;doc.external_protocol=response['external_protocol'];doc.retryable=int(response['retryable']);doc.error_class=response['error_class'];doc.pending_attempt_key=None;doc.pending_outcome=None;doc.pending_actor=None;doc.save(ignore_permissions=True)
        append('TS_SIMULATED_RESULT',doc.doctype,doc.name,{'status':'SUBMITTED'},{'status':status,'attempt':attempt.name,'simulated':True},'Synthetic independent TS worker result')
        return fiscal.result(doc)
    finally:frappe.set_user(previous)


def catch_up():
    fiscal.guard()
    from centrochange_core.security.guards import current_rows
    for name in current_rows('CC Fiscal Transaction',{'domain':'TS','status':'SUBMITTED'},pluck='name'):
        frappe.enqueue('centrochange_core.finance.ts.dispatch',queue='short',enqueue_after_commit=True,name=name)


def review_query(user=None):return fiscal.names_condition('CC TS Input Review',fiscal.names('CC TS Input Review',user))
