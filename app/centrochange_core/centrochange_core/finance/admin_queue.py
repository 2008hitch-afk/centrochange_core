"""Condition-driven administrative work items; lifecycle never erases source facts."""
from hashlib import sha256
import frappe
from centrochange_core.security.audit import atomic,append,internal_write,serialize
from centrochange_core.security.lifecycle import lock
from centrochange_core.security.guards import current_rows,is_manager,centers,names_condition,enabled
from centrochange_core.finance.guards import allowed,require_finance,require_synthetic
from centrochange_core.operations.lifecycle import now_utc


def protected(doc,method=None):
    if method=='on_trash' or not frappe.flags.get('cc_queue_write'):
        frappe.throw('Administrative conditions require audited queue services',frappe.PermissionError)
    old=doc.get_doc_before_save()
    if old and any(doc.get(k)!=old.get(k) for k in ('center','condition_key','exception_type','reference_doctype','reference_name','detected_at')):
        frappe.throw('Administrative condition identity is immutable',frappe.PermissionError)


def _at():return now_utc().replace(tzinfo=None)

def _conditions(center):
    out={}
    def add(kind,dt,name,value):
        key=sha256(serialize([center,kind,dt,name]).encode()).hexdigest()
        out[key]={'center':center,'exception_type':kind,'reference_doctype':dt,'reference_name':name,
            'condition_key':key,'condition_hash':sha256(serialize(value).encode()).hexdigest()}
    for row in current_rows('CC Incoming Invoice',{'center':center},fields=['name','state','problem']):
        if row.state not in ('Submitted','Cancelled'):add('Incoming Invoice Review','CC Incoming Invoice',row.name,[row.state,row.problem])
    for row in current_rows('Bank Transaction',{'cc_center':center,'docstatus':1},fields=['name','unallocated_amount']):
        if row.unallocated_amount>0:add('Unresolved Bank Movement','Bank Transaction',row.name,row.unallocated_amount)
    from centrochange_core.finance.collections import _debts
    patients=current_rows('Patient Appointment',{'cc_center':center},pluck='patient')
    for patient in set(patients):
        for row in _debts(patient,center):
            if row['deadline']<now_utc():add('Overdue Payment',row['doctype'],row['name'],[row['amount'],row['due_date'],row['override']])
    latest={}
    for row in sorted(current_rows('CC Professional Expectation',{'center':center},fields=['name','appointment','state','problem','creation']),key=lambda r:(r.creation,r.name)):
        latest[row.appointment]=row
    for appointment,row in latest.items():
        if row.state=='REVIEW':add('Professional Expectation Review','Patient Appointment',appointment,[row.name,row.problem])
    latest={}
    for row in sorted(current_rows('CC Professional Comparison',{'center':center},fields=['name','purchase_invoice','state','problem','creation']),key=lambda r:(r.creation,r.name)):
        latest[row.purchase_invoice]=row
    for name,row in latest.items():
        if row.state=='REVIEW' and frappe.db.get_value('Purchase Invoice',name,'docstatus')==1:
            add('Professional Invoice Difference','Purchase Invoice',name,[row.name,row.problem])
    for row in current_rows('CC Economic Source Link',{'center':center},fields=['name','appointment','supplier']):
        if not row.supplier:add('Professional Supplier Mapping','CC Economic Source Link',row.name,'Missing historical supplier mapping')
    fiscal_rows=current_rows('CC Fiscal Transaction',{'center':center},fields=['name','domain','status','error_class','corrects'])
    resolved={row.name for row in fiscal_rows if row.status in ('ACCEPTED_OR_DELIVERED','ACCEPTED')}
    # An accepted correction resolves its entire retained ancestor chain, not only its parent.
    while True:
        ancestors={row.corrects for row in fiscal_rows if row.name in resolved and row.corrects}
        if ancestors<=resolved:break
        resolved.update(ancestors)
    for row in fiscal_rows:
        if row.name not in resolved and row.status in ('REJECTED','FAILED_RETRYABLE','FAILED_TERMINAL','CORRECTION_REQUIRED','RETRY_REQUIRED','ELIGIBILITY_PENDING'):
            add(row.domain+' Fiscal Review','CC Fiscal Transaction',row.name,[row.status,row.error_class])
    return out


@frappe.whitelist(methods=['POST'])
@atomic
def refresh(center,reason):
    lock();require_synthetic();require_finance(center,True)
    return _refresh(center,reason)


