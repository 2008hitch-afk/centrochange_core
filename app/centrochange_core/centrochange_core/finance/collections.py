"""Approved payment agreements, retained debt and explicit temporary overrides."""
from datetime import datetime,time,timedelta
from calendar import monthrange
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,is_manager,centers,names_condition
from centrochange_core.finance.guards import require_finance,patient_context,allowed,require_synthetic
from centrochange_core.operations.lifecycle import ROME,now_utc,start_utc


@frappe.whitelist(methods=['POST'])
@atomic
def agree(patient,center,mode,reason,due_date=None):
    lock(); require_synthetic(); patient_context(patient,center,True)
    if mode not in ('Immediate','Month End','Specific Date'):
        frappe.throw('Choose an explicit supported payment agreement')
    if mode=='Specific Date':
        if not due_date or frappe.utils.getdate(due_date)<now_utc().astimezone(ROME).date():
            frappe.throw('An agreed current/future payment date is required')
        due_date=frappe.utils.getdate(due_date)
    elif due_date:
        frappe.throw('Only a specific-date agreement accepts an explicit date')
    previous=_agreement(patient,center)
    if previous and previous.mode==mode and str(previous.due_date or '')==str(due_date or ''):
        return {'name':previous.name,'replay':True}
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Payment Agreement','patient':patient,'center':center,'mode':mode,
            'due_date':due_date,'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    append('PAYMENT_AGREEMENT_RECORDED',doc.doctype,doc.name,{'previous':previous.name} if previous else None,
        {'mode':mode,'due_date':due_date},reason)
    return {'name':doc.name,'replay':False}


def _agreement(patient,center):
    rows=current_rows('CC Payment Agreement',{'patient':patient,'center':center},fields=['name','mode','due_date','creation'])
    return max(rows,key=lambda row:(row.creation,row.name)) if rows else None


def _deferred(doctype,name):
    rows=current_rows('CC Payment Override',{'reference_doctype':doctype,'reference_name':name},fields=['name','due_date','creation'])
    return max(rows,key=lambda row:(row.creation,row.name)) if rows else None


def _end_date(date):
    return datetime.combine(frappe.utils.getdate(date),time.max).replace(tzinfo=ROME)


def _debts(patient,center):
    rows=current_rows('Patient Appointment',{'patient':patient,'cc_center':center,'cc_economic_state':'Due'},
        fields=['name','appointment_date','appointment_time','duration','cc_price_snapshot','cc_currency_snapshot','cc_paid','cc_closure_state','cc_payment_terms_mode','cc_payment_agreed_date'])
    debts=[]; seen=set()
    for row in rows:
        links=frappe.db.sql('''select distinct p.name,p.outstanding_amount,p.due_date,p.currency,p.customer
            from `tabSales Invoice` p join `tabSales Invoice Item` i on i.parent=p.name
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus=1 and p.is_return=0'''+(' for update' if frappe.flags.get('cc_permission_current_read') else ''),(row.name,),as_dict=True)
        if links:
            for invoice in links:
                if invoice.name in seen or invoice.outstanding_amount<=0:
                    continue
                seen.add(invoice.name)
                override=_deferred('Sales Invoice',invoice.name)
                deadline=_end_date(override.due_date if override else invoice.due_date)
                debts.append({'doctype':'Sales Invoice','name':invoice.name,'amount':invoice.outstanding_amount,
                    'currency':invoice.currency,'original_due_date':invoice.due_date,'due_date':deadline.date(),'deadline':deadline,'override':override.name if override else None})
            # After posting, accounting balance is authoritative, including paid/credited originals.
            continue
        if row.cc_price_snapshot<=0 or row.cc_paid or row.cc_closure_state not in ('Closed','Auto Locked'):
            continue
        override=_deferred('Patient Appointment',row.name)
        if row.cc_payment_terms_mode=='Month End':
            date=frappe.utils.getdate(row.appointment_date)
            deadline=_end_date(date.replace(day=monthrange(date.year,date.month)[1]))
        elif row.cc_payment_terms_mode=='Specific Date':
            if not row.cc_payment_agreed_date and not override:
                frappe.throw('Specific payment terms require their immutable agreed date')
            deadline=_end_date(row.cc_payment_agreed_date) if row.cc_payment_agreed_date else None
        else:
            deadline=(start_utc(frappe._dict(row))+timedelta(minutes=frappe.utils.flt(row.duration))).astimezone(ROME)
        original_due_date=deadline.date() if deadline else None
        if override:deadline=_end_date(override.due_date)
        debts.append({'doctype':'Patient Appointment','name':row.name,'amount':row.cc_price_snapshot,
            'currency':row.cc_currency_snapshot,'original_due_date':original_due_date,'due_date':deadline.date(),'deadline':deadline,'override':override.name if override else None})
    return debts


