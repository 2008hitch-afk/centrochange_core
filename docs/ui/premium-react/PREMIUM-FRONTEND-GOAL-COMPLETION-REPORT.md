# #148 — Premium frontend rebuild: completion report

**Status: PARTIAL. Not READY_FOR_OWNER_VISUAL_UAT. No Owner acceptance.** Prepared 2026-10-21 UTC from implementation commits `77db91d15252d111b4d4b94808c5ec392c6cd86a` and `56a1933f893fa018948767132b836460602b7eac`, branch `issue-148/premium-react-frontend`, stacked on preparatory PR #149 commit `640b221feba0e9f1772bd082a788391cc4a109ad`. Issue: [#148](https://github.com/2008hitch-afk/centrochange_core/issues/148). Implementation: [DRAFT PR #150](https://github.com/2008hitch-afk/centrochange_core/pull/150).

## W0–W7

| Stream | Current result | Evidence / gap |
|---|---|---|
| W0 preflight | PASS for Git isolation and authority review | Existing checkouts clean; preparatory branch fetched non-destructively; new worktree `/home/empv26/src/centrochange_core-premium-react`; no shared DEV write. HC-0005 DECISION-060/061 approved; manifest GOAL-02 `AUTHORIZED_ACTIVE`, GOAL-03 unauthorized; #23 closed in repo, not reconciled. HITCH primary repo inaccessible: **NOT_VERIFIED**. |
| W1 skill, supply chain, brand | PARTIAL | Repo skill read; public skill candidates reviewed, none installed. Direct npm pins/lockfile, 60 installed packages license-reviewed, scripts disabled, audit 0. Official logo/palette checked; formal redistribution document **NOT_VERIFIED**. |
| W2 API/security architecture | PARTIAL | Frappe `www/premium` same-origin shell, CSRF, domain API client; contract matrix. Live page/permission integration **NOT_VERIFIED**; no backend/DocType change. |
| W3 foundation | PARTIAL | Shared shell, tokens, responsive navigation, table, drawer, modal, feedback, loading, Italian date input. Full accessibility/role matrix **NOT_VERIFIED**. |
| W4 Agenda/operations | PARTIAL | Day resource/week calendar; booking, session actions, patient search/history/notes and correction, availability and report UI; public first-meeting React flow. Synthetic booking/notes/public flow PASS; live server workflow, package/catalog and parity incomplete. |
| W5 finance/admin | PARTIAL | Finance overview/lists, invoice draft/payment/credit/amend, bank import/reconcile, professional threshold, administrative queue, local SdI/TS simulation forms, access management, notifications. Representative synthetic draft/payment/membership PASS; XML classification and compensation rule/compare UI missing; live accounting **NOT_VERIFIED**. |
| W6 QA | PARTIAL | Typecheck/build/Python compile PASS, 27 Playwright synthetic PASS and 1 intentionally skipped; screenshots inspected. Seven roles+Guest live, 128 routes, 22 lists/forms, 38 security checks, live functional mutations and p50/p95 baseline **NOT_VERIFIED**. |
| W7 candidate/report | PASS as DRAFT candidate/report, not product gate | Reproducible source/static build and sanitized screenshots. No merge/cutover/deploy. |

## Candidate and evidence

- Build artifacts: `app.js` SHA-256 `8133b9657a9b096919a743eb675a8d54389f0a187d828f2d2675bc42980393fc` (474.45 kB raw / 141.54 kB gzip), `app.css` SHA-256 `8e0431d12187ea9dc773ef94d4cd60c257fb258951fe63d5d37d63be0deea731` (29.77 kB / 7.11 kB gzip). Logo SHA-256 `c05795b5c84a02c11df6548266ee743e6a41f4ddd04384a0faf81e31d1a5109e`.
- Playwright: 1440×900 desktop and 390×844 mobile, Chromium, synthetic API intercept. 27 PASS, 1 project-specific skip. Booking/payment/first meeting POST include CSRF; invoice bridge/draft and note correction/membership exercised; role denied finance hash fallback; Italian invalid date rejection and ISO payload; no generic CRUD request in tested paths. Screenshots: [Agenda desktop](../../evidence/issue-148/agenda-desktop.png), [Agenda mobile](../../evidence/issue-148/agenda-mobile.png), [Finanza desktop](../../evidence/issue-148/finance-desktop.png), [Finanza mobile](../../evidence/issue-148/finance-mobile.png), [Primo incontro desktop](../../evidence/issue-148/first-meeting-desktop.png), [Primo incontro mobile](../../evidence/issue-148/first-meeting-mobile.png). Further area screenshots in `UX-VISUAL-REFERENCE.md`. They are **not** live Frappe screenshots.
- Typecheck and Vite build pass. `python3 -m py_compile` of Frappe controller passes. `git diff --check` passes. `npm audit --json` has zero current findings. Exact lockfile pins and source inventory in `LICENSE-INVENTORY.md`.
- #139 PR #140 evidence was consulted for defect/route/security baseline. Its 128/128, 22/22 and 38/38 results are historical for a different candidate and were **not** transferred to React. The shared DEV currently runs an issue-75 image, not this branch; this report did not change it.

## Open material gates

1. **Functional completeness:** React UI still lacks incoming XML line classification, compensation rule/compare, package/catalog/assignment forms, full financial report drill-down, and 11 native list/form equivalent decisions. See `FUNCTIONAL-COVERAGE.md`. This is an implementation gap, not a server approval substitute.
2. **Isolated runtime:** DECISION-061 explicitly does not authorize a server clone or shared DEV mutation. Owner must separately specify/authorize an isolated Frappe Site with synthetic fixtures, infrastructure boundary, rollback/cleanup and no provider access before real integration, role, permission, security and p95 testing. No clone was started.
3. **Permission and visual acceptance:** seven roles plus Guest, center A/B negatives, direct URL/report/export, private notes, 38 security assertions, full desktop/mobile visual list and performance p50/p95 remain **NOT_VERIFIED**. No readiness claim can be made from mocked Playwright.
4. **Brand rights:** Official site asset was reused under explicit Owner brand direction; formal redistribution evidence for a release remains **NOT_VERIFIED**.

## Owner decision requested

Review the DRAFT implementation and coverage table. For continuation to the product gate, authorize a **separate isolated server clone/test Site** with only synthetic data and named rollback/cleanup/fingerprint limits; confirm brand redistribution evidence if release is desired. The branch can then complete missing W4/W5 UI and rerun live W6. This report does not authorize DEV shared changes, merge, cutover, production, paid licenses, real providers, GOAL-03 or GOAL-02 closure.
