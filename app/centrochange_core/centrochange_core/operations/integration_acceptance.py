"""Final composed DEV regression and actionable native patient intake boundaries."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import ts_acceptance,receivables_acceptance
from centrochange_core.operations import workspace
from centrochange_core.security.lifecycle import set_assignment,set_practitioner_state


def checks(fixture):
    result=ts_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    center=fixture['center'];frappe.set_user(fixture['secretary'])
    args={'center':center,'first_name':'SYNTHETIC INTEGRATED PATIENT','last_name':'DEV','sex':'Female','uid':'SYNTHETIC-INTEGRATED-UID',
        'practitioner':fixture['prac1'],'request_key':'synthetic-integrated-intake','reason':'Synthetic integrated patient intake','email':'synthetic.integrated@example.invalid'}
    before={dt:frappe.db.count(dt) for dt in ('Patient','User','Email Queue')}
    patient=workspace.create_patient(**args)['name']
    assert workspace.create_patient(**args)['replay']
    assert frappe.db.count('Patient')==before['Patient']+1 and frappe.db.count('User')==before['User'] and frappe.db.count('Email Queue')==before['Email Queue']
    frappe.get_doc('Patient',patient).check_permission('read')
    assert frappe.db.count('CC Audit Event',{'event_type':'PATIENT_INTAKE_CREATED','reference_name':patient})==1
    reject(lambda:workspace.create_patient(**{**args,'first_name':'SYNTHETIC CHANGED RETRY'}))
    reject(lambda:workspace.create_patient(**{**args,'request_key':'synthetic-duplicate-uid'}))
    result.append('secretariat native patient creation plus audited assignment replay once without portal invitation or email; changed request and duplicate UID denied')
    doc=frappe.get_doc('Patient',patient);doc.cc_intake_key='FORGED';reject(lambda:doc.save(ignore_permissions=True))
    reject(lambda:workspace.create_patient(**{**args,'center':fixture['other'],'request_key':'synthetic-other-center','uid':'SYNTHETIC-OTHER-CENTER'}))
    reject(lambda:workspace.create_patient(**{**args,'first_name':'UNMARKED INPUT','request_key':'synthetic-unmarked','uid':'SYNTHETIC-UNMARKED'}))
    reject(lambda:workspace.create_patient(**{**args,'email':'synthetic@example.com','request_key':'synthetic-nonfictional-email','uid':'SYNTHETIC-NONFICTIONAL'}))
    result.append('controlled patient intake metadata immutable and unauthorized center/nonfictional input cannot create a master')
    frappe.set_user('Administrator');set_practitioner_state(fixture['prac1'],0,'Synthetic invalid assignment rollback test')
    frappe.set_user(fixture['secretary']);count=frappe.db.count('Patient')
    reject(lambda:workspace.create_patient(**{**args,'request_key':'synthetic-disabled-prac','uid':'SYNTHETIC-DISABLED-PRACTITIONER'}))
    assert frappe.db.count('Patient')==count
    frappe.set_user('Administrator');set_practitioner_state(fixture['prac1'],1,'Synthetic valid practitioner restoration')
    set_assignment(patient,center,fixture['prac1'],0,'Synthetic integrated intake context revocation')
    frappe.set_user(fixture['secretary']);reject(lambda:workspace.create_patient(**args))
    result.append('invalid practitioner assignment rolls native patient creation back; replay after context revocation cannot regrant access')
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid',fixture['secretary']):
        frappe.set_user(actor);reject(lambda:workspace.management_context(center))
        if actor!=fixture['secretary']:reject(lambda:workspace.create_patient(**{**args,'request_key':actor,'uid':'SYNTHETIC-UNAUTHORIZED'}))
    frappe.set_user('Administrator');context=workspace.management_context(center)
    assert context['memberships'] and all(set(row)<={'name','full_name','enabled'} for row in context['users'])
    assert fixture['prac1'] in {r.name for r in context['practitioners']}
    boot=workspace.bootstrap(center)
    assert center in {r.name for r in boot['centers']} and fixture['prac1'] in {r.name for r in boot['practitioners']}
    result.append('Management unfiltered center and practitioner discovery remains nonempty on an assigned native fixture')
    result.append('management context excludes credentials and clinical data; professional accountant and secretariat cannot administer center memberships')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:return security.run(extra_checks=checks)
    finally:frappe.flags.cc_test_clock=previous
