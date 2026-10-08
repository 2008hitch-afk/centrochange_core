"""Transport-neutral fictional XML intake and reviewed native payables."""
from decimal import Decimal,InvalidOperation
from hashlib import sha256
from html import escape
import re
from xml.etree import ElementTree as ET
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,is_manager,centers,names_condition
from centrochange_core.finance.guards import require_finance,require_finance_manager,require_synthetic,allowed
from centrochange_core.finance.receivables import key

RAW_FIELDS=('center','company','payload_sha','semantic_key','issuer_id','issuer_name','invoice_number','invoice_date',
    'document_type','currency','net_total','tax_total','total','lines_json')


def _path(root,*parts):
    node=root
    for part in parts:
        node=next((child for child in node if child.tag.rsplit('}',1)[-1]==part),None) if node is not None else None
    return node


def _text(root,*parts,default=None):
    node=_path(root,*parts)
    return (node.text or '').strip() if node is not None else default


def _money(value):
    try:
        amount=Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid numeric source') from None
    if not amount.is_finite() or abs(amount)>Decimal('1000000000000'):
        raise ValueError('Invalid numeric source')
    return amount


def parse(xml):
    if re.search(r'<!\s*(DOCTYPE|ENTITY)|<\?xml-stylesheet',xml,re.I):
        raise ValueError('Unsafe XML construct')
    root=ET.fromstring(xml)
    if root.tag.rsplit('}',1)[-1]!='FatturaElettronica' or len(list(root.iter()))>3000:
        raise ValueError('Unsupported XML envelope')
    header=_path(root,'FatturaElettronicaHeader')
    bodies=[n for n in root if n.tag.rsplit('}',1)[-1]=='FatturaElettronicaBody']
    if header is None or len(bodies)!=1:
        raise ValueError('Exactly one invoice body is supported by the DEV intake')
    body=bodies[0]
    issuer=_text(header,'CedentePrestatore','DatiAnagrafici','IdFiscaleIVA','IdCodice') or _text(header,'CedentePrestatore','DatiAnagrafici','CodiceFiscale')
    receiver=_text(header,'CessionarioCommittente','DatiAnagrafici','IdFiscaleIVA','IdCodice') or _text(header,'CessionarioCommittente','DatiAnagrafici','CodiceFiscale')
    if not issuer or not issuer.startswith('SYNTHETIC') or receiver!='00000000000':
        raise ValueError('Only explicitly fictional issuer and receiver identities are accepted in DEV')
    general=_path(body,'DatiGenerali','DatiGeneraliDocumento')
    number=_text(general,'Numero'); date=_text(general,'Data'); currency=_text(general,'Divisa'); kind=_text(general,'TipoDocumento')
    if not number or len(number)>140 or not date or currency!='EUR':
        raise ValueError('Incomplete or unsupported invoice identity/currency')
    date=str(frappe.utils.getdate(date))
    goods=_path(body,'DatiBeniServizi')
    if goods is None:
        raise ValueError('Invoice lines are required')
    lines=[]; taxes=Decimal(0)
    for node in goods:
        tag=node.tag.rsplit('}',1)[-1]
        if tag=='DettaglioLinee':
            qty=_money(_text(node,'Quantita',default='1'));rate=_money(_text(node,'PrezzoUnitario'));amount=_money(_text(node,'PrezzoTotale'))
            vat=_money(_text(node,'AliquotaIVA',default='0'))
            if qty<=0 or rate<0 or abs(qty*rate-amount)>Decimal('0.01') or vat<0 or _path(node,'ScontoMaggiorazione') is not None:
                raise ValueError('Unsupported invoice line pricing')
            description=_text(node,'Descrizione',default='')
            if len(description)>500 or len(lines)>=100:
                raise ValueError('Invoice lines exceed the bounded DEV intake')
            lines.append({'description':description,'qty':str(qty),'rate':str(rate),'amount':str(amount),'vat_rate':str(vat)})
        elif tag=='DatiRiepilogo':
            taxes+=_money(_text(node,'Imposta',default='0'))
    if not lines or taxes<0:
        raise ValueError('Invoice lines/taxes are required')
    net=sum((_money(line['amount']) for line in lines),Decimal(0))
    total=_money(_text(general,'ImportoTotaleDocumento',default=str(net+taxes)))
    if abs(net+taxes-total)>Decimal('0.01'):
        raise ValueError('Invoice totals differ from retained line/tax facts')
    return {'issuer_id':issuer,'issuer_name':_text(header,'CedentePrestatore','DatiAnagrafici','Anagrafica','Denominazione',default=issuer),
        'invoice_number':number,'invoice_date':date,'document_type':kind,'currency':currency,
        'net_total':float(net),'tax_total':float(taxes),'total':float(total),'lines_json':serialize(lines)}


