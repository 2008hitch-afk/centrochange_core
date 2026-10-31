"""Race a synthetic center deactivation against a new membership in CI only."""
import threading
import frappe
from centrochange_core.security.audit import internal_write
from centrochange_core.security.center_state import set_operational
from centrochange_core.security.lifecycle import set_membership

SITE = 'centrochange.local'
frappe.init(SITE, sites_path='sites')
frappe.connect()
try:
    assert frappe.conf.get('cc_synthetic_dev') == 1 and frappe.conf.get('cc_uat_demo') == 1
    frappe.set_user('Administrator')
    manager = frappe.get_all('Has Role', filters={'role': 'CC Manager', 'parenttype': 'User'}, pluck='parent', limit_page_length=1)[0]
    user = frappe.get_all('Has Role', filters={'role': 'CC Professional', 'parenttype': 'User'}, pluck='parent', limit_page_length=1)[0]
    with internal_write('cc_center_state_write'):
        center = frappe.get_doc({'doctype': 'Branch', 'branch': 'AUDIT10 SYNTHETIC RACE', 'cc_operational': 1}).insert(ignore_permissions=True).name
    frappe.db.commit()
    held, attempted, release = threading.Event(), threading.Event(), threading.Event()
    result = {}
    def worker(kind):
        frappe.init(SITE, sites_path='sites')
        frappe.connect()
        try:
            frappe.set_user(manager)
            if kind == 'deactivate':
                set_operational(center, 0, 'Synthetic concurrency test')
                held.set()
                if not release.wait(15):
                    raise AssertionError('Concurrency synchronization timed out')
                frappe.db.commit()
                result[kind] = 'committed'
            else:
                if not held.wait(15):
                    raise AssertionError('Deactivation did not acquire lock')
                attempted.set()
                try:
                    set_membership(user, center, 1, 'Synthetic concurrency test')
                except frappe.PermissionError:
                    result[kind] = 'denied'
                    frappe.db.rollback()
                else:
                    frappe.db.rollback()
                    result[kind] = 'unexpectedly allowed'
        except Exception as exc:
            result[kind] = repr(exc)
            frappe.db.rollback()
        finally:
            frappe.destroy()
    first = threading.Thread(target=worker, args=('deactivate',), daemon=True)
    second = threading.Thread(target=worker, args=('activate',), daemon=True)
    first.start(); second.start()
    assert attempted.wait(20), 'Activation did not start'
    second.join(1)
    assert second.is_alive(), 'Activation failed to wait for the permission mutation lock'
    release.set()
    first.join(30); second.join(30)
    assert not first.is_alive() and not second.is_alive(), 'Concurrency threads did not finish'
    assert result == {'deactivate': 'committed', 'activate': 'denied'}, result
    frappe.db.rollback()  # Refresh this connection after the other committed.
    assert not frappe.db.exists('CC Center Membership', {'user': user, 'center': center})
    print('AUDIT10_CONCURRENCY_PASS: committed deactivation blocks concurrent activation')
finally:
    frappe.db.rollback()
    frappe.destroy()
