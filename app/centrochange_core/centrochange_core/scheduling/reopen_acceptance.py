"""Governed reschedule regression, rolled back against synthetic UAT only."""
import frappe
from centrochange_core.scheduling.booking import reschedule, SNAPSHOTS
from centrochange_core.operations.lifecycle import reopen, close
from centrochange_core.finance.guards import require_synthetic


def run():
    require_synthetic()
    user=frappe.session.user
    frappe.db.savepoint('cc_reopen_regression')
    try:
        frappe.set_user('cc-http-uat0000001-m@example.invalid')
        name='HLC-APP-2026-00133'
        doc=frappe.get_doc('Patient Appointment',name)
        assert doc.status=='Closed' and doc.cc_closure_state=='Closed'
        historical={k:doc.get(k) for k in SNAPSHOTS}
        try:
            reschedule(name,'2026-09-30','16:00:00','SYNTHETIC regression closed deny')
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError('Closed reschedule allowed')
        direct=frappe.get_doc('Patient Appointment',name);direct.appointment_time='16:00:00'
        try:
            direct.save(ignore_permissions=True)
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError('Generic appointment update allowed')
        assert not reopen(name,'SYNTHETIC regression authorized reopen')['replay']
        assert not reschedule(name,'2026-09-30','16:00:00','SYNTHETIC regression governed move')['replay']
        assert reschedule(name,'2026-09-30','16:00:00','SYNTHETIC regression move replay')['replay']
        doc.reload();assert {k:doc.get(k) for k in SNAPSHOTS}==historical
        assert not close(name,0,'SYNTHETIC regression reclose')['replay']
        doc.reload();assert doc.cc_closure_state=='Closed'
        events=frappe.get_all('CC Audit Event',filters={'reference_name':name,'reason':['like','SYNTHETIC regression%']},fields=['event_type','before_state','after_state'])
        moved=next(e for e in events if e.event_type=='APPOINTMENT_RESCHEDULED')
        assert frappe.parse_json(moved.before_state)['appointment_date']=='2026-09-28'
        assert frappe.parse_json(moved.after_state)['appointment_date']=='2026-09-30'
        assert {'SESSION_REOPENED','SESSION_CLOSED'} <= {e.event_type for e in events}
        return {'status':'PASS','checks':['closed deny','direct bypass deny','authorized reopen','governed move','move replay','historical snapshots retained','reclose','audit before/after']}
    finally:
        frappe.db.rollback(save_point='cc_reopen_regression');frappe.set_user(user)