def source(name,write=False):
    doc=frappe.get_doc('CC Incoming Invoice',name,for_update=True)
    require_finance(doc.center,write)
    return doc


def projection(doc,replay=False):
    doc.reload()
    return {'name':doc.name,'state':doc.state,'problem':doc.problem,'supplier':doc.supplier,
        'purchase_invoice':doc.purchase_invoice,'payload_sha':doc.payload_sha,'replay':replay}


@frappe.whitelist(methods=['POST'])
@atomic
def intake(center,xml,reason):
    lock(); company=require_synthetic(); require_finance(center,True)
    if not isinstance(xml,str) or not xml or len(xml.encode('utf-8'))>1048576:
        frappe.throw('A bounded fictional UTF-8 XML payload is required')
    digest=sha256(xml.encode('utf-8')).hexdigest()
    existing=frappe.db.get_value('CC Incoming Invoice',{'payload_sha':digest},for_update=True)
    if existing:
        return projection(source(existing,True),True)
    try:
        parsed=parse(xml)
        identity=sha256(serialize([company,parsed['issuer_id'],parsed['invoice_number'],parsed['invoice_date'],parsed['document_type']]).encode()).hexdigest()
        duplicate=frappe.db.get_value('CC Incoming Invoice',{'semantic_key':identity},for_update=True)
        if duplicate:
            source(duplicate,True)
            frappe.throw('Invoice identity already has different immutable XML; review an explicit correction')
        state='Needs Supplier Mapping' if parsed['document_type']=='TD01' else 'Unsupported Document'
        problem=None if state=='Needs Supplier Mapping' else 'Document type requires explicit native correction review'
    except (ValueError,ET.ParseError):
        parsed={}; identity=None; state='Invalid Source';problem='Invalid, unsupported or non-fictional XML; no accounting document created'
    with internal_write('cc_incoming_write'):
        doc=frappe.get_doc({'doctype':'CC Incoming Invoice','center':center,'company':company,'payload_sha':digest,
            'semantic_key':identity,**parsed,'state':state,'problem':problem}).insert(ignore_permissions=True)
        # Unknown extension is an attachment, never active/inline XML in a browser.
        payload=frappe.get_doc({'doctype':'File','file_name':'CC-INCOMING-'+digest+'.xml.payload','is_private':1,
            'attached_to_doctype':doc.doctype,'attached_to_name':doc.name,'content':xml}).insert(ignore_permissions=True)
        frappe.db.set_value(doc.doctype,doc.name,'payload_file',payload.name)
    append('INCOMING_XML_RETAINED',doc.doctype,doc.name,None,{'payload_sha':digest,'state':state},reason)
    return projection(doc)


@frappe.whitelist(methods=['POST'])
@atomic
def bind_supplier(name,supplier,reason):
    lock(); require_synthetic(); doc=source(name,True)
    if doc.state not in ('Needs Supplier Mapping','Needs Classification'):
        frappe.throw('Only a valid unprocessed source can be mapped')
    target=frappe.get_doc('Supplier',supplier,for_update=True)
    if not is_manager():
        target.check_permission('read')
    if target.disabled or target.tax_id!=doc.issuer_id:
        frappe.throw('Explicit supplier fiscal identity must match the immutable XML issuer')
    if doc.supplier==supplier:
        return projection(doc,True)
    before=doc.supplier
    with internal_write('cc_incoming_write'):
        doc.supplier=supplier; doc.state='Needs Classification';doc.problem=None;doc.save(ignore_permissions=True)
    append('INCOMING_SUPPLIER_MAPPED',doc.doctype,name,{'supplier':before},{'supplier':supplier},reason)
    return projection(doc)


