"""Explicit fictional fiscal inputs for DEV evidence, never a production tax policy."""
import frappe
from centrochange_core.finance.guards import require_synthetic,require_finance_manager


def setup(customer):
    require_finance_manager(); company=require_synthetic()
    if not customer or not frappe.db.exists('Customer',customer):
        frappe.throw('A synthetic native customer is required')
    def address(doctype,name):
        existing=frappe.db.get_value('Dynamic Link',{'parenttype':'Address','link_doctype':doctype,'link_name':name},'parent')
        if existing:
            return existing
        return frappe.get_doc({'doctype':'Address','address_title':'SYNTHETIC '+name,'address_type':'Billing',
            'address_line1':'Via SYNTHETIC DEV 0','city':'Roma','state':'Roma','pincode':'00100','country':'Italy',
            'country_code':'IT','is_primary_address':1,'is_your_company_address':int(doctype=='Company'),
            'links':[{'link_doctype':doctype,'link_name':name}]}).insert(ignore_permissions=True).name
    address('Company',company); address('Customer',customer)
    frappe.db.set_value('Company',company,{'fiscal_regime':'RF01','tax_id':'00000000000','fiscal_code':'00000000000'})
    frappe.db.set_value('Customer',customer,{'fiscal_code':'SYNTHETICDEV00000'})
    frappe.clear_document_cache('Company',company); frappe.clear_document_cache('Customer',customer)
    mode='CC DEV PROFILE CASH'
    if not frappe.db.exists('Mode of Payment',mode):
        frappe.get_doc({'doctype':'Mode of Payment','mode_of_payment':mode,'type':'Cash','enabled':1,
            'mode_of_payment_code':'MP01-Contanti','accounts':[{'company':company,'default_account':frappe.db.get_value('Company',company,'default_cash_account')}]}).insert(ignore_permissions=True)
    template='CC SYNTHETIC UNVERIFIED TAX - CCDEV'
    if not frappe.db.exists('Sales Taxes and Charges Template',template):
        tax=frappe.db.get_value('Account',{'company':company,'account_type':'Tax','is_group':0},'name')
        doc=frappe.get_doc({'doctype':'Sales Taxes and Charges Template','title':'CC SYNTHETIC UNVERIFIED TAX','company':company,
            'taxes':[{'charge_type':'On Net Total','account_head':tax,'rate':0,'description':'SYNTHETIC DEV tax input only',
                'tax_exemption_reason':'N2-Non Soggette','tax_exemption_law':'SYNTHETIC UNVERIFIED DEV'}]}).insert(ignore_permissions=True)
        template=doc.name
    settings=frappe.get_doc('CC Finance Settings')
    settings.company=company; settings.sales_tax_template=template; settings.receipt_mode=mode
    settings.fiscal_configuration_verified=0
    settings.save(ignore_permissions=True)
    return {'synthetic':True,'verified':False}
