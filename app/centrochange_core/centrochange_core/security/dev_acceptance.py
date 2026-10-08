"""Synthetic security regression via bench, never a whitelisted API."""
import frappe
from functools import wraps


def synthetic_test(function):
	@wraps(function)
	def wrapped(*args, **kwargs):
		previous=frappe.in_test
		frappe.in_test=True
		try:
			return function(*args,**kwargs)
		finally:
			frappe.in_test=previous
	return wrapped

from centrochange_core.security import lifecycle as service
from centrochange_core.security.api import discover_patient, get_patient_detail


@synthetic_test
def run(extra_checks=None):
	if frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1:
		frappe.throw('Synthetic DEV Administrator required')
	frappe.db.savepoint('cc_security_acceptance')
	checks = []
	def check(label, condition):
		assert condition, label
		checks.append(label)
	def denied(label, action):
		try:
			action()
		except frappe.PermissionError:
			checks.append(label)
		else:
			raise AssertionError(label)
	def user(label, role):
		return frappe.get_doc({'doctype':'User', 'email':f'{label}.cc-regression@example.invalid',
			'first_name':label, 'enabled':1, 'send_welcome_email':0,
			'roles':[{'role':role}]}).insert(ignore_permissions=True).name
	try:
		pro1, pro2 = user('professional-a', 'CC Professional'), user('professional-b', 'CC Professional')
		secretary = user('secretariat-a', 'CC Secretariat')
		center = frappe.get_doc({'doctype':'Branch', 'branch':'CC SYNTHETIC A'}).insert().name
		other = frappe.get_doc({'doctype':'Branch', 'branch':'CC SYNTHETIC B'}).insert().name
		for principal in (pro1, pro2, secretary):
			service.set_membership(principal, center, 1, 'Synthetic fixture')
		prac1, prac2 = [frappe.get_doc({'doctype':'Healthcare Practitioner', 'first_name':label,
			'status':'Active', 'user_id':principal}).insert().name
			for label, principal in [('CC SYNTHETIC A',pro1),('CC SYNTHETIC B',pro2)]]
		patient, cross = [frappe.get_doc({'doctype':'Patient', 'first_name':label, 'sex':'Female',
			'uid':uid}).insert().name for label,uid in [('CC SYNTHETIC OWN','CC-SYNTH-OWN'),('CC SYNTHETIC CROSS','CC-SYNTH-CROSS')]]
		if extra_checks:
			checks.extend(extra_checks(locals()))
		frappe.set_user(pro1)
		denied('zero assignment list denied', lambda:frappe.get_list('Patient', pluck='name'))
		denied('zero assignment direct denied', lambda:frappe.get_doc('Patient',patient).check_permission())
		denied('professional mutation denied',lambda:service.set_membership(pro1,other,1,'Unauthorized'))
		frappe.set_user('Administrator')
		service.set_assignment(patient,center,prac1,1,'Synthetic assignment')
		service.set_assignment(cross,other,None,1,'Synthetic cross-center assignment')
		frappe.set_user(pro1)
		check('own nonempty list',frappe.get_list('Patient',pluck='name') == [patient])
		frappe.get_doc('Patient',patient).check_permission()
		check('own detail read',get_patient_detail(patient)['name']==patient)
		denied('cross detail denied',lambda:get_patient_detail(cross))
		denied('cross document denied',lambda:frappe.get_doc('Patient',cross).check_permission())
		denied('own write denied',lambda:frappe.get_doc('Patient',patient).check_permission('write'))
		denied('manual share denied',lambda:frappe.share.add_docshare('Patient',cross,user=pro1,read=1,flags={'ignore_share_permission':True}))
		frappe.set_user(secretary)
		check('secretariat exact identity discovery',discover_patient(center,'CC-SYNTH-CROSS')[0]['name']==cross)
		denied('discovery unauthorized center',lambda:discover_patient(other,'CC-SYNTH-CROSS'))
		frappe.set_user('Administrator')
		before=frappe.db.count('CC Audit Event')
		service.set_assignment(patient,center,prac1,1,'Retry')
		check('assignment retry no duplicate audit',before==frappe.db.count('CC Audit Event'))
		try:
			service.reassign(patient,center,prac1,prac2,'')
		except frappe.ValidationError:
			pass
		else:
			raise AssertionError('Empty reason must fail')
		frappe.set_user(pro1)
		check('failed reassignment preserves access',get_patient_detail(patient)['name']==patient)
		frappe.set_user('Administrator')
		service.reassign(patient,center,prac1,prac2,'Synthetic reassignment')
		frappe.set_user(pro1)
		denied('old professional revoked',lambda:get_patient_detail(patient))
		check('old shares removed',not frappe.db.exists('DocShare',{'share_doctype':'Patient','share_name':patient,'user':pro1}))
		frappe.set_user(pro2)
		check('new professional granted',get_patient_detail(patient)['name']==patient)
		frappe.set_user('Administrator')
		try:
			service.set_practitioner_state(prac2,0,'')
		except frappe.ValidationError:
			pass
		else:
			raise AssertionError('Empty lifecycle reason must fail')
		check('failed offboarding rolls back user',frappe.db.get_value('User',pro2,'enabled')==1)
		service.set_practitioner_state(prac2,0,'Synthetic offboarding')
		check('offboarding user disabled',frappe.db.get_value('User',pro2,'enabled')==0)
		check('offboarding permission removed',not frappe.db.exists('User Permission',{'user':pro2,'allow':'Healthcare Practitioner'}))
		frappe.set_user(pro2)
		denied('disabled direct denied',lambda:get_patient_detail(patient))
		frappe.set_user('Administrator')
		event=frappe.get_last_doc('CC Audit Event')
		event.reason='Tampered'
		denied('audit update denied even Administrator',lambda:event.save())
		denied('audit delete denied even Administrator',lambda:frappe.delete_doc('CC Audit Event',event.name))
		denied('relationship generic insert denied',lambda:frappe.get_doc({'doctype':'CC Center Membership','user':pro1,'center':other,'active':1}).insert())
		return {'status':'PASS','checks':checks,'cleanup':'rollback'}
	finally:
		frappe.set_user('Administrator')
		frappe.db.rollback(save_point='cc_security_acceptance')
		for principal in locals().get('pro1',''), locals().get('pro2',''), locals().get('secretary',''):
			if principal:
				frappe.clear_cache(user=principal)


