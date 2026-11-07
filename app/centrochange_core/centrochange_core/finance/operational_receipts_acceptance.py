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
        from centrochange_core.operations import notifications as notification_ops
        alerts = notification_ops.pending_outcomes(center)
        assert isinstance(alerts, list)
        assert all(set(row) == {'date', 'practitioner', 'practitioner_name', 'count'} for row in alerts)
        assert len({(row['date'], row['practitioner']) for row in alerts}) == len(alerts)
        for limited_role in ('a', 'f', 't'):
            frappe.set_user(data['fixture']['users'][limited_role]['name'])
            try:
                notification_ops.pending_outcomes(center)
                raise AssertionError('Limited account can inspect manager outcome alerts')
            except frappe.PermissionError:
                pass
        frappe.set_user('Guest')
        try:
            notification_ops.pending_outcomes(center)
            raise AssertionError('Guest can inspect manager outcome alerts')
        except frappe.PermissionError:
            pass
        frappe.set_user(manager)
        # Restored UAT fixtures may have advanced since the fresh CI seed.
        # Re-close a reopened session via the normal lifecycle; never patch its
        # state directly or bypass the approved daily closure rule.
        from datetime import timedelta
        from centrochange_core.operations import lifecycle
        draft_doc = frappe.get_doc('Patient Appointment', draft_appointment)
        if draft_doc.cc_closure_state == 'Reopened':
            lifecycle.close(draft_appointment, 0, 'Synthetic acceptance: close reopened fixture')
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
        recorded = next(row for row in receipts.history(patient, center) if row['name'] == result['name'])
        allocation = recorded['allocations'][0]
        assert allocation['session']['name'] == appointment
        assert allocation['session']['patient'] == patient and allocation['session']['cc_center'] == center
        assert allocation['session']['appointment_date'] and allocation['session']['cc_service_label']
        for role in ('f', 't'):
            frappe.set_user(data['fixture']['users'][role]['name'])
            limited = next(row for row in receipts.history(patient, center) if row['name'] == result['name'])
            assert all('session' not in item and 'service_label' not in item for item in limited['allocations'])
        frappe.set_user(manager)
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
        correction = receipts.reverse(patient, center, multi['name'], 'Synthetic correction', 'cc156-correction')
        assert not correction['replay']
        assert receipts.reverse(patient, center, multi['name'], 'Synthetic correction', 'cc156-correction')['replay']
        try:
            receipts.reverse(patient, center, multi['name'], 'Duplicate correction', 'cc156-duplicate-correction')
            raise AssertionError('Duplicate correction accepted')
        except frappe.ValidationError:
            pass
        assert round(float(next(d['amount'] for d in collections.position(patient,center)['debts'] if d['name']==appointment)),2) == round(before-partial,2)
        assert receipts.history(patient,center)[-1]['allocations']
        receipts.record(**{**payload,'request_key':'cc156-multi-replacement', 'allocations':[
            {'appointment':appointment,'amount':1}, {'appointment':draft_appointment,'amount':1}]})
        final = receipts.record(**{**payload,'request_key':'cc156-final', 'allocations':[
            {'appointment':appointment,'amount':round(before-partial-1,2)}]})
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_paid') == 1
        assert not any(d['name']==appointment for d in collections.position(patient,center)['debts'])
        receipts.reverse(patient, center, final['name'], 'Synthetic full-paid correction', 'cc156-final-correction')
        assert frappe.db.get_value('Patient Appointment',appointment,'cc_paid') == 0
        assert round(float(next(d['amount'] for d in collections.position(patient,center)['debts'] if d['name']==appointment)),2) == round(before-partial-1,2)
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
        try:
            receipts.reverse(patient,center,result['name'],'Unauthorized correction','cc156-denied')
            raise AssertionError('Professional correction accepted')
        except frappe.PermissionError:
            pass
        pending = data['appointments']['Alfa da prenotare']
        frappe.set_user(manager)
        recovered = frappe.db.get_value('Patient Appointment', pending, 'cc_closure_state') == 'Auto Locked'
        if recovered:
            lifecycle.reopen(pending, 'Synthetic acceptance: authorised late recovery')
        frappe.set_user(data['fixture']['users']['a']['name'])
        pending_doc = frappe.get_doc('Patient Appointment', pending)
        frappe.db.savepoint('cc156_unpaid_closure')
        if recovered:
            lifecycle.close(pending, 0, 'Synthetic unpaid closure')
        else:
            from unittest.mock import patch
            with patch('centrochange_core.operations.lifecycle.now_utc', return_value=lifecycle.start_utc(pending_doc)+timedelta(hours=2)):
                lifecycle.close(pending, 0, 'Synthetic unpaid closure')
        frappe.set_user(manager)
        unpaid = next(d for d in collections.position(patient,center)['debts'] if d['name']==pending)
        assert float(unpaid['amount']) == float(pending_doc.cc_price_snapshot)
        receipts.record(patient, center, frappe.utils.today(), method, 'Synthetic later partial receipt',
                        'cc156-after-unpaid', [{'appointment':pending,'amount':1}])
        assert float(next(d for d in collections.position(patient,center)['debts'] if d['name']==pending)['amount']) == float(pending_doc.cc_price_snapshot)-1
        assert collections.position(patient,center)['blocked'] is False
        from datetime import datetime
        from types import SimpleNamespace
        from zoneinfo import ZoneInfo
        from centrochange_core.scheduling.booking import book, validate_slot
        found = None
        today = datetime.now(ZoneInfo('Europe/Rome')).date()
        for offset in range(1, 22):
            for hour in range(8, 19):
                for minute in (0, 30):
                    candidate = SimpleNamespace(patient=patient, practitioner=pending_doc.practitioner,
                        cc_center=center, appointment_date=today+timedelta(days=offset),
                        appointment_time=f'{hour:02d}:{minute:02d}:00', duration=pending_doc.duration, name=None)
                    try:
                        validate_slot(candidate)
                        found = candidate
                        break
                    except frappe.ValidationError:
                        continue
                if found: break
            if found: break
        assert found, 'No synthetic future slot available for booking with an outstanding balance'
        booked = book(patient, pending_doc.practitioner, center, pending_doc.appointment_type,
                      found.appointment_date, found.appointment_time, 'cc156-outstanding-booking',
                      'Synthetic booking with outstanding balance')
        assert frappe.db.exists('Patient Appointment', booked['name'])
        frappe.db.rollback(save_point='cc156_unpaid_closure')
        frappe.set_user(data['fixture']['users']['a']['name'])
        if recovered:
            lifecycle.close(pending, 1, 'Synthetic professional paid closure', method)
        else:
            # Fresh CI seed simulates the original same-day closure window.
            from unittest.mock import patch
            with patch('centrochange_core.operations.lifecycle.now_utc', return_value=lifecycle.start_utc(pending_doc)+timedelta(hours=2)):
                lifecycle.close(pending, 1, 'Synthetic professional paid closure', method)
        frappe.set_user(manager)
        assert receipts.allocated(patient,center)[pending] == int(float(pending_doc.cc_price_snapshot)*100)
        assert frappe.db.get_value('Patient Appointment',pending,'cc_paid') == 1
        assert {dt:frappe.db.count(dt) for dt in accounting} == accounting
        return {'partial_multi_complete_and_replay':'PASS','receipt_corrections_and_residuals':'PASS',
            'unpaid_closure_later_partial_and_booking':'PASS','draft_invoice_and_overpayment_denied':'PASS',
            'professional_denied':'PASS','no_accounting_documents':'PASS','notification_target_and_dedup':'PASS',
            'professional_paid_closure_uses_receipt':'PASS'}
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


