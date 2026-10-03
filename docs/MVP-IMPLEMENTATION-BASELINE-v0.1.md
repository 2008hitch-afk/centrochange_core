# Centro Change — MVP Implementation Baseline v0.1

**Status:** OWNER-AUTHORIZED IMPLEMENTATION BASELINE  
**Date:** 2026-10-03  
**Client:** HC-0005 — Centro Change  
**Purpose:** executable technical handoff for Codex. This document does not replace client governance or production gates.

## 1. Definition of MVP in this repository

For Centro Change, "MVP" means the **first complete implementation baseline** that is safe and operable for the approved current scope.

It is not a reduced prototype that ignores security, audit, reproducibility or accounting integrity.

The implementation is composed of two inherited layers:

1. **Operational Core / Step 1** — the capability set already evaluated through `CC-CAP-001..040`, with deferred capabilities kept deferred unless explicitly reactivated.
2. **Finance/Admin extension** — the accepted HC-0005 delivery delta, including ordinary Sistema Tessera Sanitaria submission and the separate SDI adapter boundary.

## 2. Authoritative source order

When sources appear inconsistent, Codex must use this order and stop/escalate if a material conflict remains:

1. client delivery decisions and approved scope in `2008hitch-afk/hitch-client-discovery/clients/HC-0005/`;
2. this implementation baseline and its capability map;
3. `docs/CAPABILITY-EVALUATION-MATRIX.md`;
4. `docs/DECISIONS.md`;
5. cleanup-verified/runtime evidence in `2008hitch-afk/centrochange-testlab`;
6. older architecture/spike documents as historical evidence only.

No old proposal may override a later owner-approved classification.

## 3. Technical foundation

### Current clean-bootstrap seed

Use the current repository-pinned Frappe/ERPNext/Builder/MariaDB/Redis baseline as the starting point for WP-00.

Known validated Marley/Healthcare reference from the prior runtime evidence:

- app repository: `earthians/marley`;
- Frappe app name: `healthcare`;
- tag: `v16.5.2`;
- commit: `934d6c162868139dfbe80c23d6102adb7ec25adb`.

This Marley reference is a **verified seed pin**, not an instruction to skip compatibility checks.

WP-00 must prove the complete clean bootstrap with Marley declared in versioned infrastructure. If the current upstream stack requires a different compatible Marley pin, Codex must produce evidence and request a decision rather than silently changing architecture.

### Foundation rule

```text
fresh clone
→ pinned image/apps
→ build
→ fresh site
→ ERPNext setup
→ install healthcare
→ install centrochange_core
→ migrate/assets
→ workers/scheduler/websocket
→ health/smoke
→ synthetic fixtures
→ capability regression
```

No manual container patch is an acceptable persistent solution.

## 4. Canonical application ownership

```text
Frappe / ERPNext
├─ identity/auth primitives
├─ accounting master + documents
├─ reports/export/print infrastructure
├─ bank/accounting primitives
└─ background/runtime primitives

Marley / Healthcare
├─ Patient
├─ Healthcare Practitioner
├─ Patient Appointment
├─ Practitioner Schedule
└─ Practitioner Availability

centrochange_core
├─ server-side authorization guards
├─ assignment/reassignment lifecycle
├─ appointment concurrency boundary
├─ public booking ingress
├─ historical snapshots
├─ packages / ledgers
├─ settlement/economic disposition
├─ closure / 48h / correction rules
├─ private professional notes
├─ business audit
├─ reporting/dashboard joins
├─ finance bridge
├─ admin exception queue
├─ SDI adapter
├─ TS adapter
└─ regression / acceptance tests
```

Do not duplicate Patient, Practitioner or Patient Appointment merely to simplify implementation.

ERPNext becomes authoritative for submitted accounting documents, balances and reconciliation once accounting is active.

## 5. Proposed code layout

Codex may adapt names to Frappe conventions, but responsibilities must remain separated.

```text
centrochange_core/
├─ security/
│  ├─ permissions.py
│  ├─ guards.py
│  └─ service_identity.py
├─ healthcare/
│  ├─ practitioner_lifecycle.py
│  ├─ patient_assignment.py
│  ├─ appointment_guard.py
│  ├─ availability.py
│  ├─ concurrency.py
│  └─ patient_feed.py
├─ operations/
│  ├─ service_snapshot.py
│  ├─ settlement.py
│  ├─ packages.py
│  ├─ cancellation.py
│  ├─ closure.py
│  └─ corrections.py
├─ finance/
│  ├─ mappings.py
│  ├─ economic_source.py
│  ├─ receivables.py
│  ├─ reconciliation.py
│  ├─ incoming_invoice.py
│  ├─ professional_economics.py
│  └─ exceptions.py
├─ integrations/
│  ├─ sdi/
│  └─ ts/
├─ reporting/
├─ jobs/
├─ api/
└─ tests/
```

This is a responsibility map, not permission to invent DocTypes before checking native fit.

## 6. Implementation sequence

### Wave 0 — WP-00 clean foundation
- make Marley/Healthcare part of the reproducible build;
- complete ERPNext setup synthetically;
- prove fresh rebuild;
- establish test fixtures and smoke/regression harness.

