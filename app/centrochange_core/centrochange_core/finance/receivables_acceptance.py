"""Synthetic native accounting regression; fixture transaction rolls back."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.security.lifecycle import set_assignment
from centrochange_core.finance import dev_acceptance,bridge,receivables as ar
from centrochange_core.security.audit import internal_write


def _mode_of_payment_type_for_account(account):
	"""Use ERPNext's native Cash/Bank type for the synthetic POS ledger."""
	account_type=frappe.db.get_value('Account',account,'account_type')
	if account_type not in ('Bank','Cash'):
		frappe.throw('Il conto del pagamento sintetico deve essere di tipo banca o cassa.')
	return account_type


@security.synthetic_test
def prepare_browser_invoice(fixture):
	"""Create one exact-tagged native invoice for browser tests; recovery owns its IDs."""
	if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
		frappe.throw('Synthetic DEV Administrator required')
	if isinstance(fixture,str):fixture=frappe.parse_json(fixture)
	tag=fixture['tag'];assert tag.startswith('CC-HTTP-')
	source=fixture.get('finance',{}).get('source')
	if not source:
		frappe.throw('Il fixture di fatturazione browser deve indicare la fonte sintetica preparata.')
	center=fixture['centers'][0]
	company=frappe.db.get_value('Branch',center,'cc_company')
	settings=frappe.get_doc('CC Finance Settings')
	account=settings.bank_account or frappe.db.get_value('Company',company,'default_cash_account')
	mode=tag+' BROWSER POS'
	frappe.get_doc({'doctype':'Mode of Payment','mode_of_payment':mode,'type':_mode_of_payment_type_for_account(account),'enabled':1,
		'accounts':[{'company':company,'default_account':account}]}).insert(ignore_permissions=True)
	invoice=ar.draft([source],'2026-10-05','2026-10-31',tag+'-browser-invoice',tag)['name']
	ar.submit(invoice,tag+' browser invoice')
	frappe.db.commit()
	return {'invoice':invoice,'source':source,'center':center,'mode':mode}


def rejected(fn):
    try:
        fn()
    except (frappe.ValidationError,frappe.PermissionError):
        return
    raise AssertionError('Unauthorized or invalid accounting action accepted')


