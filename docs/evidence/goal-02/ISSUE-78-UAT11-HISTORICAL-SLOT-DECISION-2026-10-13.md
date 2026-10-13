# Issue #78 / UAT-11 — historical slot correction decision

**Outcome: PARTIAL — exact business decision required before product change.** The
Owner's 28 September 2026 09:00 → 10:00 case is reproducible without touching
its historical record. UAT-11 remains open; no Owner PASS is inferred.

## Baseline and authorized boundary

- GitHub issue #78 remains open. This branch starts at PR #127 HEAD
  `f0521445257a8298c35d8056c94f7a7b64254f0e`, with PR #126 still DRAFT.
- Existing `centrochange-dev`: one site, Frappe and ERPNext 16.50.0,
  Healthcare 16.6.1, Builder 1.35.1. Active backend image:
  `sha256:f38215267771e4db2e42af9312211931dc039b07ff17b69953c10f50026c6285`.
- No deployment, site reset, seed, data correction, permission change or merge.

## Cause and approved rule check

`reschedule()` allows a `Closed` native appointment only if its closure state is
`Reopened`, then saves the canonical `Patient Appointment`. The guarded
`AppointmentMixin.validate()` calls `validate_slot()`, which rejects a start at
or before current Rome time for **every** save. The rejection occurs before
schedule, absence and collision checks. Thus this error is a date-policy
rejection, not evidence of an occupied 10:00 slot or practitioner unavailability.

The accepted #78 implementation and its prior report explicitly tested a
**future** destination and retained a negative future-time restriction. The
report says no rule allowing past-slot booking was introduced. The approved
CC-CAP-022..026 lifecycle permits audited correction after reopen, but neither
it nor issue #78 specifies that the corrected start may be in the past. The
UAT guide says “modifica/chiudi dove consentito” without defining this date
boundary. The Owner's observation establishes the desired test case, but the
latest mandate expressly reserves a new business rule for Owner decision.

## Isolated runtime evidence

Run from the host checkout, using the versioned probe source through stdin:

```sh
sg docker -c 'python3 infra/issue78_historical_probe.py'
```

The probe creates its own synthetic center/practitioner/patient/service, a
Monday schedule, and a 28 September 2026 09:00 appointment under a test-only
clock. It closes and reopens that appointment through the real services. It
never reads or mutates the Owner's appointment or an RC22 identifier. The
existing DEV source is executed; the test source is loaded into memory only.

| Check | Result |
|---|---|
| Ordinary booking in the past | DENY as expected |
| Closed appointment moved without reopen | DENY as expected |
| Authorized reopen and replay; direct document mutation | PASS; direct bypass denied |
| Reopened, same historical date 09:00 → 10:00 | DENY with `Appointment requires a future same-day interval`; document and audit unchanged |
| Reopened, move to occupied future slot | DENY with collision error |
| Reopened, future move without business reason | DENY; audit unchanged |
| Reopened, move to free future slot and replay | PASS; one before/after audit event |
| Price/duration snapshots and persistent data | Unchanged |

Runner result: `PASS` for **eight discriminating checks**, including the
expected historical rejection; the historical correction itself is **FAIL for
Owner's requested workflow**. Full transaction rollback completed. The
SHA-256 of 21 tracked persistent tables before/after was identical:
`317149da22f7a9b14e8cf4fcb3fcd9c77c6ab9bb64454cc614abcea34d6732ed`.
This hash is a scoped database check, not a full backup or system-wide audit.

## Decision requested from Owner

Should an explicitly authorized `Reopened` session be movable to a **past slot
on the same historical date**, subject to existing schedule, absence,
collision, permission, reason, audit, snapshot and replay controls?

If yes, the rule should also say whether a session already linked to an
invoice, payment, package consumption or professional compensation can be
moved, or must instead use its existing economic correction path. Those
downstream facts may depend on session time/order. The narrowest safe
implementation would exempt only the reopened governed reschedule path from
the future-start check, retain the same-day and all other guards, provide an
Italian error for disallowed dates, and add direct/API negative tests. This is
a recommendation, **not an implemented policy**.

Until that decision, keep the current future-only invariant. A normal booking
must still reject past dates. No fix has been distributed to the persistent
DEV. After approval, implement and test the bounded service change in this
PR; deployment needs the separately requested operational confirmation.
