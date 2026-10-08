"""Native receivables: reviewed snapshots, native postings and audited corrections."""
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic, append, internal_write, serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.finance.guards import require_finance, require_synthetic


def key(kind, request_key):
    if not request_key or len(str(request_key))>160:
        frappe.throw('A bounded idempotency key is required')
    return sha256(serialize([kind,frappe.session.user,request_key]).encode()).hexdigest()


def invoice(name,write=False):
    doc=frappe.get_doc('Sales Invoice',name,for_update=True)
    if not doc.cc_center:
        frappe.throw('A managed native invoice is required',frappe.PermissionError)
    require_finance(doc.cc_center,write)
    return doc


def result(doc,replay=False):
    doc.reload()
    return {'name':doc.name,'docstatus':doc.docstatus,'status':doc.status,'total':doc.grand_total,
        'outstanding':doc.outstanding_amount,'currency':doc.currency,'replay':replay}


@frappe.whitelist(methods=['POST'])
@atomic
def draft(sources,posting_date,due_date,request_key,reason):
    lock(); company=require_synthetic()
    if isinstance(sources,str):
        sources=frappe.parse_json(sources)
    if not isinstance(sources,list) or not sources or len(sources)>200 or len(set(sources))!=len(sources):
        frappe.throw('Choose 1–200 distinct economic sources')
    rows=[frappe.get_doc('CC Economic Source Link',name,for_update=True) for name in sources]
    for row in rows:
        require_finance(row.center,True)
    contexts={(r.center,r.customer,r.company,r.currency) for r in rows}
    if len(contexts)!=1 or rows[0].company!=company:
        frappe.throw('One invoice must retain one center customer company and currency')
    fingerprint=sha256(serialize([sorted(sources),str(posting_date),str(due_date)]).encode()).hexdigest()
    existing=frappe.db.get_value('Sales Invoice',{'cc_request_key':key('invoice',request_key)},for_update=True)
    if existing:
        doc=invoice(existing,True)
        if doc.cc_request_hash!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return result(doc,True)
    for row in rows:
        current=frappe.db.get_value('Patient Appointment',row.appointment,['cc_economic_state','cc_revision','cc_settlement_revision'],as_dict=True,for_update=True)
        if row.economic_state!='Due' or current.cc_economic_state!='Due' or row.revision!=current.cc_revision or row.settlement_revision!=current.cc_settlement_revision:
            frappe.throw('Only current due session snapshots are billable; refresh stale sources')
        # Native SI child rows are the billing reference. No parallel balance ledger.
        if frappe.db.sql('''select i.name from `tabSales Invoice Item` i join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus<2 and p.is_return=0 limit 1 for update''',(row.appointment,)):
            frappe.throw('Session already has an active native invoice')
    accounts=frappe.get_doc('Company',company)
    settings=frappe.get_doc('CC Finance Settings')
    income=settings.income_account or accounts.default_income_account
    if not settings.sales_tax_template or not settings.receipt_mode:
        frappe.throw('Configure and review the explicit DEV fiscal profile before drafting')
    from erpnext.controllers.accounts_controller import get_taxes_and_charges
    taxes=get_taxes_and_charges('Sales Taxes and Charges Template',settings.sales_tax_template)
    with internal_write('cc_accounting_write'):
        doc=frappe.get_doc({'doctype':'Sales Invoice','customer':rows[0].customer,'company':company,
            'currency':rows[0].currency,'conversion_rate':1,'posting_date':posting_date,'set_posting_time':1,
            'due_date':due_date,'debit_to':accounts.default_receivable_account,'cc_center':rows[0].center,
            'cc_request_key':key('invoice',request_key),'cc_request_hash':fingerprint,
            'cc_fiscal_profile':'SYNTHETIC_UNVERIFIED','taxes':taxes,
            'payment_schedule':[{'due_date':due_date,'invoice_portion':100,'mode_of_payment':settings.receipt_mode}],'items':[{'item_code':r.service_item,'item_name':r.service_label,
                'description':r.service_label,'qty':1,'rate':r.price,'income_account':income,'cost_center':r.cost_center,
                'cc_economic_source':r.name} for r in rows]}).insert(ignore_permissions=True)
    append('RECEIVABLE_DRAFTED',doc.doctype,doc.name,None,{'sources':sources,'total':doc.grand_total},reason)
    return result(doc)


