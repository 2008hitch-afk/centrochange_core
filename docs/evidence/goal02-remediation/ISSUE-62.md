# #62 — Reconciled bank document trace

## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

4 backend checks and browser trace PASS: existing native Bank Transaction allocation of 60 EUR remains mapped to its Payment Entry, invoice and fiscal subject; no duplicate reconciliation.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

Status: PARTIAL — static PASS; combined Wave B runtime/browser checks pending.
Branch `issue-62/bank-reconciliation-trace`, base `issue-81/readable-expectations`.

Read-only trace follows existing native Bank Transaction Payment Entries → submitted Payment Entry References → invoice/subject/allocated amount. Each linked document must retain the same center; no allocation is inferred from current outstanding. UI displays reconciled documents when candidates are empty and hides the second-match action. Accounting writers/audit unchanged.

Expected preserved UAT: Beta ACC-SINV-2026-00081 allocation 60 EUR. Read-only backend and browser regressions versioned. Official docs: https://docs.frappe.io/erpnext/bank-transaction and https://docs.frappe.io/erpnext/payment-reconciliation; pinned ERPNext 16.32.0 Bank Transaction source checked for native payment_entries allocation. No schema migration, seed, reset or permission changes.
