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
        elevated = frappe.get_doc({'doctype':'User', 'email':'ci.elevated@example.invalid', 'first_name':'Synthetic elevated',
            'enabled':1, 'send_welcome_email':0, 'roles':[{'role':'CC Professional'}, {'role':'CC Manager'}]}).insert(ignore_permissions=True).name
        frappe.set_user(manager)
        from centrochange_core.security.lifecycle import set_membership
        set_membership(user, center, 1, 'Synthetic acceptance')
        set_membership(other_user, other, 1, 'Synthetic acceptance')
        set_membership(elevated, center, 1, 'Synthetic acceptance')
        counts = {doctype: frappe.db.count(doctype) for doctype in ('User', 'Sales Invoice', 'Payment Entry', 'Email Queue')}
        args = {'center':center, 'first_name':'SYNTHETIC CI Professional', 'last_name':'Test', 'email':user,
                'user':user, 'account_mode':'existing', 'mobile_phone':'000300', 'request_key':'CI-PRACTITIONER-ACCEPTANCE', 'reason':'Synthetic acceptance'}
        for changes in ({'user':None}, {'user':other_user, 'email':other_user}, {'user':elevated, 'email':elevated}, {'email':'mismatch@example.invalid'}, {'email':''}, {'last_name':''}):
            try:
                profiles.practitioner_create(**{**args, **changes})
            except (frappe.ValidationError, frappe.PermissionError):
                pass
            else:
                raise AssertionError('Missing or cross-center account/data accepted')
        for principal in (data['fixture']['users']['a']['name'], data['fixture']['users']['t']['name'], 'Guest'):
            frappe.set_user(principal)
            try:
                profiles.practitioner_create(**args)
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError('Unauthorized role created a practitioner')
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
        assert pending.get('first_access_url') and profiles.practitioner_create(**pending_args)['replay']
        assert 'first_access_url' not in profiles.practitioner_create(**pending_args)
        from urllib.parse import parse_qs, urlsplit
        from frappe.core.doctype.user.user import _get_user_for_update_password
        token = parse_qs(urlsplit(pending['first_access_url']).fragment)['key'][0]
        assert _get_user_for_update_password(token, None).user == pending_args['email']
        assert token != frappe.db.get_value('User', pending_args['email'], 'reset_password_key')
        assert not frappe.db.exists('CC Audit Event', {'reference_name':pending['name'], 'after_state':['like','%' + token + '%']})
        frappe.db.set_value('User', pending_args['email'], 'last_reset_password_key_generated_on', frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-2))
        assert _get_user_for_update_password(token, None).get('message')
        frappe.db.set_value('User', pending_args['email'], 'last_reset_password_key_generated_on', frappe.utils.now_datetime())
        pending_doc = frappe.get_doc('Healthcare Practitioner', pending['name'])
        assert pending_doc.user_id == pending_args['email'] and pending_doc.status == 'Active'
        assert frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert frappe.db.exists('CC Center Membership', {'user':pending_doc.user_id, 'center':center, 'active':1})
        assert practitioner_in_center(pending_doc, center)
        profiles.practitioner_set_state(center, pending_doc.name, 0, str(pending_doc.modified), 'Synthetic disable')
        pending_doc.reload()
        assert not frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert not _get_user_for_update_password(token, None).get('user')
        profiles.practitioner_set_state(center, pending_doc.name, 1, str(pending_doc.modified), 'Synthetic reactivation')
        pending_doc.reload()
        assert pending_doc.status == 'Active' and frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert set(frappe.get_roles(pending_doc.user_id)) <= {'CC Professional','All','Guest','Desk User'}
        from unittest.mock import patch
        frappe.in_test = False
        callback_count = len(frappe.db.after_commit._functions)
        with patch('centrochange_core.security.lifecycle.set_membership', side_effect=frappe.ValidationError('Synthetic injected failure')):
            try:
                profiles.practitioner_create(**{**pending_args, 'email':'ci.failed@example.invalid', 'request_key':'CI-FAILURE'})
            except frappe.ValidationError:
                pass
            else:
                raise AssertionError('Injected provisioning error was ignored')
        assert not frappe.db.exists('User', 'ci.failed@example.invalid')
        assert len(frappe.db.after_commit._functions) == callback_count
        frappe.in_test = True
        assert frappe.db.count('Email Queue') == counts['Email Queue']
        return {'personal_account':'PASS', 'active_account_and_reactivation':'PASS', 'center_isolation':'PASS', 'missing_and_duplicate_denied':'PASS', 'audit_and_replay':'PASS', 'no_invoice_or_email':'PASS'}
    finally:
        frappe.in_test = previous_test_mode
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc_profile_acceptance')
