"""Native receivables: reviewed snapshots, native postings and audited corrections."""
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic, append, internal_write, serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.finance.guards import require_finance, require_synthetic


def key(kind, request_key):
    if not request_key or len(str(request_key))>160:
        frappe.throw('Indica un identificativo valido per la richiesta.')
    return sha256(serialize([kind,frappe.session.user,request_key]).encode()).hexdigest()


def invoice(name,write=False):
    doc=frappe.get_doc('Sales Invoice',name,for_update=True)
    if not doc.cc_center:
        frappe.throw('Seleziona una fattura nativa gestita da Centro Change.',frappe.PermissionError)
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
        frappe.throw('Seleziona da 1 a 200 fonti economiche distinte.')
    rows=[frappe.get_doc('CC Economic Source Link',name,for_update=True) for name in sources]
    for row in rows:
        require_finance(row.center,True)
    contexts={(r.center,r.customer,r.company,r.currency) for r in rows}
    if len(contexts)!=1 or rows[0].company!=company:
        frappe.throw('Una fattura deve riferirsi a una sola sede, cliente, società e valuta.')
    fingerprint=sha256(serialize([sorted(sources),str(posting_date),str(due_date)]).encode()).hexdigest()
    existing=frappe.db.get_value('Sales Invoice',{'cc_request_key':key('invoice',request_key)},for_update=True)
    if existing:
        doc=invoice(existing,True)
        if doc.cc_request_hash!=fingerprint:
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return result(doc,True)
    for row in rows:
        current=frappe.db.get_value('Patient Appointment',row.appointment,['cc_economic_state','cc_revision','cc_settlement_revision'],as_dict=True,for_update=True)
        if row.economic_state!='Due' or current.cc_economic_state!='Due' or row.revision!=current.cc_revision or row.settlement_revision!=current.cc_settlement_revision:
            frappe.throw('Sono fatturabili solo sedute attualmente dovute: aggiorna le fonti non più valide.')
        # Native SI child rows are the billing reference. No parallel balance ledger.
        if frappe.db.sql('''select i.name from `tabSales Invoice Item` i join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus<2 and p.is_return=0 limit 1 for update''',(row.appointment,)):
            frappe.throw('La seduta ha già una fattura nativa attiva.')
    accounts=frappe.get_doc('Company',company)
    if rows[0].currency!=accounts.default_currency:
        frappe.throw('Il profilo fiscale DEV usa solo la valuta della società; nessun cambio viene calcolato automaticamente.')
    settings=frappe.get_doc('CC Finance Settings')
    income=settings.income_account or accounts.default_income_account
    if not settings.sales_tax_template or not settings.receipt_mode:
        frappe.throw('Configura e verifica il profilo fiscale DEV prima della bozza.')
    from centrochange_core.finance.native_adapter import sales_taxes
    taxes=sales_taxes(rows[0].center,company)
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
        frappe.throw('Verifica la bozza nativa prima di contabilizzarla.')
    with internal_write('cc_accounting_write'):
        doc.flags.ignore_permissions=True
        doc.submit()
    append('RECEIVABLE_SUBMITTED',doc.doctype,doc.name,{'docstatus':0},{'docstatus':1,'total':doc.grand_total},reason)
    return result(doc)


@frappe.whitelist(methods=['POST'])
@atomic
def pay(name,amount,posting_date,request_key,reason,reference=None,bank_account=None,mode_of_payment=None):
    lock(); require_synthetic(); doc=invoice(name,True)
    company=frappe.get_doc('Company',doc.company)
    settings=frappe.get_doc('CC Finance Settings')
    selected_mode=mode_of_payment
    if selected_mode:
        from centrochange_core.finance.native_adapter import payment_mode_account
        method_account=payment_mode_account(selected_mode,doc.company)
        if bank_account and bank_account!=method_account:
            frappe.throw('Il conto deve corrispondere al metodo di pagamento selezionato.',frappe.PermissionError)
        bank=method_account
    elif bank_account:
        configured=frappe.db.get_value('Branch',doc.cc_center,'cc_bank_account',for_update=True)
        if not configured or frappe.db.get_value('Bank Account',configured,'account')!=bank_account:
            frappe.throw('Il conto dell’incasso deve corrispondere al conto configurato per la sede.',frappe.PermissionError)
        bank=bank_account
    else:
        bank=settings.bank_account or company.default_cash_account
    payload=[name,str(amount),str(posting_date),reference,bank_account]
    if selected_mode:
        payload.append(selected_mode)
    fingerprint=sha256(serialize(payload).encode()).hexdigest()
    existing=frappe.db.get_value('Payment Entry',{'cc_request_key':key('receipt',request_key)},for_update=True)
    if existing:
        payment=frappe.get_doc('Payment Entry',existing)
        if payment.cc_request_hash!=fingerprint:
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return {'payment':existing,'invoice':result(doc,True)}
    from math import isfinite
    amount=frappe.utils.flt(amount,2)
    if not isfinite(amount):
        frappe.throw('Indica un importo di incasso valido.')
    if doc.docstatus!=1 or doc.is_return or amount<=0 or amount>doc.outstanding_amount:
        frappe.throw('L’incasso deve essere positivo e non superare il residuo aperto.')
    before_outstanding=doc.outstanding_amount
    from centrochange_core.finance.native_adapter import payment_document
    payment=payment_document(doc,amount,bank,selected_mode)
    payment.update({'posting_date':posting_date,'reference_no':reference or request_key,'reference_date':posting_date,
        'cc_center':doc.cc_center,'cc_request_key':key('receipt',request_key),'cc_request_hash':fingerprint})
    with internal_write('cc_accounting_write'):
        payment.insert(ignore_permissions=True); payment.submit()
    append('RECEIPT_POSTED',payment.doctype,payment.name,{'invoice':name,'outstanding':before_outstanding},
        {'invoice':name,'allocated':amount,'outstanding':frappe.db.get_value('Sales Invoice',name,'outstanding_amount')},reason)
    return {'payment':payment.name,'invoice':result(doc)}


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(name,reason):
    lock(); require_synthetic(); doc=invoice(name,True)
    if doc.docstatus==2:
        return result(doc,True)
    if doc.docstatus!=1:
        frappe.throw('Puoi annullare solo una fattura nativa contabilizzata.')
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
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return result(doc,True)
    if original.docstatus!=1 or original.is_return:
        frappe.throw('Seleziona una fattura originale contabilizzata.')
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
        frappe.throw('Le modifiche contabili richiedono il servizio verificato e tracciato.',frappe.PermissionError)
    if doc.doctype=='Sales Invoice':
        if doc.patient or any(i.reference_dt or i.reference_dn for i in doc.items):
            frappe.throw('La fatturazione clinica nativa non è prevista dal collegamento contabile.')
        if not doc.cc_center or doc.cc_fiscal_profile!='SYNTHETIC_UNVERIFIED':
            frappe.throw('È obbligatorio un contesto contabile sintetico.')
        for item in doc.items:
            source=frappe.get_doc('CC Economic Source Link',item.cc_economic_source)
            if (source.center,source.customer,source.company,source.currency)!=(doc.cc_center,doc.customer,doc.company,doc.currency) or item.item_code!=source.service_item or abs(item.qty)!=1 or item.rate!=source.price or item.cost_center!=source.cost_center:
                frappe.throw('La riga fattura deve conservare la fonte economica originale.')


