# #62 — Reconciled bank document trace

Status: PARTIAL — static PASS; combined Wave B runtime/browser checks pending.
Branch `issue-62/bank-reconciliation-trace`, base `issue-81/readable-expectations`.

Read-only trace follows existing native Bank Transaction Payment Entries → submitted Payment Entry References → invoice/subject/allocated amount. Each linked document must retain the same center; no allocation is inferred from current outstanding. UI displays reconciled documents when candidates are empty and hides the second-match action. Accounting writers/audit unchanged.

Expected preserved UAT: Beta ACC-SINV-2026-00081 allocation 60 EUR. Read-only backend and browser regressions versioned. Official docs: https://docs.frappe.io/erpnext/bank-transaction and https://docs.frappe.io/erpnext/payment-reconciliation; pinned ERPNext 16.32.0 Bank Transaction source checked for native payment_entries allocation. No schema migration, seed, reset or permission changes.
