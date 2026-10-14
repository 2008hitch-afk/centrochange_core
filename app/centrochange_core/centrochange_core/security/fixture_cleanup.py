"""Ownership checks for disposable synthetic HTTP fixture dependents."""


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