@synthetic_test
def create_http(scheduling=False,operations=False,finance=False):
	"""Create explicitly marked disposable HTTP fixtures; harness destroys them."""
	if frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1:
		frappe.throw('Synthetic DEV Administrator required')
	from frappe.utils.password import update_password
	tag = 'CC-HTTP-' + frappe.generate_hash(length=10)
	result = {'tag':tag, 'users':{}, 'patients':[], 'practitioners':[], 'centers':[]}
	identities=[('a','CC Professional'),('b','CC Professional'),('c','CC Professional'),('s','CC Secretariat'),('m','CC Manager')]
	if finance:
		identities += [('f','CC Finance'),('t','CC Accountant')]
	for label, role in identities:
		name = tag.lower() + '-' + label + '@example.invalid'
		frappe.get_doc({'doctype':'User','email':name,'first_name':tag+' '+label,
			'enabled':1,'send_welcome_email':0,'roles':[{'role':role}]}).insert(ignore_permissions=True)
		password = frappe.generate_hash(length=32)
		update_password(name,password)
		result['users'][label]={'name':name,'password':password}
	for label in ('A','B'):
		result['centers'].append(frappe.get_doc({'doctype':'Branch','branch':tag+' '+label}).insert().name)
	for principal in result['users'].values():
		service.set_membership(principal['name'],result['centers'][0],1,tag)
	for label in ('a','b'):
		result['practitioners'].append(frappe.get_doc({'doctype':'Healthcare Practitioner',
			'first_name':tag+' '+label,'status':'Active','user_id':result['users'][label]['name']}).insert().name)
	for label in ('OWN','CROSS'):
		result['patients'].append(frappe.get_doc({'doctype':'Patient','first_name':tag+' '+label,
			'sex':'Female','uid':tag+'-'+label}).insert().name)
	service.set_assignment(result['patients'][0],result['centers'][0],result['practitioners'][0],1,tag)
	service.set_assignment(result['patients'][1],result['centers'][1],None,1,tag)
	if scheduling:
		from centrochange_core.scheduling.availability import set_schedule
		item=frappe.get_doc({'doctype':'Item','item_code':tag+' SESSION','item_name':tag+' Session',
			'item_group':'Services','stock_uom':'Nos','is_stock_item':0,'is_sales_item':1}).insert()
		price_list=frappe.get_doc({'doctype':'Price List','price_list_name':tag+' PRICE','enabled':1,'selling':1,'currency':'EUR'}).insert()
		profile=frappe.get_doc({'doctype':'Appointment Type','appointment_type':tag+' SESSION',
			'allow_booking_for':'Practitioner','default_duration':60,'cc_service_item':item.name,'cc_first_meeting':1}).insert()
		price=frappe.get_doc({'doctype':'Item Price','item_code':item.name,'price_list':price_list.name,
			'price_list_rate':100,'currency':'EUR','valid_from':'2020-01-01'}).insert()
		frappe.db.set_value('Branch',result['centers'][0],'cc_price_list',price_list.name)
		availability=frappe.get_doc({'doctype':'CC Center Service','center':result['centers'][0],
			'appointment_type':profile.name,'enabled':1}).insert()
		schedule=set_schedule(result['practitioners'][0],result['centers'][0],
			[{'day':'Monday','from_time':'09:00:00','to_time':'12:00:00'}],tag)['name']
		route=frappe.get_doc({'doctype':'CC Public Booking Route','route':'Marco','center':result['centers'][0],
			'practitioner':result['practitioners'][0],'appointment_type':profile.name,'enabled':1}).insert()
		result['catalog']={'CC Public Booking Route':[route.name],'Item':[item.name],'Price List':[price_list.name],'Appointment Type':[profile.name],
			'Item Price':[price.name],'CC Center Service':[availability.name],'Practitioner Schedule':[schedule]}
	if operations:
		from centrochange_core.operations.notes import add_note
		from centrochange_core.operations.packages import issue
		frappe.set_user(result['users']['a']['name'])
		result['private_note']=add_note(result['patients'][0],result['centers'][0],tag+' SYNTHETIC PRIVATE BODY',1)['name']
		result['org_note']=add_note(result['patients'][0],result['centers'][0],tag+' SYNTHETIC ORG BODY',0)['name']
		frappe.set_user('Administrator')
		template=frappe.get_doc({'doctype':'CC Package Template','title':tag+' PACKAGE','service_item':result['catalog']['Item'][0],
			'units':1,'enabled':1}).insert()
		result['package']=issue(template.name,result['patients'][0],[result['centers'][0]],tag+'-issue',tag)['name']
		result['catalog']['CC Package Template']=[template.name]
	if finance:
		from centrochange_core.finance import bridge
		from centrochange_core.scheduling.booking import book
		frappe.set_user('Administrator')
		result['finance']={'cost_center':bridge.map_center(result['centers'][0],tag)['cost_center'],
			'customer':bridge.map_patient(result['patients'][0],result['centers'][0],tag)['customer'],
			'supplier':bridge.map_practitioner(result['practitioners'][0],result['centers'][0],tag)['supplier']}
		appointment=book(result['patients'][0],result['practitioners'][0],result['centers'][0],result['catalog']['Appointment Type'][0],
			'2099-01-12','09:00:00',tag+'-finance-book',tag)['name']
		result['finance']['source']=bridge.capture(appointment,tag)['name']
		result['finance']['appointment']=appointment
	frappe.db.commit()
	return result


