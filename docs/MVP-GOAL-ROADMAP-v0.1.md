# Centro Change — MVP Goal Roadmap v0.1

**Status:** OWNER APPROVED  
**Approved on:** 2026-10-03  
**Repository:** `2008hitch-afk/centrochange_core`  
**Client:** HC-0005 — Centro Change

## 1. Purpose

This roadmap is the canonical macro-goal path for Centro Change implementation.

It prevents delivery from becoming a sequence of chat-dependent micro-steps.

Codex may work autonomously inside the active goal, creating and resolving the technical issues, branches, PRs, tests and fixes required to reach that goal.

ChatGPT/HITCH reviews progress and goal evidence through GitHub.

The HITCH Owner remains the final authority for material gates.

## 2. Canonical path

```text
CURRENT
  ↓
GOAL-01 — MVP DEV END-TO-END
  ↓
GOAL-02 — MVP READY FOR CLIENT UAT
  ↓
GOAL-03 — PRODUCTION READINESS
  ↓
GOAL-04 — GO-LIVE & STABILIZATION
  ↓
GOAL-05 — DELIVERY CLOSURE & CONTINUITY
```

A goal does not automatically authorize the next goal where a separate HITCH gate is required.

## 3. Current status

| Goal | GitHub issue | Status | Current authority |
|---|---:|---|---|
| GOAL-01 — MVP DEV End-to-End | #22 | **OWNER ACCEPTED / DEV PASS** | Accepted by HC-0005 DECISION-055; [Completion report](MVP-GOAL-COMPLETION-REPORT-2026-10-05.md); draft stack awaits review |
| GOAL-02 — MVP Ready for Client UAT | #23 | **ACTIVE / AUTHORIZED** | Authorized by HC-0005 DECISION-056 |
| GOAL-03 — Production Readiness | #24 | QUEUED | Requires GOAL-02/UAT basis |
| GOAL-04 — Go-Live & Stabilization | #25 | QUEUED | Requires explicit production/go-live authorization |
| GOAL-05 — Delivery Closure & Continuity | #26 | QUEUED | Requires stabilized live delivery |

Technical evidence (distinct from formal authority): GOAL-01 [Completion report](MVP-GOAL-COMPLETION-REPORT-2026-10-05.md); GOAL-02 **TECHNICAL DONE / UAT READY**, [Completion report](GOAL-02-COMPLETION-REPORT-2026-10-05.md). Owner visual UAT / final acceptance pending; no automatic stack merge.

