"""DECISION-054 decisive native synthetic regression, part of WP-05 transaction."""
from datetime import timedelta
import frappe
from centrochange_core.finance import professional_economics as economics, admin_queue, bridge, collections, receivables
from centrochange_core.finance.receivables_acceptance import rejected
from centrochange_core.security.lifecycle import set_assignment
from centrochange_core.scheduling.availability import set_schedule
from centrochange_core.scheduling.booking import book
from centrochange_core.operations import lifecycle


def checks(fixture):
    center=fixture['center'];p1,p2=[frappe.get_doc({'doctype':'Patient','first_name':'CC SYNTHETIC THRESHOLD '+str(i),
        'sex':'Female','uid':'CC-SYNTHETIC-THRESHOLD-'+str(i)}).insert(ignore_permissions=True).name for i in (1,2)]
    prac1,prac2=fixture['prac1'],fixture['prac2'];result=[]
    for patient in (p1,p2):
        set_assignment(patient,center,prac1,1,'Synthetic threshold pairing')
        bridge.map_patient(patient,center,'Synthetic threshold native customer')
        collections.agree(patient,center,'Specific Date','Synthetic threshold explicit future due',due_date='2100-01-01')
    set_assignment(p1,center,prac2,1,'Synthetic second professional pairing')
    bridge.map_practitioner(prac2,center,'Synthetic second professional supplier')
    set_schedule(prac2,center,[{'day':'Monday','from_time':'09:00:00','to_time':'12:00:00'}],'Synthetic threshold second availability')
    rules={p:economics.configure_rule(center,p,'CC SYNTHETIC SESSION','2020-01-01','Fixed Amount',100,'EUR',
        'synthetic-threshold-rule-'+p,'Synthetic threshold explicit fixed compensation')['name'] for p in (prac1,prac2)}
    pairs={}
    for patient,prac,time,n in [(p1,prac1,'09:00:00',4),(p2,prac1,'10:00:00',2),(p1,prac2,'11:00:00',2)]:
        sources=[]
        for i,date in enumerate(('2099-05-04','2099-05-11','2099-05-18','2099-05-25')[:n]):
            frappe.flags.cc_test_clock=None
            appt=book(patient,prac,center,'CC SYNTHETIC SESSION',date,time,'threshold-'+patient+prac+str(i),'Synthetic threshold unpaid session')['name']
            frappe.flags.cc_test_clock=lifecycle.start_utc(frappe.get_doc('Patient Appointment',appt))+timedelta(hours=1)
            lifecycle.close(appt,0,'Synthetic threshold performed unpaid')
            sources.append(bridge.capture(appt,'Synthetic threshold original source')['name'])
        pairs[patient,prac]=sources
    settings=frappe.get_doc('CC Finance Settings');settings.unpaid_compensation_policy='Earn When Performed'
    rejected(lambda:settings.save(ignore_permissions=True))
    src=pairs[p1,prac2][0]
    missing=economics.capture(src,'Synthetic missing threshold',rules[prac2])
    assert missing['state']=='REVIEW' and missing['amount'] is None
    assert frappe.db.get_value('CC Professional Expectation',missing['name'],'problem')=='Professional Unpaid Threshold Missing'
    result.append('DECISION-054 missing professional threshold is explicit unknown configuration exception, without default')
    for value in (0,1,2,5):
        cfg=economics.configure_threshold(center,prac1,value,'threshold-'+str(value),'Synthetic threshold configuration')
        assert economics.configure_threshold(center,prac1,value,'threshold-'+str(value),'Synthetic threshold replay')['replay']
        rejected(lambda:economics.configure_threshold(center,prac1,value+1,'threshold-'+str(value),'Synthetic changed retry'))
        for patient in (p1,p2):
            for source in reversed(pairs[patient,prac1]):economics.capture(source,'Synthetic capture out of order',rules[prac1])
            rows=[economics.latest_expectations(center)[frappe.db.get_value('CC Economic Source Link',s,'appointment')] for s in pairs[patient,prac1]]
            assert [r.state for r in rows]==['OK' if i<value else 'SUSPENDED' for i in range(len(rows))]
            assert all(r.unpaid_count==len(rows) and r.unpaid_rank==i+1 for i,r in enumerate(rows))
            assert all(r.amount==100 if r.state=='OK' else not r.amount_known for r in rows)
        result.append('DECISION-054 N='+str(value)+' chronological pair ranking independent for two patients, even reversed capture order')
    for value in (-1,None,'1.5',True,'',1.0,2147483648):
        rejected(lambda:economics.configure_threshold(center,prac1,value,'invalid-'+str(value),'Synthetic invalid threshold'))
    economics.configure_threshold(center,prac1,2,'threshold-final-two','Synthetic threshold final N2')
    economics.configure_threshold(center,prac2,0,'threshold-second-zero','Synthetic independent professional N0')
    for source in pairs[p1,prac2]:assert economics.capture(source,'Synthetic second professional suspension',rules[prac2])['state']=='SUSPENDED'
    result.append('DECISION-054 independent professional N2/N0 thresholds and invalid/negative/fractional/missing values rejected')
    for row in economics.latest_expectations(center).values():
        if row.patient not in (p1,p2):continue
        exceptions=frappe.get_all('CC Admin Exception',filters={'reference_name':row.appointment,'exception_type':'Professional Expectation Review','state':['!=','Closed']},fields=['name','condition_details'])
        assert len(exceptions)==int(row.state!='OK')
        if exceptions:
            detail=frappe.parse_json(exceptions[0].condition_details)
            assert detail['patient']==row.patient and detail['practitioner']==row.practitioner and detail['threshold_snapshot']==row.threshold_snapshot
    counts={dt:frappe.db.count(dt) for dt in ('CC Professional Expectation','CC Admin Exception')}
    economics.reevaluate(center,'Synthetic job replay');admin_queue.catch_up()
    assert all(frappe.db.count(dt)==n for dt,n in counts.items())
    result.append('DECISION-054 suspended positions retain amount unknown and complete patient/professional/session/threshold/count exception facts; replay/job dedupe')
    source=pairs[p1,prac1][0]
    from centrochange_core.finance.dev_profile import setup
    setup(frappe.db.get_value('CC Economic Source Link',source,'customer'))
    invoice=receivables.draft([source],'2026-10-05','2026-10-31','threshold-native-invoice','Synthetic threshold reviewed native invoice')['name']
    receivables.submit(invoice,'Synthetic threshold invoice posting')
    receivables.pay(invoice,20,'2026-10-05','threshold-partial','Synthetic threshold partial payment')
    third=pairs[p1,prac1][2];third_appt=frappe.db.get_value('CC Economic Source Link',third,'appointment')
    assert economics.latest_expectations(center)[third_appt].state=='SUSPENDED'
    total=frappe.db.get_value('Sales Invoice',invoice,'outstanding_amount')
    payment=receivables.pay(invoice,total,'2026-10-05','threshold-paid','Synthetic threshold complete payment')
    matured=economics.latest_expectations(center)[third_appt]
    assert matured.state=='OK' and matured.amount==100 and matured.unpaid_count==3 and matured.unpaid_rank==2
    assert frappe.parse_json(matured.original_facts)['state']=='SUSPENDED'
    assert frappe.db.get_value('CC Admin Exception',{'reference_name':third_appt,'exception_type':'Professional Expectation Review'},'state')=='Closed'
    before=frappe.db.count('CC Professional Expectation')
    assert receivables.pay(invoice,total,'2026-10-05','threshold-paid','Synthetic payment replay')['invoice']['replay']
    assert frappe.db.count('CC Professional Expectation')==before
    result.append('DECISION-054 native partial/full patient receipt synchronously reevaluates pair, matures earliest suspended position and auto-closes its one exception; payment replay once')
    fourth_appt=frappe.db.get_value('CC Economic Source Link',pairs[p1,prac1][3],'appointment');old=economics.latest_expectations(center)[fourth_appt]
    assert old.state=='SUSPENDED'
    for actor in (fixture['pro1'],fixture['secretary'],'accountant.cc-regression@example.invalid'):
        frappe.set_user(actor);rejected(lambda:economics.override(old.name,'Synthetic unauthorized override'))
        rejected(lambda:economics.configure_threshold(center,prac1,99,'unauthorized-'+actor,'Synthetic unauthorized configuration'))
    frappe.set_user('Administrator')
    overridden=economics.override(old.name,'Synthetic explicit Management threshold override')
    assert overridden['state']=='OK' and overridden['amount']==100 and economics.override(old.name,'Synthetic override retry')['replay']
    row=frappe.get_doc('CC Professional Expectation',overridden['name'])
    assert row.original_facts==old.original_facts and row.paid_snapshot==0 and row.unpaid_rank==3 and row.manual_override
    audit=frappe.get_doc('CC Audit Event',{'reference_name':row.name,'event_type':'PROFESSIONAL_EXPECTATION_OVERRIDDEN'})
    assert audit.actor=='Administrator' and audit.event_time and audit.reason and frappe.parse_json(audit.before_state)['state']=='SUSPENDED'
    assert frappe.parse_json(audit.after_state)['appointment']==fourth_appt and frappe.parse_json(audit.after_state)['state']=='OK'
    economics.reevaluate(center,'Synthetic override persists across job replay');assert economics.latest_expectations(center)[fourth_appt].manual_override
    result.append('DECISION-054 authorized override matures once, actor/time/reason/before-after/source audit and unpaid/original immutable facts retained; unauthorized actors denied')
    cfg=economics.threshold(prac1)
    rejected(lambda:frappe.get_doc('CC Unpaid Threshold',cfg.name).save(ignore_permissions=True))
    for actor in (fixture['pro1'],fixture['pro2']):
        frappe.set_user(actor);rejected(lambda:frappe.get_doc('CC Unpaid Threshold',cfg.name).check_permission('read'))
        rejected(lambda:frappe.get_list('CC Unpaid Threshold',pluck='name'))
    frappe.set_user('Administrator')
    native=frappe.get_all('Purchase Invoice',filters={'cc_center':center,'docstatus':1,'is_return':0},pluck='name')[0]
    assert economics.compare(native,[matured.name],'Synthetic threshold native received comparison')['state']=='OK'
    result.append('DECISION-054 threshold REST/query permissions and immutable configuration; matured expected compensation still reconciles with native Purchase Invoice accounting truth')
    exception=frappe.db.get_value('CC Admin Exception',{'reference_name':third_appt,'exception_type':'Professional Expectation Review'})
    from centrochange_core.security.audit import internal_write
    with internal_write('cc_accounting_write'):
        reversal=frappe.get_doc('Payment Entry',payment['payment']);reversal.flags.ignore_permissions=True;reversal.cancel()
    suspended_again=economics.latest_expectations(center)[third_appt]
    assert suspended_again.state=='SUSPENDED' and suspended_again.sequence>matured.sequence
    assert suspended_again.original_facts==matured.original_facts and frappe.db.get_value('CC Professional Expectation',matured.name,'state')=='OK'
    assert frappe.db.get_value('CC Admin Exception',exception,'state') in ('Open','Assigned')
    assert frappe.db.count('CC Admin Exception',{'reference_name':third_appt,'exception_type':'Professional Expectation Review'})==1
    assert economics.latest_expectations(center)[fourth_appt].manual_override and economics.latest_expectations(center)[fourth_appt].state=='OK'
    before={dt:frappe.db.count(dt) for dt in ('CC Professional Expectation','CC Admin Exception')}
    economics.reevaluate(center,'Synthetic payment reversal replay')
    assert all(frappe.db.count(dt)==n for dt,n in before.items())
    result.append('DECISION-054 native receipt cancellation resuspends deterministically, reopens the same exception and retains original matured/override facts without replay duplicates')
    for patient,prac in pairs:set_assignment(patient,center,prac,0,'Synthetic threshold fixture permission release')
    return result