@frappe.whitelist(methods=['POST'])
@atomic
def submit(name,reason):
    lock(); require_synthetic(); doc=invoice(name,True)
    if doc.docstatus==1:
        return result(doc,True)
    if doc.docstatus!=0:
        frappe.throw('Review a native draft before submission')
    with internal_write('cc_accounting_write'):
        doc.flags.ignore_permissions=True
        doc.submit()
    append('RECEIVABLE_SUBMITTED',doc.doctype,doc.name,{'docstatus':0},{'docstatus':1,'total':doc.grand_total},reason)
    return result(doc)


@frappe.whitelist(methods=['POST'])
@atomic
def pay(name,amount,posting_date,request_key,reason,reference=None):
    lock(); require_synthetic(); doc=invoice(name,True)
    fingerprint=sha256(serialize([name,str(amount),str(posting_date),reference]).encode()).hexdigest()
    existing=frappe.db.get_value('Payment Entry',{'cc_request_key':key('receipt',request_key)},for_update=True)
    if existing:
        payment=frappe.get_doc('Payment Entry',existing)
        if payment.cc_request_hash!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return {'payment':existing,'invoice':result(doc,True)}
    amount=frappe.utils.flt(amount,2)
    if doc.docstatus!=1 or doc.is_return or amount<=0 or amount>doc.outstanding_amount:
        frappe.throw('Receipt must allocate a positive amount within the open native balance')
    company=frappe.get_doc('Company',doc.company)
    settings=frappe.get_doc('CC Finance Settings')
    bank=settings.bank_account or company.default_cash_account
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    payment=get_payment_entry('Sales Invoice',name,party_amount=amount,bank_account=bank,bank_amount=amount)
    payment.update({'posting_date':posting_date,'reference_no':reference or request_key,'reference_date':posting_date,
        'cc_center':doc.cc_center,'cc_request_key':key('receipt',request_key),'cc_request_hash':fingerprint})
    with internal_write('cc_accounting_write'):
        payment.insert(ignore_permissions=True); payment.submit()
    append('RECEIPT_POSTED',payment.doctype,payment.name,None,{'invoice':name,'allocated':amount},reason)
    return {'payment':payment.name,'invoice':result(doc)}


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(name,reason):
    lock(); require_synthetic(); doc=invoice(name,True)
    if doc.docstatus==2:
        return result(doc,True)
    if doc.docstatus!=1:
        frappe.throw('Only a submitted native invoice can be cancelled')
    with internal_write('cc_accounting_write'):
        doc.flags.ignore_permissions=True
        doc.cancel()
    append('RECEIVABLE_CANCELLED',doc.doctype,name,{'docstatus':1},{'docstatus':2},reason)
    return result(doc)


@frappe.whitelist(methods=['POST'])
@atomic
def credit(name,posting_date,request_key,reason):
    lock(); require_synthetic(); original=invoice(name,True)
    existing=frappe.db.get_value('Sales Invoice',{'cc_request_key':key('credit',request_key)},for_update=True)
    if existing:
        doc=invoice(existing,True)
        if doc.return_against!=name or str(doc.posting_date)!=str(posting_date):
            frappe.throw('Idempotency key payload differs')
        return result(doc,True)
    if original.docstatus!=1 or original.is_return:
        frappe.throw('A submitted original invoice is required')
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    target=frappe.new_doc('Sales Invoice')
    target.flags.ignore_permissions=True
    doc=make_sales_return(name,target_doc=target)
    doc.update({'posting_date':posting_date,'set_posting_time':1,'cc_center':original.cc_center,
        'cc_request_key':key('credit',request_key),'cc_request_hash':None,'cc_fiscal_profile':'SYNTHETIC_UNVERIFIED'})
    for target,source in zip(doc.items,original.items,strict=True):
        target.cc_economic_source=source.cc_economic_source
    with internal_write('cc_accounting_write'):
        doc.insert(ignore_permissions=True)
    append('CREDIT_DRAFTED',doc.doctype,doc.name,None,{'return_against':name},reason)
    return result(doc)


