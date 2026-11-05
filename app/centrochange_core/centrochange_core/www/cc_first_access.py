"""Guest-only first access shell; credentials stay in the URL fragment."""
import frappe

no_cache = True


def get_context(context):
    context.is_guest = frappe.session.user == 'Guest'
    frappe.local.response_headers.update({
        'Cache-Control':'private, no-store, no-cache, max-age=0',
        'Referrer-Policy':'no-referrer',
        'X-Frame-Options':'DENY',
        'Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    })
    return context