@frappe.whitelist(methods=['GET'])
def candidates(center,from_date,to_date):
    require_finance(center)
    start,end=frappe.utils.getdate(from_date),frappe.utils.getdate(to_date)
    if start>end or (end-start).days>366:
        frappe.throw('Seleziona un periodo contabile di massimo 366 giorni.')
    rows=frappe.get_all('Patient Appointment',filters={'cc_center':center,'cc_economic_state':'Due',
        'appointment_date':['between',[start,end]]},fields=['name','patient','appointment_date','cc_price_snapshot','cc_currency_snapshot'],limit_page_length=501)
    if len(rows)>500:
        frappe.throw('Riduci il periodo contabile selezionato.')
    active={r[0] for r in frappe.db.sql('''select distinct s.appointment from `tabSales Invoice Item` i
        join `tabSales Invoice` p on p.name=i.parent join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
        where p.cc_center=%s and p.docstatus<2 and p.is_return=0''',(center,))}
    return {'candidates':[r for r in rows if r.name not in active],'period':[start,end]}


@frappe.whitelist(methods=['POST'])
@atomic
def amend(name,posting_date,due_date,request_key,reason):
    lock(); require_synthetic(); original=invoice(name,True)
    if original.docstatus!=2 or original.is_return:
        frappe.throw('Puoi rettificare solo una fattura originale nativa annullata.')
    existing=frappe.db.get_value('Sales Invoice',{'cc_request_key':key('amend',request_key)},for_update=True)
    if existing:
        doc=invoice(existing,True)
        if doc.amended_from!=name or str(doc.posting_date)!=str(posting_date) or str(doc.due_date)!=str(due_date):
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return result(doc,True)
    doc=frappe.copy_doc(original)
    doc.update({'docstatus':0,'amended_from':name,'posting_date':posting_date,'due_date':due_date,
        'cc_request_key':key('amend',request_key),'cc_request_hash':None})
    reset_amendment_due(doc,due_date)
    for item in original.items:
        source=frappe.get_doc('CC Economic Source Link',item.cc_economic_source)
        if frappe.db.get_value('Patient Appointment',source.appointment,'cc_economic_state',for_update=True)!='Due':
            frappe.throw('Una seduta con rinuncia economica o non dovuta non può essere rifatturata.')
        if frappe.db.sql('''select i.name from `tabSales Invoice Item` i join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source where s.appointment=%s and p.docstatus<2
            and p.is_return=0 limit 1 for update''',(source.appointment,)):
            frappe.throw('La seduta ha già una fattura sostitutiva attiva.')
    with internal_write('cc_accounting_write'):
        doc.insert(ignore_permissions=True)
    append('RECEIVABLE_AMENDED',doc.doctype,doc.name,{'amended_from':name},{'sources':[i.cc_economic_source for i in doc.items]},reason)
    return result(doc)


class InvoiceMixin:
    @frappe.whitelist()
    def set_healthcare_services(self,checked_values):
        frappe.throw('Usa fonti economiche verificate e non modificabili.',frappe.PermissionError)


def reset_amendment_due(doc,due_date):
    # The approved core uses one explicit ordinary deadline, not inferred installments.
    if len(doc.payment_schedule)>1:
        frappe.throw('Una rettifica in più rate richiede un piano di pagamento verificato.')
    mode=doc.payment_schedule[0].mode_of_payment if doc.payment_schedule else None
    doc.payment_terms_template=None
    doc.set('payment_schedule',[{'due_date':due_date,'invoice_portion':100,'mode_of_payment':mode}])
