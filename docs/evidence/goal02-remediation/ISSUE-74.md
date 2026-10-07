# #74 — Authorized patient search

## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

6 backend authorization/bounded search checks PASS. Browser A/B/C and Secretariat positive/negative searches PASS; final UID and delayed query checks recorded in search-browser.json.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

Status: static PASS; runtime/browser acceptance pending integrated Wave B deploy.
Branch `issue-74/authorized-patient-search`, base `issue-73/first-meeting-confirmation`.
Operational search uses native get_list for Manager and a narrow native get_all identity projection for other operational roles, with mandatory current exact Patient/center pairs AND name/UID filters, bounded 50 results and explicit narrow/empty states. Roles and identity permissions unchanged. Accounting profiles retain only their existing fiscal Patient/Customer projection; search filters already-authorized labels/identifiers in that projection and never grants operational Patient API access. Async generation/context checks retain stale-response protection.

Official source: https://docs.frappe.io/framework/user/en/api/database ; pinned Frappe 16 get_list/or_filters semantics verified in earlier source/runtime checks and exercised by versioned search regression. No migration, reset, note fields or permission expansion. Owner UAT required.

Runtime discriminant: pinned Frappe 16 generic get_list requires doctype-level read/select; CC Professional deliberately has document-only Patient access. Initial get_list failed safely with 403. Fix retains zero generic list grants and uses exact authorized names with fixed identity fields. No empty-scope fallback or ignore-permissions argument from callers.
