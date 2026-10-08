"""Pure simulated fiscal transport regression on synthetic native invoices."""
from hashlib import sha256
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import reporting_acceptance,receivables_acceptance,receivables,sdi,fiscal,incoming_acceptance,admin_queue


def checks(fixture):
    result=reporting_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    frappe.set_user('Administrator');center=fixture['center']
    invoices=frappe.get_all('Sales Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0},pluck='name')
    assert len(invoices)>=3
    correction_invoice=next(name for name in invoices if not frappe.db.exists('Payment Entry Reference',{'reference_doctype':'Sales Invoice','reference_name':name,'docstatus':1}))
    invoices=[name for name in invoices if name!=correction_invoice]+[correction_invoice]
    accepted=sdi.prepare(invoices[0],'synthetic-sdi-accepted','Synthetic native XML preparation')
    assert accepted['status']=='PREPARED' and accepted['route']=='SIMULATED'
    assert sdi.prepare(invoices[0],'synthetic-sdi-accepted','Synthetic prepare replay')['replay']
    assert sdi.prepare(invoices[0],'synthetic-sdi-alias','Synthetic same version dedupe')['name']==accepted['name']
    transaction=frappe.get_doc('CC Fiscal Transaction',accepted['name']);file=frappe.get_doc('File',transaction.payload_file)
    raw=file.get_content();raw=raw.encode('utf-8') if isinstance(raw,str) else raw
    assert file.is_private and sha256(raw).hexdigest()==transaction.payload_hash
    result.append('native submitted invoice version private XML digest and exact/semantic preparation dedupe without provider traffic')
    queued=sdi.queue(transaction.name,'synthetic-attempt-1','Accepted','Synthetic queued local transport')
    assert queued['status']=='QUEUED' and sdi.queue(transaction.name,'synthetic-attempt-1','Accepted','Synthetic queued replay')['replay']
    sdi.dispatch(transaction.name)
    assert fiscal.status(transaction.name)['status']=='ACCEPTED_OR_DELIVERED'
    assert sdi.queue(transaction.name,'synthetic-attempt-1','Accepted','Synthetic completed attempt replay')['replay']
    reject(lambda:sdi.queue(transaction.name,'synthetic-attempt-1','Rejected','Synthetic changed attempt payload'))
    reject(lambda:sdi.queue(transaction.name,'synthetic-attempt-2','Accepted','Synthetic terminal resubmission'))
    assert sdi.dispatch(transaction.name)['replay']
    result.append('simulated queued sent accepted normalized receipt protocol immutable attempt and result replay')
    retry=sdi.prepare(invoices[1],'synthetic-sdi-retry','Synthetic retryable transport')['name']
    for i in range(3):
        sdi.queue(retry,'synthetic-retry-'+str(i),'Retryable Failure','Synthetic bounded retry')
        sdi.dispatch(retry)
    state=fiscal.status(retry)
    assert state['status']=='FAILED_TERMINAL' and not state['retryable'] and len(state['attempts'])==3
    assert state['error_class']=='SYNTHETIC_RETRY_EXHAUSTED'
    reject(lambda:sdi.queue(retry,'synthetic-retry-4','Accepted','Synthetic retry limit denial'))
    assert all(a.processed_by=='cc-automation-service@example.invalid' and a.origin_actor=='Administrator' for a in state['attempts'])
    result.append('retry classification three-attempt exhaustion retained history sanitized failure and actor provenance')
    source_invoice=correction_invoice
    rejected=sdi.prepare(source_invoice,'synthetic-sdi-rejected','Synthetic rejection')['name']
    sdi.queue(rejected,'synthetic-reject-attempt','Rejected','Synthetic explicit rejection');sdi.dispatch(rejected)
    admin_queue.refresh(center,'Synthetic rejected fiscal queue')
    exception=frappe.db.get_value('CC Admin Exception',{'reference_doctype':'CC Fiscal Transaction','reference_name':rejected},'name')
    assert exception
    retained=frappe.get_doc('CC Fiscal Transaction',rejected);original_hash=retained.payload_hash
    receivables.cancel(source_invoice,'Synthetic native rejected document correction')
    native=receivables.amend(source_invoice,'2026-11-01','2026-11-30','synthetic-sdi-native-amend','Synthetic native correction')['name']
    receivables.submit(native,'Synthetic corrected document native submit')
    corrected=sdi.prepare(native,'synthetic-sdi-correction','Synthetic linked corrected fiscal version',corrects=rejected)['name']
    sdi.queue(corrected,'synthetic-corrected-attempt','Accepted','Synthetic corrected local result');sdi.dispatch(corrected)
    assert frappe.db.get_value('CC Fiscal Transaction',corrected,'corrects')==rejected
    raw=frappe.get_doc('File',retained.payload_file).get_content();raw=raw.encode('utf-8') if isinstance(raw,str) else raw
    assert sha256(raw).hexdigest()==original_hash
    admin_queue.refresh(center,'Synthetic corrected fiscal condition resolution')
    assert frappe.db.get_value('CC Admin Exception',exception,'state')=='Closed'
    result.append('rejected source survives native cancellation; linked amended payload accepted and condition auto-closes preserving original')
    payload=incoming_acceptance.xml(number='SYNTHETIC-SDI-INBOUND')
    before=frappe.db.count('Purchase Invoice')
    inbound=sdi.intake(center,'SYNTHETIC-INBOUND-1',payload,'Synthetic inbound simulated handoff')
    assert inbound['incoming_state']=='Needs Supplier Mapping' and frappe.db.count('Purchase Invoice')==before
    assert sdi.intake(center,'SYNTHETIC-INBOUND-1',payload,'Synthetic inbound replay')['replay']
    reject(lambda:sdi.intake(center,'SYNTHETIC-INBOUND-1',payload.replace('SYNTHETIC PROVIDER','CHANGED SYNTHETIC PROVIDER'),'Synthetic changed external message'))
    result.append('synthetic inbound external-message dedupe immutable WP04 handoff and explicit mapping exception without auto-submit')
    transaction.payload_hash='changed';reject(lambda:transaction.save(ignore_permissions=True))
    reject(lambda:frappe.delete_doc('CC Fiscal Transaction',transaction.name,ignore_permissions=True))
    attempt=frappe.get_doc('CC Fiscal Attempt',state['attempts'][0].name);reject(lambda:attempt.save(ignore_permissions=True))
    reject(lambda:frappe.share.add_docshare('CC Fiscal Transaction',transaction.name,user=fixture['pro1'],read=1,flags={'ignore_share_permission':True}))
    reject(lambda:frappe.delete_doc('File',file.name,ignore_permissions=True))
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid'):
        frappe.set_user(actor);reject(lambda:sdi.queue(transaction.name,'unauthorized','Accepted','Unauthorized fiscal mutation'))
        reject(lambda:sdi.intake(center,'SYNTHETIC-UNAUTHORIZED',payload,'Unauthorized intake'))
        if not actor.startswith('accountant'):
            reject(lambda:fiscal.status(transaction.name));reject(lambda:frappe.get_doc('File',file.name).check_permission('read'))
        else:assert fiscal.status(transaction.name)['status']=='ACCEPTED_OR_DELIVERED'
        result.append('professional and readonly Accountant fiscal mutation scope; source result and private payload permissions')
    frappe.set_user('Administrator');return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:return security.run(extra_checks=checks)
    finally:frappe.flags.cc_test_clock=previous