def checks(fixture):
    results=dev_acceptance.checks(fixture)
    frappe.set_user('Administrator')
    patient,center,prac=[fixture[k] for k in ('patient','center','prac1')]
    set_assignment(patient,center,prac,1,'Synthetic receivable assignment')
    from centrochange_core.scheduling.booking import book
    from centrochange_core.operations import lifecycle
    from datetime import timedelta
    frappe.flags.cc_test_clock=None
    appointment=book(patient,prac,center,'CC SYNTHETIC SESSION','2099-03-09','09:00:00','ar-fixture','Synthetic standalone due booking')['name']
    frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',appointment))+timedelta(hours=1)
    lifecycle.close(appointment,0,'Synthetic performed non-package session')
    source=frappe.get_doc('CC Economic Source Link',bridge.capture(appointment,'Synthetic receivable snapshot')['name'])
    from centrochange_core.finance.dev_profile import setup
    setup(source.customer)
    before_paid=frappe.db.get_value('Patient Appointment',source.appointment,'cc_paid')
    name=ar.draft([source.name],'2026-10-05','2026-10-31','synthetic-invoice','Synthetic reviewed single invoice')['name']
    assert ar.draft([source.name],'2026-10-05','2026-10-31','synthetic-invoice','Synthetic retry')['replay']
    rejected(lambda: ar.draft([source.name],'2026-10-05','2026-11-01','synthetic-invoice','Different payload'))
    rejected(lambda: ar.draft([source.name],'2026-10-05','2026-10-31','duplicate','Duplicate bill'))
    doc=frappe.get_doc('Sales Invoice',name)
    assert doc.items[0].rate==source.price and doc.items[0].cc_economic_source==source.name
    assert not doc.patient and not doc.items[0].reference_dn and doc.docstatus==0
    assert not frappe.db.count('GL Entry',{'voucher_no':name})
    results.append('native reviewed draft frozen price idempotence payload binding and duplicate session guard')
    rejected(lambda: doc.save(ignore_permissions=True))
    results.append('direct native accounting mutation cannot bypass audited bridge')
    submitted=ar.submit(name,'Synthetic reviewed native posting')
    assert submitted['docstatus']==1 and frappe.db.count('GL Entry',{'voucher_no':name})>0
    assert ar.submit(name,'Synthetic submit retry')['replay']
    assert submitted['outstanding']==submitted['total']
    results.append('native submitted invoice generates GL and receivable once')
    total=submitted['total']
    company=frappe.get_doc('Company',doc.company)
    settings=frappe.get_doc('CC Finance Settings')
    pos_account=settings.bank_account or company.default_cash_account
    assert pos_account and frappe.db.get_value('Account',pos_account,'account_type') in ('Bank','Cash')
    pos_method='CC SYNTHETIC POS '+frappe.generate_hash(length=8)
    frappe.get_doc({'doctype':'Mode of Payment','mode_of_payment':pos_method,'type':_mode_of_payment_type_for_account(pos_account),'enabled':1,
        'accounts':[{'company':doc.company,'default_account':pos_account}]}).insert()
    pos=ar.pay(name,5,'2026-10-05','synthetic-pos-single','Synthetic manual card/POS payment',mode_of_payment=pos_method)
    pos_entry=frappe.get_doc('Payment Entry',pos['payment'])
    assert pos_entry.mode_of_payment==pos_method and pos_entry.paid_to==pos_account
    assert pos['invoice']['outstanding']==total-5
    assert ar.pay(name,5,'2026-10-05','synthetic-pos-single','Synthetic POS retry',mode_of_payment=pos_method)['invoice']['replay']
    rejected(lambda:ar.pay(name,4,'2026-10-05','synthetic-pos-single','Synthetic changed POS payload',mode_of_payment=pos_method))
    results.append('single manual card/POS receipt binds exactly one native Mode of Payment account, Payment Entry, invoice residual, replay and changed-payload guard')
    remaining=pos['invoice']['outstanding']; half=frappe.utils.flt(remaining/2,2)
    paid=ar.pay(name,half,'2026-10-05','synthetic-partial','Synthetic partial receipt')
    assert paid['invoice']['outstanding']==remaining-half
    assert ar.pay(name,half,'2026-10-05','synthetic-partial','Synthetic receipt retry')['invoice']['replay']
    rejected(lambda: ar.pay(name,total,'2026-10-05','overpay','Synthetic rejected overpayment'))
    ar.pay(name,remaining-half,'2026-10-05','synthetic-full','Synthetic balance receipt')
    assert ar.position(name)['outstanding']==0
    assert frappe.db.get_value('Patient Appointment',source.appointment,'cc_paid')==before_paid
    results.append('native POS, partial and full receipt, residual balance, retries, overpayment guard and operational isolation')
    credit=ar.credit(name,'2026-10-05','synthetic-credit','Synthetic reviewed credit note')['name']
    assert ar.credit(name,'2026-10-05','synthetic-credit','Synthetic credit retry')['replay']
    ar.submit(credit,'Synthetic native credit posting')
    assert frappe.db.get_value('Sales Invoice',credit,'return_against')==name
    assert frappe.db.get_value('Sales Invoice',credit,'is_return')
    assert frappe.db.count('GL Entry',{'voucher_no':credit})>0
    results.append('native credit correction preserves original invoice and source trace')
    # Two sessions, same center/customer/currency: explicit month-end aggregation.
    from centrochange_core.finance.collections import agree
    agree(patient,center,'Month End','Synthetic explicit monthly payment agreement')
    aggregate=[]
    for date in ('2099-03-16','2099-03-23'):
        frappe.flags.cc_test_clock=None
        appt=book(patient,prac,center,'CC SYNTHETIC SESSION',date,'09:00:00','ar-'+date,'Synthetic monthly session')['name']
        frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',appt))+timedelta(hours=1)
        lifecycle.close(appt,0,'Synthetic monthly performed session')
        aggregate.append(bridge.capture(appt,'Synthetic monthly source')['name'])
    monthly=ar.draft(aggregate,'2026-10-05','2026-10-31','synthetic-monthly','Synthetic reviewed aggregation')['name']
    assert len(frappe.get_doc('Sales Invoice',monthly).items)==2
    ar.submit(monthly,'Synthetic monthly native posting')
    ar.cancel(monthly,'Synthetic native cancellation')
    assert ar.cancel(monthly,'Synthetic cancellation retry')['replay']
    replacement=ar.amend(monthly,'2026-10-05','2026-10-31','synthetic-amend','Synthetic native amendment')['name']
    assert ar.amend(monthly,'2026-10-05','2026-10-31','synthetic-amend','Synthetic amendment retry')['replay']
    ar.submit(replacement,'Synthetic amended reissue posting')
    assert frappe.db.get_value('Sales Invoice',replacement,'amended_from')==monthly
    assert frappe.db.get_value('Sales Invoice',monthly,'docstatus')==2
    assert len(frappe.get_doc('Sales Invoice',replacement).items)==2
    results.append('aggregate draft native cancel amend reissue and retained source trace are idempotent')
    excluded=frappe.get_all('CC Economic Source Link',filters={'economic_state':['!=','Due']},pluck='name')
    for index,candidate in enumerate(excluded):
        rejected(lambda: ar.draft([candidate],'2026-10-05','2026-10-31','exclude-'+str(index),'Rejected package or non-due source'))
    assert excluded
    assert not ar.candidates(center,'2099-03-01','2099-03-31')['candidates']
    results.append('package-covered and non-due sources cannot bill; active native invoices leave candidate list')
    for actor in (fixture['pro1'],fixture['pro2']):
        frappe.set_user(actor)
        rejected(lambda: ar.position(name))
        rejected(lambda: ar.submit(name,'Unauthorized posting'))
        rejected(lambda: frappe.get_doc('Sales Invoice',name).check_permission('read'))
        rejected(lambda: frappe.get_list('Sales Invoice',pluck='name'))
        rejected(lambda: frappe.get_list('GL Entry',pluck='name'))
        results.append('professional direct API list and GL center-wide accounting denied')
    frappe.set_user('Administrator')
    accountant='accountant.cc-regression@example.invalid'
    frappe.set_user(accountant)
    assert ar.position(name)['name']==name
    rejected(lambda: ar.credit(name,'2026-10-05','unauthorized-credit','Unauthorized read-only mutation'))
    results.append('accountant native financial read works and financial mutation denied')
    frappe.set_user('Administrator')
    assert frappe.db.exists('CC Audit Event',{'event_type':'RECEIPT_POSTED','reference_name':paid['payment']})
    results.append('accounting postings and correction retain append-only reasoned audit')
    set_assignment(patient,center,prac,0,'Synthetic receivable fixture release')
    return results


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:
        return security.run(extra_checks=checks)
    finally:
        frappe.flags.cc_test_clock=previous


