"""Finance mappings use native fields and Cost Center, configured through guarded services."""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure_roles():
    if not frappe.db.exists('Role','CC Accountant'):
        frappe.get_doc({'doctype':'Role','role_name':'CC Accountant','desk_access':1}).insert(ignore_permissions=True)


def configure():
    ensure_roles()
    create_custom_fields({'Branch':[
        {'fieldname':'cc_company','label':'Accounting Company','fieldtype':'Link','options':'Company','read_only':1},
        {'fieldname':'cc_cost_center','label':'Accounting Cost Center','fieldtype':'Link','options':'Cost Center','read_only':1},
        {'fieldname':'cc_bank_account','label':'Native Bank Account','fieldtype':'Link','options':'Bank Account','read_only':1}]})
    fields={dt:[
        {'fieldname':'cc_center','label':'Centro Change Center','fieldtype':'Link','options':'Branch','read_only':1},
        {'fieldname':'cc_request_key','label':'Idempotency Key','fieldtype':'Data','read_only':1,'unique':1},
        {'fieldname':'cc_request_hash','label':'Request Fingerprint','fieldtype':'Data','read_only':1}]
        for dt in ('Sales Invoice','Payment Entry')}
    fields['Patient Appointment']=[{'fieldname':'cc_payment_terms_mode','label':'Payment Terms Snapshot','fieldtype':'Select','options':'Immediate\nMonth End\nSpecific Date','default':'Immediate','read_only':1},
        {'fieldname':'cc_payment_agreed_date','label':'Agreed Payment Date Snapshot','fieldtype':'Date','read_only':1}]
    fields['Bank Account']=[{'fieldname':'cc_center','label':'Centro Change Center','fieldtype':'Link','options':'Branch','read_only':1}]
    fields['Bank Transaction']=[{'fieldname':'cc_center','label':'Centro Change Center','fieldtype':'Link','options':'Branch','read_only':1},
        {'fieldname':'cc_source_key','label':'Movement Source Key','fieldtype':'Data','read_only':1,'unique':1},
        {'fieldname':'cc_source_hash','label':'Immutable Source Hash','fieldtype':'Data','read_only':1}]
    fields['Sales Invoice'].append({'fieldname':'cc_fiscal_profile','label':'DEV Fiscal Profile','fieldtype':'Data','read_only':1})
    fields['Sales Invoice Item']=[{'fieldname':'cc_economic_source','label':'Economic Source','fieldtype':'Link','options':'CC Economic Source Link','read_only':1}]
    create_custom_fields(fields)
    for dt in ('Sales Invoice','Payment Entry','GL Entry','Payment Ledger Entry','Bank Transaction','Bank Account'):
        frappe.db.delete('Custom DocPerm',{'parent':dt})
        for role in ('CC Manager','CC Finance','CC Secretariat','CC Accountant'):
            rights={key:0 for key in ('read','write','create','delete','submit','cancel','amend','report','export','import','share','print','email','select')}
            rights.update({'read':1,'select':1,'report':1,'export':1,'print':1})
            frappe.get_doc({'doctype':'Custom DocPerm','parent':dt,'parenttype':'DocType','parentfield':'permissions',
                'role':role,'permlevel':0,**rights}).insert(ignore_permissions=True)
        frappe.clear_cache(doctype=dt)
    for dt in ('Item','Item Price','Price List','UOM','Mode of Payment'):
        for role in ('CC Manager','CC Secretariat','CC Finance','CC Accountant'):
            if not frappe.db.exists('Custom DocPerm',{'parent':dt,'role':role,'permlevel':0}):
                rights={key:0 for key in ('read','write','create','delete','submit','cancel','amend','report','export','import','share','print','email','select')}
                rights.update({'read':1,'select':1})
                frappe.get_doc({'doctype':'Custom DocPerm','parent':dt,'parenttype':'DocType','parentfield':'permissions',
                    'role':role,'permlevel':0,**rights}).insert(ignore_permissions=True)
        frappe.clear_cache(doctype=dt)
    frappe.db.add_unique('CC Economic Source Link',['source_key'],constraint_name='cc_economic_source_key')
    for doctype in ('Customer','Supplier','Cost Center','Account'):
        frappe.db.delete('Custom DocPerm',{'parent':doctype})
        for role in ('CC Manager','CC Finance','CC Secretariat','CC Accountant'):
            rights={key:0 for key in ('read','write','create','delete','submit','cancel','amend','report','export','import','share','print','email','select')}
            rights.update({'read':1,'select':1})
            if role=='CC Manager':
                rights.update({'write':1,'create':1})
            frappe.get_doc({'doctype':'Custom DocPerm','parent':doctype,'parenttype':'DocType','parentfield':'permissions',
                'role':role,'permlevel':0,**rights}).insert(ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)
