"""Synthetic-only isolated acceptance, all mutations rolled back."""
import frappe
from centrochange_core.uat import demo
from centrochange_core.finance import operational_receipts as receipts, collections


def run():
    demo.guard()
    data = demo.read()
    manager = data['fixture']['users']['m']['name']
    patient = data['patients']['Alfa']
    center = data['fixture']['centers'][0]
    appointment = data['appointments']['Alfa non incassata 2']
    draft_appointment = data['appointments']['Alfa non incassata 1']
    method = frappe.get_all('Mode of Payment', filters={'enabled':1}, pluck='name', limit_page_length=1)[0]
    accounting = {dt:frappe.db.count(dt) for dt in ('Sales Invoice','Payment Entry','GL Entry')}
    frappe.db.savepoint('cc156_acceptance')
    try:
        frappe.set_user(manager)
        initial_history = len(receipts.history(patient,center))
        initial = collections.position(patient, center)
        assert initial['blocked'] is False
        debt = next(d for d in initial['debts'] if d['name'] == appointment)
        before = float(debt['amount'])
        partial = round(before / 2, 2)
        payload = {'patient':patient,'center':center,'receipt_date':frappe.utils.today(), 'mode_of_payment':method,
            'reason':'Synthetic isolated acceptance','request_key':'cc156-acceptance',
            'allocations':[{'appointment':appointment,'amount':partial}]}
        result = receipts.record(**payload)
        assert not result['replay'] and receipts.record(**payload)['replay']
        position = collections.position(patient, center)
        assert round(float(next(d['amount'] for d in position['debts'] if d['name']==appointment)),2) == round(before-partial,2)
        assert len(receipts.history(patient,center)) == initial_history+1
        try:
            receipts.record(**{**payload,'request_key':'cc156-draft','allocations':[{'appointment':draft_appointment,'amount':1}]})
            raise AssertionError('Draft invoice accepted')
        except frappe.ValidationError:
            pass
        try:
            receipts.record(**{**payload,'request_key':'cc156-over','allocations':[{'appointment':appointment,'amount':before}]})
            raise AssertionError('Overpayment accepted')
        except frappe.ValidationError:
            pass
        try:
            receipts.record(**{**payload,'allocations':[{'appointment':appointment,'amount':1}]})
            raise AssertionError('Changed idempotency payload accepted')
        except frappe.ValidationError:
            pass
        # Synthetic rollback-only fixture: remove the draft relationship from the
        # active set to exercise one receipt allocated to two separate sessions.
        frappe.db.set_value('Sales Invoice', data['invoices']['Alfa bozza'], 'docstatus', 2)
        multi = receipts.record(**{**payload,'request_key':'cc156-multi', 'allocations':[
            {'appointment':appointment,'amount':1}, {'appointment':draft_appointment,'amount':1}]})
        assert not multi['replay']
        assert len(receipts.history(patient,center)) == initial_history+2
        receipts.record(**{**payload,'request_key':'cc156-final', 'allocations':[
            {'appointment':appointment,'amount':round(before-partial-1,2)}]})
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_paid') == 1
        assert not any(d['name']==appointment for d in collections.position(patient,center)['debts'])
        from centrochange_core.security.audit import internal_write
        from centrochange_core.operations.automation import enqueue_notice
        from centrochange_core.operations import notifications
        with internal_write('cc_operation_write'):
            notice = frappe.get_doc({'doctype':'CC Payment Notice', 'patient':patient, 'center':center,
                'event_key':'cc156-test-notice', 'email_state':'Email Unavailable',
                'subject':'Synthetic review', 'message':'Open patient payments'}).insert(ignore_permissions=True)
        notification = enqueue_notice('cc156-test-notification', manager, 'Payment Block', notice.doctype, notice.name, 'Open patient payments')
        assert notification == enqueue_notice('cc156-test-notification', manager, 'Payment Block', notice.doctype, notice.name, 'Open patient payments')
        assert notifications.target(notification) == {'patient':patient,'center':center}
        assert frappe.db.count('CC Notification', {'event_key':'cc156-test-notification'}) == 1
        reminder = enqueue_notice('closure-reminder:2026-10-01:synthetic-practitioner', manager,
            'CLOSURE_REMINDER', 'Healthcare Practitioner', data['fixture']['practitioners'][0], 'Close day')
        assert notifications.target(reminder) == {'day_closure':'2026-10-01'}
        frappe.set_user(data['fixture']['users']['a']['name'])
        try:
            notifications.target(notification)
            raise AssertionError('Professional notification access accepted')
        except frappe.PermissionError:
            pass
        try:
            receipts.history(patient,center)
            raise AssertionError('Professional history access accepted')
        except frappe.PermissionError:
            pass
        from datetime import timedelta
        from centrochange_core.operations import lifecycle
        pending = data['appointments']['Alfa da prenotare']
        pending_doc = frappe.get_doc('Patient Appointment', pending)
        from unittest.mock import patch
        with patch('centrochange_core.operations.lifecycle.now_utc', return_value=lifecycle.start_utc(pending_doc)+timedelta(hours=2)):
            lifecycle.close(pending, 1, 'Synthetic professional paid closure', method)
        frappe.set_user(manager)
        assert receipts.allocated(patient,center)[pending] == int(float(pending_doc.cc_price_snapshot)*100)
        assert frappe.db.get_value('Patient Appointment',pending,'cc_paid') == 1
        assert {dt:frappe.db.count(dt) for dt in accounting} == accounting
        return {'partial_multi_complete_and_replay':'PASS','draft_invoice_and_overpayment_denied':'PASS','professional_denied':'PASS','no_accounting_documents':'PASS','notification_target_and_dedup':'PASS','professional_paid_closure_uses_receipt':'PASS'}
    finally:
        frappe.flags.cc_test_clock = None
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc156_acceptance')