def invoice(name,write=False):
    doc=frappe.get_doc('Purchase Invoice',name,for_update=True)
    if not doc.cc_center or not doc.cc_incoming_source:
        frappe.throw('A managed native payable is required')
    require_finance(doc.cc_center,write)
    return doc


def balance(doc,replay=False):
    doc.reload()
    return {'name':doc.name,'docstatus':doc.docstatus,'status':doc.status,'total':doc.grand_total,
        'outstanding':doc.outstanding_amount,'currency':doc.currency,'replay':replay}


@frappe.whitelist(methods=['POST'])
@atomic
def draft(name,items,expense_account,posting_date,due_date,request_key,reason,tax_account=None):
    lock(); company=require_synthetic(); doc=source(name,True)
    if isinstance(items,str):
        items=frappe.parse_json(items)
    facts=frappe.parse_json(doc.lines_json or '[]')
    if not isinstance(items,list) or len(items)!=len(facts) or not facts:
        frappe.throw('Review one explicit native purchase item per retained source line')
    fingerprint=sha256(serialize([name,items,expense_account,str(posting_date),str(due_date),tax_account]).encode()).hexdigest()
    existing=frappe.db.get_value('Purchase Invoice',{'cc_request_key':key('payable',request_key)},for_update=True)
    if existing:
        native=invoice(existing,True)
        if native.cc_request_hash!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return balance(native,True)
    if doc.state!='Needs Classification' or not doc.supplier:
        frappe.throw('Complete supplier mapping and classification before drafting')
    if doc.purchase_invoice:
        frappe.throw('Source already has a native payable')
    expense=frappe.get_doc('Account',expense_account)
    if expense.company!=company or expense.disabled or expense.is_group or expense.root_type!='Expense':
        frappe.throw('Review an enabled native expense account for the synthetic company')
    center=frappe.get_doc('Branch',doc.center)
    if center.cc_company!=company or not center.cc_cost_center:
        frappe.throw('Complete the native center accounting mapping')
    rows=[]
    for item_code,fact in zip(items,facts,strict=True):
        item=frappe.get_doc('Item',item_code)
        if item.disabled or item.is_stock_item or not item.is_purchase_item:
            frappe.throw('Review enabled non-stock purchase service items')
        rows.append({'item_code':item.name,'description':escape(fact['description']),'qty':float(_money(fact['qty'])),
            'rate':float(_money(fact['rate'])),'expense_account':expense_account,'cost_center':center.cc_cost_center})
    taxes=[]
    if doc.tax_total:
        if not tax_account:
            frappe.throw('Explicit native tax account classification is required')
        tax=frappe.get_doc('Account',tax_account)
        if tax.company!=company or tax.is_group or tax.disabled or tax.account_type!='Tax':
            frappe.throw('Review an enabled native tax account')
        taxes=[{'charge_type':'Actual','account_head':tax_account,'tax_amount':doc.tax_total,'description':'SYNTHETIC reviewed incoming tax'}]
    with internal_write('cc_accounting_write'):
        native=frappe.get_doc({'doctype':'Purchase Invoice','company':company,'supplier':doc.supplier,'currency':doc.currency,
            'conversion_rate':1,'posting_date':posting_date,'set_posting_time':1,'due_date':due_date,'bill_no':doc.invoice_number,
            'bill_date':doc.invoice_date,'cc_center':doc.center,'cc_incoming_source':doc.name,'cc_request_key':key('payable',request_key),
            'cc_request_hash':fingerprint,'cc_fiscal_profile':'SYNTHETIC_UNVERIFIED','items':rows,'taxes':taxes}).insert(ignore_permissions=True)
    if abs(native.grand_total-doc.total)>0.01:
        frappe.throw('Native draft total differs from immutable XML facts')
    with internal_write('cc_incoming_write'):
        doc.purchase_invoice=native.name;doc.state='Drafted';doc.reviewed_by=frappe.session.user;doc.save(ignore_permissions=True)
    append('PAYABLE_DRAFT_REVIEWED',native.doctype,native.name,None,{'source':name,'supplier':doc.supplier,'total':native.grand_total},reason)
    return balance(native)


