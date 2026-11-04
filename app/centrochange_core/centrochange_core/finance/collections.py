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
        frappe.throw('Seleziona un accordo di pagamento supportato.')
    if mode=='Specific Date':
        if not due_date or frappe.utils.getdate(due_date)<now_utc().astimezone(ROME).date():
            frappe.throw('Indica una data di pagamento concordata, odierna o futura.')
        due_date=frappe.utils.getdate(due_date)
    elif due_date:
        frappe.throw('Solo un accordo con data specifica accetta una data esplicita.')
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
        fields=['name','appointment_date','appointment_time','duration','cc_price_snapshot','cc_currency_snapshot','cc_service_label','cc_paid','cc_closure_state','cc_payment_terms_mode','cc_payment_agreed_date'])
    from centrochange_core.finance.operational_receipts import allocated
    amounts=allocated(patient,center)
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
        draft=bool(frappe.db.sql('''select i.name from `tabSales Invoice Item` i
            join `tabSales Invoice` p on p.name=i.parent
            join `tabCC Economic Source Link` s on s.name=i.cc_economic_source
            where s.appointment=%s and p.docstatus=0 and p.is_return=0 limit 1''',(row.name,)))
        remaining=frappe.utils.flt(row.cc_price_snapshot,2)-amounts.get(row.name,0)/100
        if remaining <= 0:
            continue
        override=_deferred('Patient Appointment',row.name)
        if row.cc_payment_terms_mode=='Month End':
            date=frappe.utils.getdate(row.appointment_date)
            deadline=_end_date(date.replace(day=monthrange(date.year,date.month)[1]))
        elif row.cc_payment_terms_mode=='Specific Date':
            if not row.cc_payment_agreed_date and not override:
                frappe.throw('I termini di pagamento devono conservare la data concordata.')
            deadline=_end_date(row.cc_payment_agreed_date) if row.cc_payment_agreed_date else None
        else:
            deadline=(start_utc(frappe._dict(row))+timedelta(minutes=frappe.utils.flt(row.duration))).astimezone(ROME)
        original_due_date=deadline.date() if deadline else None
        if override:deadline=_end_date(override.due_date)
        debts.append({'doctype':'Patient Appointment','name':row.name,'amount':remaining,'appointment_date':row.appointment_date,'service_label':row.cc_service_label,'invoice_draft':draft,
            'currency':row.cc_currency_snapshot,'original_due_date':original_due_date,'due_date':deadline.date(),'deadline':deadline,'override':override.name if override else None})
    return debts


@frappe.whitelist(methods=['GET'])
def position(patient,center):
    patient_context(patient,center)
    at=now_utc().astimezone(ROME)
    debts=_debts(patient,center)
    return {'patient':patient,'center':center,'blocked':False,
        'debts':[{k:v for k,v in d.items() if k!='deadline'} for d in debts],
        'agreement':_agreement(patient,center)}


def _booking_debts(patient):
    # Shared Patient identity: changing center must not bypass a previous-session hold.
    scopes=current_rows('Patient Appointment',{'patient':patient,'cc_economic_state':'Due'},pluck='cc_center')
    return [dict(debt,center=center) for center in sorted({c for c in scopes if c}) for debt in _debts(patient,center)]


def require_booking(doc):
    # Ordinary unpaid balances never prevent scheduling or closure.
    return None


@frappe.whitelist(methods=['POST'])
@atomic
def override(patient,center,reference_doctype,reference_name,due_date,request_key,reason):
    lock(); require_synthetic(); patient_context(patient,center,True)
    if not reason or not reason.strip():
        frappe.throw('Indica il motivo operativo.')
    if not due_date:
        frappe.throw('Indica la nuova scadenza.')
    due=frappe.utils.getdate(due_date)
    if due<now_utc().astimezone(ROME).date():
        frappe.throw('La nuova scadenza autorizzata deve essere odierna o futura.')
    identity=sha256(serialize([frappe.session.user,request_key]).encode()).hexdigest()
    if not request_key or len(str(request_key))>160:
        frappe.throw('Indica un identificativo valido per la richiesta.')
    fingerprint=sha256(serialize([patient,center,reference_doctype,reference_name,str(due),reason]).encode()).hexdigest()
    existing=frappe.db.get_value('CC Payment Override',{'request_key':identity},for_update=True)
    if existing:
        if frappe.db.get_value('CC Payment Override',existing,'request_hash')!=fingerprint:
            frappe.throw('La richiesta è già stata usata con dati diversi.')
        return {'name':existing,'replay':True}
    debt=next((d for d in _debts(patient,center) if d['doctype']==reference_doctype and d['name']==reference_name),None)
    if not debt or due<=debt['due_date']:
        frappe.throw('Seleziona un debito aperto e una scadenza successiva a quella attuale.')
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
    # Historical notices remain intact; ordinary arrears no longer create holds.
    return {'blocked':False,'notice':None}


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