@frappe.whitelist(methods=['GET'])
def position(name):
    return result(invoice(name))


def protected(doc,method=None):
    if not frappe.flags.get('cc_accounting_write'):
        frappe.throw('Accounting mutations require the reviewed audited service',frappe.PermissionError)
    if doc.doctype=='Sales Invoice':
        if doc.patient or any(i.reference_dt or i.reference_dn for i in doc.items):
            frappe.throw('Native clinical billing side effects are excluded from the accounting bridge')
        if not doc.cc_center or doc.cc_fiscal_profile!='SYNTHETIC_UNVERIFIED':
            frappe.throw('Synthetic accounting context is mandatory')
        for item in doc.items:
            source=frappe.get_doc('CC Economic Source Link',item.cc_economic_source)
            if (source.center,source.customer,source.company,source.currency)!=(doc.cc_center,doc.customer,doc.company,doc.currency) or item.item_code!=source.service_item or abs(item.qty)!=1 or item.rate!=source.price or item.cost_center!=source.cost_center:
                frappe.throw('Invoice line must retain the immutable economic source snapshot')


@frappe.whitelist(methods=['GET'])
def candidates(center,from_date,to_date):
    require_finance(center)
    start,end=frappe.utils.getdate(from_date),frappe.utils.getdate(to_date)
    if start>end or (end-start).days>366:
        frappe.throw('Use a bounded accounting period of at most 366 days')
    rows=frappe.get_all('Patient Appointment',filters={'cc_center':center,'cc_economic_state':'Due',
        'appointment_date':['between',[start,end]]},fields=['name','patient','appointment_date','cc_price_snapshot','cc_currency_snapshot'],limit_page_length=501)
    if len(rows)>500:
        frappe.throw('Narrow the accounting period')
    active={r[0] for r in frappe.db.sql('''select distinct s.appointment from `tabSales Invoice Item` i
        join `tabSales Invoice` p on p.name=i.parent join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
        where p.cc_center=%s and p.docstatus<2 and p.is_return=0''',(center,))}
    return {'candidates':[r for r in rows if r.name not in active],'period':[start,end]}


@frappe.whitelist(methods=['POST'])
@atomic
def amend(name,posting_date,due_date,request_key,reason):
    lock(); require_synthetic(); original=invoice(name,True)
    if original.docstatus!=2 or original.is_return:
        frappe.throw('Only a cancelled original native invoice can be amended')
    existing=frappe.db.get_value('Sales Invoice',{'cc_request_key':key('amend',request_key)},for_update=True)
    if existing:
        doc=invoice(existing,True)
        if doc.amended_from!=name or str(doc.posting_date)!=str(posting_date) or str(doc.due_date)!=str(due_date):
            frappe.throw('Idempotency key payload differs')
        return result(doc,True)
    doc=frappe.copy_doc(original)
    doc.update({'docstatus':0,'amended_from':name,'posting_date':posting_date,'due_date':due_date,
        'cc_request_key':key('amend',request_key),'cc_request_hash':None})
    for item in original.items:
        source=frappe.get_doc('CC Economic Source Link',item.cc_economic_source)
        if frappe.db.get_value('Patient Appointment',source.appointment,'cc_economic_state',for_update=True)!='Due':
            frappe.throw('A waived or non-due session cannot be reissued')
        if frappe.db.sql('''select i.name from `tabSales Invoice Item` i join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source where s.appointment=%s and p.docstatus<2
            and p.is_return=0 limit 1 for update''',(source.appointment,)):
            frappe.throw('Session already has an active replacement invoice')
    with internal_write('cc_accounting_write'):
        doc.insert(ignore_permissions=True)
    append('RECEIVABLE_AMENDED',doc.doctype,doc.name,{'amended_from':name},{'sources':[i.cc_economic_source for i in doc.items]},reason)
    return result(doc)


class InvoiceMixin:
    @frappe.whitelist()
    def set_healthcare_services(self,checked_values):
        frappe.throw('Use reviewed immutable economic sources',frappe.PermissionError)
