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
        {'fieldname':'cc_cost_center','label':'Accounting Cost Center','fieldtype':'Link','options':'Cost Center','read_only':1}]})
    frappe.db.add_unique('CC Economic Source Link',['source_key'],constraint_name='cc_economic_source_key')
    for doctype in ('Customer','Supplier','Cost Center'):
        frappe.db.delete('Custom DocPerm',{'parent':doctype})
        for role in ('CC Manager','CC Finance','CC Secretariat','CC Accountant'):
            rights={key:0 for key in ('read','write','create','delete','submit','cancel','amend','report','export','import','share','print','email','select')}
            rights.update({'read':1,'select':1})
            if role=='CC Manager':
                rights.update({'write':1,'create':1})
            frappe.get_doc({'doctype':'Custom DocPerm','parent':doctype,'parenttype':'DocType','parentfield':'permissions',
                'role':role,'permlevel':0,**rights}).insert(ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)
