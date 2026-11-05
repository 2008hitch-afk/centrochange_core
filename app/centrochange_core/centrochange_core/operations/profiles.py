"""Existing operational identities, scoped to an authorized center context."""
import frappe
from centrochange_core.security.audit import atomic
from centrochange_core.scoped_api import bounded, create, deny_extra, manager, mutate, page
from centrochange_core.security.guards import is_manager, patient_contexts, practitioner_for, require_center, require_operational_center, roles


def _atomic_provision(function):
    """Rollback Frappe 16 savepoint callbacks as well as database writes."""
    from functools import wraps
    secured = atomic(function)
    @wraps(function)
    def wrapped(*args, **kwargs):
        hooks = [getattr(frappe.db, name) for name in ('before_commit', 'after_commit', 'before_rollback', 'after_rollback')]
        counts = [len(hook._functions) for hook in hooks]
        try:
            return secured(*args, **kwargs)
        except Exception:
            for hook, count in zip(hooks, counts):
                while len(hook._functions) > count:
                    hook._functions.pop()
            raise
    return wrapped


def _patient(center, doc, allow_historical=False):
    require_center(center)
    active=bool(frappe.db.exists('CC Patient Assignment', {'patient': doc.name, 'center': center, 'active': 1}))
    if not active and not (allow_historical and is_manager() and
            frappe.db.exists('CC Patient Assignment', {'patient': doc.name, 'center': center})):
        frappe.throw('Paziente non disponibile per questo centro', frappe.PermissionError)
    if not is_manager() and (doc.name, center) not in patient_contexts():
        frappe.throw('Paziente non disponibile per questo centro', frappe.PermissionError)
    return active


def _practitioner(center, doc):
    require_center(center)
    require_operational_center(center)
    if doc.get('cc_profile_center') != center and (not doc.user_id or not frappe.db.exists('CC Center Membership', {'user': doc.user_id, 'center': center, 'active': 1})):
        frappe.throw('Professionista non disponibile per questo centro', frappe.PermissionError)
    if not is_manager() and (doc.name != practitioner_for() or 'CC Professional' not in roles()):
        frappe.throw('Professionista non disponibile per questo centro', frappe.PermissionError)


@frappe.whitelist(methods=['GET'])
def patients(center, limit=50, offset=0, search=''):
    limit, offset = page(limit, offset)
    require_center(center)
    search = bounded(search, 'Ricerca', 100, required=False)
    filters = {'center': center}
    if not is_manager():
        filters['active'] = 1
    allowed = frappe.get_all('CC Patient Assignment', filters=filters, pluck='patient')
    if not is_manager():
        allowed = list(set(allowed) & {p for p, c in patient_contexts() if c == center})
    options = {}
    if search:
        needle = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        options['or_filters'] = {field: ['like', needle] for field in ('patient_name', 'first_name', 'last_name', 'email', 'name')}
    # Secretariat/Professional have document-scoped hooks, not a broad native list grant.
    lookup = frappe.get_list if is_manager() else frappe.get_all
    rows = lookup('Patient', filters={'name': ['in', allowed or ['']]},
                  fields=['name', 'patient_name', 'first_name', 'last_name', 'email', 'modified'],
                  order_by='patient_name,name', start=offset, page_length=limit + 1, **options)
    row_names = [row.name if hasattr(row, 'name') else row['name'] for row in rows[:limit]]
    active = set(frappe.get_all('CC Patient Assignment',
        filters={'center': center, 'active': 1, 'patient': ['in', row_names or ['']]},
        pluck='patient'))
    return {'rows': [{**(row if isinstance(row, dict) else vars(row)),
                      'active_assignment': (row.name if hasattr(row, 'name') else row['name']) in active}
                     for row in rows[:limit]],
            'has_more': len(rows) > limit}


@frappe.whitelist(methods=['GET'])
def patient_detail(center, name):
    doc = frappe.get_doc('Patient', bounded(name, 'Paziente'))
    doc.check_permission('read')
    active=_patient(center, doc, allow_historical=True)
    return {**{field: doc.get(field) for field in ('name', 'patient_name', 'first_name', 'last_name', 'email', 'mobile', 'phone', 'modified')},
            **({'cc_ts_preference': doc.get('cc_ts_preference')} if is_manager() else {}),
            'active_assignment':active}


