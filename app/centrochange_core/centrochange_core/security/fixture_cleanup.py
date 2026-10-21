"""Ownership checks for disposable synthetic HTTP fixture dependents."""


def owned_audit_ids(events, groups, tag):
	"""Validate every synthetic audit link before voucher cleanup deletes it."""
	names = sorted(set(groups.get('CC Audit Event', [])))
	if len(events) != len(names) or {row['name'] for row in events} != set(names):
		raise ValueError('Fixture audit inventory changed before cleanup')
	for row in events:
		if row['reason'] != tag and row['reference_name'] not in groups.get(row['reference_doctype'], []):
			raise ValueError('Audit cleanup escaped fixture ownership')
	return names


def confirmation_dependents(appointments, centers, confirmations, communications):
	"""Return exact IDs only when every dependent belongs to the fixture."""
	appointments, centers = set(appointments), set(centers)
	confirmation_ids = set()
	communication_ids = set()
	for row in confirmations:
		assert row['name'] not in confirmation_ids
		assert row['appointment'] in appointments and row['center'] in centers
		assert str(row['recipient']).endswith('@example.invalid')
		confirmation_ids.add(row['name'])
	for row in communications:
		assert row['name'] not in communication_ids
		assert row['reference_doctype'] == 'Patient Appointment'
		assert row['reference_name'] in appointments
		assert str(row['recipients']).endswith('@example.invalid')
		communication_ids.add(row['name'])
	for row in confirmations:
		assert not row['communication'] or row['communication'] in communication_ids
	return {
		'CC Booking Confirmation': sorted(confirmation_ids),
		'Communication': sorted(communication_ids),
	}


def require_native_accounting_cleanup():
	"""Do not create committed financial fixtures without native reversibility."""
	import frappe
	if frappe.session.user != 'Administrator' or frappe.conf.get('cc_synthetic_dev') != 1:
		frappe.throw('Cleanup consentito soltanto sul DEV sintetico.', frappe.PermissionError)
	if not frappe.db.get_single_value('Accounts Settings', 'delete_linked_ledger_entries'):
		frappe.throw('Fixture contabili bloccate: la configurazione nativa conserva i ledger; nessuna modifica automatica alla configurazione.')


def native_accounting_cleanup(groups, centers):
	"""Cancel dependencies before invoices; never raw-delete financial vouchers."""
	import frappe
	from centrochange_core.security.audit import internal_write
	kinds = ('Bank Transaction', 'Payment Entry', 'Sales Invoice', 'Purchase Invoice')
	if not any(groups.get(kind) for kind in kinds):
		return
	require_native_accounting_cleanup()
	# Validate the complete scope before the first cancellation.
	documents = []
	for kind in kinds:
		for name in sorted(set(groups.get(kind, []))):
			doc = frappe.get_doc(kind, name, for_update=True)
			if doc.cc_center not in centers:
				raise ValueError('Accounting cleanup escaped fixture centers')
			documents.append(doc)
	# Return/credit documents precede their originals within each invoice type.
	documents.sort(key=lambda doc: (kinds.index(doc.doctype), not bool(doc.get('is_return')), doc.name))
	with internal_write('cc_accounting_write'):
		for doc in documents:
			doc.reload()
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()
			if doc.docstatus not in (0, 2):
				raise ValueError('Native cancellation did not complete')
		# Native link checks remain enabled. Unexpected dependencies fail closed.
		for doc in documents:
			frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
	for kind in (*kinds, 'GL Entry', 'Payment Ledger Entry'):
		if any(frappe.db.exists(kind, name) for name in groups.get(kind, [])):
			raise ValueError('Native accounting cleanup left residual records')
