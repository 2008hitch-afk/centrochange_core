"""Single DEV synthetic POS proof; run by the host harness through Docker exec.

The script creates a fresh fixture in the existing operational center. Native
vouchers and their ledger history are retained after cancellation. It never
deletes a posted voucher or changes Accounts Settings.
"""
import json
import os
import sys
from datetime import timedelta

import frappe


PREFIX = 'CC-MVP-POS-'
tag = os.environ['CC_POS_TEST_TAG']
stage = sys.argv[1]
assert tag.startswith(PREFIX) and len(tag) == len(PREFIX) + 12
assert stage in ('preflight', 'prepare', 'finalize', 'inspect')
frappe.init(site='centrochange.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
frappe.set_user('Administrator')


def context():
    assert frappe.conf.get('cc_synthetic_dev') == 1
    assert frappe.conf.get('cc_uat_demo') == 1
    branches = frappe.get_all('Branch', fields=['name', 'cc_operational', 'cc_company', 'cc_cost_center'], order_by='name')
    assert len(branches) == 2 and [int(row.cc_operational) for row in branches] == [1, 0]
    center = branches[0]
    assert center.cc_company and center.cc_cost_center
    assert frappe.db.get_value('Company', center.cc_company, 'default_currency') == 'EUR'
    assert not frappe.db.get_single_value('Accounts Settings', 'delete_linked_ledger_entries')
    account = frappe.get_all('Account', filters={'company': center.cc_company, 'account_type': 'Bank',
        'account_currency': 'EUR', 'is_group': 0, 'disabled': 0}, pluck='name')
    assert len(account) == 1
    return center, account[0]


def owned(invoice_name):
    invoice = frappe.get_doc('Sales Invoice', invoice_name, for_update=True)
    assert invoice.cc_center == context()[0].name and invoice.cc_fiscal_profile == 'SYNTHETIC_UNVERIFIED'
    assert invoice.cc_request_key
    assert len(invoice.items) == 1 and invoice.items[0].cc_economic_source
    source = frappe.get_doc('CC Economic Source Link', invoice.items[0].cc_economic_source)
    appointment = frappe.get_doc('Patient Appointment', source.appointment)
    assert frappe.db.get_value('Patient', appointment.patient, 'uid') == tag
    assert appointment.cc_center == invoice.cc_center and source.center == invoice.cc_center
    return invoice, source, appointment


def ledger(voucher_type, name):
    rows = frappe.get_all('GL Entry', filters={'voucher_type': voucher_type, 'voucher_no': name},
        fields=['account', 'debit', 'credit', 'is_cancelled'], limit_page_length=0)
    by_account = {}
    for row in rows:
        by_account[row.account] = by_account.get(row.account, 0) + float(row.debit) - float(row.credit)
    return rows, all(abs(value) < 0.011 for value in by_account.values())


try:
    center, bank_account = context()
    if stage in ('preflight', 'prepare'):
        from centrochange_core.finance import bridge, receivables
        from centrochange_core.security.lifecycle import set_assignment
        from centrochange_core.scheduling.booking import book
        from centrochange_core.operations import lifecycle

        # A native voucher hook refreshes this queue on submit. Reject an
        # orphaned dynamic link before creating any synthetic documents.
        exceptions = frappe.get_all('CC Admin Exception',
            filters={'center': center.name, 'state': ['!=', 'Closed']},
            fields=['reference_doctype', 'reference_name'], limit_page_length=0)
        assert all(frappe.db.exists(row.reference_doctype, row.reference_name)
            for row in exceptions), 'open administrative exception has a missing source'
        assert not frappe.db.exists('Patient', {'uid': tag})
        assert not frappe.db.exists('Mode of Payment', tag + ' Carta POS')
        schedules = frappe.get_all('Practitioner Schedule', filters={'cc_center': center.name, 'disabled': 0},
            fields=['name', 'cc_practitioner'])
        candidates = []
        for schedule in schedules:
            slots = frappe.get_all('Healthcare Schedule Time Slot', filters={'parent': schedule.name,
                'day': 'Monday'}, fields=['from_time', 'to_time'])
            target_time = frappe.utils.get_time('15:00:00')
            if any(frappe.utils.get_time(slot.from_time) <= target_time
                    and target_time < frappe.utils.get_time(slot.to_time) for slot in slots):
                candidates.append(schedule.cc_practitioner)
        assert candidates
        practitioner = candidates[0]
        service = frappe.get_all('CC Center Service', filters={'center': center.name, 'enabled': 1},
            pluck='appointment_type')
        assert len(service) == 1
        profile = frappe.get_doc('Appointment Type', service[0])
        assert profile.cc_service_item and float(profile.default_duration) > 0
        assert frappe.db.get_value('Branch', center.name, 'cc_price_list')
        finance_settings = frappe.get_doc('CC Finance Settings')
        assert finance_settings.sales_tax_template and finance_settings.receipt_mode
        assert frappe.db.get_value('Mode of Payment', finance_settings.receipt_mode, 'mode_of_payment_code')
        assert frappe.db.exists('Dynamic Link', {'parenttype': 'Address',
            'link_doctype': 'Company', 'link_name': center.cc_company})
        assert frappe.db.count('Sales Taxes and Charges', {'parent': finance_settings.sales_tax_template})
        assert not frappe.db.exists('Patient Appointment', {
            'appointment_date': '2099-01-12', 'appointment_time': '15:00:00',
            'practitioner': practitioner, 'cc_center': center.name,
        })
        groups = frappe.get_all('Customer Group', filters={'is_group': 0}, pluck='name')
        territories = frappe.get_all('Territory', filters={'is_group': 0}, pluck='name')
        assert groups and territories
        if stage == 'preflight':
            print('CC_POS_STAGE=' + json.dumps({'stage': 'preflight', 'status': 'PASS',
                'center': center.name, 'practitioner': practitioner,
                'bank_account_type': frappe.db.get_value('Account', bank_account, 'account_type'),
                'ledger_retained': True}))
            frappe.db.rollback()
            sys.exit(0)

        patient = frappe.get_doc({'doctype': 'Patient', 'first_name': tag, 'sex': 'Female', 'uid': tag}).insert()
        set_assignment(patient.name, center.name, practitioner, 1, tag + ' synthetic POS assignment')
        customer = frappe.get_doc({'doctype': 'Customer', 'customer_name': tag,
            'customer_type': 'Individual', 'customer_group': sorted(groups)[0],
            'territory': sorted(territories)[0],
            'fiscal_code': 'SYNTHETICDEV00000'}).insert(ignore_permissions=True)
        frappe.get_doc({'doctype': 'Address', 'address_title': tag + ' synthetic billing',
            'address_type': 'Billing', 'address_line1': 'Via SYNTHETIC DEV 0',
            'city': 'Roma', 'state': 'Roma', 'pincode': '00100', 'country': 'Italy',
            'country_code': 'IT', 'is_primary_address': 1,
            'links': [{'link_doctype': 'Customer', 'link_name': customer.name}],
        }).insert(ignore_permissions=True)
        bridge.map_patient(patient.name, center.name, tag + ' synthetic POS customer', customer.name)
        appointment = book(patient.name, practitioner, center.name, service[0], '2099-01-12',
            '15:00:00', tag + '-booking', tag + ' synthetic POS booking')['name']
        assert not frappe.db.sql('''select i.name from `tabSales Invoice Item` i
            join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus<2 and p.is_return=0 limit 1 for update''', (appointment,))
        previous = frappe.flags.get('cc_test_clock')
        was_test = frappe.in_test
        try:
            frappe.in_test = True
            frappe.flags.cc_test_clock = lifecycle.start_utc(frappe.get_doc('Patient Appointment', appointment)) + timedelta(hours=2)
            lifecycle.close(appointment, 0, tag + ' synthetic POS performed')
        finally:
            frappe.flags.cc_test_clock = previous
            frappe.in_test = was_test
        source = bridge.capture(appointment, tag + ' synthetic POS source')['name']
        assert frappe.db.get_value('CC Economic Source Link', source, 'economic_state') == 'Due'
        mode = tag + ' Carta POS'
        frappe.get_doc({'doctype': 'Mode of Payment', 'mode_of_payment': mode, 'type': 'Bank',
            'enabled': 1, 'mode_of_payment_code': 'MP08-Carta di pagamento',
            'accounts': [{'company': center.cc_company, 'default_account': bank_account}]}).insert(ignore_permissions=True)
        today = frappe.utils.today()
        due = frappe.utils.add_days(today, 14)
        invoice = receivables.draft([source], today, due, tag + '-invoice', tag + ' synthetic POS invoice')['name']
        submitted = receivables.submit(invoice, tag + ' synthetic POS submit')
        assert submitted['docstatus'] == 1 and submitted['outstanding'] > 5
        assert frappe.db.count('GL Entry', {'voucher_type': 'Sales Invoice', 'voucher_no': invoice}) > 0
        frappe.db.commit()
        print('CC_POS_STAGE=' + json.dumps({'stage': 'prepared', 'invoice': invoice, 'total': submitted['total'],
            'outstanding': submitted['outstanding'], 'mode': mode, 'center': center.name}))

    elif stage == 'finalize':
        from centrochange_core.security.audit import internal_write
        from centrochange_core.finance import receivables
        invoice_name = os.environ['CC_POS_INVOICE']
        payment_name = os.environ.get('CC_POS_PAYMENT') or ''
        invoice, source, appointment = owned(invoice_name)
        assert invoice.docstatus == 1
        payment_checked = False
        if payment_name:
            payment = frappe.get_doc('Payment Entry', payment_name, for_update=True)
            assert payment.docstatus == 1 and payment.cc_center == center.name
            assert payment.mode_of_payment == tag + ' Carta POS'
            assert len(payment.references) == 1 and payment.references[0].reference_name == invoice.name
            assert float(payment.references[0].allocated_amount) == 5.0
            assert float(invoice.outstanding_amount) == float(invoice.grand_total) - 5.0
            assert frappe.db.count('GL Entry', {'voucher_type': 'Payment Entry', 'voucher_no': payment.name}) > 0
            assert frappe.db.count('Payment Ledger Entry', {'voucher_type': 'Payment Entry', 'voucher_no': payment.name}) > 0
            payment_checked = True
            with internal_write('cc_accounting_write'):
                payment.flags.ignore_permissions = True
                payment.cancel()
            invoice.reload()
            assert abs(float(invoice.outstanding_amount) - float(invoice.grand_total)) < 0.011
        receivables.cancel(invoice.name, tag + ' synthetic POS native reversal')
        invoice.reload()
        assert invoice.docstatus == 2
        vouchers = [('Sales Invoice', invoice.name)] + ([('Payment Entry', payment_name)] if payment_name else [])
        effects = {}
        for kind, name in vouchers:
            rows, zero = ledger(kind, name)
            assert rows and zero
            effects[kind] = {'gl_rows': len(rows), 'net_zero': zero}
        frappe.db.commit()
        frappe.destroy()
        frappe.init(site='centrochange.local', sites_path='/home/frappe/frappe-bench/sites')
        frappe.connect()
        frappe.set_user('Administrator')
        assert frappe.db.get_value('Sales Invoice', invoice_name, 'docstatus') == 2
        if payment_name:
            assert frappe.db.get_value('Payment Entry', payment_name, 'docstatus') == 2
        assert not frappe.db.get_single_value('Accounts Settings', 'delete_linked_ledger_entries')
        print('CC_POS_STAGE=' + json.dumps({'stage': 'finalized', 'payment_checked': payment_checked,
            'effects': effects, 'retained_native_history': True}))
    else:
        invoice_name = os.environ.get('CC_POS_INVOICE') or ''
        if invoice_name:
            invoice, source, appointment = owned(invoice_name)
            payment = os.environ.get('CC_POS_PAYMENT') or ''
            matching = frappe.db.sql('''select distinct p.name from `tabPayment Entry` p
                join `tabPayment Entry Reference` r on r.parent=p.name
                where r.reference_doctype='Sales Invoice' and r.reference_name=%s
                and p.mode_of_payment=%s''', (invoice_name, tag + ' Carta POS'), as_dict=True)
            print('CC_POS_STAGE=' + json.dumps({'stage': 'inspected', 'invoice_status': invoice.docstatus,
                'payment_status': frappe.db.get_value('Payment Entry', payment, 'docstatus') if payment else None,
                'center_unchanged': context()[0].name == invoice.cc_center,
                'matching_payments': [row.name for row in matching]}))
        else:
            print('CC_POS_STAGE=' + json.dumps({'stage': 'inspected', 'no_invoice': True}))
    frappe.db.rollback()
except SystemExit:
    raise
except BaseException as error:
    frappe.db.rollback()
    print('CC_POS_STAGE=' + json.dumps({'stage': stage, 'status': 'FAIL', 'error_type': type(error).__name__}))
    raise
finally:
    frappe.destroy()
