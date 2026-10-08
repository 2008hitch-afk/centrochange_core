"""Synthetic reports, internal delivery and public projection acceptance."""
from datetime import datetime,timedelta
from types import SimpleNamespace
import frappe
from centrochange_core.operations import dev_acceptance,notifications,reporting,workspace
from centrochange_core.security import dev_acceptance as security
from centrochange_core.security.lifecycle import set_assignment
from centrochange_core.operations.automation import enqueue_notice
from centrochange_core.scheduling.booking import validate_slot


def checks(fixture):
    result=dev_acceptance.checks(fixture)
    patient,center,prac1,pro1,pro2,secretary=(fixture[key] for key in ('patient','center','prac1','pro1','pro2','secretary'))
    frappe.set_user('Administrator')
    set_assignment(patient,center,prac1,1,'Synthetic surface fixture')
    name=enqueue_notice('synthetic-internal-reminder',pro1,'CLOSURE_REMINDER','Healthcare Practitioner',prac1,'Synthetic pending closure')
    assert notifications.deliver(name)['state']=='Sent'
    assert notifications.deliver(name)['replay']
    assert frappe.db.count('Notification Log',{'cc_notification':name})==1
    result.append('internal native Notification Log delivery and replay exactly once')
    fail=enqueue_notice('synthetic-disabled-recipient','Guest','CLOSURE_REMINDER','Healthcare Practitioner',prac1,'Synthetic unavailable recipient')
    # Guest is an enabled native user but never an eligible delivery recipient.
    frappe.db.set_value('User','Guest','enabled',0)
    assert notifications.deliver(fail)['state']=='Failed'
    frappe.set_user(pro1)
    try:
        notifications.retry(fail,'Unauthorized retry')
    except frappe.PermissionError:
        result.append('professional administrative retry denied')
    else:
        raise AssertionError('Unauthorized retry accepted')
    frappe.set_user('Administrator')
    assert notifications.retry(fail,'Synthetic authorized retry')['replay'] is False
    assert frappe.db.get_value('CC Notification',fail,'attempts')==1
    assert frappe.db.get_value('CC Notification',fail,'retry_limit')==6
    result.append('failed delivery visible and authorized retry retains attempt history')
    frappe.set_user(pro1)
    assert name in frappe.get_list('CC Notification',pluck='name')
    own=reporting.summary(center,'2099-01-01','2099-03-01')
    appointments=workspace.agenda(center,'2099-01-01','2099-03-01')['appointments']
    assert sum(row['sessions'] for row in own['currencies'].values())==len(appointments)
    result.append('scoped operational report totals reconcile with agenda')
    doc=next(row for row in appointments if row.patient==patient)
    markup=reporting.print_session(doc.name)
    assert 'SYNTHETIC PRIVATE' not in markup and 'SYNTHETIC ORGANIZATIONAL' not in markup
    result.append('allowlisted printable session excludes private and organizational bodies')
    try:
        reporting.dashboard(center,'2099-01-01','2099-03-01')
    except frappe.PermissionError:
        result.append('professional management dashboard denied')
    else:
        raise AssertionError('Management aggregate accepted for professional')
    frappe.set_user('Administrator')
    aggregate=reporting.dashboard(center,'2099-01-01','2099-03-01')
    assert 'PRIVATE' not in str(aggregate) and 'patient' not in str(aggregate)
    result.append('management aggregate contains no clinical or patient identity fields')
    frappe.set_user(pro2)
    assert name not in frappe.get_list('CC Notification',pluck='name')
    try:
        reporting.print_session(doc.name)
    except frappe.PermissionError:
        result.append('cross professional printable session denied')
    else:
        raise AssertionError('Cross professional print accepted')
    for date,time in [('2099-03-29','02:30:00'),('2099-10-25','02:30:00')]:
        # Explicit 2026 transition dates are sufficient to prove temporal validation.
        date='2026-03-29' if '03-' in date else '2026-10-25'
        try:
            validate_slot(SimpleNamespace(appointment_date=date,appointment_time=time,duration=60,practitioner=prac1,cc_center=center,patient=patient,name=None))
        except frappe.ValidationError as error:
            assert 'Ambiguous or nonexistent' in str(error)
        else:
            raise AssertionError('DST fold/gap booking accepted')
    result.append('DST gap and fold booking rejected before canonical insert')
    from centrochange_core.security.diagnostics import redact,ConfidentialLogFilter
    import logging
    previous=frappe.flags.get('cc_confidential_request')
    try:
        frappe.flags.cc_confidential_request=True
        error=frappe.get_doc({'doctype':'Error Log','method':'Sensitive failure','error':'SYNTHETIC PRIVATE BODY',
            'metadata':'SYNTHETIC PRIVATE REQUEST','fingerprint':'synthetic'})
        error.insert(ignore_permissions=True)
        assert 'SYNTHETIC PRIVATE' not in frappe.db.get_value('Error Log',error.name,'error')
        assert 'SYNTHETIC PRIVATE' not in str(error.as_dict())
        record=logging.LogRecord('frappe',logging.ERROR,'',0,'SYNTHETIC PRIVATE REQUEST',(),None)
        ConfidentialLogFilter().filter(record)
        assert 'SYNTHETIC PRIVATE' not in record.getMessage()
        result.append('confidential Error Log and native logging records redact body and request context')
    finally:
        frappe.flags.cc_confidential_request=previous
    from centrochange_core.scheduling.availability import create_absence,cancel_absence
    from centrochange_core.scheduling.booking import book
    frappe.set_user(pro1)
    absence=create_absence(prac1,center,'2099-03-02','2099-03-02','09:00:00','12:00:00','Synthetic blocking absence')['name']
    try:
        book(patient,prac1,center,'CC SYNTHETIC SESSION','2099-03-02','09:00:00','synthetic-absence-book','Synthetic unavailable booking')
    except frappe.ValidationError:
        result.append('submitted native absence blocks canonical booking')
    else:
        raise AssertionError('Booking during submitted absence accepted')
    cancel_absence(absence,'Synthetic blocking absence cancellation')
    assert book(patient,prac1,center,'CC SYNTHETIC SESSION','2099-03-02','09:00:00','synthetic-absence-book','Synthetic restored availability')['name']
    result.append('native absence correction restores guarded booking availability')
    assert reporting.safe_cell('=SUM(1)')=="'=SUM(1)" and reporting.safe_cell('@formula')=="'@formula"
    result.append('CSV spreadsheet-formula cells neutralized')
    frappe.set_user('Administrator')
    set_assignment(patient,center,prac1,0,'Synthetic surface fixture release')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:
        return security.run(extra_checks=checks)
    finally:
        frappe.flags.cc_test_clock=previous
