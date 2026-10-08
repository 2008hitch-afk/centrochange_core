import frappe
no_cache=True

def get_context(context):
    from frappe.sessions import get_csrf_token
    context.csrf_token=get_csrf_token()
    context.title='Centro Change — Primo incontro'
