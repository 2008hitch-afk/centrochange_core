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


def closure_regressions():
    """Exercise legacy and non-monetary closure semantics on disposable records."""
    from datetime import timedelta
    from unittest.mock import patch
    from centrochange_core.operations import lifecycle
    demo.guard()
    data = demo.read()
    appointment = data['appointments']['Alfa da prenotare']
    method = frappe.get_all('Mode of Payment', filters={'enabled':1}, pluck='name', limit_page_length=1)[0]
    manager = data['fixture']['users']['m']['name']
    counts = {dt:frappe.db.count(dt) for dt in ('CC Operational Receipt','Sales Invoice','Payment Entry','GL Entry')}
    frappe.db.savepoint('cc156_closure_regressions')
    try:
        frappe.set_user(manager)
        # A non-synthetic environment must not gain the new ledger write via closure.
        before = frappe.db.get_value('Patient Appointment', appointment, ['status','cc_closure_state','cc_paid','cc_revision'], as_dict=True)
        doc = frappe.get_doc('Patient Appointment', appointment)
        clock = lifecycle.start_utc(doc) + timedelta(hours=2)
        with patch('centrochange_core.operations.lifecycle.now_utc', return_value=clock), patch.dict(frappe.conf, {'cc_synthetic_dev':0}):
            try:
                lifecycle.close(appointment,1,'Synthetic environment guard test',method)
                raise AssertionError('Non-synthetic receipt accepted')
            except frappe.PermissionError:
                pass
        assert frappe.db.get_value('Patient Appointment', appointment, ['status','cc_closure_state','cc_paid','cc_revision'], as_dict=True) == before
        assert {dt:frappe.db.count(dt) for dt in counts} == counts
        # Run complete paid closures for a waived session and a reserved package,
        # then roll back each isolated scenario before testing the next one.
        frappe.db.savepoint('cc156_waived')
        frappe.db.set_value('Patient Appointment',appointment,'cc_economic_state','Waived')
        with patch('centrochange_core.operations.lifecycle.now_utc', return_value=clock):
            lifecycle.close(appointment,1,'Synthetic waived closure',method)
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_economic_state') == 'Waived'
        assert frappe.db.count('CC Operational Receipt') == counts['CC Operational Receipt']
        frappe.db.rollback(save_point='cc156_waived')
        frappe.db.savepoint('cc156_package')
        from centrochange_core.operations import packages
        package = packages.issue(data['fixture']['catalog']['CC Package Template'][0],
            data['patients']['Alfa'], [data['fixture']['centers'][0]], 'cc156-package-test', 'Synthetic package test')['name']
        frappe.db.set_value('Patient Appointment',appointment,'cc_package',package)
        package_doc = frappe.get_doc('Patient Appointment',appointment,for_update=True)
        packages.reserve(package_doc,'Synthetic package reservation')
        with patch('centrochange_core.operations.lifecycle.now_utc', return_value=clock):
            lifecycle.close(appointment,1,'Synthetic package closure',method)
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_economic_state') == 'Package Covered'
        assert frappe.db.count('CC Operational Receipt') == counts['CC Operational Receipt']
        frappe.db.rollback(save_point='cc156_package')
        # A free first meeting still closes with the legacy marker and no invented receipt.
        frappe.db.set_value('Patient Appointment',appointment,'cc_price_snapshot',0)
        with patch('centrochange_core.operations.lifecycle.now_utc', return_value=clock):
            lifecycle.close(appointment,1,'Synthetic free meeting closure',method)
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_closure_state') == 'Closed'
        assert frappe.db.count('CC Operational Receipt') == counts['CC Operational Receipt']
        # Existing binary event replay and correction remain available without receipt.
        legacy = frappe.get_doc('Patient Appointment',appointment,for_update=True)
        old = lifecycle.current_settlements(appointment)[0].name
        assert lifecycle._settlement(legacy,1,method,'Synthetic replay') == old
        lifecycle.record_settlement(appointment,0,'Synthetic legacy correction')
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_paid') == 0
        assert frappe.db.count('CC Operational Receipt') == counts['CC Operational Receipt']
        # Existing covered and waived records retain their historical binary semantics.
        for label in ('Epsilon pacchetto','Delta annullata puntuale'):
            doc = frappe.get_doc('Patient Appointment',data['appointments'][label],for_update=True)
            assert doc.cc_economic_state in ('Package Covered','Waived','Non Due')
            lifecycle._settlement(doc,1,method,'Synthetic non monetary state')
            assert frappe.db.count('CC Operational Receipt') == counts['CC Operational Receipt']
        assert {dt:frappe.db.count(dt) for dt in counts} == counts
        return {'non_synthetic_denied_atomic':'PASS','free_closure':'PASS',
            'legacy_replay_and_correction':'PASS','package_and_waiver_closure_and_binary':'PASS','no_accounting_documents':'PASS'}
    finally:
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='cc156_closure_regressions')
