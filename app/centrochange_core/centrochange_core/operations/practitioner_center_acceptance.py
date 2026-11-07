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
        rotate_args = {'center':center, 'name':pending_doc.name, 'expected_version':str(pending_doc.modified), 'request_key':'CI-ROTATE', 'reason':'Synthetic rotation'}
        rotated = profiles.practitioner_regenerate_access(**rotate_args)
        assert rotated['first_access_url'] and not rotated['replay']
        assert profiles.practitioner_regenerate_access(**rotate_args) == {'name':pending_doc.name, 'replay':True}
        from centrochange_core.security.audit import append
        for index in range(101):
            append('PRACTITIONER_ACCESS_LINK_ROTATED', pending_doc.doctype, pending_doc.name,
                   {'request_key_hash':'synthetic-' + str(index)}, {'center':center}, 'Synthetic history')
        assert profiles.practitioner_regenerate_access(**rotate_args) == {'name':pending_doc.name, 'replay':True}
        rotated_token = parse_qs(urlsplit(rotated['first_access_url']).fragment)['key'][0]
        assert not _get_user_for_update_password(token, None).get('user')
        assert _get_user_for_update_password(rotated_token, None).user == pending_doc.user_id
        try:
            profiles.practitioner_regenerate_access(**{**rotate_args, 'center':other, 'request_key':'CI-CROSS-CENTER-ROTATE'})
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Cross-center key rotation accepted')
        try:
            profiles.practitioner_regenerate_access(**{**rotate_args, 'request_key':'CI-ROTATE-AGAIN'})
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Rotation cooldown bypassed')
        frappe.set_user('Administrator')
        try:
            profiles.practitioner_regenerate_access(**{**rotate_args, 'request_key':'CI-OTHER-MANAGER-ROTATE'})
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Rotation cooldown bypassed by another manager')
        for principal in (data['fixture']['users']['a']['name'], data['fixture']['users']['t']['name'], 'Guest'):
            frappe.set_user(principal)
            try:
                profiles.practitioner_regenerate_access(**{**rotate_args, 'request_key':'CI-UNAUTHORIZED-ROTATE'})
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError('Unauthorized account rotated a key')
        frappe.set_user(manager)
        acl = {'user':pending_doc.user_id, 'allow':'Healthcare Practitioner', 'for_value':pending_doc.name}
        assert frappe.db.exists('User Permission', acl)
        profiles.practitioner_set_state(center, pending_doc.name, 0, str(pending_doc.modified), 'Synthetic disable')
        pending_doc.reload()
        assert not frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert not frappe.db.exists('User Permission', acl)
        assert not _get_user_for_update_password(rotated_token, None).get('user')
        profiles.practitioner_set_state(center, pending_doc.name, 1, str(pending_doc.modified), 'Synthetic reactivation')
        pending_doc.reload()
        assert pending_doc.status == 'Active' and frappe.db.get_value('User', pending_doc.user_id, 'enabled')
        assert frappe.db.exists('User Permission', acl)
        assert set(frappe.get_roles(pending_doc.user_id)) <= {'CC Professional','All','Guest','Desk User'}
        from centrochange_core.security.lifecycle import replace_principal
        for forbidden in (elevated, user, other_user):
            try:
                replace_principal(pending_doc.name, forbidden, 'Synthetic forbidden association', confirm_email=forbidden)
            except (frappe.PermissionError, frappe.ValidationError):
                pass
            else:
                raise AssertionError('Direct association bypassed role, identity or center checks')
        assert frappe.db.get_value('Healthcare Practitioner', pending_doc.name, 'user_id') == pending_args['email']
        # Existing account association is based on explicit confirmation of
        # its login email, independent of the professional contact email.
        from centrochange_core.security.audit import internal_write
        set_membership(other_user, center, 1, 'Synthetic association')
        with internal_write('cc_practitioner_center_write'):
            unlinked = frappe.get_doc({'doctype':'Healthcare Practitioner', 'first_name':'SYNTHETIC Unlinked',
                'status':'Disabled', 'cc_profile_center':center}).insert(ignore_permissions=True)
        try:
            profiles.practitioner_link_user(center, unlinked.name, other_user, str(unlinked.modified), 'Synthetic mismatch', confirm_email='wrong@example.invalid')
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Unconfirmed account association accepted')
        profiles.practitioner_link_user(center, unlinked.name, other_user, str(unlinked.modified), 'Synthetic association', confirm_email=other_user)
        assert frappe.db.get_value('Healthcare Practitioner', unlinked.name, 'user_id') == other_user
        from unittest.mock import patch
        rename_args = {'center':center, 'name':pending_doc.name, 'email':'ci.renamed@example.invalid',
                       'expected_version':str(pending_doc.modified), 'request_key':'CI-RENAME', 'reason':'Synthetic rename'}
        try:
            profiles.practitioner_change_login_email(**{**rename_args, 'center':other, 'request_key':'CI-CROSS-CENTER-RENAME'})
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Cross-center login rename accepted')
        for principal in (data['fixture']['users']['a']['name'], data['fixture']['users']['t']['name'], 'Guest'):
            frappe.set_user(principal)
            try:
                profiles.practitioner_change_login_email(**rename_args)
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError('Unauthorized account changed a login email')
        frappe.set_user(manager)
        with patch('centrochange_core.security.lifecycle.reconcile_user', side_effect=frappe.ValidationError('Synthetic rename failure')):
            try:
                profiles.practitioner_change_login_email(**rename_args)
            except frappe.ValidationError:
                pass
            else:
                raise AssertionError('Rename failure was ignored')
        assert frappe.db.exists('User', pending_args['email']) and not frappe.db.exists('User', rename_args['email'])
        assert frappe.db.get_value('Healthcare Practitioner', pending_doc.name, 'user_id') == pending_args['email']
        try:
            profiles.practitioner_change_login_email(**{**rename_args, 'email':user, 'request_key':'CI-DUPLICATE-LOGIN'})
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Duplicate login accepted')
        changed = profiles.practitioner_change_login_email(**rename_args)
        assert not changed['replay'] and profiles.practitioner_change_login_email(**rename_args)['replay']
        assert not frappe.db.exists('User', pending_args['email']) and frappe.db.exists('User', rename_args['email'])
        assert frappe.db.get_value('Healthcare Practitioner', pending_doc.name, 'user_id') == rename_args['email']
        assert frappe.db.exists('CC Center Membership', {'user':rename_args['email'], 'center':center, 'active':1})
        assert frappe.db.exists('User Permission', {'user':rename_args['email'], 'allow':'Healthcare Practitioner', 'for_value':pending_doc.name})
        assert frappe.db.exists('CC Audit Event', {'event_type':'PRACTITIONER_LOGIN_EMAIL_CHANGED', 'reference_name':pending_doc.name})
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



