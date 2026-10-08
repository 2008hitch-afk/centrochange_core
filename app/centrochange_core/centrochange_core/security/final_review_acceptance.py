"""Private final review against preserved Owner demo. Revoke probes fully roll back."""
import frappe
from centrochange_core.security import guards,lifecycle,audit_view
from centrochange_core.finance import guards as finance,reporting,patient_reporting
from centrochange_core.operations import workspace,notes,booking_confirmation


def run():
    from centrochange_core.uat.demo import credentials,inspect
    fixture=credentials();demo=inspect();previous=frappe.session.user;center=fixture['centers'][0];other=fixture['centers'][1];checks=[];matrix={}
    args=dict(center=center,start='2026-09-28',end='2026-10-31')
    private=frappe.get_doc('CC Private Note',fixture['private_note'])
    def denied(call):
        try:call()
        except frappe.PermissionError:return
        raise AssertionError('Unexpected permission allowance')
    try:
        for role in ('m','s','f','t','a','b','c'):
            frappe.set_user(fixture['users'][role]['name']);assigned=guards.roles();assert 'System Manager' not in assigned
            manager=role=='m';operational=role in ('m','s','a','b','c');accounting=role in ('m','s','f','t');writer=role in ('m','s','f')
            assert finance.allowed()==accounting and finance.allowed(write=True)==writer
            if manager:finance.require_finance_manager();workspace.management_context(center);audit_view.events('2026-10-06','2026-10-07');booking_confirmation.records(center)
            else:
                for call in (finance.require_finance_manager,lambda:workspace.management_context(center),lambda:audit_view.events('2026-10-06','2026-10-07'),lambda:booking_confirmation.records(center)):denied(call)
            if operational:
                boot=workspace.bootstrap(center)
                names={r.name for r in workspace.patient_search(center,'')['patients']}
                if role=='a':assert demo['patients']['Alfa'] in names and demo['patients']['Zeta'] not in names
                if role=='b':assert demo['patients']['Zeta'] in names and demo['patients']['Alfa'] not in names
                if role=='c':assert not names and not boot['patients']
                if role=='a':private.check_permission('read')
                else:denied(lambda:private.check_permission('read'))
            else:denied(lambda:workspace.bootstrap(center));denied(lambda:private.check_permission('read'))
            if accounting:
                data=patient_reporting.patient_view(**args,patient=demo['patients']['Theta']);assert 'PRIVATE BODY' not in frappe.as_json(data)
                reporting.professional_view(**{**args,'practitioner':fixture['practitioners'][0]})
                frappe.get_doc('Sales Invoice',demo['invoices']['Theta insoluto scaduto']).check_permission('read')
            else:
                denied(lambda:patient_reporting.patient_view(**args));denied(lambda:reporting.summary(**args));denied(lambda:frappe.get_doc('Sales Invoice',demo['invoices']['Theta insoluto scaduto']).check_permission('read'))
            if not manager:
                denied(lambda:guards.require_center(other));denied(lambda:reporting.summary(**{**args,'center':other}))
            matrix[role]={'roles':assigned,'manager':manager,'operational':operational,'finance_read':accounting,'finance_write':writer,'private_note':role=='a','technical_admin':False}
            checks.append(role+' role/application/center/direct-note/direct-invoice/audit/recovery guards')
        frappe.set_user('Guest')
        for call in (lambda:workspace.bootstrap(center),lambda:reporting.summary(**args),finance.require_finance_manager):denied(call)
        checks.append('Guest internal application/finance/management denied; public ingress separate')
        # Actual governed relationship revocation, in this transaction only.
        frappe.set_user(fixture['users']['m']['name']);lifecycle.set_membership(fixture['users']['a']['name'],center,0,'Synthetic final-review rollback revocation')
        frappe.set_user(fixture['users']['a']['name']);denied(lambda:workspace.patient_search(center,'Alfa'));denied(lambda:frappe.get_doc('Patient',demo['patients']['Alfa']).check_permission('read'))
        checks.append('governed membership revocation removes identity/API scope immediately; rolled back')
        frappe.db.rollback()
        frappe.set_user(fixture['users']['m']['name']);lifecycle.set_assignment(demo['patients']['Alfa'],center,fixture['practitioners'][0],0,'Synthetic final-review rollback assignment')
        frappe.set_user(fixture['users']['a']['name']);assert not workspace.patient_search(center,'Alfa')['patients'];denied(lambda:private.check_permission('read'))
        checks.append('governed patient assignment revocation removes private-note and search access immediately; rolled back')
        return {'status':'PASS','checks':checks,'matrix':matrix,'permission_delta':'NONE','dataset_mutations':'ROLLBACK_ONLY'}
    finally:
        frappe.db.rollback();frappe.set_user(previous)
