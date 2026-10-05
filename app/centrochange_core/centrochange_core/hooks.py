app_name = "centrochange_core"
app_title = "Centro Change Core"
app_publisher = "Centro Change"
app_description = "Custom Frappe application for Centro Change."
app_email = "dev@centrochange.local"
app_license = "agpl-3.0"

required_apps = ["erpnext", "healthcare"]
before_install = ["centrochange_core.security.install.ensure_roles", "centrochange_core.finance.install.ensure_roles"]
after_install = ["centrochange_core.security.install.configure", "centrochange_core.operations.install.configure", "centrochange_core.finance.install.configure"]
before_migrate = ["centrochange_core.security.install.ensure_roles", "centrochange_core.finance.install.ensure_roles"]
after_migrate = ["centrochange_core.security.install.configure", "centrochange_core.operations.install.configure", "centrochange_core.finance.install.configure"]
before_request = ["centrochange_core.finance.request_guard.before_request", "centrochange_core.security.diagnostics.before_request", "centrochange_core.security.api.before_request", "centrochange_core.operations.notes.request_guard"]

permission_query_conditions = {
    "Customer": "centrochange_core.finance.permissions.customer_query",
    "Supplier": "centrochange_core.finance.permissions.supplier_query",
    "Cost Center": "centrochange_core.finance.permissions.cost_center_query",
    "CC Economic Source Link": "centrochange_core.finance.guards.source_query",
    "CC Notification": "centrochange_core.operations.permissions.notification_query",
    "CC Settlement": "centrochange_core.operations.permissions.settlement_query",
    "CC Package Ledger": "centrochange_core.operations.permissions.ledger_query",
    "CC Patient Package": "centrochange_core.operations.permissions.package_query",
    "CC Private Note": "centrochange_core.operations.notes.private_query",
    "CC Organizational Note": "centrochange_core.operations.notes.organizational_query",
    "Practitioner Schedule": "centrochange_core.scheduling.availability.schedule_query",
    "Practitioner Availability": "centrochange_core.scheduling.availability.availability_query",
    "Patient Appointment": "centrochange_core.scheduling.booking.appointment_query",
    "Patient": "centrochange_core.security.permissions.patient_query",
    "Healthcare Practitioner": "centrochange_core.security.permissions.practitioner_query",
    "Branch": "centrochange_core.security.permissions.branch_query",
    "CC Center Membership": "centrochange_core.security.permissions.membership_query",
    "CC Patient Assignment": "centrochange_core.security.permissions.assignment_query",
}
has_permission = {
    **{doctype: "centrochange_core.finance.permissions.master_permission" for doctype in ("Customer","Supplier","Cost Center")},
    "CC Economic Source Link": "centrochange_core.finance.guards.source_permission",
    "CC Notification": "centrochange_core.operations.permissions.notification_permission",
    "CC Settlement": "centrochange_core.operations.permissions.settlement_permission",
    "CC Package Ledger": "centrochange_core.operations.permissions.ledger_permission",
    "CC Patient Package": "centrochange_core.operations.permissions.package_permission",
    "CC Private Note": "centrochange_core.operations.notes.private_permission",
    "CC Organizational Note": "centrochange_core.operations.notes.organizational_permission",
    "Practitioner Schedule": "centrochange_core.scheduling.availability.schedule_permission",
    "Practitioner Availability": "centrochange_core.scheduling.availability.availability_permission",
    "Patient Appointment": "centrochange_core.scheduling.booking.appointment_permission",
    "Patient": "centrochange_core.security.permissions.patient_permission",
    "Healthcare Practitioner": "centrochange_core.security.permissions.practitioner_permission",
    "Branch": "centrochange_core.security.permissions.branch_permission",
    "CC Center Membership": "centrochange_core.security.permissions.membership_permission",
    "CC Patient Assignment": "centrochange_core.security.permissions.assignment_permission",
}
extend_doctype_class = {
    "Error Log": ["centrochange_core.security.diagnostics.ErrorLogMixin"],
    "Patient Appointment": ["centrochange_core.scheduling.booking.AppointmentMixin"],
    "Patient": ["centrochange_core.security.mixins.PatientMixin"],
    "Healthcare Practitioner": ["centrochange_core.security.mixins.PractitionerMixin"],
    "DocShare": ["centrochange_core.security.mixins.ManagedShareMixin"],
    "User": ["centrochange_core.security.mixins.UserMixin"],
}
doc_events = {
    "Branch": {"validate": "centrochange_core.finance.bridge.protected_center"},
    "Practitioner Schedule": {event: "centrochange_core.scheduling.availability.protected_schedule" for event in ("validate", "on_trash")},
    "Practitioner Availability": {event: "centrochange_core.scheduling.availability.protected_schedule" for event in ("validate", "on_cancel", "on_trash")},
    "CC Audit Event": {event: "centrochange_core.security.audit.immutable"
                       for event in ("validate", "on_trash")},
    "CC Center Membership": {event: "centrochange_core.security.lifecycle.protected_relationship"
                             for event in ("validate", "on_trash")},
    "CC Patient Assignment": {event: "centrochange_core.security.lifecycle.protected_relationship"
                              for event in ("validate", "on_trash")},
    "DocShare": {event: "centrochange_core.security.lifecycle.protect_share" for event in ("validate", "on_trash")},
    "User Permission": {event: "centrochange_core.security.lifecycle.protect_user_permission" for event in ("validate", "on_trash")},
    "Healthcare Practitioner": {"on_update": "centrochange_core.security.lifecycle.practitioner_updated"},
    "User": {"on_update": "centrochange_core.security.lifecycle.user_updated",
             "validate": "centrochange_core.security.lifecycle.protect_user_lifecycle"},
}
override_whitelisted_methods = {
    "healthcare.healthcare.doctype.patient.patient.get_patient_detail": "centrochange_core.security.api.get_patient_detail",
    "healthcare.healthcare.doctype.healthcare_practitioner.healthcare_practitioner.get_practitioner_list": "centrochange_core.security.api.get_practitioner_list",
    "healthcare.healthcare.doctype.healthcare_practitioner.healthcare_practitioner.get_supplier_and_user": "centrochange_core.security.api.get_supplier_and_user",
}