def fiscal_patient_run():
    """Real Frappe/MariaDB acceptance for Patient–Customer atomicity on a clone."""
    from unittest.mock import patch
    from centrochange_core.operations import workspace
    demo.guard()
    fixture = demo.read()['fixture']
    center = fixture['centers'][0]
    manager = fixture['users']['m']['name']
    previous_test_mode = frappe.in_test
    frappe.db.savepoint('cc_fiscal_patient_acceptance')
    try:
        frappe.in_test = True
        frappe.set_user(manager)
        female = frappe.db.get_value('Gender', {'name': 'Female'}, 'name') or frappe.db.get_value('Gender', {}, 'name')
        assert female, 'Gender master missing from isolated clone'
        customer_count = frappe.db.count('Customer')
        patient_count = frappe.db.count('Patient')
        email_count = frappe.db.count('Email Queue')

        def args(serial, **overrides):
            return {**{
                'center': center, 'first_name': 'SYNTHETIC Fiscal ' + serial,
                'last_name': 'Persona', 'sex': female, 'uid': 'SYNTHETIC-FISCAL-' + serial,
                'practitioner': None, 'request_key': 'CI-FISCAL-' + serial,
                'reason': 'Collaudo anagrafica fiscale in clone',
                'email': None, 'mobile': None, 'phone': None,
            }, **overrides}

        # Case 1: self-payer; native Healthcare must assign exactly one Customer.
        self_args = args('SELF', payer_mode='self')
        self_result = workspace.create_patient(**self_args)
        self_record = frappe.get_doc('Patient', self_result['name'])
        assert self_record.customer and not self_record.get('cc_external_payer')
        assert workspace.create_patient(**self_args)['replay']
        assert frappe.db.count('Customer') == customer_count + 1

        # Case 2: new payer within one transaction.
        new_args = args('THIRD', payer_mode='new', payer_first_name='Maria',
                        payer_last_name='Bianchi', payer_tax_id='CC-HTTP-CF-PAYER-001')
        third_result = workspace.create_patient(**new_args)
        third_record = frappe.get_doc('Patient', third_result['name'])
        customer = third_record.customer
        assert customer and third_record.get('cc_external_payer')
        original_customer_name = frappe.db.get_value('Customer',customer,'customer_name')
        assert original_customer_name == 'Maria Bianchi'
        assert frappe.db.count('Customer') == customer_count + 2
        assert workspace.create_patient(**new_args)['replay']
        assert frappe.db.count('Customer') == customer_count + 2

        # Upstream Healthcare would overwrite a sole third-party Customer here.
        third_record.first_name = 'SYNTHETIC Fiscal Changed'
        third_record.save()
        assert frappe.db.get_value('Customer',customer,'customer_name') == original_customer_name

        # Case 3: second Patient reuses existing Customer from this center.
        shared_args = args('SHARED', payer_mode='existing',payer_customer=customer)
        shared_result = workspace.create_patient(**shared_args)
        shared = frappe.get_doc('Patient',shared_result['name'])
        assert shared.customer == customer and shared.get('cc_external_payer')
        assert frappe.db.count('Customer') == customer_count + 2
        assert frappe.db.count('Patient',{'customer':customer}) == 2

        # Case 4: identity collision cannot silently create another Customer.
        try:
            workspace.create_patient(**args('DUPLICATE',payer_mode='new',
                payer_first_name='Maria',payer_last_name='Bianchi',payer_tax_id='CC-HTTP-CF-PAYER-001'))
        except (frappe.ValidationError, frappe.PermissionError, frappe.DuplicateEntryError):
            pass
        else:
            raise AssertionError('Duplicate fiscal identifier accepted')

        # Case 5: failure after both inserts rolls back both masters and callbacks.
        after_customers = frappe.db.count('Customer')
        after_patients = frappe.db.count('Patient')
        callback_count = len(frappe.db.after_commit._functions)
        with patch('centrochange_core.security.lifecycle.set_assignment',
                   side_effect=frappe.ValidationError('Injected assignment failure')):
            try:
                workspace.create_patient(**args('FAIL',payer_mode='new',
                    payer_first_name='Mario',payer_last_name='Verdi',payer_tax_id='CC-HTTP-CF-FAIL'))
            except frappe.ValidationError:
                pass
            else:
                raise AssertionError('Expected atomic creation to fail')
        assert frappe.db.count('Customer') == after_customers
        assert frappe.db.count('Patient') == after_patients
        assert len(frappe.db.after_commit._functions) == callback_count

        # A forbidden role cannot provision Patient or see fiscal data.
        frappe.set_user('Guest')
        try:
            workspace.create_patient(**args('GUEST',payer_mode='self'))
        except (frappe.PermissionError, frappe.ValidationError):
            pass
        else:
            raise AssertionError('Guest created a Patient')
        frappe.set_user(manager)
        assert frappe.db.count('Email Queue') == email_count
        assert frappe.db.count('Patient') == patient_count + 3
        return {'self_payer':'PASS', 'external_payer_no_overwrite':'PASS',
                'shared_customer':'PASS', 'atomic_rollback':'PASS', 'idempotence':'PASS',
                'unauthorized_denied':'PASS', 'no_email':'PASS'}
    finally:
        frappe.in_test = previous_test_mode
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc_fiscal_patient_acceptance')
