"""WP-01 synthetic native master/source regression, rolled back with fixtures."""
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.security.lifecycle import set_membership,set_assignment
from centrochange_core.operations import surfaces_acceptance
from centrochange_core.finance import bridge


def checks(fixture):
    accounting_before={dt:frappe.db.count(dt) for dt in ('Sales Invoice', 'Purchase Invoice', 'Payment Entry', 'GL Entry')}
    result=surfaces_acceptance.checks(fixture)
    patient,center,other,prac1,prac2,pro1,secretary=(fixture[key] for key in ('patient','center','other','prac1','prac2','pro1','secretary'))
    frappe.set_user('Administrator')
    set_assignment(patient,center,prac1,1,'Synthetic finance fixture')
    mapped=bridge.map_center(center,'Synthetic native center mapping')
    assert frappe.db.get_value('Cost Center',mapped['cost_center'],'company')==mapped['company']
    assert bridge.map_center(center,'Synthetic center retry')['replay']
    result.append('native Cost Center mapping and retry preserve one accounting dimension')
    customer=bridge.map_patient(patient,center,'Synthetic customer mapping')['customer']
    supplier=bridge.map_practitioner(prac1,center,'Synthetic supplier mapping')['supplier']
    assert bridge.map_patient(patient,center,'Synthetic customer retry')['replay']
    assert bridge.map_practitioner(prac1,center,'Synthetic supplier retry')['replay']
    result.append('native Patient Customer and Professional Supplier mapping idempotent')
    # Select a performed native source with the booking-date historical price.
    appointment=frappe.db.get_value('Patient Appointment',{'patient':patient,'cc_performed':1})
    historical_price=frappe.db.get_value('Patient Appointment',appointment,'cc_price_snapshot')
    frappe.db.set_value('Item Price',{'item_code':'CC SYNTHETIC SESSION'},'price_list_rate',42)
    captured=bridge.capture(appointment,'Synthetic economic trace')['name']
    assert bridge.capture(appointment,'Synthetic economic trace retry')['replay']
    source=frappe.get_doc('CC Economic Source Link',captured)
    assert source.customer==customer and source.supplier==supplier and source.cost_center==mapped['cost_center']
    assert source.price==historical_price and source.price!=42 and source.service_item=='CC SYNTHETIC SESSION' and source.patient==patient
    result.append('canonical session traces native subjects item dimension and historical immutable price')
    source.price=999
    try:
        source.save(ignore_permissions=True)
    except frappe.PermissionError:
        result.append('economic source snapshots cannot be rewritten')
    else:
        raise AssertionError('Historical source overwritten')
    replacement=frappe.get_doc({'doctype':'Customer','customer_name':'CC SYNTHETIC CORRECTED CUSTOMER','customer_type':'Individual',
        'customer_group':frappe.db.get_single_value('Selling Settings','customer_group'),'territory':frappe.db.get_single_value('Selling Settings','territory')}).insert()
    bridge.map_patient(patient,center,'Synthetic audited customer correction',replacement.name)
    corrected=bridge.capture(appointment,'Synthetic corrected master source')['name']
    assert corrected!=captured and frappe.db.get_value('CC Economic Source Link',captured,'customer')==customer
    assert frappe.db.get_value('CC Economic Source Link',corrected,'customer')==replacement.name
    assert frappe.db.exists('CC Audit Event',{'event_type':'PATIENT_CUSTOMER_MAPPED','reason':'Synthetic audited customer correction'})
    result.append('mapping correction appends source trace and retains prior native subject history')
    native_patient=frappe.get_doc('Patient',patient)
    native_patient.customer=customer
    try:
        native_patient.save(ignore_permissions=True)
    except frappe.PermissionError:
        result.append('generic Patient Customer mapping mutation denied')
    else:
        raise AssertionError('Unaudited mapping bypass accepted')
    finance=frappe.get_doc({'doctype':'User','email':'finance.cc-regression@example.invalid','first_name':'Synthetic Finance',
        'send_welcome_email':0,'roles':[{'role':'CC Finance'}]}).insert(ignore_permissions=True).name
    accountant=frappe.get_doc({'doctype':'User','email':'accountant.cc-regression@example.invalid','first_name':'Synthetic Accountant',
        'send_welcome_email':0,'roles':[{'role':'CC Accountant'}]}).insert(ignore_permissions=True).name
    for user in (finance,accountant):
        set_membership(user,center,1,'Synthetic finance membership')
    for user in (finance,accountant,secretary):
        frappe.set_user(user)
        source=frappe.get_doc('CC Economic Source Link',captured)
        source.check_permission('read')
        assert captured in frappe.get_list('CC Economic Source Link',pluck='name')
        frappe.get_doc('Customer',replacement.name).check_permission('read')
        frappe.get_doc('Supplier',supplier).check_permission('read')
        result.append('authorized accounting source and native master read: '+('finance' if user==finance else 'accountant' if user==accountant else 'secretariat'))
        if user!=secretary:
            try:
                frappe.get_doc('Patient',patient).check_permission('read')
            except frappe.PermissionError:
                result.append('accounting role has no clinical Patient master read: '+('finance' if user==finance else 'accountant'))
            else:
                raise AssertionError('Finance acquired clinical Patient master')
    frappe.set_user(accountant)
    try:
        bridge.map_patient(patient,center,'Unauthorized accountant mutation',customer)
    except frappe.PermissionError:
        result.append('read-only accountant mapping mutation denied')
    else:
        raise AssertionError('Accountant changed fiscal mapping')
    frappe.set_user(pro1)
    for doctype,name in [('CC Economic Source Link',captured),('Customer',replacement.name),('Supplier',supplier)]:
        try:
            frappe.get_doc(doctype,name).check_permission('read')
        except frappe.PermissionError:
            result.append('professional center-wide financial direct read denied: '+doctype)
        else:
            raise AssertionError('Professional financial master read accepted')
    try:
        bridge.capture(appointment,'Unauthorized professional accounting action')
    except frappe.PermissionError:
        result.append('professional accounting capture denied')
    else:
        raise AssertionError('Professional captured center finance')
    frappe.set_user('Administrator')
    set_membership(finance,center,0,'Synthetic finance center revocation')
    set_membership(finance,other,1,'Synthetic finance other center')
    frappe.set_user(finance)
    assert not frappe.get_list('CC Economic Source Link',pluck='name')
    try:
        frappe.get_doc('CC Economic Source Link',captured).check_permission('read')
    except frappe.PermissionError:
        result.append('cross-center financial source list/direct denied after membership revocation')
    else:
        raise AssertionError('Cross-center financial source read accepted')
    frappe.set_user('Administrator')
    try:
        frappe.share.add_docshare('Customer',replacement.name,user=pro1,read=1,flags={'ignore_share_permission':True})
    except frappe.PermissionError:
        result.append('manual finance share cannot override professional denial')
    else:
        raise AssertionError('Financial manual share accepted')
    assert accounting_before=={dt:frappe.db.count(dt) for dt in accounting_before}
    result.append('finance master bridge does not auto-post native accounting documents')
    settings=frappe.get_doc('CC Finance Settings')
    settings.simulation_only=0
    try:
        settings.save(ignore_permissions=True)
    except frappe.PermissionError:
        result.append('finance configuration cannot activate real fiscal providers in DEV')
    else:
        raise AssertionError('Real provider configuration enabled')
    set_assignment(patient,center,prac1,0,'Synthetic finance fixture release')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:
        return security.run(extra_checks=checks)
    finally:
        frappe.flags.cc_test_clock=previous
