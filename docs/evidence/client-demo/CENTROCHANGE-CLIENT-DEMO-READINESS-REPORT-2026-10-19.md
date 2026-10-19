# Centro Change — Client Demo Readiness Report, 19 October 2026

**Result: `CLIENT_DEMO_READY = YES` for an Owner-led screen-share using synthetic DEV data.** This is neither client acceptance nor production readiness. Direct client login remains outside this authorization.

## Runtime and integrity

- Branch `audit/mvp-functional-completion`; PR #141 remains DRAFT and depends on #140. The cumulative application source installed is `cf0eff79a74de4ec36cb20611e5c518de5ba7f8e` (the operational wrapper and this evidence follow it on the same branch). No merge occurred.
- One authorized DEV update ran with pinned `infra/client_demo_install.py` SHA-256 `de987af2fe13e6ee9358b8e03816828eb3d83130052ff9b855b179b6efd6e7fb`. Its private gate began at `2026-10-19T21:01:11Z` with a four-hour operation limit and one-hour recovery reserve. No second image update or rollback occurred.
- Six application services now run `centrochange-single:client-demo-cf0eff7`, image `sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834`. Database and both Redis services were preserved. All nine project services run; Frappe ping returned HTTP 200. Centro A remains active and Centro B inactive.
- The four-part encrypted backup was verified before activation. Essential authentication, Administrator, assets, Socket.IO origin checks and direct API denials passed. The monitored synthetic data fingerprint stayed `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd` before activation, after activation and after the final browser sweep. The sweep wrote no records.
- The prior [MVP completion evidence](../mvp-functional-audit/CENTROCHANGE-MVP-DEV-FIRST-COMPLETION-2026-10-19.md) documents **46/46 technical capability PASS**, including a real synthetic partial POS payment, private attachment persistence, report rows/export and server-side role denial. This presentation update did not rerun those write workflows. Its separate mutative finance/security fixture suites remain `BLOCKED` by the executor's documented cleanup risk; historical PASS is not presented as a fresh rerun.

## Corrections and observed result

| Problem | Cause | Correction | Live proof |
|---|---|---|---|
| Two active sidebar links for one destination | «Inizio» and «Agenda» (or Finance home) shared a route and both matched | Pick one active destination; navigation structure unchanged | Fresh Chromium m desktop/mobile and f desktop: exactly one active link; 87/87 role/route sweep PASS |
| Canceled POS fixtures dominated invoice list with raw customer codes | Native Sales Invoice list used canonical synthetic customer values as subject | Frappe List View formatter gives a readable presentation label; canonical IDs and accounting history stay intact | Fresh Chromium list shows “Paziente dimostrativo POS”, cancellation status and canonical document ID, desktop/mobile |
| New list formatter initially did not appear | Frappe 16.50 `doctype_form_meta::Sales Invoice` client cache retained old `__list_js` after image activation | Versioned, bounded `infra/client_demo_refresh_meta.py` invalidated only that cache key after verifying the source; no DB record or service changed | New login returned updated formatter; browser inspection and screenshot PASS |
| Mobile weekly Agenda did not explain horizontal navigation | Seven-day grid exceeds phone width by design | Added an Italian scroll hint and keyboard focus/accessibility label | At 390 px Chromium scrolled to later days; screenshot shows hint and calendar |
| Initial browser proof raced native list loading | It checked the header before asynchronous invoice rows rendered | Post-install proof waits for actual row data and text | `infra/browser/client_demo_readiness_post.cjs`: 3/3 sessions PASS, zero page errors |

The pinned one-shot executor and its original test checksum remain unchanged after installation. The post-install proof and cache refresh are separate versioned files. No second deployment was used to correct test timing or cache.

## Browser coverage and screenshots

The read-only Owner UAT sweep was rerun on the **installed image** in fresh Chromium contexts: Direzione desktop/mobile 23+23 routes, Segreteria mobile 14, Professionals A/B/C 4+4+4, Finance desktop 10, Commercialista desktop 5. **87/87 route renders PASS, zero unexpected writes.** Checks include visible content, asset/JS failures, layout overflow, status badges, navigation and active sidebar state. The targeted post-install proof adds Agenda landing, Finance landing, mobile calendar scrolling and native invoice subject.

Actual after-update screenshots: [Agenda desktop](agenda-desktop-after.png), [Agenda mobile](agenda-mobile-after.png), [Fatture pazienti desktop](fatture-native-after.png), [Fatture pazienti mobile](fatture-native-mobile-after.png). The [before screenshots](agenda-desktop-before.png) remain for comparison. Full sweep JSON and other screenshots are retained privately at `~/.local/state/centrochange-single/browser-evidence/client-demo-post-deploy-sweep/`.

## Twelve customer walkthrough paths

The [runbook](../../uat/CLIENT-DEMO-RUNBOOK-2026-10-19.md) gives sequence, roles, synthetic examples and expected results. All twelve paths have a currently reachable browser surface in the post-update sweep plus corresponding prior functional evidence; **none was re-executed as a new end-to-end write transaction during this visual deployment**.

| Path | Current browser | Functional evidence to reuse |
|---|---|---|
| 1 Login → Agenda | PASS desktop/mobile | Agenda/booking acceptance |
| 2 Patient search and registry | PASS | Patient assignment and access tests |
| 3 Professionals and availability | PASS | Availability and role tests |
| 4 Book, reschedule, cancel | PASS route | Synthetic booking lifecycle tests |
| 5 Session, private notes, history | PASS route | Note revision and authorization tests |
| 6 Services, tariffs, packages | PASS lists/forms | Catalog and pricing tests |
| 7 Invoice, POS, outstanding balance | PASS invoice/payment routes | [Live synthetic POS proof](../mvp-functional-audit/CENTROCHANGE-MVP-DEV-FIRST-COMPLETION-2026-10-19.md) |
| 8 Bank and reconciliation | PASS | Traceability/reconciliation tests |
| 9 Administrative attachment | PASS document route | Private attachment persistence/denial tests |
| 10 Reports and accounting | PASS routes | General ledger/trial balance rows and CSV in this installation |
| 11 Simulated SdI and TS | PASS | Simulation contract tests; no real transmission |
| 12 Access management and audit | PASS | Server-side role/denial and audit tests |

## Presentation limits and access

- Native invoice columns still shorten long names on a phone; native filter controls expose `ID` and compact symbols. Subject, status and date remain legible for a guided demo. Start with Beta/Gamma/Theta examples; retain canceled synthetic POS rows in history. This is a visual polish item under #75/#134, not an accounting failure.
- Italian customer surfaces and date/time samples were checked, but no complete copy audit of every native form, error, print and export was performed. **UI/UX and localization are `PARTIAL` for final Owner visual acceptance**, while the guided demo is usable. No `OWNER VISUAL PASS` is claimed.
- Use the private SSH tunnel from the [runbook](../../uat/CLIENT-DEMO-RUNBOOK-2026-10-19.md). Credentials stay in the existing private channel; do not send them to the client. Present first by Owner screen sharing. Client observations and acceptance must be recorded explicitly.
