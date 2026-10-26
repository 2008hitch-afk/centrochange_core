"""Existing operational identities, scoped to an authorized center context."""
import frappe
from centrochange_core.scoped_api import bounded, deny_extra, manager, mutate, page
from centrochange_core.security.guards import is_manager, patient_contexts, practitioner_for, require_center, require_operational_center, roles


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
    if not doc.user_id or not frappe.db.exists('CC Center Membership', {'user': doc.user_id, 'center': center, 'active': 1}):
        frappe.throw('Professionista non disponibile per questo centro', frappe.PermissionError)
    if not is_manager() and (doc.name != practitioner_for() or 'CC Professional' not in roles()):
        frappe.throw('Professionista non disponibile per questo centro', frappe.PermissionError)


@frappe.whitelist(methods=['GET'])
def patients(center, limit=50, offset=0):
    limit, offset = page(limit, offset)
    require_center(center)
    filters={'center':center}
    if not is_manager():
        filters['active']=1
    allowed = frappe.get_all('CC Patient Assignment', filters=filters, pluck='patient')
    if not is_manager():
        allowed = list(set(allowed) & {p for p, c in patient_contexts() if c == center})
    # Secretariat/Professional have document-scoped hooks, not a broad native list grant.
    lookup = frappe.get_list if is_manager() else frappe.get_all
    rows = lookup('Patient', filters={'name': ['in', allowed or ['']]},
                           fields=['name', 'patient_name', 'first_name', 'last_name', 'email', 'modified'],
                           order_by='patient_name,name', start=offset, page_length=limit + 1)
    active=set(frappe.get_all('CC Patient Assignment',
        filters={'center':center,'active':1,'patient':['in',[row.name for row in rows[:limit]] or ['']]},
        pluck='patient'))
    return {'rows':[{**row,'active_assignment':row.name in active} for row in rows[:limit]],
            'has_more':len(rows)>limit}


@frappe.whitelist(methods=['GET'])
def patient_detail(center, name):
    doc = frappe.get_doc('Patient', bounded(name, 'Paziente'))
    doc.check_permission('read')
    active=_patient(center, doc, allow_historical=True)
    return {**{field: doc.get(field) for field in ('name', 'patient_name', 'first_name', 'last_name', 'email', 'modified')},
            'active_assignment':active}


@frappe.whitelist(methods=['POST'])
def patient_save(center, name, first_name, last_name, email, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    email = bounded(email, 'Email', 140, required=False).lower()
    if email and not frappe.utils.validate_email_address(email):
        frappe.throw('Email non valida')
    return mutate('patient', center, 'Patient', name,
                  {'first_name': bounded(first_name, 'Nome'), 'last_name': bounded(last_name, 'Cognome', required=False), 'email': email},
                  ('first_name', 'last_name', 'email'), expected_version, request_key, reason,
                  lambda doc: _patient(center, doc))


@frappe.whitelist(methods=['GET'])
def practitioners(center, limit=50, offset=0, search=''):
    limit, offset = page(limit, offset)
    require_center(center)
    require_operational_center(center)
    search = bounded(search, 'Ricerca', 100, required=False)
    users = frappe.get_all('CC Center Membership', filters={'center': center, 'active': 1}, pluck='user')
    filters = {'user_id': ['in', users or ['']]}
    if not is_manager():
        filters['name'] = practitioner_for() or ''
    options = {}
    if search:
        # Use the exact UAT-owned manifest for display aliases, but always apply the
        # membership / self-only / DocType predicates from this authorized query.
        # Never alter the native Healthcare Practitioner name or search the bootstrap.
        from centrochange_core.uat.display import _manifest
        manifest = _manifest()
        alias_names = []
        if manifest:
            for index, name in enumerate(manifest['fixture']['practitioners'], 1):
                if search.casefold() in f'Professionista {index}'.casefold():
                    alias_names.append(name)
        needle = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        or_filters = [[field, 'like', needle] for field in ('practitioner_name', 'first_name', 'last_name', 'name')]
        if alias_names:
            or_filters.append(['name', 'in', alias_names])
        options = {'or_filters': or_filters}
    rows = frappe.get_list('Healthcare Practitioner', filters=filters, **options,
                           fields=['name', 'practitioner_name', 'first_name', 'last_name', 'user_id', 'status', 'modified'],
                           order_by='practitioner_name,name', start=offset, page_length=limit + 1)
    return {'rows': rows[:limit], 'has_more': len(rows) > limit}


@frappe.whitelist(methods=['GET'])
def practitioner_detail(center, name):
    doc = frappe.get_doc('Healthcare Practitioner', bounded(name, 'Professionista'))
    doc.check_permission('read')
    _practitioner(center, doc)
    return {field: doc.get(field) for field in ('name', 'practitioner_name', 'first_name', 'last_name', 'user_id', 'status', 'modified')}


@frappe.whitelist(methods=['POST'])
def practitioner_save(center, name, first_name, last_name, expected_version, request_key, reason, **extra):
    deny_extra(extra)
    return mutate('practitioner', center, 'Healthcare Practitioner', name,
                  {'first_name': bounded(first_name, 'Nome'), 'last_name': bounded(last_name, 'Cognome', required=False)},
                  ('first_name', 'last_name'), expected_version, request_key, reason,
                  lambda doc: _practitioner(center, doc))
