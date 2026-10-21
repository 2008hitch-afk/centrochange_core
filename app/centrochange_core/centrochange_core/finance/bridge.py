"""Audited native master mappings and immutable operational economic snapshots."""
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows
from centrochange_core.finance.guards import require_finance_manager,patient_context,require_finance,require_synthetic


@frappe.whitelist(methods=['POST'])
@atomic
def map_center(center,reason,cost_center=None):
    lock()
    require_finance_manager()
    company=require_synthetic()
    branch=frappe.get_doc('Branch',center,for_update=True)
    old={'company':branch.cc_company,'cost_center':branch.cc_cost_center}
    if not cost_center:
        if branch.cc_company==company and branch.cc_cost_center:
            return {'company':company,'cost_center':branch.cc_cost_center,'replay':True}
        root=frappe.db.get_value('Cost Center',{'company':company,'is_group':1,'parent_cost_center':['is','not set']},'name',for_update=True)
        if not root:
            frappe.throw('Manca il centro di costo principale della società.')
        doc=frappe.get_doc({'doctype':'Cost Center','cost_center_name':'CC '+center,'company':company,
            'parent_cost_center':root,'is_group':0}).insert(ignore_permissions=True)
        cost_center=doc.name
    doc=frappe.get_doc('Cost Center',cost_center,for_update=True)
    if doc.company!=company or doc.is_group or doc.disabled:
        frappe.throw('Serve un centro di costo operativo attivo per la società configurata.')
    if old=={'company':company,'cost_center':cost_center}:
        return {'company':company,'cost_center':cost_center,'replay':True}
    with internal_write('cc_finance_mapping_write'):
        frappe.db.set_value('Branch',center,{'cc_company':company,'cc_cost_center':cost_center})
    append('ACCOUNTING_CENTER_MAPPED','Branch',center,old,{'company':company,'cost_center':cost_center},reason)
    return {'company':company,'cost_center':cost_center,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def map_patient(patient,center,reason,customer=None):
    lock()
    require_synthetic()
    patient_context(patient,center,write=True)
    row=frappe.db.get_value('Patient',patient,['name','patient_name','customer'],as_dict=True,for_update=True)
    if not row:
        frappe.throw('L’identità del paziente non esiste.')
    if not customer and row.customer:
        return {'customer':row.customer,'replay':True}
    created=not customer
    if not customer:
        group=frappe.db.get_single_value('Selling Settings','customer_group')
        if not group or frappe.db.get_value('Customer Group',group,'is_group'):
            frappe.throw('Configura un gruppo clienti nativo ordinario prima del collegamento.')
        # Native Customer is the fiscal master; no clinical fields are copied.
        customer=frappe.get_doc({'doctype':'Customer','customer_name':row.patient_name,'customer_type':'Individual',
            'customer_group':group,
            'territory':frappe.db.get_single_value('Selling Settings','territory') or 'All Territories'}).insert(ignore_permissions=True).name
    target=frappe.get_doc('Customer',customer,for_update=True)
    if not created:
        target.check_permission('read')
    if target.disabled:
        frappe.throw('Il cliente contabile è disattivato.')
    if row.customer==customer:
        return {'customer':customer,'replay':True}
    with internal_write('cc_finance_mapping_write'):
        frappe.db.set_value('Patient',patient,'customer',customer)
    append('PATIENT_CUSTOMER_MAPPED','Patient',patient,{'customer':row.customer},{'customer':customer,'center':center},reason)
    return {'customer':customer,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def map_practitioner(practitioner,center,reason,supplier=None):
    lock()
    require_synthetic()
    require_finance(center,write=True)
    row=frappe.db.get_value('Healthcare Practitioner',practitioner,['name','practitioner_name','user_id','supplier'],as_dict=True,for_update=True)
    if not row or not current_rows('CC Center Membership',{'user':row.user_id,'center':center,'active':1},pluck='name'):
        frappe.throw('Il contesto contabile del professionista non è disponibile.',frappe.PermissionError)
    if not supplier and row.supplier:
        return {'supplier':row.supplier,'replay':True}
    created=not supplier
    if not supplier:
        supplier=frappe.get_doc({'doctype':'Supplier','supplier_name':row.practitioner_name,'supplier_type':'Individual',
            'supplier_group':frappe.db.get_single_value('Buying Settings','supplier_group') or 'All Supplier Groups',
            'country':'Italy'}).insert(ignore_permissions=True).name
    target=frappe.get_doc('Supplier',supplier,for_update=True)
    if not created:
        target.check_permission('read')
    if target.disabled:
        frappe.throw('Il fornitore contabile è disattivato.')
    if row.supplier==supplier:
        return {'supplier':supplier,'replay':True}
    with internal_write('cc_finance_mapping_write'):
        frappe.db.set_value('Healthcare Practitioner',practitioner,'supplier',supplier)
    append('PROFESSIONAL_SUPPLIER_MAPPED','Healthcare Practitioner',practitioner,{'supplier':row.supplier},
        {'supplier':supplier,'center':center},reason)
    return {'supplier':supplier,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def capture(appointment,reason):
    lock()
    require_synthetic()
    doc=frappe.get_doc('Patient Appointment',appointment,for_update=True)
    patient_context(doc.patient,doc.cc_center,write=True)
    center=frappe.get_doc('Branch',doc.cc_center,for_update=True)
    customer=frappe.db.get_value('Patient',doc.patient,'customer',for_update=True)
    supplier=frappe.db.get_value('Healthcare Practitioner',doc.practitioner,'supplier',for_update=True)
    if not customer or not center.cc_company or not center.cc_cost_center or not doc.cc_service_item or not doc.cc_currency_snapshot:
        frappe.throw('Completa i collegamenti contabili nativi e i dati storici delle sedute.')
    native_center=frappe.get_doc('Cost Center',center.cc_cost_center,for_update=True)
    if native_center.company!=doc.company or center.cc_company!=doc.company:
        frappe.throw('Società o centro di costo contabile non corrispondono al contesto operativo.')
    snapshot={'appointment':doc.name,'patient':doc.patient,'customer':customer,'practitioner':doc.practitioner,'supplier':supplier,
        'center':doc.cc_center,'company':doc.company,'cost_center':center.cc_cost_center,'service_item':doc.cc_service_item,
        'service_label':doc.cc_service_label,'duration':doc.duration,'price':doc.cc_price_snapshot,'currency':doc.cc_currency_snapshot,
        'payment_terms_mode':doc.cc_payment_terms_mode or 'Immediate','payment_agreed_date':doc.cc_payment_agreed_date,
        'booking_date':doc.cc_booking_date,'session_date':doc.appointment_date,'economic_state':doc.cc_economic_state,
        'performed':doc.cc_performed,'operational_paid':doc.cc_paid,'revision':doc.cc_revision,
        'settlement_revision':doc.cc_settlement_revision,'package':doc.cc_package}
    digest=sha256(serialize(snapshot).encode()).hexdigest()
    existing=frappe.db.get_value('CC Economic Source Link',{'source_key':digest},for_update=True)
    if existing:
        return {'name':existing,'replay':True}
    with internal_write('cc_operation_write'):
        link=frappe.get_doc({'doctype':'CC Economic Source Link',**snapshot,'source_key':digest,'snapshot_hash':digest,
            'captured_by':frappe.session.user}).insert(ignore_permissions=True)
    append('ECONOMIC_SOURCE_CAPTURED',link.doctype,link.name,None,{'appointment':doc.name,'snapshot_hash':digest},reason)
    return {'name':link.name,'replay':False}


def protected_center(doc,method=None):
    previous=doc.get_doc_before_save()
    from centrochange_core.security.center_state import protect_operational_state
    protect_operational_state(doc,previous)
    if not frappe.flags.get('cc_finance_mapping_write') and any(doc.get(field)!=(previous.get(field) if previous else None) for field in ('cc_company','cc_cost_center','cc_bank_account')):
        frappe.throw('I collegamenti contabili della sede richiedono il servizio tracciato.',frappe.PermissionError)
