# AUDIT-04 Pazienti Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` task by task. This plan follows Issue #167 and the approved HC-0005 decisions; the Owner requested one autonomous cycle.

**Goal:** Make `/premium/#Pazienti` complete for approved patient workflows, with evidence from real Frappe on an isolated synthetic Site.

**Architecture:** Keep Marley Patient, CC assignments, notes and package ledger authoritative. Extend only the existing React view and narrowly scoped projections; retain the current Frappe session, CSRF and service guards. Use an isolated Site/DB for every write test and leave `centrochange-dev` unchanged.

**Tech Stack:** React 19, TypeScript, Playwright, Frappe 16, ERPNext 16, Healthcare 16, MariaDB 11.8.

**Spec:** GitHub Issue #167; `docs/qa/FUNCTIONAL-COVERAGE-DETAIL.csv`; HC-0005 DECISION-005/006/011/018/063.

## Global Constraints

- No DEV install, merge, schema, DocPerm, role or production change.
- No standalone Patient creation or arbitrary Patient→Customer link.
- B remains inactive on DEV; use two synthetic operational centers only in the disposable clone.
- Notes stay separate and private text stays visible only to the assigned professional.
- Use exact owned synthetic fixtures; verify isolated environment teardown by resource ID.

## Review Focus

- A reused central Patient in another center must not expose that center's notes, appointments or packages.
- A revoked professional must lose direct API and list access immediately.
- Repeating an identical package issuance as a new user action must create a new package; retrying the same action must replay once.
- Search beyond the first 50 results must say it is truncated; stale/failed requests must not display earlier results as current.
- A lost response after an authorized write must not create duplicate records or silently overwrite a newer Patient version.

### Task 1: Acceptance oracle and baseline

**Files:** Create `docs/qa/AUDIT-04-PATIENTS-UAT.md`; update only relevant matrix rows later.

- [ ] Map each Issue #167 capability to UI action, API, DocType, role/center, positive and negative test.
- [ ] Reproduce baseline gaps with Playwright or isolated Frappe; record failure before modifying product code.
- [ ] Record existing approved cross-center behavior and deferred scope separately.

### Task 2: Patient list, profile and history

**Files:** Modify `frontend/premium/src/views.tsx`; create focused Patient components if needed; test `frontend/premium/tests/patients.spec.ts`.

- [ ] Write failing tests for search loading/empty/error/truncation, Patient detail, Manager edit/version conflict, and history timeline.
- [ ] Reuse `workspace.patient_search`, `profiles.patient_detail/patient_save`, `workspace.patient_history` and `workspace.appointment_events`.
- [ ] Show approved administrative fields and permit only Manager to save through existing typed adapter.
- [ ] Re-run the focused browser tests, React typecheck and build.

### Task 3: Assignments, notes and packages

**Files:** Modify `patient_assignments.tsx`, `patient_packages.tsx`, `note_history.tsx`; add narrow backend projection only if existing methods cannot show approved history; tests in existing Python and Playwright suites.

- [ ] Write failing tests for searchable professional selection, assign/revoke/reassign, private/organizational note create/correct and package issue/adjust/reissue.
- [ ] Reuse current service guards and append-only audit/ledger; preserve `request_key` only across retry of one action.
- [ ] Verify in an isolated real Site that center, role, direct API, CSRF, concurrency and rollback boundaries hold.

### Task 4: Isolated UAT and regression

**Files:** Create or update an `infra` acceptance harness only when needed; keep credentials, snapshots and screenshots outside Git.

- [ ] Verify clone identity, distinct Site/DB/volumes/network and baseline fingerprint before writes.
- [ ] Exercise real HTTP/API and browser desktop 1440×900/mobile 390×844 with seven roles plus Guest and two synthetic centers.
- [ ] Check expected DB/audit/ledger state, teardown by exact resource IDs, and DEV unchanged.
- [ ] Run offline Python, TypeScript, build, Playwright and relevant prior audit regressions.

### Task 5: Independent review and delivery

**Files:** Update `docs/qa/FUNCTIONAL-COVERAGE-MATRIX.md`, `FUNCTIONAL-COVERAGE-DETAIL.csv`, interface inventory and UAT report.

- [ ] Have independent reviewer inspect exact HEAD, tests and permission claims; resolve Critical/Important findings.
- [ ] Commit and push branch; open DRAFT PR linked to #167; wait for CI on exact SHA and fix failures.
- [ ] Post synthetic evidence and limits to #167/PR; attempt #156 only if accessible.
- [ ] Report `READY_FOR_OWNER_UAT` only if isolated real UAT, CI, review and cleanup all pass.
