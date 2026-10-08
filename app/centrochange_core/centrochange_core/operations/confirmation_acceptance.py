"""Synthetic confirmation/replay/failure/retry end-to-end; rollback preserves Owner data."""
from unittest.mock import patch
import frappe
from centrochange_core.scheduling.public_booking import first_meeting, available_slots
from centrochange_core.operations import booking_confirmation as confirmation
from centrochange_core.finance.guards import require_synthetic


def run():
    require_synthetic();user=frappe.session.user
    frappe.db.savepoint('cc_confirmation_acceptance')
    try:
        frappe.set_user('Guest')
        queues=frappe.db.count('Email Queue')
        slots=available_slots('Marco',frappe.utils.add_days(frappe.utils.nowdate(),7))['slots']
        assert len(slots)>1
        suffix=frappe.generate_hash(length=12)
        payload={'route':'Marco','first_name':'SYNTHETIC Conferma','last_name':'Test','email':suffix+'@example.invalid','sex':'Other','appointment_date':slots[0]['date'],'appointment_time':slots[0]['time'],'request_key':'confirmation-'+suffix}
        result=first_meeting(**payload);assert result['confirmation']['state']=='Simulated Sent'
        assert first_meeting(**payload)['replay']
        outbox=frappe.get_doc('CC Booking Confirmation',{'appointment':result['name']})
        assert outbox.attempts==1 and outbox.communication
        assert frappe.db.count('Communication',{'reference_doctype':'Patient Appointment','reference_name':result['name'],'communication_medium':'Email'})==1
        assert 'Marco' in outbox.message and 'minuti' in outbox.message and 'HLC-PRAC' not in outbox.message and 'CC-HTTP-' not in outbox.message
        remaining=available_slots('Marco',frappe.utils.add_days(frappe.utils.nowdate(),7))['slots'][0]
        failed={**payload,'email':'failed-'+suffix+'@example.invalid','request_key':'failed-'+suffix,'appointment_date':remaining['date'],'appointment_time':remaining['time']}
        with patch('centrochange_core.operations.booking_confirmation._simulate',side_effect=RuntimeError('synthetic failure')):
            second=first_meeting(**failed)
        assert frappe.db.exists('Patient Appointment',second['name']) and second['confirmation']['state']=='Failed'
        out=frappe.get_doc('CC Booking Confirmation',{'appointment':second['name']});assert not out.communication
        frappe.set_user('cc-http-uat0000001-m@example.invalid')
        assert any(r.name==out.name and r.state=='Failed' for r in confirmation.records(out.center))
        assert confirmation.retry(out.name,'SYNTHETIC confirmation retry')['state']=='Simulated Sent'
        assert confirmation.retry(out.name,'SYNTHETIC retry replay')['replay']
        out.reload();assert out.attempts==2 and out.communication
        assert frappe.db.count('Email Queue')==queues
        for role in ['a','b','c','s','f','t']:
            frappe.set_user('cc-http-uat0000001-'+role+'@example.invalid')
            try:confirmation.records(out.center)
            except frappe.PermissionError:pass
            else:raise AssertionError('Confirmation administration leak')
        return {'status':'PASS','checks':['public booking immediate native Communication','same booking replay once','recognizable content/no internal practitioner identifier','simulated failure preserves booking','management sees failure/retry','retry replay once','no Email Queue or real transport','unauthorized administration denied']}
    finally:
        frappe.db.rollback(save_point='cc_confirmation_acceptance');frappe.set_user(user)
