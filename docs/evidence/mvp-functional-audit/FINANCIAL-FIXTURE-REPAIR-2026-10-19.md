# Financial fixture repair — 2026-10-19

**PARTIAL / NOT READY FOR DEV UPDATE.** Source fixes and offline prevention are complete for the demonstrated duplicate-invoice path. Native accounting cleanup is fail-closed; runtime execution is neither authorized in this phase nor claimed. No GitHub publication.

## Causes

- `finance_browser_acceptance` prepared incoming XML via `incoming_acceptance.prepare_http`. That helper called `banking_acceptance.prepare_http`, which closes two sessions and submits two native Sales Invoices. `prepare_browser_invoice` then tried to invoice the first session again. The product's anti-double-billing check correctly rejected it.
- The subsequent cleanup failed with MariaDB 1020, wrapped as Frappe `QueryDeadlockError`, inside `destroy_http` at the raw deletion loop. The retained traceback does **not** establish the competing transaction, affected table or root cause of that concurrency event. No unsupported claim of a solved deadlock is made.
- Cleanup also retained an obsolete `Credit Card` enum expectation after the POS fixture was corrected to native Bank/Cash.
- More importantly, cleanup directly deleted submitted invoices/payments and GL/Payment Ledger rows. This bypassed native cancellation. Read-only pinned-source inspection (`erpnext/controllers/accounts_controller.py:on_trash`, v16.50) shows native ledger deletion depends on `Accounts Settings.delete_linked_ledger_entries`. The current DEV setting is **0**. Therefore a native exact cleanup with no retained ledger cannot presently be promised. This setting was not changed.

## Implemented locally

- Optional bank preparation in the incoming helper; existing API suites retain their explicit banking setup, while the browser suite opts out. The browser gets its own previously unbilled fixture session; XML supplier/profile/bank configuration remains available without creating prior invoices.
- Before lifecycle changes or Mode of Payment creation, reject any active non-return invoice for the target appointment. Exact synthetic patient/center/service and no-package checks remain.
- Global financial-fixture precondition in `create_http(finance=True)`: require synthetic Administrator and native accounting cleanup capability **before creating users or other fixture records**. With current DEV configuration these suites are BLOCKED before writes.
- Cleanup refuses to start if fixture Contact jobs are still pending; the old runner timeout cannot silently proceed into teardown. This prevents one identified race opportunity, but does not prove it caused the observed 1020.
- Cleanup validates all native accounting documents against exact fixture centers, cancels Bank Transaction → Payment Entry → invoices (returns first), then calls native `delete_doc` with link checks enabled. No forced links or direct ledger deletion. Residual accounting records are an error. Native cancellation/link errors propagate; no blind retry after partial file cleanup.
- The raw fixture deletion loop excludes accounting vouchers and ledger tables. POS ownership validation uses Bank/Cash.
- Existing structured exception transport remains; failures roll back the DB transaction. Filesystem cleanup is not a DB transaction: no automatic retry added that could hide partial file effects.

## Six-capability preventive review

| Capability | Preparation/cleanup review | Current verification |
|---|---|---|
| POS (042) | Duplicate creation removed; pre-invoice guard; native cleanup gate | Offline positive/negative tests; live BLOCKED |
| GL/TB (047) | Browser no longer inherits bank invoices; API suite intentionally creates its own tagged invoices | Offline source review; live BLOCKED |
| Administrative attachments | Same browser-owned invoice, private File path; native deletion may invoke file hooks | Native file/DB recovery still requires runtime evidence; BLOCKED |
| Localization/export (029) | Read-only export assertions use the financial fixture; no second invoice preparation | Shared precondition prevents unsafe setup; no new live PASS |
| Obsolete fixtures (050) | POS enum corrected in teardown; six financial runners use guarded create_http(finance=True) | Offline regression coverage; no security checks removed |
| Role saves/mobile | Same isolated browser fixture, credentials removed in finally; permission checks unchanged | No 128-route campaign repeated; functional live verification BLOCKED |

Also reviewed `reporting_acceptance`, `incoming_acceptance`, `professional_acceptance`, `sdi_acceptance`, `ts_acceptance`: all request `finance=True` and therefore inherit the pre-write gate. Their banking preparation is deliberate and no subsequent browser invoice helper is invoked. No configuration or permissions were widened.

## Tests

94 offline tests PASS; Python compile checks and `git diff --check` PASS. New executable fake-native tests cover native cancellation order, already-cancelled documents, empty cleanup replay, foreign document rejection before deletion, intermediate cancellation failure, residual ledger rejection, and disabled native cleanup. Structural regressions cover opt-out of bank invoices, the already-invoiced guard preceding mutations, pending Contact jobs, and exclusion of accounting records from raw deletion.

These tests do **not** prove real ERPNext cancellation, all cross-document dependencies, file recovery or zero residues after a committed live financial test. Those remain BLOCKED and are not disguised as PASS.

## DEV read-only evidence

Nine services; preflight PASS. Data, Communication, schema and permissions equal the last checkpoint. Data fingerprint `caba48b14430cd975213fde6273aada780aecd6e6604ad4fbb5ccda8bfc4eae0`. Baseline image remains `sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc`. No deployment, restart, clone, test writes or configuration changes.

## Required boundary

Candidate is **not ready for an update**: current native retention policy prevents a verified zero-residue committed financial fixture cleanup. A decision is needed on the accounting test recovery approach: retain native cancelled synthetic history with an explicit inventory, or authorize a DEV-specific native ledger cleanup policy. Neither alternative was adopted. Meanwhile the financial fixture preflight prevents unsafe tests. Executor candidate/dependency pins were deliberately not advanced to make this unverified cleanup deployable.
