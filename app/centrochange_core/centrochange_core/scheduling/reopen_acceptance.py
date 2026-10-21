"""Governed lifecycle regression with an isolated, rollback-only synthetic fixture."""
from datetime import timedelta
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.scheduling.booking import reschedule, SNAPSHOTS, book
from centrochange_core.operations.lifecycle import reopen, close, start_utc
from centrochange_core.finance.guards import require_synthetic


@security.synthetic_test
def run():
    require_synthetic()
    user=frappe.session.user
    frappe.db.savepoint('cc_reopen_regression')
    try:
        frappe.set_user('Administrator')
        fixture=security.create_http(scheduling=True,commit=False,public_route=False)
        patient,center,prac=fixture['patients'][0],fixture['centers'][0],fixture['practitioners'][0]
        name=book(patient,prac,center,fixture['catalog']['Appointment Type'][0],
            '2099-03-09','09:00:00','reopen-fixture','Synthetic reopen regression')['name']
        doc=frappe.get_doc('Patient Appointment',name)
        historical={k:doc.get(k) for k in SNAPSHOTS}
        frappe.flags.cc_test_clock=start_utc(doc)+timedelta(hours=1)
        close(name,0,'Synthetic close before reopen regression')
        target='2099-03-16'
        try:
            reschedule(name,target,'10:00:00','Synthetic closed reschedule deny')
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Closed reschedule allowed')
        direct=frappe.get_doc('Patient Appointment',name);direct.appointment_time='10:00:00'
        try:
            direct.save(ignore_permissions=True)
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Generic appointment update allowed')
        assert not reopen(name,'Synthetic authorized reopen')['replay']
        assert not reschedule(name,target,'10:00:00','Synthetic governed move')['replay']
        assert reschedule(name,target,'10:00:00','Synthetic governed move replay')['replay']
        doc.reload();assert {k:doc.get(k) for k in SNAPSHOTS}==historical
        try:
            close(name,0,'Synthetic future close deny')
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Future close allowed')
        frappe.flags.cc_test_clock=start_utc(doc)+timedelta(hours=2)
        assert not close(name,0,'Synthetic reclose after session end')['replay']
        doc.reload();assert doc.cc_closure_state=='Closed'
        events=frappe.get_all('CC Audit Event',filters={'reference_name':name,'reason':['like','Synthetic %']},fields=['event_type','before_state','after_state'])
        moved=next(e for e in events if e.event_type=='APPOINTMENT_RESCHEDULED')
        assert frappe.parse_json(moved.before_state)['appointment_date']=='2099-03-09'
        assert frappe.parse_json(moved.after_state)['appointment_date']==target
        assert {'SESSION_REOPENED','SESSION_CLOSED'} <= {e.event_type for e in events}
        return {'status':'PASS','checks':['isolated booking and closure','closed reschedule denied','direct bypass denied','authorized reopen','governed future move','move replay idempotent','historical snapshots retained','future close denied','reclose after session end','audit before/after']}
    finally:
        frappe.flags.cc_test_clock=None
        frappe.db.rollback(save_point='cc_reopen_regression')
        frappe.set_user(user)
