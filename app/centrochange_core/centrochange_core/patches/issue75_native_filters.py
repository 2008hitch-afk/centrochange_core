"""Keep Healthcare's unused department Link out of the client standard filter."""

from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	# This changes only List View presentation metadata. The Link remains in
	# Healthcare, and its server-side permission still denies direct requests.
	make_property_setter(
		"Healthcare Practitioner", "department", "in_standard_filter", 0, "Check",
		validate_fields_for_doctype=False,
	)
