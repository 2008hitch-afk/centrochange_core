"""Audit visibility test with a unique rollback-only synthetic business event."""
import frappe
from centrochange_core.security import dev_acceptance
from centrochange_core.security.audit import append
from centrochange_core.security.audit_view import events


@dev_acceptance.synthetic_test
def run():
    if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
        frappe.throw('Synthetic DEV Administrator required')
    user=frappe.session.user;frappe.db.savepoint('cc_audit_view_regression')
    try:
        event_name='MVP-AUDIT-'+frappe.generate_hash(length=10)
        append('MVP_AUDIT_VIEW_TEST','Branch',event_name,{}, {'synthetic':True},'Synthetic audit visibility regression')
        managers=frappe.get_all('Has Role',filters={'role':'CC Manager'},pluck='parent',limit_page_length=0)
        manager=next((name for name in managers if frappe.db.get_value('User',name,'enabled')),None)
        assert manager,'An enabled Direzione account is required for audit acceptance.'
        row=frappe.get_all('CC Audit Event',filters={'event_type':'MVP_AUDIT_VIEW_TEST','reference_name':event_name},fields=['name','event_time'],limit=1)[0]
        date=frappe.utils.getdate(row.event_time)
        frappe.set_user(manager)
        result=events(str(date),str(date),event_type='MVP_AUDIT_VIEW_TEST',reference=event_name)
        assert any(item.name==row.name for item in result['events'])
        for role in ('CC Professional','CC Secretariat','CC Finance','CC Accountant'):
            principals=frappe.get_all('Has Role',filters={'role':role},pluck='parent',limit_page_length=0)
            principal=next((name for name in principals if frappe.db.get_value('User',name,'enabled')),None)
            if not principal:continue
            frappe.set_user(principal)
            try:events(str(date),str(date))
            except frappe.PermissionError:pass
            else:raise AssertionError('Unauthorized audit access: '+role)
        frappe.set_user('Guest')
        try:events(str(date),str(date))
        except frappe.PermissionError:pass
        else:raise AssertionError('Guest audit access')
        return {'status':'PASS','checks':['isolated synthetic event visible to Direzione with date/type/reference filters','professional, secretariat, finance and accountant denied','Guest denied']}
    finally:
        frappe.db.rollback(save_point='cc_audit_view_regression');frappe.set_user(user)
