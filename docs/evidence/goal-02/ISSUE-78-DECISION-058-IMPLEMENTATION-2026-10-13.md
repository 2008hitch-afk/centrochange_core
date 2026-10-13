# Issue #78 / UAT-11 — DECISION-058 implementation

**Technical result: PASS for the tested delta; Owner UAT-11: PENDING.** The
earlier [boundary diagnosis](ISSUE-78-UAT11-HISTORICAL-SLOT-DECISION-2026-10-13.md)
remains historical evidence. The approved decision is
[`HC-0005 DECISION-058`](https://github.com/2008hitch-afk/hitch-client-discovery/blob/afda9ae4b9f4f03615adc8c793bca88fd1d4d633/clients/HC-0005/decisions/DECISION-058-governed-historical-same-day-session-time-correction.md).

## Scope and implementation

The PR #128 changes product logic only in `scheduling/booking.py`; the other
code changes are the isolated acceptance probe and its runner. No schema, permission grant, finance service or upstream
Frappe/ERPNext source was changed.

For a proposed start in the past, `reschedule()` now requires native status
`Closed`, closure state `Reopened`, exactly the current historical session
date, a business reason and absence of retained economic/administrative
effects. Only this guarded save carries a document-local correction flag.
`AppointmentMixin.validate()` then verifies the previous persisted closure
state/date, the guarded internal write, and the same economic boundary before
using the unchanged schedule, absence and overlap checks. Ordinary booking
and ordinary reschedule retain their future-time requirement. Same-day end,
Rome timezone/DST and immutable snapshots remain enforced. Relevant
rejection messages are in Italian.

The existing lifecycle `close()` always writes a `CC Settlement` with
`paid=0` for an unpaid completed session. That record is preserved and does
not itself block the approved correction. A paid settlement, `cc_paid=1`,
package `Consumed`/`Released` state, or any non-`RESERVE` package ledger
event blocks it.

Canonical downstream checks block on **any** `CC Economic Source Link` for
the appointment. This immutable source is the parent of managed patient
invoice lines (`Sales Invoice Item.cc_economic_source`), receipts through
native invoice allocation, professional expectations, and fiscal/TS
simulations. An explicit `CC Professional Expectation` also blocks, including
one on another appointment in the same patient/professional/day pair because
DECISION-054 ranks unpaid sessions by time. Direct appointment payment
overrides, administrative exceptions, booking confirmations and native
Communications also block. A `CC Payment Notice` is patient/center scoped
without an exact session reference, so any such notice blocks conservatively.
Query failures return an Italian “impossibile verificare” error and deny the
write. No derived record is edited automatically.

The check covers canonical links stored by this product. A free-text or
otherwise unlinked legacy financial document cannot be attributed safely to
one appointment from this model. Such data requires a separate reconciliation
before Owner UAT; this code does not infer links from names or text.

## Runtime method and result

Single-stack reference: `centrochange-dev`, one Site, Frappe/ERPNext 16.50.0,
Healthcare 16.6.1, Builder 1.35.1. The active backend image remained
`sha256:f38215267771e4db2e42af9312211931dc039b07ff17b69953c10f50026c6285`.
**The correction was not deployed.** The versioned `infra/issue78_historical_probe.py`
loaded the changed booking module and probe into a single Python process
through stdin, ran against the existing synthetic DEV with test fixtures,
and rolled back its transaction. No container source file or persistent
Owner row was patched. No RC22 identifier was used.

Command:

```sh
sg docker -c 'python3 infra/issue78_historical_probe.py'
```

| Scenario | Result |
|---|---|
| Historical Closed → move without reopen; ordinary past booking | DENY |
| Authorized reopen → 28/09/2026 09:00 → 10:00 free slot | PASS |
| Retry; audit before/after; frozen snapshots; later reclosure | PASS |
| Other historical date, empty reason (including replay), collision, absence | DENY |
| Direct document write and cross-professional user | DENY |
| Paid settlement; consumed package state and ledger event | DENY |
| Economic source and professional expectation | DENY |
| Payment override, booking confirmation, unavailable link verification | DENY |
| Ordinary future booking and governed future move/replay | PASS |
| Existing scheduling regression | PASS, 42 checks |

The ten focused check groups and 42 existing scheduling checks passed.
The 33 tracked persistent tables had identical before/after SHA-256:
`5fb8a1be8a3aa9fddb5222bac65a99748ac7303c8a2492310f105e8bd0bc8c5e`.
All fixture and nested economic rows rolled back. This is scoped evidence,
not a backup or Owner acceptance.

## Next gate

PR #128 remains DRAFT. HITCH/Owner must approve the separate operational
deployment gate before the changed source is installed on persistent DEV.
Then Owner can re-run UAT-11 on an eligible synthetic reopened session,
confirm that no economic/administrative links exist, move 09:00 → 10:00
within the same date, inspect audit/replay and reclose. If the chosen Owner
session has a derived fact, the expected result is the Italian block and a
separate economic-administrative correction decision, not an automatic move.
No merge, Mission C, GOAL-03 or Owner PASS is implied.
