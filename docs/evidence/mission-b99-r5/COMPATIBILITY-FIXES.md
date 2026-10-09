# B99 R5 — compatibility fixes (DRAFT / NOT fully validated)

Owner authority: issue #99, comment 6080880107. Product baseline: main
`2fab181cd61cfc69e341d9fa1849038c6646e87e`; original application source
`e85fce588de6012a47da302710b9f9c615211279`. No main merge or UAT deployment.

## Changes

- Internal tax projection authorizes the actual Finance/Secretariat actor and
  center/company before resolving the configured synthetic native template.
- Internal unsaved Payment Entry factory reloads/locks the canonical managed
  invoice, authorizes actual actor/read/center/company and validates ordinary
  EUR open balance and account context. Native posting/ledger validation remains
  in the original audited service. Unsupported FX/installments/discounts fail
  closed. Payment audit retains actor, invoice, allocated amount and before/after
  native outstanding. No new public endpoint, grants, SQL posting or user switch.
- The existing FinancialFileMixin delegates only private local Italy XML under
  the existing guarded accounting service. The actual actor still requires
  Finance write for the canonical invoice center and invoice read. Deletion is
  restricted to the native XML of an actually cancelled managed synthetic Sales
  Invoice; retained CC Fiscal Transaction payloads are excluded. Generic REST
  write/delete and the role model remain unchanged.
- Login footer explicitly includes shared local UI assets when the upstream login
  template overrides head_include. Shared JS supports the native submit button
  and retains Tabler primary styling.

## Verified root causes and official pinned source

Target: Frappe/ERPNext 16.50.0. Runtime trace demonstrated that invoice submission
fails in File.validate_attachment_references while native Italy XML is saved:
https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/core/doctype/file/file.py

A separate real HTTP trace demonstrated SdI cancellation fails when Italy
sales_invoice_on_cancel removes the generated File under the actual Secretariat:
https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/regional/italy/utils.py

Native Payment Entry source:
https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/accounts/doctype/payment_entry/payment_entry.py

## Actual R5 results

At app revision f80cf534fd071d283cb2c8efc6fe3f1fbd0cb920:

- Scoped adapter runtime acceptance: PASS, 10 checks covering real Finance without
  native create/select, canonical reload, invalid amounts, A/B/C/accountant
  negatives, center revocation, native partial posting, idempotence and audit.
- Finance HTTP: 7/9 PASS (security, finance bridge, banking, incoming, professional,
  reporting, TS). Receivables submit and SdI cancellation FAIL with the verified
  File root causes above.
- Later XML fix and expanded acceptance at 8639b7982255: syntax/static PASS only.
  New immutable image was imported, but PSI guard stopped the mission before it
  was started. **The XML fix and login fix have no final runtime acceptance.**
- Browser 14, backend 240, HTTP 55, hooks 6 and R5 real CURRENT rollback:
  NOT EXECUTED. Historical R3/R4 evidence is retained, not counted as R5 PASS.

## Stop and limitations

The unchanged host memory PSI guard fired after image import. All R5 containers
are stopped; no OOM occurred. 112 pre-existing containers retain image, state,
restart count, mounts and network configuration; RC22 HTTP remains 200.
The complete CURRENT checkpoint and CURRENT/QA/TARGET images are preserved.
Do not merge or deploy this draft until actual final-image positive/negative,
Finance/browser/full regression and real rollback acceptance have passed.
