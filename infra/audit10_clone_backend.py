"""Real Frappe checks; executed only inside the disposable CI clone."""
import json
import frappe
from centrochange_core.security import lifecycle, audit_view
from centrochange_core.operations import workspace

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
    def denied(fn):
        try:
            fn()
        except frappe.PermissionError:
            return
        raise AssertionError('Unauthorized call succeeded')
    frappe.set_user(manager)
    assert workspace.management_context(center)['memberships']
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
    assert audit_view.events('2000-01-01', '2000-12-31')['events'] == []
    frappe.db.rollback(save_point='audit10')
    assert frappe.db.get_value('CC Center Membership', membership, 'active') == before
    assert not frappe.get_all('CC Audit Event', filters={'reason': 'Synthetic access test'}, limit_page_length=1)
    for role in ('CC Professional', 'CC Secretariat', 'CC Finance', 'CC Accountant'):
        user = principal(role)
        frappe.set_user(user)
        denied(lambda: workspace.management_context(center))
        denied(lambda: audit_view.events('2000-01-01', '2000-12-31'))
        denied(lambda: lifecycle.set_membership(professional, center, 0, 'Denied synthetic test'))
    frappe.set_user('Guest')
    denied(lambda: workspace.management_context(center))
    denied(lambda: audit_view.events('2000-01-01', '2000-12-31'))
    print(json.dumps({'status': 'PASS', 'checks': ['real roles and manager-only APIs', 'invalid state', 'membership revoke/reactivate', 'practitioner state', 'audit append-only', 'savepoint rollback']}))
finally:
    frappe.db.rollback()
    frappe.destroy()