def _refresh(center,reason):
    at=_at();conditions=_conditions(center)
    existing={d.condition_key:d for d in [frappe.get_doc('CC Admin Exception',n,for_update=True) for n in current_rows('CC Admin Exception',{'center':center},pluck='name')]}
    changed=[]
    with internal_write('cc_queue_write'):
        for key,data in conditions.items():
            doc=existing.get(key)
            if not doc:
                doc=frappe.get_doc({'doctype':'CC Admin Exception',**data,'state':'Open','priority':2,'detected_at':at}).insert(ignore_permissions=True)
                append('ADMIN_EXCEPTION_DETECTED',doc.doctype,doc.name,None,{'state':doc.state,'condition_hash':doc.condition_hash},reason);changed.append(doc.name)
            else:
                before={'state':doc.state,'condition_hash':doc.condition_hash}
                if doc.state=='Closed' or doc.state=='Deferred' and (not doc.defer_until or doc.defer_until<=at):
                    doc.state='Assigned' if doc.assignee else 'Open';doc.defer_until=None;doc.resolved_at=None;doc.resolution_reason=None
                doc.condition_hash=data['condition_hash']
                if before!={'state':doc.state,'condition_hash':doc.condition_hash}:
                    doc.save(ignore_permissions=True);append('ADMIN_EXCEPTION_REFRESHED',doc.doctype,doc.name,before,{'state':doc.state,'condition_hash':doc.condition_hash},reason);changed.append(doc.name)
        for key,doc in existing.items():
            if key not in conditions and doc.state!='Closed':
                before={'state':doc.state};doc.state='Closed';doc.resolved_at=at;doc.defer_until=None;doc.resolution_reason='Underlying condition resolved'
                doc.save(ignore_permissions=True);append('ADMIN_EXCEPTION_AUTO_CLOSED',doc.doctype,doc.name,before,{'state':doc.state},reason);changed.append(doc.name)
    return {'changed':changed,'conditions':len(conditions)}


@frappe.whitelist(methods=['POST'])
@atomic
def manage(name,priority,reason,assignee=None,due_at=None,defer_until=None):
    lock();require_synthetic();doc=frappe.get_doc('CC Admin Exception',name,for_update=True);require_finance(doc.center,True)
    if doc.state=='Closed':frappe.throw('Resolved conditions cannot be manually reopened')
    try:priority=int(priority)
    except (ValueError,TypeError):frappe.throw('Choose a priority from 1 through 4')
    if priority not in (1,2,3,4):frappe.throw('Choose a priority from 1 through 4')
    if assignee and (not enabled(assignee) or not allowed(assignee,True) or not is_manager(assignee) and doc.center not in centers(assignee)):
        frappe.throw('Assignee must be enabled and authorized for center administration',frappe.PermissionError)
    due=frappe.utils.get_datetime(due_at) if due_at else None
    defer=frappe.utils.get_datetime(defer_until) if defer_until else None
    if defer and defer<=_at():frappe.throw('Deferral requires an explicit future UTC timestamp')
    before={k:doc.get(k) for k in ('priority','assignee','due_at','defer_until','state')}
    after={'priority':priority,'assignee':assignee,'due_at':due,'defer_until':defer,'state':'Deferred' if defer else ('Assigned' if assignee else 'Open')}
    if before==after:return {'name':name,'state':doc.state,'replay':True}
    with internal_write('cc_queue_write'):
        doc.update(after);doc.save(ignore_permissions=True)
    append('ADMIN_EXCEPTION_MANAGED',doc.doctype,doc.name,before,after,reason)
    return {'name':name,'state':doc.state,'replay':False}


def names(user=None):
    if not allowed(user):return []
    return current_rows('CC Admin Exception',{} if is_manager(user) else {'center':['in',centers(user) or ['']]},pluck='name')
def query(user=None):return names_condition('CC Admin Exception',names(user))
def permission(doc,user=None,ptype=None):return bool(ptype in ('read','select') and doc.name in names(user))


@frappe.whitelist(methods=['GET'])
def list_items(center,include_closed=0):
    require_finance(center)
    filters={'center':center}
    if not frappe.utils.cint(include_closed):filters['state']=['!=','Closed']
    return current_rows('CC Admin Exception',filters,fields=['name','exception_type','reference_doctype','reference_name','state','priority','assignee','detected_at','due_at','defer_until','resolved_at'])


def catch_up():
    previous=frappe.session.user
    try:
        from centrochange_core.operations.install import AUTOMATION_USER
        require_synthetic();frappe.set_user(AUTOMATION_USER);lock()
        for center in current_rows('Branch',{'cc_company':['is','set']},pluck='name'):
            _refresh(center,'Scheduled administrative condition reconciliation')
    finally:frappe.set_user(previous)