def _concurrent_worker(site, user, payload, barrier, queue):
    import frappe as child
    from centrochange_core.finance import operational_receipts as child_receipts
    child.init(site=site)
    child.connect()
    child.set_user(user)
    try:
        barrier.wait(timeout=20)
        result = child_receipts.record(**payload)
        child.db.commit()
        queue.put('replay' if result['replay'] else 'accepted')
    except Exception:
        child.db.rollback()
        queue.put('rejected')
    finally:
        child.destroy()


def concurrent(label='Alfa non incassata 2'):
    """Run once in a disposable, freshly seeded site; worker commits are test-owned."""
    import multiprocessing
    demo.guard()
    data = demo.read()
    appointment = data['appointments'][label]
    patient = frappe.db.get_value('Patient Appointment', appointment, 'patient')
    center = data['fixture']['centers'][0]
    before = frappe.db.get_value('Patient Appointment', appointment, 'cc_price_snapshot')
    assert float(before) == 100
    method = frappe.get_all('Mode of Payment', filters={'enabled':1}, pluck='name', limit_page_length=1)[0]
    ctx = multiprocessing.get_context('spawn')
    barrier = ctx.Barrier(2)
    queue = ctx.Queue()
    processes = []
    for i in range(2):
        payload = {'patient':patient,'center':center,'receipt_date':frappe.utils.today(), 'mode_of_payment':method,
            'reason':'Synthetic concurrent acceptance','request_key':f'cc156-{label}-concurrent-{i}',
            'allocations':[{'appointment':appointment,'amount':60}]}
        p = ctx.Process(target=_concurrent_worker, args=(frappe.local.site, data['fixture']['users']['m']['name'], payload, barrier, queue))
        p.start(); processes.append(p)
    for p in processes:
        p.join(timeout=60)
        assert p.exitcode == 0, 'Concurrent worker failed'
    outcomes = sorted(queue.get(timeout=5) for _ in processes)
    assert outcomes == ['accepted','rejected'], outcomes
    barrier = ctx.Barrier(2)
    queue = ctx.Queue()
    payload = {'patient':patient,'center':center,'receipt_date':frappe.utils.today(), 'mode_of_payment':method,
        'reason':'Synthetic concurrent replay','request_key':f'cc156-{label}-concurrent-replay',
        'allocations':[{'appointment':appointment,'amount':20}]}
    processes = [ctx.Process(target=_concurrent_worker, args=(frappe.local.site, data['fixture']['users']['m']['name'], payload, barrier, queue)) for _ in range(2)]
    for p in processes: p.start()
    for p in processes:
        p.join(timeout=60)
        assert p.exitcode == 0, 'Replay worker failed'
    replay_outcomes = sorted(queue.get(timeout=5) for _ in processes)
    assert replay_outcomes == ['accepted','replay'], replay_outcomes
    return {'competing_60_eur_allocations':'PASS','concurrent_same_key_replay':'PASS'}
