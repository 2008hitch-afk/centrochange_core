"""Synthetic security regression via bench, never a whitelisted API."""
import frappe
from centrochange_core.security import lifecycle as service
from centrochange_core.security.api import discover_patient, get_patient_detail


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


def create_http():
	"""Create explicitly marked disposable HTTP fixtures; harness destroys them."""
	if frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1:
		frappe.throw('Synthetic DEV Administrator required')
	from frappe.utils.password import update_password
	tag = 'CC-HTTP-' + frappe.generate_hash(length=10)
	result = {'tag':tag, 'users':{}, 'patients':[], 'practitioners':[], 'centers':[]}
	for label, role in [('a','CC Professional'), ('b','CC Professional'), ('c','CC Professional'), ('s','CC Secretariat')]:
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
	groups['CC Patient Assignment']=frappe.get_all('CC Patient Assignment',filters={'patient':['in',fixture['patients']]},pluck='name')
	groups['CC Center Membership']=frappe.get_all('CC Center Membership',filters={'user':['in',users]},pluck='name')
	groups['CC Audit Event']=frappe.get_all('CC Audit Event',filters={'reason':tag},pluck='name')
	# Native Patient creates contacts/customers; discover only links to these exact fixtures.
	groups['Contact']=frappe.get_all('Contact',filters={'user':['in',users]},pluck='name')
	groups['Contact']+=frappe.get_all('Dynamic Link',filters={'parenttype':'Contact','link_doctype':'Patient',
		'link_name':['in',fixture['patients']]},pluck='parent')
	groups['Customer']=[frappe.db.get_value('Patient',name,'customer') for name in fixture['patients']]
	groups['Customer']=[name for name in groups['Customer'] if name]
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