@frappe.whitelist(methods=['POST'])
def patient_save(center, name, first_name, last_name, email, expected_version, request_key, reason, mobile=None, phone=None, ts_preference=None, **extra):
    deny_extra(extra)
    email = bounded(email, 'Email', 140, required=False).lower() if email is not None else None
    if email and not frappe.utils.validate_email_address(email):
        frappe.throw('Email non valida')
    if ts_preference is not None and ts_preference not in ('', 'No Opposition', 'Opposed'):
        frappe.throw('Preferenza TS non valida')
    values = {'first_name': bounded(first_name, 'Nome'), 'last_name': bounded(last_name, 'Cognome', required=False) if last_name is not None else None, 'email': email,
              **({'mobile': bounded(mobile, 'Cellulare', 140, required=False)} if mobile is not None else {}),
              **({'phone': bounded(phone, 'Telefono', 140, required=False)} if phone is not None else {}),
              **({'cc_ts_preference': ts_preference} if ts_preference is not None else {})}
    def audit_preference(doc):
        previous = doc.get_doc_before_save()
        old = (previous.get('cc_ts_preference') or '') if previous else ''
        new = doc.get('cc_ts_preference') or ''
        if ts_preference is not None and old != new:
            from centrochange_core.security.audit import append
            append('PATIENT_TS_PREFERENCE_CHANGED', 'Patient', doc.name, {'preference': old}, {'preference': new}, reason)
    if ts_preference is None:
        return mutate('patient', center, 'Patient', name, values, tuple(values), expected_version, request_key, reason, lambda doc: _patient(center, doc))
    from centrochange_core.security.audit import internal_write
    def validate_preference_write(doc):
        _patient(center, doc)
        # mutate() has already checked manager, center and native document write
        # permission. The scoped whitelist is the only path allowed to update
        # this permlevel-1 field; native APIs must not expose it to other roles.
        doc.flags.ignore_permissions = True
    with internal_write('cc_ts_preference_write'):
        return mutate('patient', center, 'Patient', name, values, tuple(values), expected_version, request_key, reason,
                      validate_preference_write, after_save=audit_preference)


@frappe.whitelist(methods=['GET'])
def patient_ts_history(center, name):
    manager(center)
    doc = frappe.get_doc('Patient', bounded(name, 'Paziente'))
    doc.check_permission('read')
    _patient(center, doc, allow_historical=True)
    events = frappe.get_all('CC Audit Event', filters={'event_type':'PATIENT_TS_PREFERENCE_CHANGED', 'reference_doctype':'Patient', 'reference_name':doc.name},
        fields=['actor', 'event_time', 'before_state', 'after_state'], order_by='event_time desc, name desc', limit_page_length=100)
    return [{'actor': row.actor, 'event_time': row.event_time,
             'before': frappe.parse_json(row.before_state or '{}').get('preference', ''),
             'after': frappe.parse_json(row.after_state or '{}').get('preference', '')} for row in events]


@frappe.whitelist(methods=['GET'])
def patient_creation_options(center):
    manager(center)
    return {'genders': frappe.get_all('Gender', pluck='name', order_by='name')}