@frappe.whitelist(methods=['POST'])
@atomic
def submit(name,reason):
    lock(); require_synthetic(); native=invoice(name,True)
    if native.docstatus==1:
        return balance(native,True)
    if native.docstatus!=0:
        frappe.throw('Explicitly review a native payable draft before posting')
    with internal_write('cc_accounting_write'):
        native.flags.ignore_permissions=True; native.submit()
    doc=source(native.cc_incoming_source,True)
    with internal_write('cc_incoming_write'):
        doc.state='Submitted';doc.save(ignore_permissions=True)
    append('PAYABLE_SUBMITTED',native.doctype,name,{'docstatus':0},{'docstatus':1},reason)
    return balance(native)


@frappe.whitelist(methods=['POST'])
@atomic
def pay(name,amount,posting_date,request_key,reason,reference=None,bank_account=None):
    lock(); require_synthetic(); native=invoice(name,True)
    fingerprint=sha256(serialize([name,str(amount),str(posting_date),reference,bank_account]).encode()).hexdigest()
    existing=frappe.db.get_value('Payment Entry',{'cc_request_key':key('supplier-payment',request_key)},for_update=True)
    if existing:
        payment=frappe.get_doc('Payment Entry',existing)
        if payment.cc_request_hash!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return {'payment':existing,'invoice':balance(native,True)}
    from math import isfinite
    amount=frappe.utils.flt(amount,2)
    if not isfinite(amount) or native.docstatus!=1 or native.is_return or amount<=0 or amount>native.outstanding_amount:
        frappe.throw('Supplier payment must allocate a positive finite amount within native open balance')
    company=frappe.get_doc('Company',native.company)
    settings=frappe.get_doc('CC Finance Settings')
    bank=bank_account or settings.bank_account or company.default_cash_account
    if bank_account:
        configured=frappe.db.get_value('Branch',native.cc_center,'cc_bank_account',for_update=True)
        if not configured or frappe.db.get_value('Bank Account',configured,'account')!=bank_account:
            frappe.throw('Payment bank must match the configured center account',frappe.PermissionError)
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    payment=get_payment_entry('Purchase Invoice',name,party_amount=amount,bank_account=bank,bank_amount=amount)
    payment.update({'posting_date':posting_date,'reference_no':reference or request_key,'reference_date':posting_date,
        'cc_center':native.cc_center,'cc_request_key':key('supplier-payment',request_key),'cc_request_hash':fingerprint})
    with internal_write('cc_accounting_write'):
        payment.insert(ignore_permissions=True);payment.submit()
    append('SUPPLIER_PAYMENT_POSTED',payment.doctype,payment.name,None,{'invoice':name,'allocated':amount},reason)
    return {'payment':payment.name,'invoice':balance(native)}


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(name,reason):
    lock(); require_synthetic(); native=invoice(name,True)
    if native.docstatus==2:
        return balance(native,True)
    if native.docstatus!=1:
        frappe.throw('Only a submitted native payable can be cancelled')
    with internal_write('cc_accounting_write'):
        native.flags.ignore_permissions=True;native.cancel()
    doc=source(native.cc_incoming_source,True)
    with internal_write('cc_incoming_write'):
        doc.state='Cancelled';doc.save(ignore_permissions=True)
    append('PAYABLE_CANCELLED',native.doctype,name,{'docstatus':1},{'docstatus':2},reason)
    return balance(native)


