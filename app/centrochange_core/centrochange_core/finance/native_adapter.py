"""Internal service adapters; no public endpoint or native permission grants.

ERPNext 16.50 UI factories require permissions intentionally absent from the
service-only role model. Authorize the actual caller, then construct native
objects; insertion/submission and audit remain in the existing scoped services.
"""
import frappe
from centrochange_core.finance.guards import require_finance, require_synthetic


def sales_taxes(center, company):
    require_finance(center, True)
    if company != require_synthetic() or frappe.db.get_value('Branch', center, 'cc_company') != company:
        frappe.throw('Il contesto fiscale non corrisponde alla sede autorizzata.', frappe.PermissionError)
    settings = frappe.get_doc('CC Finance Settings')
    name = settings.sales_tax_template
    if not name:
        frappe.throw('Verifica il modello fiscale sintetico configurato.')
    template = frappe.get_doc('Sales Taxes and Charges Template', name)
    if template.company != company or template.get('disabled'):
        frappe.throw('Il modello fiscale è fuori dal contesto contabile.', frappe.PermissionError)
    # Native internal row projection; never expose an arbitrary master-name API.
    from erpnext.controllers import accounts_controller
    project = getattr(accounts_controller, '_get_taxes_and_charges', accounts_controller.get_taxes_and_charges)
    return project('Sales Taxes and Charges Template', name)


def payment_mode_account(mode_name, company):
    """Resolve a native payment method to its reviewed account for this company."""
    if not mode_name or not company:
        frappe.throw('Seleziona un metodo di pagamento configurato per la società.')
    mode = frappe.get_doc('Mode of Payment', mode_name)
    if not mode.enabled:
        frappe.throw('Il metodo di pagamento selezionato non è attivo.', frappe.PermissionError)
    rows = [row for row in mode.accounts if row.company == company and row.default_account]
    if len(rows) != 1:
        frappe.throw('Il metodo di pagamento non ha un conto attivo per la società selezionata.')
    account = frappe.get_doc('Account', rows[0].default_account)
    default_currency = frappe.db.get_value('Company', company, 'default_currency')
    if (account.company != company or account.disabled or account.is_group
            or account.account_type not in ('Bank', 'Cash')
            or account.account_currency not in (None, '', default_currency)):
        frappe.throw('Il conto del metodo di pagamento non è valido per la società e la valuta.', frappe.PermissionError)
    return account.name


def payment_mode_for_account(account_name, company):
    """Return a unique enabled native method mapped to an already-selected account."""
    if not account_name or not company:
        return None
    methods=frappe.get_all('Mode of Payment',filters={'enabled':1},pluck='name',limit_page_length=0)
    matches=[]
    for name in methods:
        if frappe.db.exists('Mode of Payment Account',{'parent':name,'company':company,'default_account':account_name}):
            matches.append(name)
    if len(matches)>1:
        frappe.throw('Più metodi di pagamento usano lo stesso conto: seleziona un metodo esplicito.')
    return matches[0] if matches else None


def payment_document(invoice, amount, bank_account, mode_of_payment=None):
    """Unsaved native EUR invoice payment, restricted to reviewed CC documents.

    No user switch, flag-based permission bypass, SQL, or posting here. Native
    Payment Entry validation/GL/ledger posting run in the existing audited service.
    Unsupported FX/installment/discount contexts fail closed instead of inferring
    new semantics. The original service keeps its locking and idempotency checks.
    """
    if invoice.doctype not in ('Sales Invoice', 'Purchase Invoice') or not invoice.get('cc_center'):
        frappe.throw('Seleziona una fattura gestita.', frappe.PermissionError)
    # Resolve authoritative stored facts; never trust an in-memory forged owner/center.
    invoice = frappe.get_doc(invoice.doctype, invoice.name, for_update=True)
    require_finance(invoice.cc_center, True)
    invoice.check_permission('read')
    company = require_synthetic()
    branch = frappe.get_doc('Branch', invoice.cc_center)
    if invoice.company != company or branch.cc_company != company or invoice.cc_fiscal_profile != 'SYNTHETIC_UNVERIFIED':
        frappe.throw('Il contesto del pagamento non corrisponde alla sede autorizzata.', frappe.PermissionError)
    if invoice.doctype == 'Purchase Invoice' and not invoice.cc_incoming_source:
        frappe.throw('È richiesta una fonte ricevuta e verificata.', frappe.PermissionError)
    from math import isfinite
    amount = frappe.utils.flt(amount, 2)
    if not isfinite(amount) or amount <= 0 or invoice.docstatus != 1 or invoice.is_return or amount > invoice.outstanding_amount:
        frappe.throw('Il pagamento non può superare il residuo della fattura contabilizzata.')
    if invoice.currency != 'EUR' or frappe.db.get_value('Company', company, 'default_currency') != 'EUR' or invoice.conversion_rate != 1:
        frappe.throw('Verifica il pagamento in valuta diversa da EUR: non è supportato.')
    if len(invoice.get('payment_schedule') or []) > 1 or invoice.get('discount_amount') or invoice.get('additional_discount_percentage'):
        frappe.throw('Verifica rate o sconti del pagamento: il contesto non è supportato.')
    bank = frappe.get_doc('Account', bank_account)
    if bank.company != company or bank.is_group or bank.disabled or bank.account_type not in ('Bank', 'Cash') or bank.account_currency != 'EUR':
        frappe.throw('Seleziona un conto banca o cassa EUR attivo della stessa società.', frappe.PermissionError)
    receive = invoice.doctype == 'Sales Invoice'
    party_account = invoice.debit_to if receive else invoice.credit_to
    account = frappe.get_doc('Account', party_account)
    if account.company != company or account.account_currency != 'EUR' or account.disabled or account.is_group:
        frappe.throw('Il conto del soggetto fatturato non corrisponde al pagamento.', frappe.PermissionError)
    payment = frappe.new_doc('Payment Entry')
    payment.update({'payment_type': 'Receive' if receive else 'Pay', 'company': company,
        'party_type': 'Customer' if receive else 'Supplier', 'party': invoice.customer if receive else invoice.supplier,
        'cost_center': invoice.get('cost_center') or branch.cc_cost_center,
        'paid_from': party_account if receive else bank.name, 'paid_to': bank.name if receive else party_account,
        'paid_from_account_currency': 'EUR', 'paid_to_account_currency': 'EUR',
        'source_exchange_rate': 1, 'target_exchange_rate': 1,
        'paid_amount': amount, 'received_amount': amount,
        'mode_of_payment': mode_of_payment or invoice.get('mode_of_payment'),
        'letter_head': invoice.get('letter_head')})
    payment.append('references', {'reference_doctype': invoice.doctype, 'reference_name': invoice.name,
        'due_date': invoice.due_date, 'total_amount': invoice.grand_total,
        'outstanding_amount': invoice.outstanding_amount, 'allocated_amount': amount,
        'exchange_rate': 1, 'account': party_account})
    payment.setup_party_account_field()
    payment.set_missing_values()
    payment.set_missing_ref_details()
    payment.set_exchange_rate()
    payment.set_amounts()
    return payment
