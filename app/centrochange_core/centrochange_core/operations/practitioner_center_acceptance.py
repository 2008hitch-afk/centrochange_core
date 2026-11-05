"""Synthetic-only integration check for accountless center profiles."""
import frappe
from centrochange_core.uat import demo
from centrochange_core.operations import profiles, workspace
from centrochange_core.security.guards import practitioner_names_for_center


def run():
    demo.guard()
    data = demo.read()
    center, other = data['fixture']['centers'][:2]
    manager = data['fixture']['users']['m']['name']
    professional = data['fixture']['users']['a']['name']
    previous_test_mode = frappe.in_test
    frappe.db.savepoint('cc_profile_acceptance')
    try:
        # User fixtures must not enqueue background work that outlives rollback.
        frappe.in_test = True
        # Self-contained fixture: never rely on an unlinked account left by a
        # previous test run.  Rollback removes it together with the test data.
        from centrochange_core.security.lifecycle import set_membership
        frappe.set_user('Administrator')
        user = frappe.get_doc({'doctype':'User', 'email':'ci.profile-link@example.invalid',
            'first_name':'Synthetic CI account', 'enabled':1, 'send_welcome_email':0,
            'roles':[{'role':'CC Professional'}]}).insert(ignore_permissions=True).name
        other_user = frappe.get_doc({'doctype':'User', 'email':'ci.profile-other@example.invalid',
            'first_name':'Synthetic CI other center', 'enabled':1, 'send_welcome_email':0,
            'roles':[{'role':'CC Professional'}]}).insert(ignore_permissions=True).name
        frappe.set_user(manager)
        set_membership(user, center, 1, 'Synthetic acceptance')
        set_membership(other_user, other, 1, 'Synthetic acceptance')
        counts = {doctype: frappe.db.count(doctype) for doctype in ('User', 'Sales Invoice', 'Payment Entry', 'Email Queue')}
        gender = frappe.get_all('Gender', pluck='name', limit_page_length=1)[0]
        patient = workspace.create_patient(center=center, first_name='SYNTHETIC CI Patient', last_name='Test', sex=gender,
            uid='SYNTHETIC-CI-PROFILE-ACCEPTANCE', practitioner=None, request_key='CI-PATIENT-ACCEPTANCE',
            reason='Synthetic acceptance', email='ci.patient@example.invalid', phone='000100', mobile='000200')
        assert not patient['replay']
        assert frappe.db.get_value('Patient', patient['name'], 'phone') == '000100'
        assert frappe.db.exists('CC Audit Event', {'event_type':'PATIENT_INTAKE_CREATED', 'reference_name':patient['name']})
        args = {'center':center, 'first_name':'SYNTHETIC CI Professional', 'last_name':'Test', 'email':'ci.professional@example.invalid',
                'mobile_phone':'000300', 'request_key':'CI-PRACTITIONER-ACCEPTANCE', 'reason':'Synthetic acceptance'}
        created = profiles.practitioner_create(**args)
        assert not created['replay'] and profiles.practitioner_create(**args)['replay']
        doc = frappe.get_doc('Healthcare Practitioner', created['name'])
        assert not doc.user_id and doc.get('cc_profile_center') == center and doc.email_id == args['email']
        assert doc.name in practitioner_names_for_center(center) and doc.name not in practitioner_names_for_center(other)
        assert frappe.db.exists('CC Audit Event', {'event_type':'PREMIUM_MASTER_CREATED', 'reference_name':doc.name})
        from centrochange_core.security.lifecycle import set_assignment
        from centrochange_core.scheduling.booking import require_booking
        user_permissions = frappe.db.count('User Permission')
        set_assignment(patient['name'], center, doc.name, 1, 'Synthetic assignment')
        require_booking(patient['name'], doc.name, center)
        assert frappe.db.count('User Permission') == user_permissions
        try:
            profiles.practitioner_create(**{**args, 'email':'ci.changed@example.invalid'})
            raise AssertionError('changed replay accepted')
        except frappe.ValidationError:
            pass
        try:
            profiles.practitioner_detail(other, doc.name)
            raise AssertionError('cross-center profile accepted')
        except frappe.PermissionError:
            pass
        frappe.set_user(professional)
        try:
            profiles.practitioner_detail(center, doc.name)
            raise AssertionError('other professional profile accepted')
        except frappe.PermissionError:
            pass
        try:
            profiles.practitioner_create(**{**args, 'request_key':'CI-UNAUTHORIZED'})
            raise AssertionError('professional creation accepted')
        except frappe.PermissionError:
            pass
        frappe.set_user(manager)
        state = profiles.practitioner_set_state(center, doc.name, 0, str(doc.modified), 'Synthetic disable')
        assert state['status'] == 'Disabled'
        doc.reload()
        state = profiles.practitioner_set_state(center, doc.name, 1, str(doc.modified), 'Synthetic enable')
        assert state['status'] == 'Active'
        doc.reload()
        candidates = profiles.practitioner_access_candidates(center, doc.name)
        assert user in [candidate['name'] for candidate in candidates]
        old_roles = set(frappe.get_roles(user))
        profiles.practitioner_link_user(center, doc.name, user, str(doc.modified), 'Synthetic account link')
        assert frappe.db.get_value('Healthcare Practitioner', doc.name, 'user_id') == user
        assert set(frappe.get_roles(user)) == old_roles
        second = profiles.practitioner_create(**{**args, 'email':'ci.second@example.invalid', 'request_key':'CI-SECOND-PROFILE'})
        assert user not in [row['name'] for row in profiles.practitioner_access_candidates(center, second['name'])]
        from centrochange_core.security.lifecycle import replace_principal
        for forbidden in (user, other_user):
            try:
                replace_principal(second['name'], forbidden, 'Synthetic forbidden link')
            except (frappe.ValidationError, frappe.PermissionError, frappe.DuplicateEntryError):
                pass
            else:
                raise AssertionError('Shared or cross-center principal accepted')
        assert not frappe.db.get_value('Healthcare Practitioner', second['name'], 'user_id')
        assert counts == {doctype: frappe.db.count(doctype) for doctype in counts}
        return {'accountless_profile':'PASS', 'center_isolation':'PASS', 'patient_intake':'PASS', 'audit_and_replay':'PASS', 'no_user_invoice_or_email':'PASS'}
    finally:
        frappe.in_test = previous_test_mode
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc_profile_acceptance')
