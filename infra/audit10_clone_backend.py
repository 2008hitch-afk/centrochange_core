"""Real Frappe checks; executed only inside the disposable CI clone."""
import json
import frappe
from centrochange_core.security import lifecycle, audit_view
from centrochange_core.operations import workspace
from centrochange_core.security.guards import require_center, patient_names
from centrochange_core.security.center_state import set_operational

frappe.init('centrochange.local', sites_path='sites')
frappe.connect()
try:
    assert frappe.conf.get('cc_synthetic_dev') == 1 and frappe.conf.get('cc_uat_demo') == 1
    center = frappe.get_all('Branch', filters={'cc_operational': 1}, pluck='name', order_by='name', limit_page_length=1)[0]
    users = frappe.get_all('CC Center Membership', filters={'center': center, 'active': 1}, pluck='user', limit_page_length=0)
    def principal(role):
        roles = frappe.get_all('Has Role', filters={'role': role, 'parent': ['in', users]}, pluck='parent', limit_page_length=0)
        assert roles, role
        return roles[0]
    manager = principal('CC Manager')
    professional_users = frappe.get_all('Has Role', filters={'role': 'CC Professional', 'parent': ['in', users]}, pluck='parent', limit_page_length=0)
    practitioners = frappe.get_all('Healthcare Practitioner', filters={'user_id': ['in', professional_users], 'status': 'Active'}, fields=['name', 'user_id'], limit_page_length=1)
    assert practitioners, 'No active synthetic professional with an account'
    practitioner, professional = practitioners[0].name, practitioners[0].user_id
    membership = frappe.db.get_value('CC Center Membership', {'center': center, 'user': professional}, 'name')
    assert membership
    fingerprint_types = ('CC Center Membership', 'CC Audit Event', 'DocShare', 'User Permission', 'Has Role')
    fingerprint = {doctype: frappe.db.count(doctype) for doctype in fingerprint_types}
    def denied(fn):
        try:
            fn()
        except frappe.PermissionError:
            return
        raise AssertionError('Unauthorized call succeeded')
    frappe.set_user(manager)
    assert workspace.management_context(center)['memberships']
    denied(lambda: frappe.get_list('CC Private Note', pluck='name', limit_page_length=1))
    notes = audit_view.events(frappe.utils.nowdate(), frappe.utils.nowdate(), event_type='PRIVATE_NOTE_CREATED')['events']
    assert notes, 'The synthetic private-note audit fixture is missing'
    assert all('SYNTHETIC PRIVATE BODY' not in json.dumps(row, default=str) for row in notes)
    before = frappe.db.get_value('CC Center Membership', membership, 'active')
    assert before == 1
    frappe.db.savepoint('audit10')
    for bad in ('invalid', '', '2', '-1'):
        try:
            lifecycle.set_membership(professional, center, bad, 'Synthetic validation')
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Malformed state accepted')
        assert frappe.db.get_value('CC Center Membership', membership, 'active') == 1
    lifecycle.set_membership(professional, center, 0, 'Synthetic access test')
    assert frappe.db.get_value('CC Center Membership', membership, 'active') == 0
    lifecycle.set_membership(professional, center, 1, 'Synthetic access test')
    assert frappe.db.get_value('CC Center Membership', membership, 'active') == 1
    lifecycle.set_membership(professional, center, 1, 'Synthetic access test')
    lifecycle.set_practitioner_state(practitioner, 0, 'Synthetic state test')
    assert frappe.db.get_value('User', professional, 'enabled') == 0
    lifecycle.set_practitioner_state(practitioner, 1, 'Synthetic state test')
    assert frappe.db.get_value('User', professional, 'enabled') == 1
    events = frappe.get_all('CC Audit Event', filters={'reason': ['in', ['Synthetic access test', 'Synthetic state test']]}, fields=['name', 'event_type'], limit_page_length=0)
    assert sum(row.event_type == 'CENTER_MEMBERSHIP' for row in events) == 2
    assert sum(row.event_type == 'PRACTITIONER_STATE' for row in events) == 2
    original = frappe.get_doc('CC Audit Event', events[0].name)
    denied(lambda: original.check_permission('write'))
    denied(lambda: original.check_permission('delete'))
    denied(lambda: frappe.get_doc({'doctype': 'CC Audit Event', 'event_type': 'ARBITRARY', 'reason': 'Synthetic unauthorized insertion'}).insert())
    assert audit_view.events('2000-01-01', '2000-12-31')['events'] == []
    frappe.db.rollback(save_point='audit10')
    assert frappe.db.get_value('CC Center Membership', membership, 'active') == before
    assert not frappe.get_all('CC Audit Event', filters={'reason': 'Synthetic access test'}, limit_page_length=1)
    # A dual-role synthetic practitioner cannot disable their own active account.
    frappe.db.savepoint('self_lockout')
    frappe.set_user('Administrator')
    dual = frappe.get_doc('User', professional)
    dual.append('roles', {'role': 'CC Manager'})
    dual.save(ignore_permissions=True)
    frappe.set_user(professional)
    try:
        lifecycle.set_practitioner_state(practitioner, 0, 'Synthetic self-lockout test')
    except (frappe.PermissionError, frappe.ValidationError):
        pass
    else:
        raise AssertionError('Self-lockout succeeded')
    assert frappe.db.get_value('User', professional, 'enabled') == 1
    frappe.db.rollback(save_point='self_lockout')
    for role in ('CC Professional', 'CC Secretariat', 'CC Finance', 'CC Accountant'):
        user = principal(role)
        frappe.set_user(user)
        denied(lambda: workspace.management_context(center))
        denied(lambda: audit_view.events('2000-01-01', '2000-12-31'))
        denied(lambda: lifecycle.set_membership(professional, center, 0, 'Denied synthetic test'))
        denied(lambda: lifecycle.set_practitioner_state(practitioner, 0, 'Denied synthetic test'))
    frappe.set_user(professional)
    other_centers = frappe.get_all('Branch', filters={'cc_operational': 1, 'name': ['!=', center]}, pluck='name', limit_page_length=0)
    assert other_centers
    denied(lambda: require_center(other_centers[0]))
    # A new membership for an inactive center must not silently expand historical scope.
    cross = frappe.get_all('CC Patient Assignment', filters={'center': ['!=', center], 'active': 1}, fields=['center', 'patient'], limit_page_length=1)[0]
    other, target = cross.center, cross.patient
    secretary = principal('CC Secretariat')
    frappe.db.savepoint('inactive_center_test')
    frappe.set_user(manager)
    lifecycle.set_membership(secretary, other, 1, 'Synthetic historical access')
    set_operational(other, 0, 'Synthetic inactive-center test')
    frappe.set_user(secretary)
    before_scope = set(patient_names())
    assert target in before_scope, 'Existing historical scope must remain available'
    frappe.set_user(manager)
    lifecycle.set_membership(secretary, other, 1, 'Synthetic no-op')
    assert not frappe.get_all('CC Audit Event', filters={'reason': 'Synthetic no-op'}, limit_page_length=1)
    lifecycle.set_membership(secretary, other, 0, 'Synthetic revoke inactive center')
    frappe.set_user(secretary)
    assert target not in set(patient_names()), 'Revocation did not remove historical scope'
    frappe.set_user(manager)
    denied(lambda: lifecycle.set_membership(secretary, other, 1, 'Synthetic denied reactivation'))
    denied(lambda: lifecycle.set_membership(professional, other, 1, 'Synthetic denied new membership'))
    denied(lambda: lifecycle.set_membership(professional, 'CC-UNKNOWN-CENTER', 1, 'Synthetic denied unknown center'))
    assert not frappe.db.exists('CC Center Membership', {'user': professional, 'center': other})
    assert not frappe.get_all('CC Audit Event', filters={'reason': ['in', ['Synthetic denied reactivation', 'Synthetic denied new membership']]}, limit_page_length=1)
    frappe.set_user(secretary)
    expanded = target in set(patient_names())
    frappe.db.rollback(save_point='inactive_center_test')
    assert fingerprint == {doctype: frappe.db.count(doctype) for doctype in fingerprint_types}, 'Synthetic test left unexpected records'
    frappe.set_user('Guest')
    denied(lambda: workspace.management_context(center))
    denied(lambda: audit_view.events('2000-01-01', '2000-12-31'))
    denied(lambda: lifecycle.set_membership(professional, center, 0, 'Guest denied synthetic test'))
    denied(lambda: lifecycle.set_practitioner_state(practitioner, 0, 'Guest denied synthetic test'))
    print(json.dumps({'status': 'PASS', 'inactive_center_expands_historical_access': expanded, 'checks': ['real roles and manager-only APIs', 'invalid state', 'membership revoke/reactivate', 'practitioner state', 'audit append-only', 'savepoint rollback']}))
finally:
    frappe.db.rollback()
    frappe.destroy()
