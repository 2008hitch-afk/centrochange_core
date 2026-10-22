"""Ownership checks for disposable synthetic HTTP fixture dependents."""


NATIVE_LINK_DEPENDENTS = ('CC Admin Exception', 'CC Payment Override',
	'CC Notification', 'CC Fiscal Attempt',
	'CC Fiscal Transaction', 'CC TS Input Review', 'CC Incoming Invoice',
	'CC Professional Comparison')


def native_link_dependents(groups):
	"""Return exact center-scoped fixture documents linking native vouchers."""
	return {kind: sorted(set(groups.get(kind, []))) for kind in NATIVE_LINK_DEPENDENTS}


def fixture_incoming_target(target, owned_purchase_invoices):
	"""Only a fixture-owned purchase invoice link may be cleared for teardown."""
	if target and target not in owned_purchase_invoices:
		raise ValueError('Incoming source links a purchase invoice outside fixture')
	return target


def owned_audit_ids(events, groups, tag):
	"""Validate every synthetic audit link before voucher cleanup deletes it."""
	names = sorted(set(groups.get('CC Audit Event', [])))
	if len(events) != len(names) or {row['name'] for row in events} != set(names):
		raise ValueError('Fixture audit inventory changed before cleanup')
	for row in events:
		if row['reason'] != tag and row['reference_name'] not in groups.get(row['reference_doctype'], []):
			raise ValueError('Audit cleanup escaped fixture ownership')
	return names


def native_dependents_first(documents, kinds):
	"""Order fixture vouchers so returns and amendments precede their originals."""
	by_key = {(doc.doctype, doc.name): doc for doc in documents}
	if len(by_key) != len(documents):
		raise ValueError('Duplicate native voucher in fixture cleanup')
	children = {key: [] for key in by_key}
	for key, doc in by_key.items():
		for field in ('return_against', 'amended_from'):
			parent = doc.get(field)
			if parent and (doc.doctype, parent) in children:
				children[(doc.doctype, parent)].append(key)
	ordered, visited, active = [], set(), set()
	def visit(key):
		if key in active:
			raise ValueError('Cyclic native voucher correction')
		if key in visited:
			return
		active.add(key)
		for child in sorted(set(children[key])):
			visit(child)
		active.remove(key)
		visited.add(key)
		ordered.append(by_key[key])
	for key in sorted(by_key, key=lambda item: (kinds.index(item[0]), item[1])):
		visit(key)
	return ordered


def native_two_phase(documents, cancel, after_cancellation, delete):
	"""Clear hook-created fixture links between native cancel and delete."""
	for doc in documents:
		cancel(doc)
	if after_cancellation:
		after_cancellation()
	for doc in documents:
		delete(doc)


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


def native_accounting_cleanup(groups, centers, after_cancellation=None):
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
	# Native links require returns and amended successors to go before originals.
	documents = native_dependents_first(documents, kinds)
	with internal_write('cc_accounting_write'):
		def cancel(doc):
			doc.reload()
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()
			if doc.docstatus not in (0, 2):
				raise ValueError('Native cancellation did not complete')
		def delete(doc):
			frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
		# Native link checks remain enabled. Unexpected dependencies fail closed.
		native_two_phase(documents, cancel, after_cancellation, delete)
	for kind in (*kinds, 'GL Entry', 'Payment Ledger Entry'):
		if any(frappe.db.exists(kind, name) for name in groups.get(kind, [])):
			raise ValueError('Native accounting cleanup left residual records')