Per la UI cliente del DEV, la [decisione Owner `SINGLE_CLIENT_UI_PREMIUM_ONLY` (#167)](https://github.com/2008hitch-afk/centrochange_core/issues/167#issuecomment-6372823297) richiede soltanto Premium React. Il cutover del routing è distinto dall'accettazione funzionale di Agenda, Pazienti e delle altre aree. Desk Frappe rimane esclusivamente per account tecnici dedicati; GOAL-03 e produzione non sono autorizzati da questa decisione.

## 4. GOAL-01 — MVP DEV End-to-End

**Issue:** #22

### Objective

Deliver a working Centro Change MVP on an isolated, reproducible, non-production DEV runtime.

### Included macro-scope

- reproducible runtime foundation;
- operational core derived from validated `CC-CAP-001..040`;
- Finance/Admin delivery capabilities `CC-CAP-041..050`;
- provider-neutral SdI adapter;
- provider-neutral TS adapter;
- synthetic end-to-end scenarios;
- capability-critical regression/security evidence.

### Existing child work

- implementation epic #20;
- WP-00 / M0 clean runtime #21;
- future implementation issues/PRs created by Codex under this goal.

### Codex autonomy

Codex may autonomously:
- create technical child issues;
- create branches and PRs;
- implement approved baseline behavior;
- execute tests;
- fix normal bugs;
- refactor when needed for the approved goal;
- convert historical decisive probes into product regression tests;
- update technical documentation.

### Stop only for material blocker

Codex must stop/escalate when progress requires:
- changing owner-approved architecture;
- changing client scope;
- a new unresolved business rule that cannot be derived;
- real client/patient data;
- real provider credentials;
- production/server access;
- real SdI/TS traffic;
- material new external cost/dependency;
- production/go-live;
- a technical incompatibility requiring a material architecture change.

### Goal Done

GOAL-01 is complete only when a reproducible DEV MVP exists and an **MVP GOAL COMPLETION REPORT** records PASS/PARTIAL/FAIL, PRs/commits, implemented capabilities, tests/evidence, residual gaps and next-goal recommendation.

## 5. GOAL-02 — MVP Ready for Client UAT

**Issue:** #23

### Objective

Turn the DEV MVP into a stable UAT candidate the client can meaningfully validate.

### Main outcomes

- blocking defects closed;
- deterministic/demo dataset;
- UAT scenarios;
- critical regression green;
- permissions/audit checked;
- known limitations explicit;
- UAT evidence package ready.

### Goal Done

A named reproducible UAT candidate exists with no known critical integrity/security blocker and a client validation guide is ready.

## 6. GOAL-03 — Production Readiness

**Issue:** #24

### Objective

Close the dependencies necessary to make a production authorization decision.

### Main outcomes

- commercialista/fiscal verification;
- final SdI route;
- TS transmitter/credential/rule verification;
- migration/opening-balance decision if needed;
- production topology;
- secret/config model;
- backup/release/cutover/rollback preparation;
- release candidate evidence.

### Goal Done

No hidden production blocker remains and an explicit production authorization can be requested.

## 7. GOAL-04 — Go-Live & Stabilization

**Issue:** #25

### Objective

Execute the separately authorized production launch and stabilize it.

### Main outcomes

- governed deploy;
- approved data/config migration;
- separately authorized real integrations;
- production smoke;
- monitoring;
- critical defect closure;
- stabilization evidence;
- go-live verification.

### Goal Done

Production is verified usable for the authorized scope and initial stabilization is complete.

## 8. GOAL-05 — Delivery Closure & Continuity

**Issue:** #26

### Objective

Close the initial delivery and route all future work correctly.

### Main outcomes

- delivery acceptance evidence;
- handover/runbook;
- current production version baseline;
- known-issue register;
- support ownership;
- future work routed to support/defect/evolution/new opportunity.

### Goal Done

No hidden implementation scope remains and the delivery is ready for formal closure approval.

## 9. Cross-goal rules

### Evidence-first
GitHub is the technical source of truth for implementation status. Chat conversation alone does not complete a goal.

### Goal autonomy
Inside an authorized goal, normal technical progress does not require owner ping-pong.

### Goal gate
A macro goal is completed only from evidence, not because individual issues were closed.

### No authority expansion
A later goal is not automatically authorized by completion of the previous one.

### Data boundary
GOAL-01 uses synthetic data only. Real client/patient data requires a separate authorization when needed.

### Production boundary
No roadmap artifact itself authorizes production, provider credentials or real SdI/TS traffic.


### Cross-client technical learning
At the end of every macro-goal, Codex performs Goal Learning Extraction according to `AGENTS.md` and the governance in `2008hitch-afk/erpnext-frappe-delivery-knowledge`.

Only sanitized `CANDIDATE` learning artifacts may be created autonomously. Promotion to `APPROVATO` requires HITCH review and explicit Owner approval.

The completion report must record the candidate learning artifacts produced or `NO_GENERALIZABLE_LEARNING`. This housekeeping requirement does not alter the technical PASS/PARTIAL/FAIL result of the client goal.

## 10. Current command for Codex

GOAL-01 is formally accepted by HC-0005 DECISION-055.

GOAL-02 (#23) is formally authorized by HC-0005 DECISION-056.

> Execute **GOAL-02 — MVP Ready for Client UAT (#23)** autonomously according to this roadmap and `AGENTS.md`. Reuse the accepted GOAL-01 DEV candidate, load only relevant `APPROVATO` generalized learnings, verify upstream behavior against official documentation/pinned source/runtime, and continue through the technical child work required to reach GOAL-02 Done. Stop only for a material blocker. Keep all production, real-data, real-provider and GOAL-03 gates closed.

Required technical deliverables: named synthetic UAT candidate, client validation package, whole-goal learning extraction and GOAL-02 Completion Report. No automatic stack merge or real provider traffic.

