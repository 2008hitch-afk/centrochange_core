# #78 — Reopened appointment governed reschedule

Status: backend/runtime PASS; browser regression and Owner UAT-11 recheck pending.
Stack base: `issue-71/audit-register`. Candidate `goal02-20261007-rc20`; same pinned Frappe 16.31.0, ERPNext 16.32.0, Marley 16.5.2, Builder 1.33.0; no migration/reset. All app source bytes checked against branch; test harness follow-up executed through stdin with rollback, never copied/patched into a container.

The Closed status no longer rejects a service request when closure is explicitly Reopened. Cancelled/No Show, closed/auto-lock guards, assignments, slot future/same-day, availability, collision, price/duration snapshots and direct mutation rejection remain unchanged. Native Marley pinned `Patient Appointment.set_status` retains Closed status, confirming why closure state must govern this correction.

Runtime regression (9 checks): Closed ordinary move denied; generic direct save denied; authorized reopen; future scheduled move allowed; retry replay; historical snapshots unchanged; future close denied; close after simulated session end allowed; original and corrected dates in business audit retained. Entire synthetic test transaction rolled back, including all audit/settlement writes. The test initially attempted a past slot and correctly hit the existing future-only scheduling rule; corrected test now uses a future slot and controlled custom clock solely to prove subsequent reclosure. No rule allowing past-slot booking was introduced.

Upstream: https://docs.frappe.io/framework/user/en/api/document and https://docs.frappe.io/framework/user/en/api/hooks; pinned Marley source and runtime authoritative for validation/status. No upstream/core patch or role change. Owner UAT required before closure.