@frappe.whitelist(methods=['GET'])
def practitioners(center, limit=50, offset=0, search=''):
    limit, offset = page(limit, offset)
    require_center(center)
    require_operational_center(center)
    search = bounded(search, 'Ricerca', 100, required=False)
    from centrochange_core.security.guards import practitioner_names_for_center
    names = practitioner_names_for_center(center)
    filters = {'name': ['in', names or ['']]}
    if not is_manager():
        own = practitioner_for()
        filters['name'] = ['in', [own] if own in names else ['']]
    options = {}
    if search:
        # Use the exact UAT-owned manifest for display aliases, but always apply the
        # membership / self-only / DocType predicates from this authorized query.
        # Never alter the native Healthcare Practitioner name or search the bootstrap.
        # The offline guarded API harness deliberately stubs a minimal Frappe
        # module. Missing optional UAT display aliases must safely degrade to
        # canonical search, never to unrestricted practitioner results.
        try:
            from centrochange_core.uat.display import _manifest
            manifest = _manifest()
        except ImportError:
            manifest = None
        alias_names = []
        if manifest:
            for index, name in enumerate(manifest['fixture']['practitioners'], 1):
                if search.casefold() in f'Professionista {index}'.casefold():
                    alias_names.append(name)
        needle = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        or_filters = {field: ['like', needle] for field in ('practitioner_name', 'first_name', 'last_name', 'name')}
        if alias_names:
            or_filters['name'] = ['in', alias_names]
        options = {'or_filters': or_filters}
    rows = frappe.get_list('Healthcare Practitioner', filters=filters, **options,
                           fields=['name', 'practitioner_name', 'first_name', 'last_name', 'user_id', 'status', 'modified'],
                           order_by='practitioner_name,name', start=offset, page_length=limit + 1)
    return {'rows': rows[:limit], 'has_more': len(rows) > limit}


