"""Native synthetic bank movement intake and explicit assisted reconciliation."""
from hashlib import sha256
from math import isfinite
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.finance.guards import require_finance,require_finance_manager,require_synthetic
from centrochange_core.finance import receivables

SOURCE_FIELDS=('bank_account','company','currency','date','deposit','withdrawal','description','reference_number',
    'transaction_id','party_type','party','cc_center','cc_source_key','cc_source_hash')


@frappe.whitelist(methods=['POST'])
@atomic
def configure_bank(center,reason,account=None):
    lock(); require_finance_manager(); company=require_synthetic()
    branch=frappe.get_doc('Branch',center,for_update=True)
    if branch.cc_company!=company:
        frappe.throw('Configure the native center accounting mapping first')
    existing=branch.cc_bank_account
    if existing and (not account or frappe.db.get_value('Bank Account',existing,'account')==account):
        return {'bank_account':existing,'replay':True}
    if not account:
        parent=frappe.db.get_value('Account',{'company':company,'root_type':'Asset','is_group':1,'parent_account':['is','not set']},'name')
        account=frappe.get_doc({'doctype':'Account','account_name':'CC DEV BANK '+center,'company':company,
            'parent_account':parent,'account_type':'Bank','account_currency':'EUR','is_group':0}).insert(ignore_permissions=True).name
    chart=frappe.get_doc('Account',account)
    if chart.company!=company or chart.is_group or chart.disabled or chart.account_type!='Bank':
        frappe.throw('An enabled native bank GL account for the synthetic company is required')
    bank='CC SYNTHETIC BANK'
    if not frappe.db.exists('Bank',bank):
        frappe.get_doc({'doctype':'Bank','bank_name':bank}).insert(ignore_permissions=True)
    with internal_write('cc_accounting_write'):
        native=frappe.get_doc({'doctype':'Bank Account','account_name':'CC DEV '+center,'bank':bank,
            'account':account,'is_company_account':1,'company':company,'cc_center':center}).insert(ignore_permissions=True)
    with internal_write('cc_finance_mapping_write'):
        frappe.db.set_value('Branch',center,'cc_bank_account',native.name)
    append('CENTER_BANK_CONFIGURED','Branch',center,{'bank_account':existing},{'bank_account':native.name,'account':account},reason)
    return {'bank_account':native.name,'replay':False}


def bank_doc(name,write=False):
    doc=frappe.get_doc('Bank Transaction',name,for_update=True)
    require_finance(doc.cc_center,write)
    if not doc.cc_source_key:
        frappe.throw('A managed source movement is required')
    return doc


def projection(doc,replay=False):
    doc.reload()
    return {'name':doc.name,'status':doc.status,'docstatus':doc.docstatus,'deposit':doc.deposit,'withdrawal':doc.withdrawal,
        'allocated':doc.allocated_amount,'unallocated':doc.unallocated_amount,'currency':doc.currency,'replay':replay}


