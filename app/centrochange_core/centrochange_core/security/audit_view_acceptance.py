"""Read-only regression on the preserved synthetic Owner UAT audit."""
import frappe
from centrochange_core.security.audit_view import events


def run():
    old_user = frappe.session.user
    try:
        user = 'cc-http-uat0000001-m@example.invalid'
        frappe.set_user(user)
        rows = events('2026-10-06', '2026-10-07')['events']
        for kind, reason in [('PROFESSIONAL_UNPAID_THRESHOLD_CONFIGURED', 'UAT-06 verifica soglia Direzione'), ('PROFESSIONAL_EXPECTATION_OVERRIDDEN', 'UAT-06 riconoscimento manuale Direzione')]:
            assert any(r.event_type == kind and r.reason == reason for r in rows)
        for suffix in ['a', 'b', 'c', 's', 'f', 't']:
            frappe.set_user('cc-http-uat0000001-' + suffix + '@example.invalid')
            try:
                events('2026-10-06', '2026-10-07')
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError('Unauthorized audit access: ' + suffix)
        frappe.set_user('Guest')
        try:
            events('2026-10-06', '2026-10-07')
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Guest audit access')
        return {'status': 'PASS', 'checks': ['management read', 'two Owner UAT events', 'seven unauthorized principals denied']}
    finally:
        frappe.set_user(old_user)
