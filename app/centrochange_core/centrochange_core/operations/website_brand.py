"""Supported website context extension; native authentication/authorization unchanged."""
import frappe


def context(values):
    values.update(app_name='Centro Change', brand_html='Centro Change', footer_powered='Centro Change',
                  base_template_path='templates/cc_web_base.html')
    if frappe.session.user != 'Guest':
        from frappe.sessions import get_csrf_token
        values.csrf_token = get_csrf_token()
    if getattr(frappe.local,'path',None)=='login':
        values.title='Centro Change — Accesso'
        # Native login macro retains structure/logic; remove the upstream logo source too.
        values.logo='data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg"/%3E'
