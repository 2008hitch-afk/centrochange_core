"""Supported website context extension; native authentication/authorization unchanged."""
import frappe


def context(values):
    values.update(app_name='Centro Change', brand_html='Centro Change', footer_powered='Centro Change',
                  base_template_path='templates/cc_web_base.html')
    if frappe.session.user != 'Guest':
        from frappe.sessions import get_csrf_token
        values.csrf_token = get_csrf_token()
    # Native NotPermittedPage uses www/message.html, not www/error.html.
    # Supported context template override changes presentation; HTTP 403 stays native.
    native_message = frappe.local.response.get('context') or {}
    # Pinned renderer merges response.context only AFTER update_website_context.
    action = values.get('primary_action') or native_message.get('primary_action')
    if values.get('template') == 'www/message.html' and str(action or '').startswith('/login'):
        values.update(template='templates/cc_error_page.html', title='Centro Change — Accesso non consentito',
                      cc_error_title='Accesso non consentito', cc_error_action='Accedi',
                      cc_error_message='Il tuo account non è autorizzato ad aprire questa pagina. Accedi con il profilo corretto o contatta il referente del centro.')
    if getattr(frappe.local,'path',None)=='printview' and values.get('body'):
        values.body=localize_print_labels(values.body)
    if getattr(frappe.local,'path',None)=='login':
        values.title='Centro Change — Accesso'
        # Native login macro retains structure/logic; remove the upstream logo source too.
        values.logo='data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg"/%3E'


def client_language():
    # Request-local presentation only, native authentication/printing unchanged.
    if getattr(getattr(frappe.local,'request',None),'path',None) in ('/login','/printview'):
        frappe.local.lang='it'
        # Native safe Jinja globals capture lang when created during auth.
        frappe.local.jenv_restricted=None
        frappe.local.jenv_unrestricted=None


def print_template_locale(jenv, print_format):
    """Supported rendering hook, after native print permission validation.

    Explicit language avoids incidental request-language changes during guards.
    Keep the native format, fields, values, totals and print permission path.
    """
    if getattr(getattr(frappe.local, 'request', None), 'path', None) == '/printview':
        from functools import partial
        jenv.globals['_'] = partial(frappe._, lang='it')
    return None


def localize_print_labels(body):
    """Translate only pinned native template label nodes, never invoice values."""
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(body, 'html.parser')
    labels={'Sales Invoice':'Fattura di vendita','Customer Name:':'Cliente:',
            'Bill to:':'Intestatario:', 'Invoice Number:':'Numero fattura:',
            'Invoice Date:':'Data fattura:', 'Payment Due Date:':'Scadenza pagamento:'}
    for node in soup.select('.invoice-title, .title .info-text'):
        if node.string and node.string.strip() in labels:
            node.string.replace_with(labels[node.string.strip()])
    return str(soup)
