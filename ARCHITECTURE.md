# Centro Change — implemented DEV architecture

**Status: IMPLEMENTED DEV / GOAL-01 DONE / DEV PASS.**

The approved scope and native/extension/custom boundaries remain those of [the implementation baseline](docs/MVP-IMPLEMENTATION-BASELINE-v0.1.md), [capability map](docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml) and HC-0005 delivery decisions. Current implementation evidence is in [the GOAL-01 report](docs/MVP-GOAL-COMPLETION-REPORT-2026-10-05.md). This document records implementation; it does not authorize architecture, fiscal or production changes.

## Native ownership

Frappe owns authentication, User/Role primitives, permission hooks, private File storage, Communication/Notification Log, scheduler/queues and native backup. ERPNext owns Company, Customer, Supplier, Account, Cost Center, Item/Item Price/Price List, Mode of Payment, Sales Invoice, Purchase Invoice, Payment Entry, Bank/Bank Account/Bank Transaction, GL and Payment Ledger. Marley Healthcare owns the central Patient, Healthcare Practitioner identity, canonical Patient Appointment, Practitioner Schedule and Practitioner Availability. Branch is the shared center registry; explicit native Cost Center/Company mappings carry accounting context.

No upstream core is patched. Supported doctype mixins, events, permission queries and whitelisted-method overrides implement the required guards in `centrochange_core`. Exact pinned versions and commits are in `infra/Dockerfile` and `infra/compose.yaml`.

## Operational extensions

- `security`: center membership, patient/practitioner assignment, replacement/reassignment/offboarding, current transactional reads, minimal append-only audit and direct/API/export/report/session guards. Native identity is reused through exact UID discovery and explicit audited assignment. DEV intake accepts fictional inputs and freezes a payload-bound retry key.
- `scheduling`: native appointment booking/move/cancel, recurring availability and exceptions, patient/practitioner overlap prevention, serialized concurrent mutation, fixed public Marco/Francesca first-meeting ingress and backend-only subsequent sessions. Item Price is resolved on the Europe/Rome booking date; service/price/currency/duration snapshots stay immutable through catalog changes and rescheduling.
- `operations`: organizational notes separate from author-only clinical notes; native appointment closure/disposition extensions; append-only operational settlements and package grant/reserve/consume/release/correct/adjust events. Exactly 48 elapsed hours is timely. 21:00 reminder and next-day 07:00 lock use Europe/Rome boundaries, retry-safe catch-up and synchronous lock enforcement. Native internal notifications are delivered by real workers.

Operational paid status is an audited fact, not accounting settlement. Package balance derives from its ledger; it is not a second money ledger. No package sale price is inferred from unit count and service tariff. Native shared Patient fields are not a clinical-note store. Management/Secretariat/Finance/Accountant do not inherit private-note access.

## Finance/Admin extensions

`CC Economic Source Link` freezes session and accounting context and links native document lines; it is a bridge, not accounting truth. Explicit mapping/review services control native invoice drafts, submit, payments, cancellation, credit and amendment. Bank import uses native Bank Transaction; suggestions never auto-post, and human selection records native allocations/payments with replay protection.

Payment agreements retain Immediate/Month End/Specific Date terms. Previous unpaid debt blocks a subsequent booking/performance unless an authorized, audited reason and extended deadline are recorded. Original native debt remains. Local patient email traces are simulated native Communication; no real SMTP delivery is claimed.

Incoming XML is bounded, fictional and privately retained with immutable hash/identity. Explicit supplier/line/account/tax review precedes native Purchase Invoice creation. Compensation rules and snapshots are explicit and parametric; missing rules or a missing explicit professional threshold produce unknown amounts and administrative review, never implicit zero. HC-0005 DECISION-054 supplies a versioned non-negative threshold per professional, counted separately per patient/professional pair. Chronological unpaid sessions up to N mature; excess positions remain SUSPENDED. Native payment changes and scheduled reconciliation append deterministic reevaluations and update one condition per session. Management-only audited overrides preserve original unpaid/threshold/rule/source facts. Expected/received comparison reads native Supplier invoices. The condition-based queue supports assignment, priority, deadlines, defer/reappearance and automatic resolution when the underlying condition clears.

Reports compose operational sources and native submitted/cancelled/return/payment states in a bounded center/date scope. Shared Customer/Supplier figures remain shared fiscal-subject totals; no patient/professional allocation or undefined margin is invented. Accountant is read-only. Finance generic mutation and unscoped native report/helper paths are controlled server-side.

## Separate fiscal adapters

SdI and TS have separate provider-neutral simulated adapters. Private immutable transactions/payloads and append-only attempts retain source/document versions, request hashes, actor provenance, normalized states, synthetic protocols/receipts and bounded retry classification. Real short workers execute simulations; replay and recovery do not duplicate attempts. Accepted correction descendants resolve unresolved administrative ancestors without rewriting history.

TS separately retains exact source/invoice/patient, explicit fictional expense classification, opposition and subject/transmitter snapshots. Missing/unverified inputs remain pending and cannot submit. Management may record explicit synthetic eligibility for DEV tests. TS never calls SdI. Commercialista verification, final real fiscal population/correction responsibilities, SdI route, TS subject/transmitter/credentials and production activation remain gates.

## Interfaces and runtime

`/centrochange`, `/finanza` and `/primo_incontro` compose guarded APIs; supported native Desk pages handle accounting/catalog/identity administration. Browser controls never substitute for server authorization. Finance responses from an older request/center/view cannot overwrite the current view.

The isolated `centrochange-dev` Compose project uses pinned images/apps, localhost HTTP, private DB/Redis networks and four dedicated named volumes. Fresh bootstrap completes native ERPNext setup, installs all apps, migrates, builds/exposes assets and starts backend, frontend, scheduler, two workers and WebSocket. The final candidate uses a committed image without source binds; the separately versioned development overlay is only for development/debugging. Empty-volume database startup has an initial health grace period and becomes healthy as soon as checks succeed.

## Verification and boundaries

Versioned direct, actual HTTP and pinned Playwright harnesses exercise nonempty authorized/unauthorized paths, concurrency, native money trace, corrections, privacy, idempotency and worker execution. Direct fixtures fully roll back and clear callbacks; HTTP/browser fixtures use exact synthetic ownership cleanup. Source-byte parity, fresh runtime snapshots and destroy/recreate equivalence are separate evidence. Native backup is encrypted/integrity checked outside Git; restore/DR and upgrades remain deferred.

GOAL-01 is DEV and synthetic only. It does not authorize UAT, real data/providers, real SdI/TS traffic or production. Open policy values and later-goal recommendations are recorded explicitly in the completion report. Technical controls alone are not a compliance certification.
