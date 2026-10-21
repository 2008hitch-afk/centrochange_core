# QA results — #148

Run date: 2026-10-21 UTC. Candidate tested in isolated Vite preview using Playwright Chromium and synthetic API interceptions. These tests do **not** demonstrate live Frappe behavior or server permissions.

| Gate | Result | Limit |
|---|---|---|
| TypeScript `npm run typecheck` | PASS | source typecheck only |
| Vite `npm run build` | PASS | static files generated; Frappe asset service NOT_VERIFIED |
| Playwright 1440×900 / 390×844 | 45 PASS, 1 intentional desktop skip of the mobile-only menu assertion in final full run | mocked API, Manager-like fixture plus finance denied; Guest public UI exercised with mocked API |
| Agenda booking/CSRF | PASS with POST capture, cryptographic request key presence | synthetic interception; server mutation NOT_VERIFIED |
| Navigation/Finanza/Pazienti/Report | PASS in both viewports | simulated data |
| Direct hash role fallback | PASS | server route/API 403 NOT_VERIFIED |
| Date formatting/DST day boundary | PASS in both viewports | booking server DST and ambiguous time NOT_VERIFIED |
| Invalid Italian date and canonical POST | PASS in both viewports: `31/02/2026` blocked, `29/03/2026` sent as ISO | synthetic interception |
| Invoice draft, payment, note correction, membership and public first meeting | PASS in both viewports | synthetic interception; server behavior NOT_VERIFIED |
| Compensation rule/capture/compare, patient assignment, package issue and XML classification | PASS on desktop and mobile with API payload and CSRF assertions | synthetic interception; server authorization and mutations NOT_VERIFIED |
| Fiscal Customer and professional report drill-down | PASS on desktop and mobile with distinct mocked projections | live scope, export and report semantics NOT_VERIFIED |
| Cancelled-session action presentation | PASS on desktop and mobile: ordinary close/move/cancel absent, audited reopen/waive visible to Manager fixture | server transition and permission negatives NOT_VERIFIED |
| Long patient selector | PASS on desktop and mobile: search filters >10 options while preserving current choice and canonical patient ID | other large selectors use same shared component; full keyboard/screen-reader UAT NOT_VERIFIED |
| Note revision grouping | PASS on desktop and mobile with two synthetic revisions and correct `corrects` pointer | complete history beyond backend page limit NOT_VERIFIED |
| Service directory and manager audit | PASS on desktop and mobile with synthetic snapshots, audit before/after and zero writes | direct API/role enforcement live NOT_VERIFIED |
| No generic CRUD/third-party navigation request | PASS in both viewports | source/static browser behavior only |
| Console errors in section sweep | 0 on desktop and mobile after fixing duplicate React table keys | Vite still logs a non-fatal outdated JSX transform warning from the app/dependency graph; source not isolated |
| `npm audit` | 0 current findings | registry snapshot, not a security review |
| Screenshot visual inspection | Agenda, finance, first meeting desktop/mobile plus all workspace sections desktop saved; logo visible | Owner review and all roles NOT_VERIFIED |
| 128 route×role×device / 22 native lists+forms / 38 server security | NOT_VERIFIED | #139 results belong to older candidate |
| p50/p95 Agenda refresh/navigation | NOT_VERIFIED | no approved isolated Frappe runtime/baseline |
| Full accessibility keyboard/focus/screen reader | NOT_VERIFIED | only basic semantic controls and keyboard table rows |

The first Playwright run exposed a test locator ambiguity and a mobile sidebar test setup error, then a Vite-base import path error in the DST test. Each was corrected and re-run; no product rendering error remained in the final synthetic run.
