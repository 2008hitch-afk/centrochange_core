"""Supported website context extension; native authentication/authorization unchanged."""
import frappe
import re


def context(values):
    values.update(app_name='Centro Change', brand_html='Centro Change', footer_powered='Centro Change',
                  base_template_path='templates/cc_web_base.html')
    # Frappe 16.50 renders this image in desk.html before app_include_js runs,
    # and in login.js immediately after successful authentication. A client
    # CSS or post-render DOM fix cannot prevent the upstream splash flash.
    roles = set(frappe.get_roles(frappe.session.user)) if frappe.session.user != 'Guest' else set()
    if getattr(frappe.local, 'path', None) == 'login' or roles.intersection(
        {'CC Manager', 'CC Secretariat', 'CC Professional', 'CC Finance', 'CC Accountant'}
    ):
        values.splash_image = '/assets/centrochange_core/images/centrochange-wordmark.svg'
        values.favicon = '/assets/centrochange_core/images/centrochange-wordmark.svg'
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
    # get_print() also renders printview inside an API request. In that case
    # frappe.local.path remains the API path; the renderer context is decisive.
    if values.get('doctype') == 'Sales Invoice' and values.get('body'):
        values.body = localize_print_labels(values.body, frappe.form_dict.get('name'))
    if getattr(frappe.local,'path',None)=='login':
        values.title='Centro Change — Accesso'
        values.cc_login_ui=True
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
    if frappe.form_dict.get('doctype') == 'Sales Invoice' and frappe.local.lang == 'it':
        from functools import partial
        jenv.globals['_'] = partial(frappe._, lang='it')
    return None


def localize_print_labels(body, invoice_name=None):
    """Localize the rendered v16 invoice print without changing its document.

    Standard and builder print formats use different markup. Only exact label
    nodes and the designated in-words value are changed; amounts, ledger
    values, invoice identifiers and the stored ``in_words`` remain untouched.
    """
    from bs4 import BeautifulSoup
    from decimal import Decimal, ROUND_HALF_UP
    from num2words import num2words

    soup = BeautifulSoup(body, 'html.parser')
    labels = {
        'Sales Invoice': 'Fattura paziente', 'Billed To': 'Intestatario',
        'Customer Name': 'Cliente', 'Bill To': 'Intestatario',
        'Bill From': 'Emessa da', 'Invoice Number': 'Numero fattura',
        'Invoice Date': 'Data fattura', 'Payment Due Date': 'Scadenza',
        'Subtotal': 'Subtotale', 'Sub Total': 'Subtotale',
        'Grand Total': 'Totale', 'No.': 'N.', 'No': 'N.',
        'Quantity': 'Quantità', 'Rate': 'Prezzo unitario',
        'Amount': 'Importo', 'In Words': 'Importo in lettere',
        'Item': 'Servizio', 'Item Code': 'Codice servizio',
        'DRAFT': 'BOZZA', 'CANCELLED': 'ANNULLATA',
    }
    # The pinned standard renderer uses .label/.column-header; the ERPNext
    # invoice formats also emit plain heading spans and table header cells.
    for node in soup.select('.invoice-title, .title .info-text, .heading, '
                            '.label, .section-label, .column-header, '
                            '.table-header td, .totals-table td, '
                            'h1, h2, h3, [document-status] h4'):
        if node.find(True) or not node.string:
            continue
        source = node.string.strip()
        suffix = ':' if source.endswith(':') else ''
        translated = labels.get(source.removesuffix(':'))
        if translated:
            node.string.replace_with(translated + suffix)

    for node in soup.select('[data-fieldname="posting_time"] .value'):
        if node.string and re.fullmatch(r'\d{2}:\d{2}:\d{2}', node.string.strip()):
            node.string.replace_with(node.string.strip()[:5])
    for node in soup.select('td[data-fieldname="item_name"]'):
        if node.string and re.fullmatch(r'CC-HTTP-UAT\d+ Session', node.string.strip()):
            node.string.replace_with('Seduta dimostrativa')

    if invoice_name:
        # The English number in words is stored by ERPNext on submit. Render a
        # localized presentation only for EUR; never rewrite accounting data.
        invoice = frappe.get_doc('Sales Invoice', invoice_name)
        if invoice.currency == 'EUR':
            amount = Decimal(str(invoice.grand_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            words = num2words(f'{amount:.2f}', lang='it', to='currency', currency='EUR')
            for node in soup.select('[data-fieldname="in_words"] .value, .words-box'):
                if node.string and node.string.strip() == str(invoice.in_words or '').strip():
                    node.string.replace_with(words[0].upper() + words[1:] + '.')
    return str(soup)
def login_language():
    # Retained existing #75 hook; no auth/session/user-language mutation.
    if getattr(getattr(frappe.local,'request',None),'path',None)=='/login':
        frappe.local.lang='it'


def client_time_format(bootinfo):
    """Use Frappe's supported boot hook for native client Time controls.

    This changes only the browser display preference. Stored Time fields and
    all API, audit and fiscal formats retain their canonical representation.
    """
    roles = set(frappe.get_roles(frappe.session.user))
    if frappe.session.user != 'Administrator' and roles.intersection(
            {'CC Manager', 'CC Secretariat', 'CC Professional',
             'CC Finance', 'CC Accountant'}):
        bootinfo.sysdefaults['time_format'] = 'HH:mm'
