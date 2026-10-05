"""Private UAT management boundary regressions; no fixture mutation needed."""
import frappe
from centrochange_core.uat import demo


def run():
    demo.guard()
    original = frappe.session.user
    flag = frappe.conf.get('cc_uat_demo')
    synthetic = frappe.conf.get('cc_synthetic_dev')
    checks = []
    try:
        for actor in ('Guest', demo.TAG.lower() + '-m@example.invalid'):
            frappe.set_user(actor)
            for method in (demo.seed, demo.inspect, demo.validate, demo.reset, demo.credentials):
                try:
                    method()
                except frappe.PermissionError:
                    pass
                else:
                    raise AssertionError('Private UAT method accepted non-Administrator')
            checks.append('private UAT methods deny ' + ('Guest' if actor == 'Guest' else 'Management operator'))
        frappe.set_user('Administrator')
        for key in ('cc_uat_demo', 'cc_synthetic_dev'):
            frappe.conf[key] = 0
            try:
                demo.seed()
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError('Seed accepted missing explicit synthetic/UAT configuration')
            frappe.conf[key] = flag if key == 'cc_uat_demo' else synthetic
            checks.append('seed denies missing ' + key + ' even for Administrator')
        assert not any(method in frappe.whitelisted for method in (demo.seed, demo.inspect, demo.validate, demo.reset, demo.credentials))
        checks.append('all UAT management methods remain non-whitelisted')
        return {'status': 'PASS', 'checks': checks}
    finally:
        frappe.conf.cc_uat_demo = flag
        frappe.conf.cc_synthetic_dev = synthetic
        frappe.set_user(original)