@frappe.whitelist(methods=['POST'])
@_atomic_provision
def practitioner_create(center, first_name, last_name, email, request_key, reason, user=None, account_mode='new', mobile_phone=None, residence_phone=None, office_phone=None,
                        middle_name=None, practitioner_type=None, hospital=None, gender=None, department=None, designation=None, **extra):
    deny_extra(extra)
    from hashlib import sha256
    from centrochange_core.security.audit import internal_write
    require_operational_center(center)
    first_name = bounded(first_name, 'Nome')
    last_name = bounded(last_name, 'Cognome')
    email = bounded(email, 'Email', 140).lower()
    if email and not frappe.utils.validate_email_address(email):
        frappe.throw('Email non valida')
    if account_mode not in ('existing', 'new'):
        frappe.throw('Modalità account non valida')
    if account_mode == 'new' and int(frappe.get_system_settings('reset_password_link_expiry_duration') or 0) <= 0:
        frappe.throw('Configura una scadenza positiva per il link di primo accesso.')
    user = email if account_mode == 'new' else bounded(user, 'Account personale')
    if practitioner_type not in (None, '', 'Internal', 'External'):
        frappe.throw('Tipo professionista non valido')
    for value, doctype in ((gender, 'Gender'), (department, 'Medical Department'), (designation, 'Designation')):
        if value and not frappe.db.exists(doctype, bounded(value, 'Riferimento', 140)):
            frappe.throw('Riferimento professionale non valido')
    values = {'first_name':first_name, 'last_name':last_name, 'status':'Active', 'cc_profile_center':center, 'user_id':user,
              'mobile_phone':bounded(mobile_phone, 'Cellulare', 140, required=False),
              'residence_phone':bounded(residence_phone, 'Telefono', 140, required=False),
              'office_phone':bounded(office_phone, 'Telefono ufficio', 140, required=False),
              'middle_name':bounded(middle_name, 'Secondo nome', 140, required=False),
              'practitioner_type':practitioner_type or '', 'hospital':bounded(hospital, 'Struttura', 140, required=False),
              'gender':gender or None, 'department':department or None, 'designation':designation or None}
    # Contact data participates in the creation fingerprint without becoming a
    # synthetic field on Healthcare Practitioner.
    def after_insert(doc):
        if email:
            # Frappe may already have made the personal User's Contact. Reuse
            # only that exact, otherwise unlinked contact; never merge contacts.
            matches = frappe.get_all('Contact Email', filters={'email_id': email}, pluck='parent')
            if len(matches) == 1:
                contact = frappe.get_doc('Contact', matches[0], for_update=True)
                if contact.user == user and not contact.links:
                    contact.append('links', {'link_doctype':'Healthcare Practitioner', 'link_name':doc.name})
                    # The unlinked native User contact is not yet visible to
                    # the manager. The already-authorized scoped creation is
                    # the only path to attach this exact personal contact.
                    contact.save(ignore_permissions=True)
                    doc.practitioner_primary_contact = contact.name
                    doc.email_id = contact.email_id or ''
                    doc.save()
                    from centrochange_core.security.audit import append
                    append('PRACTITIONER_CONTACT_UPDATED', doc.doctype, doc.name,
                           {'email_hash':None}, {'email_hash':sha256(email.encode()).hexdigest()}, reason)
                    return
            if account_mode == 'new' and not matches:
                contact = frappe.get_doc({'doctype':'Contact', 'first_name':first_name, 'last_name':last_name, 'user':user,
                    'email_ids':[{'email_id':email, 'is_primary':1}],
                    'links':[{'link_doctype':'Healthcare Practitioner', 'link_name':doc.name}]})
                contact.check_permission('create')
                contact.insert()
                doc.practitioner_primary_contact = contact.name
                doc.email_id = contact.email_id or ''
                doc.save()
                from centrochange_core.security.audit import append
                append('PRACTITIONER_CONTACT_UPDATED', doc.doctype, doc.name,
                       {'email_hash':None}, {'email_hash':sha256(email.encode()).hexdigest()}, reason)
                return
            contact_key = sha256(('practitioner-contact:' + request_key).encode()).hexdigest()
            practitioner_save(center, doc.name, first_name, last_name, str(doc.modified), contact_key, reason, email=email, contact_version='')
            doc.reload()
    # Generic create's request fingerprint must cover the contact email too.
    def validate_account(_data):
        from centrochange_core.security.guards import enabled, personal_professional
        if account_mode == 'new':
            if frappe.db.exists('User', user):
                frappe.throw('Esiste già un account con questa email: selezionalo se autorizzato.')
            return
        if (user in ('Administrator', 'Guest') or not enabled(user) or not personal_professional(user)
                or not frappe.db.exists('CC Center Membership', {'user':user, 'center':center, 'active':1})
                or frappe.db.exists('Healthcare Practitioner', {'user_id':user})
                or (frappe.db.get_value('User', user, 'email') or '').strip().lower() != email):
            frappe.throw('Serve un account personale attivo e disponibile, autorizzato per il centro.', frappe.PermissionError)
    def prepare(doc):
        if account_mode == 'new':
            from centrochange_core.security.lifecycle import set_membership
            from centrochange_core.security.audit import append
            with internal_write('cc_user_roles_write'):
                frappe.get_doc({'doctype':'User', 'email':user, 'first_name':first_name, 'last_name':last_name,
                    'enabled':1, 'send_welcome_email':0, 'roles':[{'role':'CC Professional'}]}).insert(ignore_permissions=True)
            set_membership(user, center, 1, reason)
            append('PRACTITIONER_ACCOUNT_PREPARED', 'User', user, None, {'enabled':1, 'center':center}, reason)
        doc.flags.ignore_permissions = True
    with internal_write('cc_practitioner_center_write'):
        result = create('practitioner-create', center, 'Healthcare Practitioner', values, tuple(values), request_key, reason,
                      validate=validate_account, after_insert=after_insert, replay_guard=lambda doc: _practitioner(center, doc),
                      prepare_insert=prepare, fingerprint_extra={'email':email, 'account_mode':account_mode})
        if account_mode == 'new' and not result['replay']:
            # The bearer link is returned once only, never persisted in audit or
            # emitted in logs. A retry can use Frappe's standard password reset.
            from urllib.parse import urlsplit
            reset = urlsplit(frappe.get_doc('User', user)._reset_password(send_email=False))
            if reset.path != '/update-password' or not reset.query.startswith('key='):
                frappe.throw('Impossibile preparare il primo accesso in sicurezza.')
            result['first_access_url'] = '/cc-first-access#' + reset.query
            if getattr(frappe.local, 'request', None):
                frappe.local.response_headers['Cache-Control'] = 'private, no-store, no-cache, max-age=0'
        return result


@frappe.whitelist(methods=['GET'])
def practitioner_detail(center, name):
    doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'))
    doc.check_permission('read')
    _practitioner(center, doc)
    result = {field: doc.get(field) for field in ('name', 'practitioner_name', 'first_name', 'middle_name', 'last_name', 'user_id', 'status', 'gender', 'mobile_phone', 'residence_phone', 'office_phone', 'practitioner_type', 'hospital', 'department', 'designation', 'email_id', 'modified')}
    result['contact_modified'] = str(frappe.db.get_value('Contact', doc.get('practitioner_primary_contact'), 'modified') or '') if doc.get('practitioner_primary_contact') else ''
    result['account_enabled'] = bool(frappe.db.get_value('User', doc.user_id, 'enabled')) if doc.user_id else False
    return result


