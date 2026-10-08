"""Accounting master lookup is scoped without opening clinical master access."""
import frappe
from centrochange_core.security.guards import current_rows,centers,is_manager,names_condition
from centrochange_core.finance.guards import allowed


def master_names(doctype,user=None):
    if not allowed(user):
        return []
    scopes=centers(user) or ['']
    if doctype=='Customer':
        patients=current_rows('CC Patient Assignment',{'center':['in',scopes]},pluck='patient')
        names=current_rows('Patient',{'name':['in',patients or ['']]},pluck='customer')
        names+=current_rows('CC Economic Source Link',{'center':['in',scopes]},pluck='customer')
    elif doctype=='Supplier':
        users=current_rows('CC Center Membership',{'center':['in',scopes]},pluck='user')
        names=current_rows('Healthcare Practitioner',{'user_id':['in',users or ['']]},pluck='supplier')
        names+=current_rows('CC Economic Source Link',{'center':['in',scopes]},pluck='supplier')
    else:
        names=current_rows('Branch',{'name':['in',scopes]},pluck='cc_cost_center')
    return list({name for name in names if name})


def master_query(doctype,user=None):
    return '' if is_manager(user) else names_condition(doctype,master_names(doctype,user))


def master_permission(doc,user=None,ptype=None):
    return True if is_manager(user) else bool(ptype in ('read','select') and doc.name in master_names(doc.doctype,user))


def customer_query(user=None):
    return master_query('Customer',user)


def supplier_query(user=None):
    return master_query('Supplier',user)


def cost_center_query(user=None):
    return master_query('Cost Center',user)
