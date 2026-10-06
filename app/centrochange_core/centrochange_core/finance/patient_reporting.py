"""Patient identities grouped once by fiscal Customer; no inferred allocation."""
from datetime import datetime
from zoneinfo import ZoneInfo
import frappe
from centrochange_core.finance.guards import require_finance,patient_context
from centrochange_core.security.guards import current_rows,is_manager,roles
from centrochange_core.finance.reporting import _bounded,_interval,summary
from centrochange_core.finance import collections


def _groups(center):
    require_finance(center)
    assigned=set(current_rows('CC Patient Assignment',{'center':center,'active':1},pluck='patient'))
    sources=_bounded('CC Economic Source Link',{'center':center},['patient','customer'])
    ids=assigned|{r.patient for r in sources if r.patient}
    patients=_bounded('Patient',{'name':['in',list(ids) or ['']]},['name','patient_name','customer'])
    groups={}
    for p in patients:
        key=p.customer or 'patient:'+p.name
        groups.setdefault(key,{'key':key,'customer':p.customer,'patients':[]})['patients'].append({'name':p.name,'label':p.patient_name,'active':p.name in assigned})
    customers={r.customer for r in sources if r.customer}
    customers.update(current_rows('Sales Invoice',{'cc_center':center},pluck='customer'))
    customers.update(current_rows('Payment Entry',{'cc_center':center,'party_type':'Customer'},pluck='party'))
    for customer in customers:
        if customer:groups.setdefault(customer,{'key':customer,'customer':customer,'patients':[]})
    if len(groups)>500:frappe.throw('Narrow center scope; more than 500 fiscal subjects')
    for g in groups.values():
        g['customer_label']=frappe.db.get_value('Customer',g['customer'],'customer_name') if g['customer'] else 'Soggetto fiscale non collegato'
        # Only a shared-subject flag; no foreign Patient identities/counts are exposed.
        g['shared']=bool(g['customer'] and frappe.db.count('Patient',{'customer':g['customer']})>1)
        g['patients'].sort(key=lambda p:p['label'])
    return groups


def _project(center,start,end,group):
    customer=group['customer'];patient_ids={p['name'] for p in group['patients']}
    # Existing bounded projection owns period money semantics. Never request center
    # money as a substitute when a Patient has no fiscal mapping.
    data=summary(center,start,end,customer=customer) if customer else None
    sessions=data['sessions'] if data else _bounded('Patient Appointment',{'cc_center':center,'patient':['in',list(patient_ids) or ['']],'appointment_date':['between',[start,end]]},['name','appointment_date','appointment_time','status','patient','practitioner','duration','cc_service_label','cc_performed','cc_paid','cc_price_snapshot','cc_currency_snapshot','cc_closure_state','cc_economic_state'])
    sessions=[r for r in sessions if r.patient in patient_ids]
    now=datetime.now(ZoneInfo('Europe/Rome'));counts=dict(sessions=len(sessions),performed=0,cancelled=0,future=0,pending=0,closed_not_performed=0)
    identities={p['name']:p['label'] for p in group['patients']}
    safe_sessions=[]
    for row in sessions:
        at=datetime.combine(frappe.utils.getdate(row.appointment_date),frappe.utils.get_time(row.appointment_time),tzinfo=ZoneInfo('Europe/Rome'))
        category='cancelled' if row.status=='Cancelled' else 'performed' if row.cc_performed else 'future' if at>now else 'closed_not_performed' if row.cc_closure_state=='Closed' else 'pending'
        counts[category]+=1
        doc=frappe.get_doc('Patient Appointment',row.name)
        safe_sessions.append({**dict(row),'patient_label':identities.get(row.patient,'Identità non proiettata'),'category':category,'appointment_time':str(frappe.utils.get_time(row.appointment_time)),'can_open':bool((is_manager() or 'CC Secretariat' in roles()) and doc.has_permission('read'))})
    safe_sessions.sort(key=lambda r:(str(r['appointment_date']),r['appointment_time'],r['name']))
    invoices=[];payments=[];open_rows=[];overdue=[]
    if customer:
        for row in data['sales_invoices']:
            native=frappe.db.get_value('Sales Invoice',row.name,['due_date','payment_terms_template','status'],as_dict=True)
            refs=current_rows('Sales Invoice Item',{'parent':row.name},pluck='cc_economic_source')
            composed=current_rows('CC Economic Source Link',{'name':['in',[ref for ref in refs if ref] or ['']],'center':center,'customer':customer},fields=['name','patient','appointment'])
            invoices.append({**dict(row),**dict(native),'session_links':[{'source':r.name,'appointment':r.appointment,'patient':r.patient if r.patient in patient_ids else None} for r in composed]})
        for row in data['payments']:
            if row.payment_type=='Internal Transfer':continue
            currency=row.paid_to_account_currency if row.payment_type=='Receive' else row.paid_from_account_currency
            if currency!='EUR':frappe.throw('Separate currency reporting required')
            payments.append({**dict(row),'mode_of_payment':frappe.db.get_value('Payment Entry',row.name,'mode_of_payment'),'collected_amount':row.received_amount if row.payment_type=='Receive' else -row.paid_amount})
        open_rows=_bounded('Sales Invoice',{'cc_center':center,'customer':customer,'docstatus':1,'outstanding_amount':['>',0]},['name','posting_date','customer','currency','grand_total','outstanding_amount','due_date','status','payment_terms_template','is_return'])
        for row in open_rows:
            if row.currency!='EUR':frappe.throw('Separate currency reporting required')
            override=collections._deferred('Sales Invoice',row.name)
            row['original_due_date']=row.due_date;row['effective_due_date']=override.due_date if override else row.due_date
            row['deferral']=override.name if override else None
            row['overdue']=bool(row['effective_due_date'] and collections._end_date(row['effective_due_date'])<now)
            if row['overdue']:overdue.append(dict(row))
    positions=[]
    for patient in group['patients']:
        if not patient['active'] and not is_manager():continue
        patient_context(patient['name'],center)
        position=collections.position(patient['name'],center)
        positions.append(position)
    # Operational debts remain a separate collections projection, never added to native outstanding.
    debt_map={}
    for p in positions:
        for debt in p['debts']:
            d=dict(debt);d['patient']=p['patient']
            if d['doctype']=='Sales Invoice':d['original_due_date']=frappe.db.get_value('Sales Invoice',d['name'],'due_date')
            else:d['original_due_date']=d['due_date'] if not d['override'] else None
            debt_map.setdefault((d['doctype'],d['name']),d)
    outstanding=sum(r.outstanding_amount for r in open_rows);overdue_amount=sum(r['outstanding_amount'] for r in overdue)
    blocked=any(p['blocked'] for p in positions);deferred=any(r['deferral'] for r in open_rows) or any(d['override'] for d in debt_map.values())
    due_dates=[frappe.utils.getdate(r['effective_due_date']) for r in open_rows if r['effective_due_date']]
    dates=[d for d in due_dates if d>=now.date()] or due_dates
    state='Blocco prenotazione' if blocked else 'Scaduto' if overdue_amount else 'Differito' if deferred else 'Da incassare' if outstanding else 'Regolare'
    return {**group,'center':center,'start':start,'end':end,'as_of':now.isoformat(),'counts':counts,'sessions':safe_sessions,
        'totals':{'invoiced':sum(r['grand_total'] for r in invoices),'collected':sum(r['collected_amount'] for r in payments),'outstanding':outstanding,'overdue':overdue_amount,'open_invoices':len(open_rows)},
        'invoices':invoices,'payments':payments,'open_invoices':list(map(dict,open_rows)),'overdue_invoices':overdue,'next_due_date':min(dates) if dates else None,'deferred':bool(deferred),'blocked':blocked,'state':state,
        'collections':{'debts':list(debt_map.values()),'patients':[{'patient':p['patient'],'blocked':p['blocked'],'agreement':p['agreement']} for p in positions]},
        'scope_note':'Sedute per data seduta; fatturato lordo firmato e incassi netti Payment Entry per data contabile nel periodo. Incassi includono anticipi/rimborsi, non allocazioni alle fatture. Residuo/scaduto sono la posizione nativa corrente di tutte le fatture aperte del Customer nel centro, anche fuori periodo; non un saldo storico. Debiti operativi e blocco collections restano separati. Soggetto fiscale condiviso: nessuna allocazione a singolo Patient.'}


