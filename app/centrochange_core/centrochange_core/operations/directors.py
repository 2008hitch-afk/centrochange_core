"""Manager-only provisioning of a director with a personal practitioner profile."""
from hashlib import sha256

import frappe
from centrochange_core.scoped_api import bounded, create, deny_extra
from centrochange_core.security.audit import append, atomic, internal_write
from centrochange_core.security.guards import require_operational_center
from centrochange_core.scheduling.public_offer import configured_type


@frappe.whitelist(methods=['POST'])
@atomic
def provision(center, route, email, request_key, reason, **extra):
    """Create one Director, its enabled account, center membership and public route.

    Public availability remains empty until explicitly configured through the
    normal schedule service. No credentials or invitation are sent here.
    """
    deny_extra(extra)
    require_operational_center(center)
    if route not in ('Marco', 'Francesca'):
        frappe.throw('Direttore non autorizzato.', frappe.PermissionError)
    email = bounded(email, 'Email', 140).lower()
    if not frappe.utils.validate_email_address(email):
        frappe.throw('Email non valida')
    if int(frappe.get_system_settings('reset_password_link_expiry_duration') or 0) <= 0:
        frappe.throw('Configura una scadenza positiva per il link di primo accesso.')
    appointment_type = configured_type(frappe.conf.get('cc_public_first_meeting_types'), 'sede')
    if not frappe.db.exists('Appointment Type', appointment_type):
        frappe.throw('Il colloquio gratuito non è configurato.')
    data = {'first_name': route, 'last_name': '', 'status': 'Active',
            'cc_profile_center': center, 'user_id': email}

    def validate(_):
        if frappe.db.exists('User', email) or frappe.db.exists('Healthcare Practitioner', {'user_id': email}):
            frappe.throw('Account già esistente: non è possibile creare un duplicato.')
        if frappe.db.exists('CC Public Booking Route', route):
            frappe.throw('La rotta è già configurata.')

    def prepare(doc):
        from centrochange_core.security.lifecycle import set_membership
        with internal_write('cc_user_roles_write'):
            frappe.get_doc({'doctype': 'User', 'email': email, 'first_name': route,
                            'enabled': 1, 'send_welcome_email': 0,
                            'roles': [{'role': 'CC Manager'}]}).insert(ignore_permissions=True)
        set_membership(email, center, 1, reason)
        doc.flags.ignore_permissions = True

    def after_insert(doc):
        frappe.get_doc({'doctype': 'CC Public Booking Route', 'route': route,
                        'center': center, 'practitioner': doc.name,
                        'appointment_type': appointment_type, 'enabled': 1}).insert(ignore_permissions=True)
        append('DIRECTOR_ACCOUNT_PREPARED', doc.doctype, doc.name, None,
               {'route': route, 'center': center, 'email_hash': sha256(email.encode()).hexdigest()}, reason)

    def replay_guard(doc):
        route_doc = frappe.get_doc('CC Public Booking Route', route)
        if (doc.user_id != email or doc.status != 'Active' or doc.cc_profile_center != center
                or not frappe.db.get_value('User', email, 'enabled')
                or 'CC Manager' not in frappe.get_roles(email)
                or not frappe.db.exists('CC Center Membership', {'user': email, 'center': center, 'active': 1})
                or route_doc.practitioner != doc.name or route_doc.center != center or not route_doc.enabled):
            frappe.throw('Il profilo direttore non è più coerente; verifica i dati.', frappe.PermissionError)

    with internal_write('cc_practitioner_center_write'):
        result = create('director-provision', center, 'Healthcare Practitioner', data, tuple(data),
                        request_key, reason, validate=validate, prepare_insert=prepare,
                        after_insert=after_insert, replay_guard=replay_guard,
                        fingerprint_extra={'route': route, 'appointment_type': appointment_type})
        if not result['replay']:
            from urllib.parse import urlsplit
            reset = urlsplit(frappe.get_doc('User', email)._reset_password(send_email=False))
            if reset.path != '/update-password' or not reset.query.startswith('key='):
                frappe.throw('Impossibile preparare il primo accesso in sicurezza.')
            result['first_access_url'] = '/cc-first-access#' + reset.query
            if getattr(frappe.local, 'request', None):
                frappe.local.response_headers['Cache-Control'] = 'private, no-store, no-cache, max-age=0'
        return result
