# #71 — Management change register

## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

Audit backend and 8 browser checks PASS: Manager positive, other six roles negative, direct access, before/after filters and mobile.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

Status: TECHNICAL PASS — Owner UAT pending; issue remains OPEN.
Base: accepted Patient/Customer View stack, `issue-68/patient-customer-view`.
Application: `64b70c1`; responsive/QA update `bae5a4c`.
Runtime: Frappe 16.31.0 / ERPNext 16.32.0 / Marley 16.5.2 / Builder 1.33.0, unchanged pinned images and commits. Named immutable candidate `goal02-20261007-rc19` verified; no schema migration or dataset reset.

Management-only `/registro_modifiche`, reachable from Agenda and Finance, with period/type/reference filters, bounded paging, actor/time/reason/reference and expandable before/after. Existing CC Manager guard and native audit permissions reused; no permission change, export endpoint or audit writer added.

Validation: Python compile; JavaScript syntax; runtime `security.audit_view_acceptance.run` PASS (Owner threshold/override events found; S/F/T/A/B/C/Guest denied). Initial browser found mobile overflow from unbroken event identifiers; scoped wrapping added; repeat PASS: 7 role API/direct checks, management navigation, filter, expandable before/after, 390px no overflow, no JS errors. Audit create/write/delete hooks unchanged.

Official upstream: https://docs.frappe.io/framework/user/en/api/database and https://docs.frappe.io/framework/user/en/api/rest . Pinned runtime `frappe/client.py` delegates list to permission-aware `frappe.get_list`; `get_all` is not used for audit API. Browser plugin unavailable; pinned Playwright 1.58.2 used. Owner acceptance is required before issue closure.