def _concurrent_reverse_worker(site, user, payload, barrier, queue):
    import frappe as child
    from centrochange_core.finance import operational_receipts as child_receipts
    child.init(site=site); child.connect(); child.set_user(user)
    try:
        barrier.wait(timeout=20)
        result = child_receipts.reverse(**payload)
        child.db.commit()
        queue.put('replay' if result['replay'] else 'accepted')
    except Exception:
        child.db.rollback(); queue.put('rejected')
    finally:
        child.destroy()


def concurrent_reversal(label='Alfa non incassata 2'):
    """The preceding concurrent test leaves one replay-protected receipt to correct."""
    import multiprocessing
    from hashlib import sha256
    demo.guard()
    data = demo.read(); user = data['fixture']['users']['m']['name']
    key = f'cc156-{label}-concurrent-replay'
    receipt = sha256((user + '\0' + key).encode()).hexdigest()
    appointment = data['appointments'][label]
    patient = frappe.db.get_value('Patient Appointment', appointment, 'patient')
    center = data['fixture']['centers'][0]
    assert frappe.db.exists('CC Operational Receipt', receipt)
    ctx = multiprocessing.get_context('spawn'); barrier = ctx.Barrier(2); queue = ctx.Queue()
    processes = [ctx.Process(target=_concurrent_reverse_worker, args=(frappe.local.site, user,
        {'patient':patient,'center':center,'receipt':receipt,'reason':'Synthetic concurrent correction',
         'request_key':f'cc156-concurrent-correction-{i}'}, barrier, queue)) for i in range(2)]
    for process in processes: process.start()
    for process in processes:
        process.join(timeout=60)
        assert process.exitcode == 0, 'Concurrent correction worker failed'
    assert sorted(queue.get(timeout=5) for _ in processes) == ['accepted','rejected']
    return {'concurrent_correction_exactly_once':'PASS'}


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