@frappe.whitelist(methods=['POST'])
@atomic
def import_movements(center,movements,reason):
    lock(); company=require_synthetic(); require_finance(center,True)
    if isinstance(movements,str):
        movements=frappe.parse_json(movements)
    if not isinstance(movements,list) or not movements or len(movements)>200:
        frappe.throw('Import 1–200 explicit synthetic movements')
    bank=frappe.db.get_value('Branch',center,'cc_bank_account',for_update=True)
    if not bank or frappe.db.get_value('Bank Account',bank,'cc_center')!=center:
        frappe.throw('Configure the center native bank account first')
    rows=[]
    for movement in movements:
        if not isinstance(movement,dict) or set(movement)-{'external_id','date','deposit','withdrawal','description','reference','customer','supplier'}:
            frappe.throw('Unsupported bank movement input')
        external=movement.get('external_id')
        if not isinstance(external,str) or not external.strip() or len(external)>160:
            frappe.throw('A bounded statement movement identity is required')
        deposit,withdrawal=(frappe.utils.flt(movement.get(k),2) for k in ('deposit','withdrawal'))
        if not isfinite(deposit) or not isfinite(withdrawal) or deposit<0 or withdrawal<0 or bool(deposit)==bool(withdrawal):
            frappe.throw('A movement must contain one positive deposit or withdrawal')
        if any(not isinstance(movement.get(field) or '',str) or len(movement.get(field) or '')>size for field,size in [('description',500),('reference',160)]):
            frappe.throw('Bank description/reference must be bounded text')
        if not movement.get('date'):
            frappe.throw('An explicit bank movement date is required')
        customer=movement.get('customer');supplier=movement.get('supplier')
        if customer and (supplier or withdrawal) or supplier and deposit:
            frappe.throw('Bank party must match the movement direction')
        if customer:
            frappe.get_doc('Customer',customer).check_permission('read')
        if supplier:
            frappe.get_doc('Supplier',supplier).check_permission('read')
        snapshot={'bank_account':bank,'company':company,'cc_center':center,'currency':frappe.db.get_value('Account',frappe.db.get_value('Bank Account',bank,'account'),'account_currency'),
            'date':str(frappe.utils.getdate(movement['date'])),'deposit':deposit,'withdrawal':withdrawal,
            'description':str(movement.get('description') or '')[:500],'reference_number':str(movement.get('reference') or '')[:160],
            'transaction_id':external,'party_type':'Supplier' if supplier else 'Customer' if customer else None,'party':supplier or customer}
        source=sha256(serialize([bank,external]).encode()).hexdigest()
        fingerprint=sha256(serialize(snapshot).encode()).hexdigest()
        existing=frappe.db.get_value('Bank Transaction',{'cc_source_key':source},for_update=True)
        if existing:
            doc=bank_doc(existing,True)
            if doc.cc_source_hash!=fingerprint:
                frappe.throw('Statement source identity has different immutable content; use an audited correction')
            rows.append(projection(doc,True)); continue
        with internal_write('cc_accounting_write'):
            doc=frappe.get_doc({'doctype':'Bank Transaction',**snapshot,'cc_source_key':source,'cc_source_hash':fingerprint}).insert(ignore_permissions=True)
            doc.submit()
        append('BANK_MOVEMENT_IMPORTED',doc.doctype,doc.name,None,{'source_key':source,'source_hash':fingerprint},reason)
        rows.append(projection(doc))
    return {'movements':rows}


def reconciled_documents(doc):
    """Native allocation trace, independent of remaining invoice outstanding."""
    rows=[]
    if doc.docstatus!=1:return rows
    for allocation in doc.payment_entries:
        if allocation.payment_document!='Payment Entry':continue
        payment=frappe.get_doc('Payment Entry',allocation.payment_entry)
        if payment.cc_center!=doc.cc_center or payment.docstatus!=1:
            frappe.throw('Bank allocation context requires review')
        for ref in payment.references:
            if ref.reference_doctype not in ('Sales Invoice','Purchase Invoice'):continue
            invoice=frappe.get_doc(ref.reference_doctype,ref.reference_name)
            if invoice.cc_center!=doc.cc_center:
                frappe.throw('Bank invoice context requires review')
            subject=invoice.get('customer') or invoice.get('supplier')
            rows.append({'name':invoice.name,'document_type':ref.reference_doctype,'subject':subject,
                'allocated_amount':ref.allocated_amount,'payment':payment.name})
    return rows


@frappe.whitelist(methods=['GET'])
def candidates(name):
    doc=bank_doc(name)
    if doc.docstatus!=1 or doc.unallocated_amount<=0:
        return {'state':'Reconciled' if doc.docstatus==1 and doc.unallocated_amount<=0 else 'Not Eligible','invoices':[],'reconciled_documents':reconciled_documents(doc)}
    filters={'cc_center':doc.cc_center,'company':doc.company,'currency':doc.currency,'docstatus':1,'is_return':0,
        'outstanding_amount':['>=',doc.unallocated_amount]}
    document_type='Purchase Invoice' if doc.withdrawal else 'Sales Invoice'
    if doc.party and doc.party_type==('Supplier' if doc.withdrawal else 'Customer'):
        filters['supplier' if doc.withdrawal else 'customer']=doc.party
    from centrochange_core.security.guards import current_rows
    rows=current_rows(document_type,filters=filters,fields=['name','supplier' if doc.withdrawal else 'customer','outstanding_amount','due_date','posting_date'])
    rows.sort(key=lambda row:(row.posting_date,row.name))
    if len(rows)>100:
        frappe.throw('Narrow the bank movement customer/reference before matching')
    exact=[row for row in rows if row.name==doc.reference_number]
    if exact:
        rows=exact
    return {'state':'Unmatched' if not rows else 'Candidate' if len(rows)==1 else 'Ambiguous','document_type':document_type,'invoices':rows}


