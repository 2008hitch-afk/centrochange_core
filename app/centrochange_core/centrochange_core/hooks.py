app_name = "centrochange_core"
app_title = "Centro Change Core"
app_publisher = "Centro Change"
app_description = "Custom Frappe application for Centro Change."
app_email = "dev@centrochange.local"
app_license = "agpl-3.0"

required_apps = ["erpnext", "healthcare"]
before_install = "centrochange_core.security.install.ensure_roles"
after_install = "centrochange_core.security.install.configure"
before_migrate = "centrochange_core.security.install.ensure_roles"
after_migrate = "centrochange_core.security.install.configure"
before_request = ["centrochange_core.security.api.before_request"]

permission_query_conditions = {
    "Patient": "centrochange_core.security.permissions.patient_query",
    "Healthcare Practitioner": "centrochange_core.security.permissions.practitioner_query",
    "Branch": "centrochange_core.security.permissions.branch_query",
    "CC Center Membership": "centrochange_core.security.permissions.membership_query",
    "CC Patient Assignment": "centrochange_core.security.permissions.assignment_query",
}
has_permission = {
    "Patient": "centrochange_core.security.permissions.patient_permission",
    "Healthcare Practitioner": "centrochange_core.security.permissions.practitioner_permission",
    "Branch": "centrochange_core.security.permissions.branch_permission",
    "CC Center Membership": "centrochange_core.security.permissions.membership_permission",
    "CC Patient Assignment": "centrochange_core.security.permissions.assignment_permission",
}
extend_doctype_class = {
    "Patient": ["centrochange_core.security.mixins.PatientMixin"],
    "Healthcare Practitioner": ["centrochange_core.security.mixins.PractitionerMixin"],
    "DocShare": ["centrochange_core.security.mixins.ManagedShareMixin"],
    "User": ["centrochange_core.security.mixins.UserMixin"],
}
doc_events = {
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

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "centrochange_core",
# 		"logo": "/assets/centrochange_core/logo.png",
# 		"title": "Centro Change Core",
# 		"route": "/centrochange_core",
# 		"has_permission": "centrochange_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/centrochange_core/css/centrochange_core.css"
# app_include_js = "/assets/centrochange_core/js/centrochange_core.js"

# include js, css files in header of web template
# web_include_css = "/assets/centrochange_core/css/centrochange_core.css"
# web_include_js = "/assets/centrochange_core/js/centrochange_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "centrochange_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "centrochange_core/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "centrochange_core.utils.jinja_methods",
# 	"filters": "centrochange_core.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "centrochange_core.install.before_install"
# after_install = "centrochange_core.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "centrochange_core.uninstall.before_uninstall"
# after_uninstall = "centrochange_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "centrochange_core.utils.before_app_install"
# after_app_install = "centrochange_core.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "centrochange_core.utils.before_app_uninstall"
# after_app_uninstall = "centrochange_core.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "centrochange_core.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "centrochange_core.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
    "Practitioner Schedule": {event: "centrochange_core.scheduling.availability.protected_schedule" for event in ("validate", "on_trash")},
    "Practitioner Availability": {event: "centrochange_core.scheduling.availability.protected_schedule" for event in ("validate", "on_cancel", "on_trash")},
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"centrochange_core.tasks.all"
# 	],
# 	"daily": [
# 		"centrochange_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"centrochange_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"centrochange_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"centrochange_core.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "centrochange_core.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "centrochange_core.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "centrochange_core.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "centrochange_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["centrochange_core.utils.before_request"]
# after_request = ["centrochange_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["centrochange_core.utils.before_job"]
# after_job = ["centrochange_core.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"centrochange_core.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