@frappe.whitelist(methods=['GET'])
def position(name):
    return balance(invoice(name))


def protected_source(doc,method=None):
    if method=='on_trash' or not frappe.flags.get('cc_incoming_write'):
        frappe.throw('Incoming fiscal sources are retained and service-controlled',frappe.PermissionError)
    old=doc.get_doc_before_save()
    if old and any(serialize(doc.get(field))!=serialize(old.get(field)) for field in RAW_FIELDS):
        frappe.throw('Incoming fiscal payload and extracted source facts are immutable')
    if old and old.payload_file and doc.payload_file!=old.payload_file:
        frappe.throw('Immutable payload reference cannot change')


def protected_invoice(doc,method=None):
    if not frappe.flags.get('cc_accounting_write'):
        frappe.throw('Payable mutations require explicit audited review',frappe.PermissionError)
    src=frappe.get_doc('CC Incoming Invoice',doc.cc_incoming_source)
    if (doc.cc_center,doc.company,doc.supplier,doc.currency)!=(src.center,src.company,src.supplier,src.currency) or doc.cc_fiscal_profile!='SYNTHETIC_UNVERIFIED':
        frappe.throw('Native payable must retain the reviewed immutable source context')
    facts=frappe.parse_json(src.lines_json)
    if len(doc.items)!=len(facts) or any(abs(item.qty-float(_money(fact['qty'])))>0.000001 or abs(item.rate-float(_money(fact['rate'])))>0.000001 for item,fact in zip(doc.items,facts,strict=True)):
        frappe.throw('Native payable quantities/rates must retain XML source facts')
    if abs(doc.grand_total-src.total)>0.01:
        frappe.throw('Native payable total must retain XML source facts')


def names(user=None):
    if is_manager(user):
        return current_rows('CC Incoming Invoice',pluck='name')
    if not allowed(user):
        return []
    return current_rows('CC Incoming Invoice',{'center':['in',centers(user) or ['']]},pluck='name')


def query(user=None):
    return '' if is_manager(user) else names_condition('CC Incoming Invoice',names(user))


def permission(doc,user=None,ptype=None):
    return True if is_manager(user) else bool(ptype in ('read','select') and doc.name in names(user))


@frappe.whitelist(methods=['POST'])
@atomic
def amend(name,expense_account,posting_date,due_date,request_key,reason):
    lock(); require_synthetic(); original=invoice(name,True)
    if original.docstatus!=2 or original.is_return:
        frappe.throw('Only a cancelled original native payable can be amended')
    fingerprint=sha256(serialize([name,expense_account,str(posting_date),str(due_date)]).encode()).hexdigest()
    existing=frappe.db.get_value('Purchase Invoice',{'cc_request_key':key('payable-amend',request_key)},for_update=True)
    if existing:
        native=invoice(existing,True)
        if native.cc_request_hash!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return balance(native,True)
    doc=source(original.cc_incoming_source,True)
    if doc.state!='Cancelled' or doc.purchase_invoice!=name:
        frappe.throw('Source already has an active replacement payable')
    expense=frappe.get_doc('Account',expense_account)
    if expense.company!=original.company or expense.is_group or expense.disabled or expense.root_type!='Expense':
        frappe.throw('Explicitly review a native expense classification')
    native=frappe.copy_doc(original)
    native.update({'docstatus':0,'amended_from':name,'posting_date':posting_date,'due_date':due_date,
        'cc_request_key':key('payable-amend',request_key),'cc_request_hash':fingerprint})
    for item in native.items:
        item.expense_account=expense_account
    with internal_write('cc_accounting_write'):
        native.insert(ignore_permissions=True)
    with internal_write('cc_incoming_write'):
        doc.purchase_invoice=native.name;doc.state='Drafted';doc.reviewed_by=frappe.session.user;doc.save(ignore_permissions=True)
    append('PAYABLE_AMENDED',native.doctype,native.name,{'amended_from':name},{'source':doc.name,'expense_account':expense_account},reason)
    return balance(native)
