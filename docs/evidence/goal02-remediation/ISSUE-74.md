# #74 — Authorized patient search

Status: static PASS; runtime/browser acceptance pending integrated Wave B deploy.
Branch `issue-74/authorized-patient-search`, base `issue-73/first-meeting-confirmation`.
Operational search uses native permission-aware get_list with names/UID filters AND current Patient/center context, bounded 50 results and explicit narrow/empty states. Roles and identity permissions unchanged. Accounting profiles retain only their existing fiscal Patient/Customer projection; search filters already-authorized labels/identifiers in that projection and never grants operational Patient API access. Async generation/context checks retain stale-response protection.

Official source: https://docs.frappe.io/framework/user/en/api/database ; pinned Frappe 16 get_list/or_filters semantics verified in earlier source/runtime checks and exercised by versioned search regression. No migration, reset, note fields or permission expansion. Owner UAT required.
