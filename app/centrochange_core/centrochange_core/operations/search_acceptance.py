"""Read-only search boundaries on the preserved Owner demo."""
import frappe
from centrochange_core.operations.workspace import patient_search


def run():
    user=frappe.session.user;checks=[]
    try:
        for role,visible,hidden in [('a','Alfa','Zeta'),('b','Zeta','Alfa'),('c',None,'Alfa'),('s','Alfa',None),('m','Alfa',None)]:
            frappe.set_user('cc-http-uat0000001-'+role+'@example.invalid')
            for name in [visible,hidden]:
                if not name:continue
                rows=patient_search('CC-HTTP-UAT0000001 A',name)['patients']
                if name==visible:assert rows and all(name.lower() in r.patient_name.lower() for r in rows)
                else:assert not rows
            if role not in ['m']:
                try:patient_search('CC-HTTP-UAT0000001 B','')
                except frappe.PermissionError:pass
                else:raise AssertionError('Cross-center search allowed')
            checks.append(role+' name/search scope')
        for role in ['f','t']:
            frappe.set_user('cc-http-uat0000001-'+role+'@example.invalid')
            try:patient_search('CC-HTTP-UAT0000001 A','Alfa')
            except frappe.PermissionError:pass
            else:raise AssertionError('Accounting principal gained operational identity API')
        return {'status':'PASS','checks':checks+['Finance/Accountant retain fiscal reporting identification only']}
    finally:frappe.set_user(user)