@security.synthetic_test
def prepare_http(fixture):
    from centrochange_core.finance.dev_profile import setup
    from centrochange_core.operations import lifecycle
    from datetime import timedelta
    if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
        frappe.throw('Synthetic DEV Administrator required')
    if isinstance(fixture,str):
        fixture=frappe.parse_json(fixture)
    tag=fixture['tag']; assert tag.startswith('CC-HTTP-')
    appointment=frappe.get_doc('Patient Appointment',fixture['finance']['appointment'])
    assert appointment.cc_service_label.startswith(tag+' ') and appointment.patient in fixture['patients']
    previous=frappe.flags.get('cc_test_clock')
    try:
        frappe.flags.cc_test_clock=lifecycle.start_utc(appointment)+timedelta(hours=1)
        lifecycle.close(appointment.name,0,tag)
        source=bridge.capture(appointment.name,tag)['name']
        setup(fixture['finance']['customer'])
        frappe.db.commit()
        from centrochange_core.scheduling.booking import book
        collections_mode='Month End'
        from centrochange_core.finance.collections import agree
        agree(appointment.patient,appointment.cc_center,collections_mode,tag)
        frappe.flags.cc_test_clock=None
        second=book(appointment.patient,appointment.practitioner,appointment.cc_center,appointment.appointment_type,
            '2099-01-19','09:00:00',tag+'-second-due',tag)['name']
        frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',second))+timedelta(hours=1)
        lifecycle.close(second,0,tag)
        source2=bridge.capture(second,tag)['name']
        frappe.db.commit()
        return {'source':source,'source2':source2}
    finally:
        frappe.flags.cc_test_clock=previous
