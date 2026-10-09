"""One-time synthetic Mission C lab presentation setup; no permissions or real users."""
import json
import frappe

frappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
try:
    frappe.set_user('Administrator')
    assert frappe.conf.get('cc_synthetic_dev') == 1 and frappe.conf.get('cc_uat_demo') == 1
    fixture=json.load(open('/home/frappe/frappe-bench/sites/b99.local/private/uat/demo.json'))['fixture']
    users=fixture['users']
    assert set(users)==set('abcs mft'.replace(' ',''))
    for label, entry in users.items():
        user=entry['name']
        assert user.startswith('cc-http-uat0000001-') and user.endswith('@example.invalid')
        frappe.db.set_value('User',user,'language','it')
        frappe.clear_cache(user=user)
    frappe.db.commit()
    print(json.dumps({'synthetic_users_configured':len(users),'language':'it'}))
finally:
    frappe.destroy()