@frappe.whitelist(methods=['GET'])
def position(patient,center):
    patient_context(patient,center)
    at=now_utc().astimezone(ROME)
    debts=_debts(patient,center)
    return {'patient':patient,'center':center,'blocked':any(d['deadline']<at for d in debts),
        'debts':[{k:v for k,v in d.items() if k!='deadline'} for d in debts],
        'agreement':_agreement(patient,center)}


def _booking_debts(patient):
    # Shared Patient identity: changing center must not bypass a previous-session hold.
    scopes=current_rows('Patient Appointment',{'patient':patient,'cc_economic_state':'Due'},pluck='cc_center')
    return [debt for center in sorted({c for c in scopes if c}) for debt in _debts(patient,center)]


def require_booking(doc):
    # Generic authorization runs first; this hook reveals no fiscal/clinical detail to a professional.
    at=start_utc(doc).astimezone(ROME)
    if any(d['name']!=doc.name and d['deadline']<at for d in _booking_debts(doc.patient)):
        frappe.throw('Payment review required before a subsequent session; contact secretariat')


@frappe.whitelist(methods=['POST'])
@atomic
def override(patient,center,reference_doctype,reference_name,due_date,request_key,reason):
    lock(); require_synthetic(); patient_context(patient,center,True)
    if not reason or not reason.strip():
        frappe.throw('A business reason is required')
    if not due_date:
        frappe.throw('A new explicit due date is required')
    due=frappe.utils.getdate(due_date)
    if due<now_utc().astimezone(ROME).date():
        frappe.throw('An authorized current/future new due date is required')
    identity=sha256(serialize([frappe.session.user,request_key]).encode()).hexdigest()
    if not request_key or len(str(request_key))>160:
        frappe.throw('A bounded idempotency key is required')
    fingerprint=sha256(serialize([patient,center,reference_doctype,reference_name,str(due),reason]).encode()).hexdigest()
    existing=frappe.db.get_value('CC Payment Override',{'request_key':identity},for_update=True)
    if existing:
        if frappe.db.get_value('CC Payment Override',existing,'request_hash')!=fingerprint:
            frappe.throw('Idempotency key payload differs')
        return {'name':existing,'replay':True}
    debt=next((d for d in _debts(patient,center) if d['doctype']==reference_doctype and d['name']==reference_name),None)
    if not debt or due<=debt['due_date']:
        frappe.throw('Choose an open debt and extend its effective due date')
    with internal_write('cc_operation_write'):
        doc=frappe.get_doc({'doctype':'CC Payment Override','patient':patient,'center':center,
            'reference_doctype':reference_doctype,'reference_name':reference_name,'due_date':due,'reason':reason,
            'recorded_by':frappe.session.user,'request_key':identity,'request_hash':fingerprint}).insert(ignore_permissions=True)
    append('PAYMENT_BLOCK_OVERRIDDEN',doc.doctype,doc.name,{'reference':reference_name,'due_date':debt['due_date']},
        {'due_date':due,'debt_retained':True},reason)
    return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def refresh(patient,center,reason):
    lock(); require_synthetic(); patient_context(patient,center,True)
    return _notice(patient,center,reason)


