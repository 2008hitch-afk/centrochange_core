"""Synthetic decisive package/privacy/closure regressions, rolled back together."""
from datetime import datetime,timedelta,timezone
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.scheduling import dev_acceptance as scheduling
from centrochange_core.security.lifecycle import set_assignment
from centrochange_core.operations import notes,packages,lifecycle,automation
from centrochange_core.scheduling.booking import book,reschedule


def checks(fixture):
	accounting_before={dt:frappe.db.count(dt) for dt in ('Sales Invoice', 'Payment Entry', 'GL Entry', 'Payment Ledger Entry')}
	result=scheduling.checks(fixture)
	patient,center,prac1,prac2,pro1,pro2,secretary=(fixture[key] for key in ('patient','center','prac1','prac2','pro1','pro2','secretary'))
	frappe.set_user('Administrator')
	set_assignment(patient,center,prac1,1,'Synthetic operation fixture')
	set_assignment(patient,center,prac2,1,'Synthetic second assigned professional')
	frappe.set_user(pro1)
	private=notes.add_note(patient,center,'SYNTHETIC PRIVATE SECRET BODY',1)['name']
	org=notes.add_note(patient,center,'SYNTHETIC ORGANIZATIONAL BODY',0)['name']
	assert frappe.get_doc('CC Private Note',private).as_dict()['content']=='SYNTHETIC PRIVATE SECRET BODY'
	assert frappe.get_list('CC Private Note',pluck='name')==[private]
	result.append('own private note direct serialization and list allowed')
	frappe.set_user(pro2)
	try:
		frappe.get_doc('CC Private Note',private).check_permission('read')
	except frappe.PermissionError:
		result.append('second assigned professional private read denied')
	else:
		raise AssertionError('Cross professional private read accepted')
	for actor in (secretary,'Administrator'):
		frappe.set_user(actor)
		try:
			frappe.get_doc('CC Private Note',private).as_dict()
		except frappe.PermissionError:
			result.append('private body serialization denied for '+('secretariat' if actor==secretary else 'Administrator'))
		else:
			raise AssertionError('Private serialization accepted')
	frappe.set_user(pro1)
	revision=notes.add_note(patient,center,'SYNTHETIC PRIVATE CORRECTION',1,private)['name']
	assert frappe.db.get_value('CC Private Note',private,'content')=='SYNTHETIC PRIVATE SECRET BODY'
	assert frappe.db.get_value('CC Private Note',revision,'corrects')==private
	result.append('private revision appends and retains original')
	try:
		frappe.share.add_docshare('CC Private Note',private,user=secretary,read=1,flags={'ignore_share_permission':True})
	except frappe.PermissionError:
		result.append('private share bypass denied')
	else:
		raise AssertionError('Private sharing accepted')
	frappe.set_user('Administrator')
	assert not any('SYNTHETIC PRIVATE' in (row.before_state or '')+(row.after_state or '') for row in frappe.get_all('CC Audit Event',fields=['before_state','after_state']))
	assert not frappe.db.exists('Version',{'ref_doctype':'CC Private Note'})
	result.append('private body absent from management audit and native Version')
	template=frappe.get_doc({'doctype':'CC Package Template','title':'CC SYNTHETIC PACKAGE','service_item':'CC SYNTHETIC SESSION','units':2,'enabled':1}).insert()
	issued=packages.issue(template.name,patient,[center],'cc-synthetic-package','Synthetic grant')
	package=issued['name']
	assert issued['remaining']==2 and issued['reserved']==0
	assert packages.issue(template.name,patient,[center],'cc-synthetic-package','Synthetic retry')['name']==package
	result.append('package grant and issuance idempotent')
	# Re-enable the catalog disabled by scheduling checks.
	frappe.db.set_value('Item','CC SYNTHETIC SESSION','disabled',0)
	payload={'patient':patient,'practitioner':prac1,'center':center,'appointment_type':'CC SYNTHETIC SESSION',
		'appointment_date':'2099-01-26','appointment_time':'09:00:00','request_key':'cc-synthetic-package-book',
		'reason':'Synthetic package booking','patient_package':package}
	appointment=book(**payload)['name']
	assert packages.balance(package,center)=={'remaining':2,'reserved':1,'available':1}
	result.append('package reservation preserves remaining and reduces available')
	doc=frappe.get_doc('Patient Appointment',appointment)
	start=lifecycle.start_utc(doc)
	frappe.flags.cc_test_clock=start-timedelta(hours=48)
	fact=lifecycle.cancel(appointment,'Synthetic exact-boundary cancellation')
	assert not fact['late'] and packages.balance(package,center)=={'remaining':2,'reserved':0,'available':2}
	result.append('exact 48h timely cancellation releases reservation')
	second=book(**{**payload,'appointment_date':'2099-02-02','request_key':'cc-synthetic-late'})['name']
	doc=frappe.get_doc('Patient Appointment',second)
	frappe.flags.cc_test_clock=lifecycle.start_utc(doc)-timedelta(hours=48)+timedelta(microseconds=1)
	assert lifecycle.cancel(second,'Synthetic microsecond late')['late']
	assert packages.balance(package,center)=={'remaining':1,'reserved':0,'available':1}
	result.append('one microsecond below 48h late cancellation consumes unit')
	frappe.set_user(pro1)
	try:
		lifecycle.waive(second,'Unauthorized professional waiver')
	except frappe.PermissionError:
		result.append('professional economic waiver denied')
	else:
		raise AssertionError('Professional waiver accepted')
	frappe.set_user(secretary)
	assert not lifecycle.waive(second,'Synthetic authorized waiver')['replay']
	assert lifecycle.waive(second,'Synthetic waiver retry')['replay']
	doc.reload()
	assert doc.cc_late_cancellation==1 and doc.cc_economic_state=='Waived'
	assert packages.balance(package,center)=={'remaining':2,'reserved':0,'available':2}
	result.append('authorized waiver preserves late fact and appends corrective release')
	frappe.set_user('Administrator')
	third=book(**{**payload,'appointment_date':'2099-02-09','request_key':'cc-synthetic-complete'})['name']
	doc=frappe.get_doc('Patient Appointment',third)
	frappe.flags.cc_test_clock=lifecycle.start_utc(doc)+timedelta(hours=1)
	frappe.set_user(pro1)
	lifecycle.close(third,0,'Synthetic performed session')
	assert lifecycle.close(third,0,'Synthetic close retry')['replay']
	assert packages.balance(package,center)=={'remaining':1,'reserved':0,'available':1}
	result.append('performed closure consumes once and records operational unpaid')
	try:
		reschedule(third,'2099-02-16','09:00:00','Unauthorized closed move')
	except (frappe.PermissionError,frappe.ValidationError):
		result.append('closed session move denied')
	else:
		raise AssertionError('Closed move accepted')
	frappe.set_user('Administrator')
	method=frappe.get_doc({'doctype':'Mode of Payment','mode_of_payment':'CC SYNTHETIC CASH','enabled':1,'type':'Cash'}).insert().name
	frappe.set_user(pro1)
	try:
		lifecycle.record_settlement(third,1,'Unauthorized closed settlement',method)
	except frappe.PermissionError:
		result.append('professional closed settlement correction denied')
	else:
		raise AssertionError('Unauthorized settlement correction accepted')
	frappe.set_user(secretary)
	paid=lifecycle.record_settlement(third,1,'Synthetic paid correction',method)['settlement']
	assert paid==lifecycle.record_settlement(third,1,'Synthetic paid retry',method)['settlement']
	unpaid=lifecycle.record_settlement(third,0,'Synthetic unpaid correction')['settlement']
	assert unpaid!=paid and lifecycle.current_settlements(third)[0].sequence==3
	assert frappe.db.get_value('Patient Appointment',third,'cc_paid')==0
	result.append('operational payment corrections append ordered history and retry once')
	event=frappe.get_doc('CC Settlement',paid)
	event.reason='Synthetic forbidden rewrite'
	try:
		event.save(ignore_permissions=True)
	except frappe.PermissionError:
		result.append('settlement history cannot be rewritten')
	else:
		raise AssertionError('Settlement history mutation accepted')
	frappe.set_user('Administrator')
	try:
		packages.adjust(package,-2,'synthetic-invalid-adjust','Synthetic insufficient adjustment')
	except frappe.ValidationError:
		assert packages.balance(package,center)=={'remaining':1,'reserved':0,'available':1}
		result.append('invalid package adjustment rolls back without erasing history')
	else:
		raise AssertionError('Negative package balance accepted')
	assert accounting_before=={dt:frappe.db.count(dt) for dt in accounting_before}
	result.append('operations do not auto-create ERP accounting postings')
	frappe.flags.cc_test_clock=None
	fourth=book(**{**payload,'appointment_date':'2099-02-16','request_key':'cc-synthetic-auto-lock','patient_package':None})['name']
	doc=frappe.get_doc('Patient Appointment',fourth)
	date=frappe.utils.getdate(doc.appointment_date)
	frappe.flags.cc_test_clock=datetime.combine(date,datetime.min.time()).replace(hour=21,tzinfo=lifecycle.ROME).astimezone(timezone.utc)
	assert automation.catch_up()['reminders']>=1
	assert automation.catch_up()['reminders']==0
	reminder=frappe.db.get_value('CC Notification',{'event_key':f'closure-reminder:{date}:{prac1}'},
		['recipient','message'],as_dict=True)
	assert reminder and reminder.recipient==pro1 and reminder.message.startswith('Hai sedute da chiudere oggi.')
	result.append('21:00 reminder and catch-up retries idempotent')
	frappe.flags.cc_test_clock=datetime.combine(date+timedelta(days=1),datetime.min.time()).replace(hour=7,tzinfo=lifecycle.ROME).astimezone(timezone.utc)
	assert automation.catch_up()['locked']>=1
	assert automation.catch_up()['locked']==0
	assert frappe.db.get_value('Patient Appointment',fourth,'cc_closure_state')=='Auto Locked'
	result.append('07:00 next-day lock and retries idempotent')
	frappe.set_user(pro1)
	try:
		lifecycle.close(fourth,0,'Unauthorized post-lock completion')
	except frappe.PermissionError:
		result.append('post-lock professional API mutation denied')
	else:
		raise AssertionError('Post-lock mutation accepted')
	frappe.set_user(secretary)
	assert not lifecycle.reopen(fourth,'Synthetic authorized reopen')['replay']
	assert lifecycle.reopen(fourth,'Synthetic reopen retry')['replay']
	result.append('authorized reopen is audited and idempotent')
	from centrochange_core.operations.workspace import patient_history,agenda
	frappe.set_user(pro1)
	history=patient_history(patient,center)
	assert len(history['private_notes'])==2 and third in [row.name for row in history['appointments']]
	assert third in [row.name for row in agenda(center,'2099-02-01','2099-02-28')['appointments']]
	result.append('professional scoped agenda and patient history include own private revisions')
	frappe.set_user(secretary)
	assert patient_history(patient,center)['private_notes']==[]
	result.append('secretariat operational history excludes private bodies')
	# A shared Patient identity in B must not preserve revoked A operational context.
	from centrochange_core.security.lifecycle import set_membership
	other=fixture['other']
	frappe.set_user('Administrator')
	set_membership(pro1,other,1,'Synthetic second-center access')
	set_assignment(patient,other,prac1,1,'Synthetic shared identity in second center')
	set_assignment(patient,center,prac1,0,'Synthetic first-center context revocation')
	frappe.set_user(pro1)
	assert patient in frappe.get_list('Patient',pluck='name')
	for dt,name in [('CC Private Note',private),('CC Organizational Note',org),('Patient Appointment',third),('CC Patient Package',package)]:
		assert name not in frappe.get_list(dt,pluck='name')
		try:
			frappe.get_doc(dt,name).check_permission('read')
		except frappe.PermissionError:
			result.append('revoked center list and direct denied while shared identity remains: '+dt)
		else:
			raise AssertionError('Revoked operational context remained accessible')
	frappe.set_user('Administrator')
	set_assignment(patient,center,prac1,1,'Synthetic restored context')
	set_assignment(patient,other,prac1,0,'Synthetic second-center fixture release')
	set_membership(pro1,other,0,'Synthetic second-center membership release')
	for start_local,at_local in [('2026-03-30T12:00:00','2026-03-28T11:00:00'),('2026-10-26T12:00:00','2026-10-24T13:00:00')]:
		fact=lifecycle.cancellation_fact(datetime.fromisoformat(start_local).replace(tzinfo=lifecycle.ROME),
			datetime.fromisoformat(at_local).replace(tzinfo=lifecycle.ROME))
		assert fact=={'notice_seconds':172800.0,'late':False}
	result.append('spring and autumn DST boundaries use elapsed UTC hours')
	frappe.flags.cc_test_clock=None
	frappe.set_user('Administrator')
	set_assignment(patient,center,prac1,0,'Synthetic fixture release')
	set_assignment(patient,center,prac2,0,'Synthetic fixture release')
	return result


def run():
	previous=frappe.flags.get('cc_test_clock')
	try:
		return security.run(extra_checks=checks)
	finally:
		frappe.flags.cc_test_clock=previous