# Native Marley routes bypass snapshot/business semantics or query unrestricted context.
for method in ("check_payment_reqd", "invoice_appointment", "update_fee_validity", "get_availability_data", "check_in_appointment", "update_status", "make_encounter", "get_events", "get_procedure_prescribed", "get_prescribed_therapies"):
    override_whitelisted_methods["healthcare.healthcare.doctype.patient_appointment.patient_appointment." + method] = "centrochange_core.scheduling.booking.blocked_native"
for method in ("get_appointments", "get_logged_in_patient", "get_departments", "get_practitioners", "get_patients", "get_settings", "get_slots", "make_appointment", "get_fees", "get_print_format", "get_orders", "get_payment_link"):
    override_whitelisted_methods["healthcare.healthcare.api.patient_portal." + method] = "centrochange_core.scheduling.booking.blocked_native"

scheduler_events = {"cron": {"*/5 * * * *": ["centrochange_core.operations.automation.catch_up", "centrochange_core.operations.notifications.dispatch_pending"]}}

for dt, query in [('Sales Invoice','sales_invoice_query'),('Payment Entry','payment_entry_query'),('GL Entry','gl_entry_query'),('Payment Ledger Entry','payment_ledger_query')]:
    permission_query_conditions[dt]='centrochange_core.finance.permissions.'+query
    has_permission[dt]='centrochange_core.finance.permissions.transaction_permission'
for dt in ('Sales Invoice','Payment Entry'):
    doc_events[dt]={event:'centrochange_core.finance.receivables.protected' for event in ('validate','before_submit','before_cancel','on_trash')}

for method in ('export_invoices','generate_single_invoice'):
    override_whitelisted_methods['erpnext.regional.italy.utils.'+method]='centrochange_core.scheduling.booking.blocked_native'

extend_doctype_class["Sales Invoice"]=["centrochange_core.finance.receivables.InvoiceMixin"]

permission_query_conditions["Account"]="centrochange_core.finance.permissions.account_query"
has_permission["Account"]="centrochange_core.finance.permissions.master_permission"

for dt,query in [('Bank Transaction','bank_transaction_query'),('Bank Account','bank_account_query')]:
    permission_query_conditions[dt]='centrochange_core.finance.permissions.'+query
    has_permission[dt]='centrochange_core.finance.permissions.transaction_permission'
    doc_events[dt]={event:'centrochange_core.finance.banking.protected' for event in ('validate','before_submit','before_update_after_submit','before_cancel','on_trash')}

for dt,query in [('CC Payment Agreement','agreement_query'),('CC Payment Override','override_query'),('CC Payment Notice','notice_query')]:
    permission_query_conditions[dt]='centrochange_core.finance.collections.'+query
    has_permission[dt]='centrochange_core.finance.collections.permission'
scheduler_events['cron']['*/5 * * * *'].append('centrochange_core.finance.collections.catch_up')

permission_query_conditions['CC Incoming Invoice']='centrochange_core.finance.incoming.query'
has_permission['CC Incoming Invoice']='centrochange_core.finance.incoming.permission'
permission_query_conditions['Purchase Invoice']='centrochange_core.finance.permissions.purchase_invoice_query'
has_permission['Purchase Invoice']='centrochange_core.finance.permissions.transaction_permission'
doc_events['Purchase Invoice']={event:'centrochange_core.finance.incoming.protected_invoice' for event in ('validate','before_submit','before_cancel','on_trash')}

doc_events["File"]={event:"centrochange_core.finance.files.protected" for event in ("validate","on_trash")}

extend_doctype_class["File"]=["centrochange_core.finance.files.FinancialFileMixin"]

for dt,query in [('CC Compensation Rule','rule_query'),('CC Professional Expectation','expectation_query'),('CC Professional Comparison','comparison_query')]:
    permission_query_conditions[dt]='centrochange_core.finance.professional_economics.'+query
    has_permission[dt]='centrochange_core.finance.professional_economics.permission'
permission_query_conditions['CC Admin Exception']='centrochange_core.finance.admin_queue.query'
has_permission['CC Admin Exception']='centrochange_core.finance.admin_queue.permission'
scheduler_events['cron']['*/5 * * * *'].append('centrochange_core.finance.admin_queue.catch_up')