@frappe.whitelist(methods=['POST'])
def practitioner_save(center, name, first_name, last_name, expected_version, request_key, reason,
                      middle_name=None, mobile_phone=None, residence_phone=None, office_phone=None,
                      practitioner_type=None, hospital=None, gender=None, department=None, designation=None, email=None, contact_version=None, **extra):
    deny_extra(extra)
    if email is not None:
        email = bounded(email, 'Email', 140, required=False).lower()
        if email and not frappe.utils.validate_email_address(email):
            frappe.throw('Email non valida')
    values = {'first_name': bounded(first_name, 'Nome'), 'last_name': bounded(last_name, 'Cognome', required=False) if last_name is not None else None}
    for field, label in (('middle_name','Secondo nome'), ('mobile_phone','Cellulare'), ('residence_phone','Telefono'), ('office_phone','Telefono ufficio'), ('hospital','Struttura')):
        value = locals()[field]
        if value is not None:
            values[field] = bounded(value, label, 140, required=False)
    for field, doctype, value in (('gender','Gender',gender), ('department','Medical Department',department), ('designation','Designation',designation)):
        if value is not None:
            value = bounded(value, 'Riferimento', 140, required=False)
            if value and not frappe.db.exists(doctype, value):
                frappe.throw('Riferimento professionale non valido')
            values[field] = value or None
    if practitioner_type is not None:
        if practitioner_type not in ('', 'Internal', 'External'):
            frappe.throw('Tipo professionista non valido')
        values['practitioner_type'] = practitioner_type
    def save_email(doc):
        if email is None:
            return
        from hashlib import sha256
        from centrochange_core.security.audit import append
        linked = frappe.get_all('Dynamic Link', filters={'parenttype':'Contact', 'link_doctype':'Healthcare Practitioner', 'link_name':doc.name}, pluck='parent')
        contact = frappe.get_doc('Contact', doc.practitioner_primary_contact, for_update=True) if doc.practitioner_primary_contact else None
        if contact and str(contact.modified) != str(contact_version or ''):
            frappe.throw('Il contatto è stato modificato da un altro utente. Ricarica la scheda e riprova.')
        if not contact and contact_version:
            frappe.throw('Il contatto è stato modificato da un altro utente. Ricarica la scheda e riprova.')
        old = (contact.email_id or '').strip().lower() if contact else ''
        if old == email:
            return
        if not contact and linked:
            frappe.throw('Esiste già un contatto collegato: verifica il contatto principale prima di modificarlo.')
        if contact:
            contact.check_permission('write')
            if {(row.link_doctype, row.link_name) for row in contact.links} != {('Healthcare Practitioner', doc.name)}:
                frappe.throw('Il contatto è condiviso: non è possibile modificarlo da questa scheda.')
        if email:
            matches = frappe.get_all('Contact Email', filters={'email_id':email}, pluck='parent')
            if any(parent != (contact.name if contact else None) for parent in matches):
                frappe.throw('Questa email è già presente in un altro contatto: verifica prima la possibile duplicazione.')
        if not contact:
            contact = frappe.get_doc({'doctype':'Contact', 'first_name':doc.first_name, 'last_name':doc.last_name,
                                      'links':[{'link_doctype':'Healthcare Practitioner','link_name':doc.name}]})
            contact.check_permission('create')
        # Keep all addresses as secondary where native Contact supports an
        # empty primary; a sole address must be removed or Frappe reselects it.
        if not email:
            if len(contact.email_ids) == 1:
                contact.email_ids = []
            else:
                for row in contact.email_ids:
                    row.is_primary = 0
        else:
            found = False
            for row in contact.email_ids:
                row.is_primary = int(row.email_id.lower() == email)
                found |= bool(row.is_primary)
            if not found:
                contact.append('email_ids', {'email_id':email, 'is_primary':1})
        contact.insert() if contact.is_new() else contact.save()
        doc.practitioner_primary_contact = contact.name
        doc.email_id = contact.email_id or ''
        doc.save()
        digest = lambda value: sha256(value.encode()).hexdigest()
        append('PRACTITIONER_CONTACT_UPDATED', doc.doctype, doc.name, {'email_hash':digest(old)}, {'email_hash':digest(email)}, reason)
    return mutate('practitioner', center, 'Healthcare Practitioner', name, values, tuple(values), expected_version, request_key, reason,
                  lambda doc: _practitioner(center, doc), after_save=save_email if email is not None else None,
                  fingerprint_extra={'email':email, 'contact_version':contact_version or ''} if email is not None else None)


