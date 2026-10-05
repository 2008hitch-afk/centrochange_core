# GOAL-02 — UAT Evidence Package

**Result: PASS / UAT READY**, 2026-10-05. Named candidate: **goal02-20261005-rc1**. Client UAT: **NOT_EXECUTED**; Owner acceptance: **PENDING**.

The [candidate manifest](UAT-CANDIDATE.json) identifies immutable application code, local image ID and semantic dataset hash. Later documentation commits do not alter that application image. This is a DEV candidate, not a published registry release.

| Evidence | Result and scope |
|---|---|
| [Build](evidence/build.json), [image parity](evidence/image.json) | PASS; exact git archive, 171 tracked app files match, six app services use one image, no source overlay |
| [Upstream compatibility](evidence/upstream.json), [sources and approved learning](UPSTREAM-AND-KNOWLEDGE-BASELINE.md) | PASS; 12 official pinned source files byte-verified; 18 formally approved learnings consulted as advice |
| [Runtime](evidence/runtime.json), [baseline](evidence/runtime-baseline.json) | PASS; login, assets, websocket, enabled scheduler, actual short/long jobs, native synthetic smoke; 977 schema tables |
| [Critical regression](evidence/critical-regression.json) | PASS; 12 suites, 189 direct checks, 160 HTTP groups, 35 browser checks plus one actual Notification Log worker delivery |
| [Threshold browser](evidence/threshold-browser.json) | PASS; eight corrective-policy UI checks |
| [Dataset](evidence/dataset.json), [reproduction](evidence/dataset-reproduction.json) | PASS; eight validations, reset/recreate semantic hash equality; generated native IDs change and passwords rotate |
| [Modifying UAT browser](evidence/uat-exercise-browser.json) | PASS; 21 checks including reasoned due-date deferral, original native debt retained |
| [Final read-only UAT browser](evidence/uat-readonly-browser.json) | PASS; 20 checks on final restored starting dataset, seven identities, direct API denials, desktop/mobile and no JS exceptions |
| [Private preparation guards](evidence/management-guards.json) | PASS; five checks, privileged local-only preparation, both DEV flags required, no whitelisted credential/reset API |
| [Scheduler](evidence/scheduler.json) | PASS for configuration and separately evidenced real workers; no claim of successful completion based only on periodic last_execution timestamps |

The integrated runner stopped between suites; completed passing suites were retained and only remaining suites resumed. All suites have completed PASS and disposable cleanup. No raw logs, cookies, credentials or private manifest are committed. Browser plugin was unavailable; the documented fallback uses Playwright 1.58.2 in its pinned container.

Reviewed synthetic screenshots: [mobile validation guide](evidence/uat-guide-mobile.png), [desktop Finance/TS](evidence/uat-finance-desktop.png). The guide is also rendered at `/validazione`, linking role-scoped operational and Finance workspaces.

The [Client Validation Guide](CLIENT-VALIDATION-GUIDE.md) contains 16 scenarios and expected outcomes; its client result fields intentionally remain NOT_EXECUTED. [Known limitations](KNOWN-LIMITATIONS.md) distinguish simulations and readiness from fiscal certification, production qualification or completed client validation. [Operator reproduction](OPERATOR-REPRODUCTION.md) provides exact build/seed/reset/handoff commands. Passwords are generated locally and delivered outside Git in a 0600 file.

## Failures and discarded assumptions

- An old agenda response could replace the selected Patients view. Issue #59 / PR #60 adds generation/context guards; deterministic delayed-response reproduction failed before the fix and passes on the candidate.
- Preparation initially reevaluated projections before initializing each source. Explicit source capture precedes reevaluation; no financial policy changed.
- A browser probe initially selected an old invoice detail while the next detail loaded. Controls are cleared during loading and guarded by context; the final browser suite exercises the resulting behavior.
- A modifying browser run lost connectivity after an authorized deferral. Retrying against this mutated dataset correctly failed its initial-state assertion. Seed replay retained the mutation; explicit owned reset/reseed restored initial state, then all 21 checks passed. This was not treated as a new product business rule or silent-reset permission.
- Native Patient names are deterministic and therefore are not proof that recreation happened. Changed generated Item Price/Schedule IDs, rotated credentials and equal normalized semantics provide the discriminating reset/recreate evidence.

## Learning extraction

Whole-goal extraction produced only **EFK-CANDIDATE-0019 — RECIPE: persistent synthetic validation dataset**, [knowledge draft PR #3](https://github.com/2008hitch-afk/erpnext-frappe-delivery-knowledge/pull/3), commit `aa21326af645bbd1b921fd29d86ca24e10c694f5`. The artifact is CANDIDATE / PENDING, sanitized and generic. Other observations duplicate already approved knowledge. Approved files and governance were unchanged; no promotion or merge occurred.