def destroy_http(fixture):
	"""Private DEV-only fixture teardown; exact IDs, never an operational deletion API."""
	if frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1:
		frappe.throw('Synthetic DEV Administrator required')
	if isinstance(fixture,str):
		fixture=frappe.parse_json(fixture)
	tag=fixture['tag']
	assert tag.startswith('CC-HTTP-')
	users=[row['name'] for row in fixture['users'].values()]
	assert all(name.startswith(tag.lower()+'-') and name.endswith('@example.invalid') for name in users)
	# Exact ownership checks prevent this private helper from deleting arbitrary documents.
	for doctype,names,field in [('Patient',fixture['patients'],'first_name'),
		('Healthcare Practitioner',fixture['practitioners'],'first_name'),('Branch',fixture['centers'],'branch')]:
		assert all((frappe.db.get_value(doctype,name,field) or '').startswith(tag+' ') for name in names)
	groups={'Patient':fixture['patients'],'Healthcare Practitioner':fixture['practitioners'],
		'Branch':fixture['centers'],'User':users}
	if fixture.get('catalog'):
		assert all((frappe.db.get_value('Item',name,'item_name') or '').startswith(tag+' ') for name in fixture['catalog']['Item'])
		groups.update(fixture['catalog'])
		groups['Patient Appointment']=frappe.get_all('Patient Appointment',filters={'patient':['in',fixture['patients']]},pluck='name')
		assert all((frappe.db.get_value('Patient Appointment',name,'cc_service_label') or '').startswith(tag+' ') for name in groups['Patient Appointment'])
	groups['Practitioner Availability']=frappe.get_all('Practitioner Availability',filters={'scope_type':'Healthcare Practitioner','scope':['in',fixture['practitioners']]},pluck='name')
	groups['CC Public Booking Route']=frappe.get_all('CC Public Booking Route',filters={'center':['in',fixture['centers']]},pluck='name')
	groups['CC Private Note']=frappe.get_all('CC Private Note',filters={'patient':['in',fixture['patients']]},pluck='name')
	groups['CC Organizational Note']=frappe.get_all('CC Organizational Note',filters={'patient':['in',fixture['patients']]},pluck='name')
	groups['CC Patient Package']=frappe.get_all('CC Patient Package',filters={'patient':['in',fixture['patients']]},pluck='name')
	groups['CC Package Ledger']=frappe.get_all('CC Package Ledger',filters={'package':['in',groups['CC Patient Package'] or ['']]},pluck='name')
	groups['CC Economic Source Link']=frappe.get_all('CC Economic Source Link',filters={'appointment':['in',groups.get('Patient Appointment') or ['']]},pluck='name')
	groups['Supplier']=[name for name in (frappe.db.get_value('Healthcare Practitioner',prac,'supplier') for prac in fixture['practitioners']) if name]
	groups['Cost Center']=[name for name in (frappe.db.get_value('Branch',center,'cc_cost_center') for center in fixture['centers']) if name]
	groups['CC Settlement']=frappe.get_all('CC Settlement',filters={'appointment':['in',groups.get('Patient Appointment') or ['']]},pluck='name')
	groups['CC Notification']=frappe.get_all('CC Notification',filters={'recipient':['in',users]},pluck='name')
	groups['CC Patient Assignment']=frappe.get_all('CC Patient Assignment',filters={'patient':['in',fixture['patients']]},pluck='name')
	groups['CC Center Membership']=frappe.get_all('CC Center Membership',filters={'user':['in',users]},pluck='name')
	groups['CC Audit Event']=frappe.get_all('CC Audit Event',filters={'reason':tag},pluck='name')
	if fixture.get('catalog'):
		groups['CC Audit Event']+=frappe.get_all('CC Audit Event',filters={'reference_doctype':'Patient Appointment',
			'reference_name':['in',groups.get('Patient Appointment') or ['']]},pluck='name')
		for protected in ('CC Private Note','CC Organizational Note','CC Patient Package','CC Economic Source Link'):
			groups['CC Audit Event']+=frappe.get_all('CC Audit Event',filters={'reference_doctype':protected,'reference_name':['in',groups[protected] or ['']]},pluck='name')
		groups['CC Audit Event']+=frappe.get_all('CC Audit Event',filters={'reference_doctype':'CC Patient Assignment',
			'reference_name':['in',groups.get('CC Patient Assignment') or ['']]},pluck='name')
	# Native Patient creates contacts/customers; discover only links to these exact fixtures.
	groups['Contact']=frappe.get_all('Contact',filters={'user':['in',users]},pluck='name')
	groups['Contact']+=frappe.get_all('Dynamic Link',filters={'parenttype':'Contact','link_doctype':'Patient',
		'link_name':['in',fixture['patients']]},pluck='parent')
	groups['Customer']=[frappe.db.get_value('Patient',name,'customer') for name in fixture['patients']]
	groups['Customer']=[name for name in groups['Customer'] if name]
	for doctype,names,field,prefix in [('Supplier',groups.get('Supplier',[]),'supplier_name',tag),
		('Customer',groups.get('Customer',[]),'customer_name',tag),('Cost Center',groups.get('Cost Center',[]),'cost_center_name','CC '+tag)]:
		assert all((frappe.db.get_value(doctype,name,field) or '').startswith(prefix) for name in names)
	for doctype,names in groups.items():
		if not names:
			continue
		for field in frappe.get_meta(doctype).get_table_fields():
			frappe.db.delete(field.options,{'parenttype':doctype,'parent':['in',names]})
		for dependent,filters in [('DocShare',{'share_doctype':doctype,'share_name':['in',names]}),
			('Version',{'ref_doctype':doctype,'docname':['in',names]}),
			('Comment',{'reference_doctype':doctype,'reference_name':['in',names]})]:
			frappe.db.delete(dependent,filters)
		frappe.db.delete(doctype,{'name':['in',names]})
	frappe.db.delete('User Permission',{'user':['in',users]})
	frappe.db.delete('DocShare',{'user':['in',users]})
	frappe.db.delete('Sessions',{'user':['in',users]})
	frappe.db.delete('Notification Log',{'for_user':['in',users]})
	frappe.db.delete('DefaultValue',{'parent':['in',users]})
	frappe.db.delete('__Auth',{'doctype':'User','name':['in',users]})
	frappe.db.commit()
	for user in users:
		frappe.clear_cache(user=user)
	assert not any(frappe.db.exists(doctype,{'name':['in',names]}) for doctype,names in groups.items() if names)
	return {'cleanup':'PASS'}