### Wave 1 — security + canonical identities
Primary inherited capabilities:
`001, 002, 003, 004, 033, 034, 038, 039, 040`.

Output:
- safe User/Practitioner lifecycle;
- Patient assignment boundary;
- common server-side guard primitives;
- audit primitives;
- direct/API/report/export/query negative-test harness.

### Wave 2 — scheduling and services
Primary inherited capabilities:
`005..013`.

Output:
- canonical Patient Appointment lifecycle;
- practitioner schedule/absence;
- row-lock concurrency protection;
- public first-meeting ingress;
- backend-only subsequent sessions;
- service/price snapshots.

### Wave 3 — operational economics and patient operations
Primary inherited capabilities:
`014, 016..020, 022..026`.

Output:
- operational economic disposition;
- package ledger;
- organizational/private notes;
- unified patient operational surface;
- guarded history feed;
- closure/reminder/autolock;
- 48h cancellation + audited waiver/correction.

### Wave 4 — communication and management surfaces
Primary inherited capabilities:
`027..030, 035`.

Output:
- notification reliability;
- reports/export/print/email;
- management dashboard;
- backup procedure.

### Wave 5 — Finance/Admin core
New delivery capabilities `CC-CAP-041..047`.

Output:
- operational-to-accounting bridge;
- receivables/invoicing/payment;
- bank reconciliation;
- incoming e-invoices;
- professional economics;
- admin exception queue;
- finance reporting/security.

### Wave 6 — fiscal adapters
New delivery capabilities `CC-CAP-048..049`.

Output:
- provider-neutral SDI adapter;
- provider-neutral TS adapter;
- retry/idempotency/audit/exception handling.

Provider-specific activation remains separately gated.

### Wave 7 — integrated hardening
New delivery capability `CC-CAP-050` plus inherited security/reproducibility regression.

Output:
- cross-domain regression;
- UAT evidence set;
- release-readiness package;
- explicit remaining production gates.

## 7. Deferred legacy capabilities

The following remain deferred unless a later owner decision reactivates them:

- `CC-CAP-021` Patient Progress / clinical analytics;
- `CC-CAP-031` full branded public website;
- `CC-CAP-032` Builder/Git reproducibility specifically for that deferred website surface;
- `CC-CAP-036` full DR rehearsal;
- `CC-CAP-037` upgrade/migration rehearsal if its final discriminating evidence is not yet canonical at implementation start.

Historical `CC-CAP-015` was "future invoice/payment/accounting pathway". The accepted Finance/Admin project now activates accounting through the new delivery capability set `041..050`; do not silently reinterpret the old CC-CAP-015 evidence as proof that the new Finance/Admin implementation already exists.

## 8. Test reuse rule

The existing 40-capability evidence is not throwaway research.

For each inherited capability Codex must:

1. read the canonical classification;
2. locate the corresponding testlab evidence/probe;
3. preserve the proven native/extension/custom boundary;
4. convert the decisive scenario into automated product regression where practical;
5. rerun only what is necessary against the new clean runtime;
6. never replace a negative security test with a UI-only check.

A capability is not implementation-complete merely because its historical probe passed. Historical evidence determines **how to build**; the new regression proves **the implementation still behaves correctly**.

## 9. Synthetic fixture policy

Initial DEV fixtures must be clearly artificial, e.g.:

- `patient.alpha@example.invalid`;
- `professional.a@example.invalid`;
- synthetic CF-like identifiers explicitly marked invalid/test-only;
- fake appointments/prices/payments;
- fake invoice numbers and XML payloads;
- fake bank movements;
- fake SDI/TS responses.

No real patient/client identifiers, invoices, fiscal documents, credentials or provider tokens.

Fixtures required for regression should be deterministic and reproducible from code/test setup, not manually typed into a persistent DEV database as hidden state.

## 10. Definition of done per unit

Every implementation issue/PR must provide:

- capability/work-package IDs;
- source decisions/evidence;
- changed code/modules;
- schema/migration impact;
- automated tests;
- relevant runtime test;
- security negative tests when applicable;
- idempotency/concurrency test when applicable;
- synthetic fixture/cleanup evidence;
- result: PASS / PARTIAL / FAIL;
- residual risks/unknowns.

No merge solely because the happy path works.

## 11. First executable milestone

The first milestone is **M0 — Reproducible Clean Runtime**.

It is complete only when:

- Marley/Healthcare is declared and pinned in versioned bootstrap;
- a clean site can be created from repository inputs;
- ERPNext setup is reproducible with synthetic configuration;
- all required apps install and migrate;
- assets build;
- workers/scheduler/websocket are healthy;
- synthetic smoke fixtures can be created;
- no hidden manual patch is required;
- the environment can be destroyed and recreated with the same result.

Only after M0 should Codex begin feature implementation waves.

## 12. External gates that remain closed

Implementation authorization does not imply:

- real patient/client data;
- production server access/change;
- provider credentials;
- real SDI traffic;
- real TS traffic;
- production accounting activation;
- go-live.

Those gates remain governed separately by HC-0005 delivery decisions.