def _notice(patient,center,reason):
    at=now_utc().astimezone(ROME)
    overdue=[d for d in _debts(patient,center) if d['deadline']<at]
    if not overdue:
        return {'blocked':False,'notice':None}
    identity=sha256(serialize([patient,center,[(d['doctype'],d['name'],str(d['due_date']),d['override']) for d in overdue]]).encode()).hexdigest()
    existing=frappe.db.get_value('CC Payment Notice',{'event_key':identity},for_update=True)
    if existing:
        return {'blocked':True,'notice':existing,'replay':True}
    email=frappe.db.get_value('Patient',patient,'email')
    if email and not email.lower().endswith('@example.invalid'):
        frappe.throw('DEV payment email accepts only synthetic example.invalid recipients',frappe.PermissionError)
    amounts='; '.join(f"{debt['amount']:.2f} {debt['currency']} — scadenza {debt['due_date']}" for debt in overdue)
    native_bank=frappe.db.get_value('Branch',center,'cc_bank_account')
    bank_name=frappe.db.get_value('Bank Account',native_bank,'bank') if native_bank else None
    instruction=f'Bonifico DEV simulato: {bank_name}.' if bank_name else 'Istruzioni di pagamento DEV presso la segreteria.'
    message=f'Prima di una seduta successiva è richiesta la verifica del pagamento. Importi aperti: {amounts}. {instruction}'
    with internal_write('cc_operation_write'):
        notice=frappe.get_doc({'doctype':'CC Payment Notice','patient':patient,'center':center,'event_key':identity,
            'recipient_email':email,'email_state':'SIMULATED' if email else 'Email Unavailable',
            'subject':'Centro Change DEV payment review','message':message}).insert(ignore_permissions=True)
    if email:
        # Native local draft/trace only: no Email Queue, SMTP, gateway or fabricated delivery.
        communication=frappe.get_doc({'doctype':'Communication','communication_type':'Communication',
            'communication_medium':'Email','sent_or_received':'Sent','recipients':email,
            'subject':notice.subject,'content':message,'reference_doctype':notice.doctype,'reference_name':notice.name,
            'status':'Linked'}).insert(ignore_permissions=True)
        frappe.db.set_value(notice.doctype,notice.name,'communication',communication.name)
    from centrochange_core.operations.automation import enqueue_notice
    users=current_rows('CC Center Membership',{'center':center,'active':1},pluck='user')
    from centrochange_core.security.guards import roles,enabled
    for user in users:
        if enabled(user) and 'CC Secretariat' in roles(user):
            enqueue_notice('payment-block:'+identity+':'+user,user,'Payment Block',notice.doctype,notice.name,message)
    append('PAYMENT_BLOCK_NOTIFIED',notice.doctype,notice.name,None,{'email_state':notice.email_state},reason)
    return {'blocked':True,'notice':notice.name,'replay':False}


@atomic
def catch_up():
    require_synthetic()
    from centrochange_core.operations.install import AUTOMATION_USER
    previous=frappe.session.user
    try:
        frappe.set_user(AUTOMATION_USER); lock()
        rows=current_rows('Patient Appointment',{'cc_economic_state':'Due'},fields=['patient','cc_center'])
        count=0
        for patient,center in sorted({(r.patient,r.cc_center) for r in rows}):
            notice=_notice(patient,center,'Scheduled payment-rule catch-up')
            count+=int(bool(notice.get('notice')) and not notice.get('replay',False))
        return {'notices':count}
    finally:
        frappe.set_user(previous)


def names(doctype,user=None):
    if is_manager(user):
        return current_rows(doctype,pluck='name')
    if not allowed(user):
        return []
    return current_rows(doctype,{'center':['in',centers(user) or ['']]},pluck='name')


def permission(doc,user=None,ptype=None):
    return True if is_manager(user) else bool(ptype in ('read','select') and doc.name in names(doc.doctype,user))


def agreement_query(user=None):
    return '' if is_manager(user) else names_condition('CC Payment Agreement',names('CC Payment Agreement',user))


def override_query(user=None):
    return '' if is_manager(user) else names_condition('CC Payment Override',names('CC Payment Override',user))


def notice_query(user=None):
    return '' if is_manager(user) else names_condition('CC Payment Notice',names('CC Payment Notice',user))
