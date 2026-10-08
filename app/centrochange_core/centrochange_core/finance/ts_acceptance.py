"""Independent synthetic TS snapshots, gates, protocol, retry and correction."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import sdi_acceptance,receivables_acceptance,ts,fiscal,admin_queue


def checks(fixture):
    result=sdi_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    frappe.set_user('Administrator');center=fixture['center']
    invoice=frappe.get_all('Sales Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0},pluck='name')[0]
    source=frappe.db.get_value('Sales Invoice Item',{'parent':invoice},'cc_economic_source')
    pending=ts.prepare(source,invoice,'synthetic-ts-pending','Synthetic unknown fiscal population')['name']
    assert fiscal.status(pending)['status']=='ELIGIBILITY_PENDING'
    assert ts.prepare(source,invoice,'synthetic-ts-pending','Synthetic pending replay')['replay']
    reject(lambda:ts.queue(pending,'synthetic-ts-pending-send','Accepted','Synthetic unresolved eligibility cannot submit'))
    admin_queue.refresh(center,'Synthetic TS eligibility condition')
    exception=frappe.db.get_value('CC Admin Exception',{'reference_doctype':'CC Fiscal Transaction','reference_name':pending},'name');assert exception
    result.append('TS source document patient and opposition snapshot default pending; unknown eligibility cannot submit or disappear from admin queue')
    args={'source':source,'invoice':invoice,'opposition':'Opposed','eligibility':'SYNTHETIC_ELIGIBLE','expense_amount':float(frappe.db.get_value('Sales Invoice',invoice,'grand_total')),
        'expense_code':'SYNTHETIC_EXPENSE','request_key':'synthetic-ts-opposed','reason':'Synthetic explicit opposition review'}
    opposed=ts.review_inputs(**args)['name'];assert ts.review_inputs(**args)['replay']
    hold=ts.prepare(source,invoice,'synthetic-ts-opposed-payload','Synthetic opposition handling unverified',opposed)['name']
    assert fiscal.status(hold)['status']=='ELIGIBILITY_PENDING'
    reject(lambda:ts.queue(hold,'synthetic-ts-opposed-send','Accepted','Synthetic opposed input cannot assume fiscal treatment'))
    doc=frappe.get_doc('CC TS Input Review',opposed);doc.opposition='No Opposition';reject(lambda:doc.save(ignore_permissions=True))
    reject(lambda:ts.review_inputs(**{**args,'opposition':'No Opposition'}))
    result.append('explicit immutable expense opposition review retained; opposed treatment stays gated and changed replay is denied')
    review=ts.review_inputs(**{**args,'opposition':'No Opposition','request_key':'synthetic-ts-ready'})['name']
    ready=ts.prepare(source,invoice,'synthetic-ts-ready-payload','Synthetic DEV eligibility version',review,corrects=pending)['name']
    assert fiscal.status(ready)['status']=='READY'
    snapshot=frappe.parse_json(frappe.db.get_value('CC Fiscal Transaction',ready,'input_snapshot'))
    assert snapshot['patient']==frappe.db.get_value('CC Economic Source Link',source,'patient') and snapshot['opposition']=='No Opposition'
    assert snapshot['commercialista_verified'] is False and snapshot['simulated'] is True
    branch_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_BRANCH','request_key':'synthetic-ts-live-branch'})['name']
    reject(lambda:ts.prepare(source,invoice,'synthetic-ts-live-branch-payload','Synthetic live correction branch denial',branch_review,corrects=pending))
    ts.queue(ready,'synthetic-ts-first-attempt','Retryable Failure','Synthetic TS transient attempt');ts.dispatch(ready)
    assert fiscal.status(ready)['status']=='RETRY_REQUIRED'
    assert ts.queue(ready,'synthetic-ts-first-attempt','Retryable Failure','Synthetic TS replay')['replay']
    ts.queue(ready,'synthetic-ts-second-attempt','Accepted','Synthetic TS explicit retry');ts.dispatch(ready)
    accepted=fiscal.status(ready)
    assert accepted['status']=='ACCEPTED' and len(accepted['attempts'])==2 and accepted['external_protocol'].startswith('SYNTHETIC-TS-')
    receipt=frappe.parse_json(accepted['attempts'][-1].receipt_json)
    assert receipt['items'][0]['source']==source and receipt['items'][0]['status']=='ACCEPTED'
    assert ts.dispatch(ready)['replay']
    reject(lambda:ts.queue(ready,'synthetic-ts-third-attempt','Accepted','Synthetic accepted resubmit denied'))
    admin_queue.refresh(center,'Synthetic accepted reviewed eligibility resolves original')
    assert frappe.db.get_value('CC Admin Exception',exception,'state')=='Closed'
    result.append('explicit DEV eligibility ready independent TS submitted transient retry accepted protocol item result and original condition auto-close')
    duplicate_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_DUPLICATE','request_key':'synthetic-ts-duplicate'})['name']
    reject(lambda:ts.prepare(source,invoice,'synthetic-ts-independent-duplicate','Synthetic duplicate expense denial',duplicate_review))
    result.append('a fresh review cannot independently submit the already accepted expense; explicit correction cannot branch around a live successor')
    pairs=[]
    for native in frappe.get_all('Sales Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0},pluck='name'):
        for row in frappe.get_all('Sales Invoice Item',filters={'parent':native},fields=['cc_economic_source']):
            if (row.cc_economic_source,native)!=(source,invoice):pairs.append((row.cc_economic_source,native))
    assert len(pairs)>=3
    source,invoice=pairs[0];args.update(source=source,invoice=invoice,expense_amount=float(frappe.db.get_value('CC Economic Source Link',source,'price')))
    other=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_CORRECTION_A','request_key':'synthetic-ts-correction-a'})['name']
    rejected=ts.prepare(source,invoice,'synthetic-ts-correction-a-payload','Synthetic correction-required version',other)['name']
    ts.queue(rejected,'synthetic-ts-correction-request','Correction Required','Synthetic TS normalized correction');ts.dispatch(rejected)
    assert fiscal.status(rejected)['status']=='CORRECTION_REQUIRED'
    corrected_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_CORRECTION_B','request_key':'synthetic-ts-correction-b'})['name']
    corrected=ts.prepare(source,invoice,'synthetic-ts-correction-b-payload','Synthetic explicit corrected TS input',corrected_review,corrects=rejected)['name']
    ts.queue(corrected,'synthetic-ts-corrected-accept','Accepted','Synthetic TS corrected result');ts.dispatch(corrected)
    assert fiscal.status(corrected)['status']=='ACCEPTED'
    assert fiscal.status(rejected)['status']=='CORRECTION_REQUIRED'
    assert frappe.db.get_value('CC Fiscal Transaction',corrected,'corrects')==rejected
    result.append('TS correction is a distinct reviewed immutable input version retaining original source protocol opposition and result')
    source,invoice=pairs[1];args.update(source=source,invoice=invoice,expense_amount=float(frappe.db.get_value('CC Economic Source Link',source,'price')))
    chain_review=ts.review_inputs(**{**args,'opposition':'UNSET','eligibility':'UNSET','request_key':'synthetic-ts-chain-root'})['name']
    chain=ts.prepare(source,invoice,'synthetic-ts-chain-root-payload','Synthetic unresolved correction ancestor',chain_review)['name']
    admin_queue.refresh(center,'Synthetic chain root condition')
    chain_exception=frappe.db.get_value('CC Admin Exception',{'reference_name':chain,'reference_doctype':'CC Fiscal Transaction'},'name');assert chain_exception
    middle_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_CHAIN_MIDDLE','request_key':'synthetic-ts-chain-middle'})['name']
    middle=ts.prepare(source,invoice,'synthetic-ts-chain-middle-payload','Synthetic first reviewed correction',middle_review,corrects=chain)['name']
    ts.queue(middle,'synthetic-ts-chain-middle-attempt','Correction Required','Synthetic second correction needed');ts.dispatch(middle)
    final_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_CHAIN_FINAL','request_key':'synthetic-ts-chain-final'})['name']
    final=ts.prepare(source,invoice,'synthetic-ts-chain-final-payload','Synthetic final reviewed correction',final_review,corrects=middle)['name']
    ts.queue(final,'synthetic-ts-chain-final-attempt','Accepted','Synthetic accepted correction descendant');ts.dispatch(final)
    admin_queue.refresh(center,'Synthetic accepted descendant resolves entire retained chain')
    assert frappe.db.get_value('CC Admin Exception',chain_exception,'state')=='Closed'
    result.append('accepted fiscal correction descendant auto-closes original unresolved ancestor through a retained multi-version chain')
    source,invoice=pairs[2];args.update(source=source,invoice=invoice,expense_amount=float(frappe.db.get_value('CC Economic Source Link',source,'price')))
    exhausted_review=ts.review_inputs(**{**args,'opposition':'No Opposition','expense_code':'SYNTHETIC_EXHAUSTION','request_key':'synthetic-ts-exhaustion'})['name']
    exhausted=ts.prepare(source,invoice,'synthetic-ts-exhaustion-payload','Synthetic TS bounded failure',exhausted_review)['name']
    for i in range(3):ts.queue(exhausted,'synthetic-ts-exhaust-'+str(i),'Retryable Failure','Synthetic TS bounded retry');ts.dispatch(exhausted)
    assert fiscal.status(exhausted)['status']=='FAILED_TERMINAL' and fiscal.status(exhausted)['attempt_count']==3
    reject(lambda:ts.queue(exhausted,'synthetic-ts-exhaust-4','Accepted','Synthetic TS retry limit'))
    ts.catch_up()
    result.append('independent TS three-attempt exhaustion classified terminal and scheduled recovery preserves principal')
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid',fixture['secretary']):
        frappe.set_user(actor);reject(lambda:ts.review_inputs(**{**args,'request_key':actor}))
        if actor==fixture['secretary']:
            assert fiscal.status(ready)['status']=='ACCEPTED'
        elif actor.startswith('accountant'):
            frappe.get_doc('CC TS Input Review',review).check_permission('read');reject(lambda:ts.prepare(source,invoice,'unauthorized-ts','Unauthorized TS mutation',review))
        else:
            reject(lambda:fiscal.status(ready));reject(lambda:frappe.get_doc('CC TS Input Review',review).check_permission('read'));reject(lambda:ts.prepare(source,invoice,'unauthorized-ts','Unauthorized TS mutation'))
        result.append('TS management-only synthetic eligibility review and professional/readonly accountant source input/result mutation boundaries')
    frappe.set_user('Administrator');return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:return security.run(extra_checks=checks)
    finally:frappe.flags.cc_test_clock=previous