@frappe.whitelist(methods=['POST'])
@atomic
def reconcile(name,invoice,reason):
    lock(); require_synthetic(); doc=bank_doc(name,True)
    document_type='Purchase Invoice' if doc.withdrawal else 'Sales Invoice'
    if doc.docstatus==1 and doc.unallocated_amount==0:
        payments=[p.payment_entry for p in doc.payment_entries if p.payment_document=='Payment Entry']
        if len(payments)!=1 or not frappe.db.exists('Payment Entry Reference',{'parent':payments[0],'reference_doctype':document_type,'reference_name':invoice}):
            frappe.throw('A reconciled movement cannot be replayed against a different invoice')
        return {'movement':projection(doc,True),'payment':payments[0]}
    if invoice not in [r.name for r in candidates(name)['invoices']]:
        frappe.throw('Choose a current eligible own-center invoice for reconciliation')
    bank_account=frappe.db.get_value('Bank Account',doc.bank_account,'account')
    from centrochange_core.finance.incoming import pay as pay_supplier
    pay=pay_supplier if doc.withdrawal else receivables.pay
    payment=pay(invoice,doc.unallocated_amount,doc.date,'bank:'+doc.cc_source_key,reason,
        reference=doc.transaction_id,bank_account=bank_account)['payment']
    with internal_write('cc_accounting_write'):
        doc.flags.ignore_permissions=True
        doc.add_payment_entries([{'payment_doctype':'Payment Entry','payment_name':payment}],is_new_voucher=True)
        doc.save(ignore_permissions=True)
    doc.reload()
    if doc.unallocated_amount!=0:
        frappe.throw('Native bank allocation did not fully reconcile the selected movement')
    append('BANK_MOVEMENT_RECONCILED',doc.doctype,name,None,{'invoice':invoice,'payment':payment,'allocated':doc.allocated_amount},reason)
    return {'movement':projection(doc),'payment':payment}


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(name,reason):
    lock(); require_synthetic(); doc=bank_doc(name,True)
    if doc.docstatus==2:
        return projection(doc,True)
    payments=[p.payment_entry for p in doc.payment_entries if p.payment_document=='Payment Entry']
    with internal_write('cc_accounting_write'):
        doc.flags.ignore_permissions=True; doc.cancel()
        for name in payments:
            payment=frappe.get_doc('Payment Entry',name,for_update=True)
            if payment.docstatus==1:
                payment.flags.ignore_permissions=True; payment.cancel()
    append('BANK_MOVEMENT_CANCELLED',doc.doctype,doc.name,None,{'cancelled_payments':payments},reason)
    return projection(doc)


def protected(doc,method=None):
    if not frappe.flags.get('cc_accounting_write'):
        frappe.throw('Bank mutations require the audited native service',frappe.PermissionError)
    old=doc.get_doc_before_save()
    def normalized(field,value):
        if field=='date':
            return str(frappe.utils.getdate(value))
        if field in ('deposit','withdrawal'):
            return frappe.utils.flt(value,2)
        return str(value or '')
    if old and doc.doctype=='Bank Transaction' and any(normalized(field,doc.get(field))!=normalized(field,old.get(field)) for field in SOURCE_FIELDS):
        frappe.throw('Imported bank movement source is immutable')
    if old and doc.doctype=='Bank Account' and any(doc.get(f)!=old.get(f) for f in ('cc_center','account','company','bank')):
        frappe.throw('Bank mapping corrections must retain historical native accounts')


@frappe.whitelist(methods=['GET'])
def unresolved(center):
    require_finance(center)
    names=frappe.get_all('Bank Transaction',filters={'cc_center':center,'docstatus':1,'unallocated_amount':['>',0]},pluck='name',limit_page_length=101)
    if len(names)>100:
        frappe.throw('Narrow unresolved bank movements')
    return [{'movement':projection(bank_doc(name)), 'matching':candidates(name)} for name in names]
