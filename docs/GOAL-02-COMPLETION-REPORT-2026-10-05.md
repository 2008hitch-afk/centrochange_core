# GOAL-02 COMPLETION REPORT — MVP Ready for Client UAT

**Technical result: PASS / UAT READY — 2026-10-05.** The roadmap Done Gate is met: a named reproducible DEV candidate exists, critical regression is green, representative scenarios and client guide are ready, and no known critical integrity/security blocker remains in the tested scope. Client UAT has **NOT_EXECUTED** status. Owner acceptance is **PENDING**; this report does not confer either acceptance or GOAL-03 authorization.

## Authority and baseline

GOAL-02 #23 is authorized by HC-0005 DECISION-056. GOAL-01 is OWNER_ACCEPTED / DEV PASS under DECISION-055. The accepted stack and reproducible foundation were reused, including DECISION-054's professional unpaid-session threshold, exact 48-hour timely cancellation and booking-date Item Price resolution with immutable session snapshot. No new business rule was introduced.

The existing draft stack #27, #30, #32, #34, #36, #38, #40, #42, #44, #47, #48, #50, #52, #54, #56 and #57 remains unmerged. GOAL-02 adds issue #59 / [draft PR #60](https://github.com/2008hitch-afk/centrochange_core/pull/60), fix `2f905ef`, and issue #58 / [draft PR #61](https://github.com/2008hitch-afk/centrochange_core/pull/61), immutable code commit `e33ce0385ab921ff50857c4d5e8f61f4721476e0`.

## Named candidate

**goal02-20261005-rc1**, image `centrochange-uat:goal02-20261005-rc1`, local Docker image ID `sha256:41bf781af80ccce7a46831e5148bce08d8c606159ace0f750be639498eb9115a` (not a registry digest). Exact tracked source archive was built and deployed on the isolated existing DEV volumes. Six application services share the image without source overlays. 171 app files match the committed manifest. Accepted GOAL-01 fresh-site/destroy-recreate foundation evidence is reused; this goal does not mislabel deployment on existing volumes as a new fresh-site cycle.

The [machine-readable manifest](uat/UAT-CANDIDATE.json), [evidence package](uat/UAT-EVIDENCE-PACKAGE.md) and [operator recipe](uat/OPERATOR-REPRODUCTION.md) identify the build, pins and reproduction procedure. Frappe 16.31.0, ERPNext 16.32.0, Marley 16.5.2 and Builder 1.33 remain pinned. Official documentation and 12 byte-verified pinned source files support compatibility; [upstream and knowledge baseline](uat/UPSTREAM-AND-KNOWLEDGE-BASELINE.md) records applicability limits.

## Done Gate assessment

| Requirement | Result | Evidence / outcome |
|---|---|---|
| Stabilization and blocking defects | PASS | Stale operational response corrected; deterministic pre-fix failure / candidate success. No outstanding known critical blocker in exercised scope |
| Deterministic representative demo | PASS | Persistent goal02-demo-v1: seven identities, eight synthetic patients, two centers/professionals, ten sessions and native Finance fixtures; eight validation checks |
| Scenarios and client-facing UI | PASS | [Guide](uat/CLIENT-VALIDATION-GUIDE.md): 16 realistic scenarios, role-specific instructions, expected outcomes; `/validazione`, readable financial states, package balance and authorized deferral control |
| Critical regression | PASS | 189 direct checks, 160 HTTP groups, 35 browser checks plus actual notice delivery; eight threshold browser checks |
| Permissions, segregation, audit | PASS | Seven-identity browser checks; foreign-center/professional denials, private note exclusion, read-only Accountant, Management controls, server-side direct API/POST checks and retained native/append-only audit |
| Finance/Admin end-to-end | PASS | Native submitted invoices, partial/full receipt, payable and bank reconcile/reversal, overdue block/authorized deferral, compensation unknown/suspension and queue; reports reconcile native accounting truth |
| SdI and TS | PASS — SIMULATED ONLY | Actual workers persist separate pure simulated outcomes/retries; unresolved TS eligibility remains explicit and blocked |
| Runtime/background jobs | PASS within scope | Login/assets/websocket, enabled scheduler, real short/long jobs and notice/fiscal worker execution. Periodic timestamps do not alone certify per-job successful completion |
| Reproducible candidate and dataset | PASS | Exact image/source parity; semantic reset/recreate hash equality, changed generated IDs and rotated passwords; seed replay preserves authorized mutation |
| Guide, limitations and evidence | PASS | [Known Limitations Register](uat/KNOWN-LIMITATIONS.md), [UAT Evidence Package](uat/UAT-EVIDENCE-PACKAGE.md), this report |
| Whole-goal learning extraction | PASS | EFK-CANDIDATE-0019, knowledge draft PR #3; no approved changes or promotion |

Final normalized dataset SHA256: `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`. A modifying 21-check UAT browser run passed, then the fixture was explicitly reset/reseeded. Final read-only 20-check browser run, dataset validation and image acceptance passed. DEV is left at the expected initial client-validation state. Generated account handoff is `/tmp/cc-goal02-uat-accounts.json`, mode 0600, outside Git; it is not durable credential storage or a production account policy.

## Technical changes and verification limits

The smallest product deltas add client-readable Finance states and source labels, visible scoped package balances, approved due-date deferral through the existing audited service, the guarded synthetic-only validation guide and asynchronous view protection. Private preparation/CLI tooling freezes synthetic scenarios without adding public seed/reset/credential APIs. Historical fixture setup uses a process-local synthetic clock. Privileged native master preparation can use `ignore_permissions=True`; this is not represented as ordinary user authorization evidence. Ordinary product security is independently tested through HTTP and direct access.

The evidence package records failed preparatory attempts, discarded assumptions and the interrupted stateful browser run. Passing suites were retained when orchestration stopped, and only missing suites resumed. No unobserved result was inferred from a job timestamp. No production, real client data, provider credentials, real SdI/TS traffic, SMTP delivery, fiscal certification, load/DR qualification or compliance assertion is included.

## Goal Learning Extraction

The entire GOAL-02 was reviewed against knowledge governance, manifest and learning template. The 18 formally approved GOAL-01 learnings were consulted as advisory input. Only one new generalizable artifact was warranted:

- **EFK-CANDIDATE-0019 — RECIPE: persistent synthetic validation dataset**, [draft PR #3](https://github.com/2008hitch-afk/erpnext-frappe-delivery-knowledge/pull/3), commit `aa21326af645bbd1b921fd29d86ca24e10c694f5`.

It records pinned versions, failed approaches, verified cause/confidence, source capture and replay/reset solution, discriminating evidence, official upstream sources and portability exclusions. No origin-project identifiers, business policy, source-project URLs, credentials or raw logs were exported. Status remains CANDIDATE / PENDING. Existing candidates, approved learnings, governance and templates were not modified.

## Handoff and stop

The technical GOAL-02 Done Gate is satisfied. Client validation should execute the guide against this named synthetic candidate, recording PASS/FAIL with scenario IDs and routing defects to their scope. Owner review/acceptance remains separate. All product PRs remain drafts and the stack is unmerged. **GOAL-03 is not started or authorized by this completion**, and its gate is unchanged.
