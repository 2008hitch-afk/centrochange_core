"""Native bank and approved payment-block regression on synthetic rolled-back records."""
from datetime import timedelta
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import banking,collections,receivables,receivables_acceptance
from centrochange_core.security.lifecycle import set_assignment


def checks(fixture):
    result=receivables_acceptance.checks(fixture)
    reject=receivables_acceptance.rejected
    frappe.set_user('Administrator')
    patient,center,prac=[fixture[k] for k in ('patient','center','prac1')]
    set_assignment(patient,center,prac,1,'Synthetic bank assignment')
    from centrochange_core.operations import lifecycle
    from centrochange_core.scheduling.booking import book
    # Native due balance from the reviewed two-session amended invoice.
    invoices=frappe.get_all('Sales Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0,'outstanding_amount':['>',0]},pluck='name')
    assert len(invoices)==1
    invoice=invoices[0]; outstanding=frappe.db.get_value('Sales Invoice',invoice,'outstanding_amount')
    frappe.flags.cc_test_clock=lifecycle.now_utc().replace(year=2099,month=3,day=24)
    assert collections.position(patient,center)['blocked']
    reject(lambda: book(patient,prac,center,'CC SYNTHETIC SESSION','2099-03-30','09:00:00','blocked-book','Synthetic prohibited subsequent session'))
    reject(lambda:collections.require_booking(frappe._dict({'patient':patient,'cc_center':fixture['other'],'appointment_date':'2099-03-30','appointment_time':'09:00:00','name':None})))
    result.append('native open balance blocks subsequent session server-side, including a center change without exposing foreign debt')
    original_due=frappe.db.get_value('Sales Invoice',invoice,'due_date')
    payload={'patient':patient,'center':center,'reference_doctype':'Sales Invoice','reference_name':invoice,
        'due_date':'2099-04-30','request_key':'synthetic-defer','reason':'Synthetic authorized temporary deferment'}
    override=collections.override(**payload)
    assert collections.override(**payload)['replay']
    assert frappe.db.get_value('Sales Invoice',invoice,'outstanding_amount')==outstanding
    assert frappe.db.get_value('Sales Invoice',invoice,'due_date')==original_due
    assert not collections.position(patient,center)['blocked']
    result.append('audited override retains native debt and due history with new deadline and replay')
    frappe.flags.cc_test_clock=None
    second=book(patient,prac,center,'CC SYNTHETIC SESSION','2099-03-30','09:00:00','blocked-book','Synthetic authorized subsequent session')['name']
    frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',second))+timedelta(hours=1)
    lifecycle.close(second,0,'Synthetic unpaid session for matching')
    from centrochange_core.finance import bridge
    collections.agree(patient,center,'Specific Date','Synthetic agreed specific deadline',due_date='2099-04-30')
    assert frappe.db.get_value('Patient Appointment',second,'cc_payment_terms_mode')=='Month End'
    original_deadline=next(d['due_date'] for d in collections.position(patient,center)['debts'] if d['name']==second)
    assert str(original_deadline)=='2099-03-31'
    result.append('payment agreement changes are prospective; held unbilled debt retains its booking snapshot')
    collections.override(patient,center,'Patient Appointment',second,'2099-04-30','synthetic-unbilled-defer','Synthetic explicit unbilled debt deferment')
    frappe.flags.cc_test_clock=None
    prebooked=book(patient,prac,center,'CC SYNTHETIC SESSION','2099-04-06','09:00:00','bank-prebooked','Synthetic session booked before invoice debt')['name']
    source=bridge.capture(second,'Synthetic second invoice source')['name']
    another=receivables.draft([source],'2026-10-05','2026-10-31','bank-second-invoice','Synthetic matching ambiguity invoice')['name']
    receivables.submit(another,'Synthetic matching invoice posting')
    frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',prebooked))+timedelta(hours=1)
    reject(lambda:lifecycle.close(prebooked,0,'Synthetic prohibited prebooked performance'))
    assert frappe.db.get_value('Patient Appointment',prebooked,'cc_closure_state')=='Pending'
    result.append('payment block also prevents performing an already-booked subsequent session')
    configuration=banking.configure_bank(center,'Synthetic native bank configuration')
    assert banking.configure_bank(center,'Synthetic bank retry')['replay']
    result.append('native bank and bank GL configuration are center-scoped and idempotent')
    before={dt:frappe.db.count(dt) for dt in ('Payment Entry','GL Entry')}
    movement={'external_id':'synthetic-statement-line-1','date':'2026-10-05','deposit':42,'description':'SYNTHETIC incoming transfer'}
    name=banking.import_movements(center,[movement],'Synthetic bank movement import')['movements'][0]['name']
    assert banking.import_movements(center,[movement],'Synthetic statement retry')['movements'][0]['replay']
    reject(lambda:banking.import_movements(center,[{**movement,'deposit':43}],'Synthetic changed duplicate'))
    assert before=={dt:frappe.db.count(dt) for dt in before}
    assert banking.candidates(name)['state']=='Ambiguous'
    result.append('immutable native movement import deduplicates without GL/payment posting and surfaces ambiguity')
    no_match=banking.import_movements(center,[{**movement,'external_id':'synthetic-unmatched','deposit':999}],'Synthetic unmatched import')['movements'][0]['name']
    assert banking.candidates(no_match)['state']=='Unmatched'
    exact=banking.import_movements(center,[{**movement,'external_id':'synthetic-exact','reference':another}],'Synthetic exact invoice reference')['movements'][0]['name']
    assert banking.candidates(exact)['state']=='Candidate' and len(banking.candidates(exact)['invoices'])==1
    assert len(banking.unresolved(center))==3
    result.append('unmatched ambiguous exact-reference and unresolved projections are deterministic')
    selected=banking.reconcile(name,invoice,'Synthetic human ambiguity selection')
    assert selected['movement']['status']=='Reconciled' and selected['movement']['unallocated']==0
    assert banking.reconcile(name,invoice,'Synthetic reconciliation retry')['movement']['replay']
    reject(lambda:banking.reconcile(name,another,'Synthetic different invoice replay'))
    assert frappe.db.get_value('Sales Invoice',invoice,'outstanding_amount')==outstanding-42
    assert frappe.db.get_value('Payment Entry',selected['payment'],'clearance_date')
    bank_account=frappe.db.get_value('Bank Account',configuration['bank_account'],'account')
    assert frappe.db.exists('GL Entry',{'voucher_no':selected['payment'],'account':bank_account})
    result.append('explicit native reconciliation posts receipt bank GL clearance allocation and retry once')
    assert banking.cancel(name,'Synthetic audited reconciliation reversal')['docstatus']==2
    assert banking.cancel(name,'Synthetic reversal retry')['replay']
    assert frappe.db.get_value('Payment Entry',selected['payment'],'docstatus')==2
    assert frappe.db.get_value('Sales Invoice',invoice,'outstanding_amount')==outstanding
    result.append('native bank cancellation reverses linked receipt and restores debt without source overwrite')
    frappe.db.set_value('Patient',patient,'email','synthetic.collections@example.invalid')
    frappe.flags.cc_test_clock=lifecycle.now_utc().replace(year=2099,month=5,day=1)
    assert collections.position(patient,center)['blocked']
    before_email=frappe.db.count('Email Queue')
    notice=collections.refresh(patient,center,'Synthetic payment block notification')['notice']
    assert collections.refresh(patient,center,'Synthetic notice retry')['replay']
    saved=frappe.get_doc('CC Payment Notice',notice)
    assert saved.email_state=='SIMULATED' and saved.communication
    reject(lambda:frappe.share.add_docshare('Communication',saved.communication,user=fixture['pro1'],read=1,flags={'ignore_share_permission':True}))
    assert frappe.db.count('Email Queue')==before_email
    assert frappe.db.exists('CC Notification',{'kind':'Payment Block','recipient':fixture['secretary'],'reference_name':notice})
    result.append('override expires; internal notice and native local email trace dedupe without SMTP or fake delivery')
    for user in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid'):
        frappe.set_user(user)
        reject(lambda:banking.reconcile(exact,another,'Unauthorized bank mutation'))
        reject(lambda:collections.override(**{**payload,'request_key':user,'due_date':'2099-06-30'}))
        if user!= 'accountant.cc-regression@example.invalid':
            for dt,id in [('Bank Transaction',name),('Bank Account',configuration['bank_account']),('CC Payment Override',override['name']),('CC Payment Notice',notice)]:
                reject(lambda:frappe.get_doc(dt,id).check_permission('read'))
        else:
            frappe.get_doc('Bank Transaction',name).check_permission('read')
            assert collections.position(patient,center)['blocked']
        result.append('professional/readonly accountant bank and override mutation boundaries')
    frappe.set_user('Administrator')
    reject(lambda:frappe.get_doc('Bank Transaction',exact).save(ignore_permissions=True))
    reject(lambda:frappe.get_doc('CC Payment Override',override['name']).save(ignore_permissions=True))
    result.append('generic native movement and append-only override mutation denied even Administrator')
    set_assignment(patient,center,prac,0,'Synthetic bank fixture release')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:
        return security.run(extra_checks=checks)
    finally:
        frappe.flags.cc_test_clock=previous


@security.synthetic_test
def prepare_http(fixture):
    if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
        frappe.throw('Synthetic DEV Administrator required')
    if isinstance(fixture,str):
        fixture=frappe.parse_json(fixture)
    assert fixture['tag'].startswith('CC-HTTP-')
    prepared=receivables_acceptance.prepare_http(fixture)
    center=fixture['centers'][0]; tag=fixture['tag']
    configuration=banking.configure_bank(center,tag)
    invoices=[]
    for index,source in enumerate((prepared['source'],prepared['source2'])):
        name=receivables.draft([source],'2026-01-01','2026-01-02',tag+'-bank-invoice-'+str(index),tag)['name']
        receivables.submit(name,tag); invoices.append(name)
    frappe.db.set_value('Patient',fixture['patients'][0],'email',tag.lower()+'-patient@example.invalid')
    frappe.db.commit()
    return {'invoices':invoices,'bank_account':configuration['bank_account']}
