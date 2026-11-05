"""Isolated synthetic acceptance for personal professional accounts."""
import frappe
from centrochange_core.uat import demo
from centrochange_core.operations import profiles
from centrochange_core.security.guards import practitioner_in_center


def run():
    demo.guard()
    data = demo.read()
    center, other = data['fixture']['centers'][:2]
    manager = data['fixture']['users']['m']['name']
    previous_test_mode = frappe.in_test
    frappe.db.savepoint('cc_profile_acceptance')
    try:
        frappe.in_test = True
        frappe.set_user('Administrator')
        def make_user(email):
            return frappe.get_doc({'doctype':'User', 'email':email, 'first_name':'Synthetic CI',
                'enabled':1, 'send_welcome_email':0, 'roles':[{'role':'CC Professional'}]}).insert(ignore_permissions=True).name
        user = make_user('ci.profile-link@example.invalid')
        other_user = make_user('ci.profile-other@example.invalid')
        frappe.set_user(manager)
        from centrochange_core.security.lifecycle import set_membership
        set_membership(user, center, 1, 'Synthetic acceptance')
        set_membership(other_user, other, 1, 'Synthetic acceptance')
        counts = {doctype: frappe.db.count(doctype) for doctype in ('User', 'Sales Invoice', 'Payment Entry', 'Email Queue')}
        args = {'center':center, 'first_name':'SYNTHETIC CI Professional', 'last_name':'Test', 'email':user,
                'user':user, 'mobile_phone':'000300', 'request_key':'CI-PRACTITIONER-ACCEPTANCE', 'reason':'Synthetic acceptance'}
        for changes in ({'user':None}, {'user':other_user, 'email':other_user}, {'email':''}, {'last_name':''}):
            try:
                profiles.practitioner_create(**{**args, **changes})
            except (frappe.ValidationError, frappe.PermissionError):
                pass
            else:
                raise AssertionError('Missing or cross-center account/data accepted')
        frappe.set_user(data['fixture']['users']['a']['name'])
        try:
            profiles.practitioner_create(**args)
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Professional role created a practitioner')
        frappe.set_user(manager)
        try:
            frappe.get_doc({'doctype':'Healthcare Practitioner', 'first_name':'Synthetic no account', 'status':'Active'}).insert(ignore_permissions=True)
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Direct active accountless profile accepted')
        created = profiles.practitioner_create(**args)
        assert not created['replay'] and profiles.practitioner_create(**args)['replay']
        doc = frappe.get_doc('Healthcare Practitioner', created['name'])
        assert doc.user_id == user and doc.status == 'Active' and doc.get('cc_profile_center') == center
        assert practitioner_in_center(doc, center) and not practitioner_in_center(doc, other)
        assert frappe.db.exists('CC Audit Event', {'event_type':'PREMIUM_MASTER_CREATED', 'reference_name':doc.name})
        try:
            profiles.practitioner_create(**{**args, 'request_key':'CI-DUPLICATE'})
        except (frappe.ValidationError, frappe.PermissionError, frappe.DuplicateEntryError):
            pass
        else:
            raise AssertionError('Shared account accepted')
        assert counts == {doctype: frappe.db.count(doctype) for doctype in counts}
        pending_args = {**args, 'user':None, 'email':'ci.pending@example.invalid', 'account_mode':'new', 'request_key':'CI-PENDING'}
        pending = profiles.practitioner_create(**pending_args)
        assert profiles.practitioner_create(**pending_args)['replay']
        pending_doc = frappe.get_doc('Healthcare Practitioner', pending['name'])
        assert pending_doc.user_id == pending_args['email'] and pending_doc.status == 'Disabled'
        assert not frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert frappe.db.exists('CC Center Membership', {'user':pending_doc.user_id, 'center':center, 'active':1})
        assert not practitioner_in_center(pending_doc, center)
        try:
            profiles.practitioner_set_state(center, pending_doc.name, 1, str(pending_doc.modified), 'Synthetic unauthorized activation')
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Inactive account activated without authorization')
        assert frappe.db.count('Email Queue') == counts['Email Queue']
        return {'personal_account':'PASS', 'pending_account':'PASS', 'center_isolation':'PASS', 'missing_and_duplicate_denied':'PASS', 'audit_and_replay':'PASS', 'no_invoice_or_email':'PASS'}
    finally:
        frappe.in_test = previous_test_mode
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc_profile_acceptance')