@frappe.whitelist(methods=['GET'])
def practitioner_history(center, name):
    manager(center)
    doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'))
    doc.check_permission('read')
    _practitioner(center, doc)
    events = frappe.get_all('CC Audit Event', filters={'event_type':['in', ['PREMIUM_MASTER_CREATED', 'PREMIUM_MASTER_UPDATED', 'PRACTITIONER_CONTACT_UPDATED', 'PRACTITIONER_STATE', 'PRINCIPAL_REPLACED']], 'reference_doctype':'Healthcare Practitioner', 'reference_name':doc.name},
        fields=['event_type','actor','event_time','before_state'], order_by='event_time desc, name desc', limit_page_length=100)
    event_fields = {'PREMIUM_MASTER_CREATED':['creazione'], 'PRACTITIONER_CONTACT_UPDATED':['email'], 'PRACTITIONER_STATE':['stato'], 'PRINCIPAL_REPLACED':['accesso']}
    return [{'actor':row.actor, 'event_time':row.event_time,
             'fields':event_fields.get(row.event_type, list(frappe.parse_json(row.before_state or '{}').get('before', {}).keys()))} for row in events]


@frappe.whitelist(methods=['POST'])
def practitioner_set_state(center, name, active, expected_version, reason):
    from centrochange_core.security.audit import atomic
    from centrochange_core.security.lifecycle import lock, set_practitioner_state
    @atomic
    def run():
        manager(center)
        lock()
        doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'), for_update=True)
        doc.check_permission('write')
        _practitioner(center, doc)
        if not expected_version or str(doc.modified) != str(expected_version):
            frappe.throw('Scheda modificata da un altro utente. Ricarica e riprova.')
        return set_practitioner_state(doc.name, active, bounded(reason, 'Motivo', 500))
    return run()


@frappe.whitelist(methods=['GET'])
def practitioner_access_candidates(center, name=None):
    manager(center)
    if name:
        doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'))
        doc.check_permission('read')
        _practitioner(center, doc)
    from centrochange_core.security.guards import enabled, personal_professional
    users = frappe.get_all('CC Center Membership', filters={'center':center, 'active':1}, pluck='user')
    return [{'name':user, 'label':frappe.db.get_value('User', user, 'full_name') or user} for user in users
            if user and user not in ('Administrator', 'Guest') and enabled(user) and personal_professional(user)
            and not frappe.db.exists('Healthcare Practitioner', {'user_id':user})]


@frappe.whitelist(methods=['POST'])
def practitioner_link_user(center, name, user, expected_version, reason):
    from centrochange_core.security.audit import atomic
    from centrochange_core.security.lifecycle import lock, replace_principal
    @atomic
    def run():
        manager(center)
        lock()
        doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'), for_update=True)
        doc.check_permission('write')
        _practitioner(center, doc)
        if not expected_version or str(doc.modified) != str(expected_version):
            frappe.throw('Scheda modificata da un altro utente. Ricarica e riprova.')
        if not frappe.db.exists('CC Center Membership', {'user':bounded(user, 'Utente'), 'center':center, 'active':1}):
            frappe.throw('L’utente deve avere un’appartenenza attiva a questo centro.', frappe.PermissionError)
        if not doc.email_id or doc.email_id.strip().lower() != (frappe.db.get_value('User', user, 'email') or '').strip().lower():
            frappe.throw('L’email del profilo deve corrispondere all’account personale.', frappe.PermissionError)
        return replace_principal(doc.name, user, bounded(reason, 'Motivo', 500))
    return run()