def pending_contacts(users):
	if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
		frappe.throw('Synthetic DEV Administrator required')
	assert all(user.startswith('cc-http-') and user.endswith('@example.invalid') for user in users)
	from frappe.utils.background_jobs import get_queue
	from rq.registry import StartedJobRegistry
	pending=0
	for queue_name in ('short','default','long'):
		queue=get_queue(queue_name)
		ids=set(queue.get_job_ids()) | set(StartedJobRegistry(queue=queue).get_job_ids())
		for job_id in ids:
			job=queue.fetch_job(job_id)
			if not job or job.kwargs.get('method')!='frappe.core.doctype.user.user.create_contact':
				continue
			principal=job.kwargs.get('kwargs',{}).get('user')
			name=principal.get('name') if isinstance(principal,dict) else getattr(principal,'name',None)
			if name in users:
				pending+=1
	return {'pending':pending}


def recover_http(tag):
	"""Recover exact fixture IDs after an interrupted harness, without recovering credentials."""
	if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
		frappe.throw('Synthetic DEV Administrator required')
	assert tag.startswith('CC-HTTP-') and len(tag)==18
	users=frappe.get_all('User',filters={'email':['like',tag.lower()+'-%@example.invalid']},pluck='name')
	fixture={'tag':tag,'users':{name.split('@')[0].rsplit('-',1)[1]:{'name':name} for name in users},
		'patients':frappe.get_all('Patient',filters={'first_name':['like',tag+' %']},pluck='name'),
		'practitioners':frappe.get_all('Healthcare Practitioner',filters={'user_id':['in',users]},pluck='name'),
		'centers':frappe.get_all('Branch',filters={'branch':['like',tag+' %']},pluck='name')}
	if frappe.db.exists('Item',tag+' SESSION'):
		fixture['catalog']={'Item':[tag+' SESSION'],'Appointment Type':[tag+' SESSION'],'Price List':[tag+' PRICE'],
			'Item Price':frappe.get_all('Item Price',filters={'item_code':tag+' SESSION'},pluck='name'),
			'CC Center Service':frappe.get_all('CC Center Service',filters={'appointment_type':tag+' SESSION'},pluck='name'),
			'Practitioner Schedule':frappe.get_all('Practitioner Schedule',filters={'cc_practitioner':['in',fixture['practitioners']]},pluck='name')}
	return destroy_http(fixture)


def queue_notice_fixture(tag,user):
	if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
		frappe.throw('Synthetic DEV Administrator required')
	assert tag.startswith('CC-HTTP-') and user.startswith(tag.lower()+'-') and user.endswith('@example.invalid')
	from centrochange_core.operations.automation import enqueue_notice
	from centrochange_core.operations.notifications import deliver
	name=enqueue_notice('queue-proof:'+tag,user,'SYNTHETIC_QUEUE',None,None,'Synthetic internal queue proof')
	frappe.enqueue(deliver,queue='short',name=name,enqueue_after_commit=True,job_id='cc-notice-'+name,deduplicate=True)
	frappe.db.commit()
	return {'name':name}


def notice_fixture_status(name):
	if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
		frappe.throw('Synthetic DEV Administrator required')
	assert (frappe.db.get_value('CC Notification',name,'event_key') or '').startswith('queue-proof:CC-HTTP-')
	return {'state':frappe.db.get_value('CC Notification',name,'state'),
		'logs':frappe.db.count('Notification Log',{'cc_notification':name})}