@frappe.whitelist(methods=['GET'])
def patient_view(center,start,end,key=None,patient=None):
    require_finance(center);start,end=_interval(start,end);groups=_groups(center)
    if patient:
        group=next((g for g in groups.values() if any(p['name']==patient for p in g['patients'])),None)
        if not group:frappe.throw('Patient report context denied',frappe.PermissionError)
        if key and key!=group['key']:frappe.throw('Fiscal report context mismatch',frappe.PermissionError)
        key=group['key']
    if key:
        if key not in groups:frappe.throw('Fiscal subject report context denied',frappe.PermissionError)
        return _project(center,start,end,groups[key])
    rows=[]
    for g in sorted(groups.values(),key=lambda r:r['customer_label'] or r['key']):
        p=_project(center,start,end,g)
        rows.append({k:p[k] for k in ['key','customer','customer_label','patients','shared','counts','totals','next_due_date','deferred','blocked','state']})
    return {'center':center,'start':start,'end':end,'rows':rows,'grouping':'One row per Customer; unmapped Patient has no inferred accounting balance.'}


@frappe.whitelist(methods=['GET'])
def patient_export(center,start,end,key=None,patient=None):
    import csv
    from io import StringIO
    from centrochange_core.operations.reporting import safe_cell
    data=patient_view(center,start,end,key,patient);output=StringIO(newline='');writer=csv.writer(output)
    writer.writerow(['kind','name','date','subject','amount','currency','due_date','effective_due_date'])
    def write(row):writer.writerow([safe_cell(v) for v in row])
    if 'rows' in data:
        for row in data['rows']:write(['Customer position',row['key'],'current',row['customer_label'],row['totals']['outstanding'],'EUR',row['next_due_date'],''])
    else:
        for row in data['sessions']:write(['Session',row['name'],row['appointment_date'],row['patient_label'],row['cc_price_snapshot'],row['cc_currency_snapshot'],'',''])
        for row in data['invoices']:write(['Invoiced',row['name'],row['posting_date'],row['customer'],row['grand_total'],row['currency'],row['due_date'],''])
        for row in data['payments']:write(['Collected',row['name'],row['posting_date'],row['party'],row['collected_amount'],'EUR','',''])
        for row in data['open_invoices']:write(['Outstanding',row['name'],row['posting_date'],row['customer'],row['outstanding_amount'],row['currency'],row['original_due_date'],row['effective_due_date']])
        for row in data['overdue_invoices']:write(['Overdue',row['name'],row['posting_date'],row['customer'],row['outstanding_amount'],row['currency'],row['original_due_date'],row['effective_due_date']])
    frappe.response.update({'type':'download','filename':'patient-customer-report.csv','filecontent':output.getvalue(),'content_type':'text/csv; charset=utf-8'})
