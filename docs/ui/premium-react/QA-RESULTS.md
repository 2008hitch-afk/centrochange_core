# QA results — #148

Run date: 2026-10-21 UTC. Candidate tested in isolated Vite preview using Playwright Chromium and synthetic API interceptions. These tests do **not** demonstrate live Frappe behavior or server permissions.

| Gate | Result | Limit |
|---|---|---|
| TypeScript `npm run typecheck` | PASS | source typecheck only |
| Vite `npm run build` | PASS | static files generated; Frappe asset service NOT_VERIFIED |
| Playwright 1440×900 / 390×844 | 15 PASS, 1 intentionally skipped (mobile-only check in desktop project) in final full run | mocked API, Manager-like fixture plus finance denied |
| Agenda booking/CSRF | PASS with POST capture, cryptographic request key presence | synthetic interception; server mutation NOT_VERIFIED |
| Navigation/Finanza/Pazienti/Report | PASS in both viewports | simulated data |
| Direct hash role fallback | PASS | server route/API 403 NOT_VERIFIED |
| Date formatting/DST day boundary | PASS in both viewports | booking server DST and ambiguous time NOT_VERIFIED |
| Invalid Italian date and canonical POST | PASS in both viewports: `31/02/2026` blocked, `29/03/2026` sent as ISO | synthetic interception |
| No generic CRUD/third-party navigation request | PASS in both viewports | source/static browser behavior only |
| `npm audit` | 0 current findings | registry snapshot, not a security review |
| Screenshot visual inspection | Agenda desktop/mobile and finance mobile inspected; logo visible | other pages/roles and Owner review NOT_VERIFIED |
| 128 route×role×device / 22 native lists+forms / 38 server security | NOT_VERIFIED | #139 results belong to older candidate |
| p50/p95 Agenda refresh/navigation | NOT_VERIFIED | no approved isolated Frappe runtime/baseline |
| Full accessibility keyboard/focus/screen reader | NOT_VERIFIED | only basic semantic controls and keyboard table rows |

The first Playwright run exposed a test locator ambiguity and a mobile sidebar test setup error, then a Vite-base import path error in the DST test. Each was corrected and re-run; no product rendering error remained in the final synthetic run.
