# #81 — Recognizable professional expectation selection

Status: TECHNICAL PASS / READY_FOR_OWNER_UAT; Owner UAT-15 pending.
Branch `issue-81/readable-expectations`, base `issue-78/governed-reschedule`; candidate `goal02-20261007-rc22`, pinned dependencies unchanged, no migration/reset.

Frontend only: option values remain exact canonical expectation IDs; labels use already authorized appointment/fiscal-subject label, Italian date, professional display name, expected EUR amount or explicit unknown, and state. No new backend query/visibility. New targeted runtime regression rolls back comparison/audit and verifies explicit Amount Difference, replay, exact reference, no new Purchase Invoice/GL/Payment Ledger and A/B/C denials. Initial browser caught an embedded technical prefix; corrected; browser repeat PASS for readable fields, exact selected value and A/B/C API denials, without JS errors. The old whole-chain professional harness assumes globally empty accounting tables; it is unsuitable for the preserved Owner UAT dataset and is not evidence of a product failure. Dataset not reset; targeted discriminant used instead.

Existing canonical comparison and native invoices unchanged. Official documentation: https://docs.frappe.io/framework/user/en/api/rest and https://docs.frappe.io/framework/user/en/api/database; runtime existing reporting projection reused.
