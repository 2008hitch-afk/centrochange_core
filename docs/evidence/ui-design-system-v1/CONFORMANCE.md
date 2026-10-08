# Design System v1 — transversal conformance / #76 → #77 → #75

## Agenda Owner-gap corrective checkpoint — 2026-10-08

**TECHNICAL PASS / READY_FOR_OWNER_RETEST.** RC22 corrects the verified Tabler header-flex/row-grid collision using one shared scoped grid template. Runtime coordinate drift now 0px across five viewports and horizontal scroll. 12 Agenda browser checks and 189 rollback backend checks PASS; Owner dataset unchanged. #75 remains OPEN, PR #94 draft/unmerged, #92/#93 unchanged. Previous general visual PASS did not prove coordinate alignment and is superseded for this specific gap. Owner visual retest required.

Evidence: `docs/evidence/ui-design-system-v1/AGENDA-GRID-ALIGNMENT-2026-10-08.md`. Candidate source `f06acca4f6c2ac757dbd3e187709f94b18554b65`; no business/permission/schema delta. GOAL-03 not authorized.


Date: **2026-10-08**. Result: **TECHNICAL PASS / READY_FOR_OWNER_UAT**. **OWNER VISUAL UAT REQUIRED**. Issues #76/#77/#75 remain OPEN; PRs #92/#93/#94 remain draft and unmerged. This report supersedes the 7 October identity-pending checkpoints; it does not declare Owner acceptance or GOAL-02 Done.

Authority: [approved v1](../../ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md), #76 authorization. [Implementation and official sources](IMPLEMENTATION.md). No permission, role, center scope, accounting, price, lifecycle or provider delta. No GOAL-03.

## Exact candidate / reproducibility

- Candidate **goal02-20261008-rc21**, exact archive commit **c51a9e7a1f887b87c0b06872a8d3e94f2e7249f5**, branch `issue-75/final-client-ux-review` (stack #92 → #93 → #94). Immutable source tag `uat-goal02-20261008-rc21`.
- Image `centrochange-uat:goal02-20261008-rc21`; local image ID `sha256:3859ce61f8030b234ffb010d2f5ac6125b3a2d09e291e7911482829639fe433a` (not registry digest).
- Six app services, no source overlay/manual container patch; 239 tracked app files byte-identical. App manifest `ebc7025792c79603da97d298f4f4a7403c25a8383da4ebe81e9e5087f72d8ae2`. [Build](candidate.json), [parity](parity.json).
- Local **Tabler Core 1.6.1**, **Icons 3.35.0**, 24 vendor hashes/integrity/licenses preserved. No CDN/fonts/plugin stack. [Static](static.json).
- Pinned Frappe 16.31.0 / ERPNext 16.32.0 / Marley 16.5.2 / Builder 1.33.0 unchanged. [Official pinned source byte proof](official-pinned-source.json); print guard verified before supported hook. Native 403 renderer uses `NotPermittedPage` → `www/message.html`; supported context overrides presentation only. No upstream patch.
- Existing DEV volumes/dataset retained; no schema migration, reset or seed for this UI deployment. Controlled six-app-service recreation and app cache clear. [Health](health.json): HTTP/assets, WebSocket101, scheduler enabled, two workers, real fresh short/long jobs finished, nine running services.
- Owner URL: `http://localhost:8082/centrochange` via SSH tunnel; server bind `127.0.0.1:8082`.

## Evidence reuse after the final print delta

[Exact source-diff proof and suite provenance](evidence-reuse.json). Relative to rc20, rc21 changes only `operations/reporting.py`: presentation of the existing guarded session-print response (Italian labels/date and synthetic human names). **All UI assets/templates, domain/report/guard code and Owner rows are unchanged.** Thirteen browser/Agenda suites and their desktop/mobile screenshots were executed on rc20 and reused, with explicit `execution_provenance` in each normalized JSON. Print and #77 HTTP matrix, full262-check backend, runtime parity/health and Owner fingerprints were executed again on rc21. No unexecuted test is presented as a new run. Subsequent commits change QA/documentation only; source build commit and final review HEAD are distinct, with identical app bytes.

The extended print check fetched the real authorized HTML and rendered it with browser setContent on the existing authenticated origin and verified local Tabler CSS, print media and screenshot; no server route/API/grant added. Expected closure is read from the native record: the current Owner session is **Reopened → Riaperta**, not an assumed Closed. Native fiscal default/Italian invoice prints and A/B/C print denials also PASS.

## Component contract and discriminating checks

Shared assets/theme + `.page`, responsive `.navbar-vertical`, `.page-wrapper`, one `main.page-body`; common page header/filter/action hierarchy. Tabler buttons, form controls, tables, cards/data-grid, text+badge statuses, alerts/loading/empty/error. Shared auth/public/error pattern. Semantic landmarks, skip link, focus styles, labelled controls, native-dialog focus confinement/Escape and return. Italian date/time/money presentation; secondary canonical IDs and audit originals retained.

Single-control ARIA Patient/Professional combobox: keyboard Arrow/Enter and click select exactly the original canonical hidden-select value; no-results clears value; Escape closes; busy feedback; 503/error/retry; delayed old request cannot overwrite latest results. Patient calls existing bounded server-authorized search; Professional uses existing authorized projection. No endpoint/grant added. [Runtime contract](ui_v1.json).

An early debounce attempt retained stale options and selected the wrong Professional; immediate option/value invalidation fixed it. Shared button flex initially flattened appointment blocks: block geometry adaptation fixed it without calendar logic change. Native login card/min-height and print locale needed supported extensions. Request locale alone did not translate native hardcoded print labels; exact label-node allowlist plus native translation hook fixed labels without changing data. The initial shared error template used `page_content` against a `content` base and rendered blank: corrected in #76, discriminated by actual generic error/403/404 browser checks. Failed rc15 (blank generic card) and rc16 (late native denied-action context merge) are not acceptance candidates. Reading the already-native response action before that merge fixed the 403 context override. Shared card-body spacing and public primary teal also explicitly verified.

## #75 surface-by-surface matrix

**P = verified technical PASS, not Owner visual acceptance. N/A = no applicable control.** Every row has local Tabler/class/token/visible-control/table assertions, no client Desk links, no ERPNext/Frappe/Powered by, desktop1536×1024 and mobile390×844 no document overflow, screenshot. See [machine matrix](ui_v1.json), [screenshots](screenshots/).

¹ Italian UI/human label review covers controlled vocabulary, professional aliases, audit access/state meanings, notification closure instruction, received-XML validation message. Stored service/customer/reason text, legal identities and native amount-in-words remain source data; not rewritten. Canonical reference numbers remain secondary where useful.

² State contract is shared across rows; exercised selector loading/empty/error/retry/stale, five core bootstrap HTTP503 faults and real future-period financial empty state in [states](states.json). It does **not** claim every endpoint fault-injected. Actual native403/404 retain statuses. Direct `/error` checks generic template; no deliberate server500 crash induced.

³ Semantic native controls/labels + shared focus baseline; mobile navbar click/Space per authenticated row, combobox keyboard, native modal focus/viewport, login/logout. This is a practical accessibility baseline, not a full WCAG/screen-reader certification.

⁴ Same final candidate server/API/direct/query/export/print/private-note/cache-switch positive/negative matrix, seven roles + Guest; detailed below. UI hiding is not authorization evidence.

⁵ Full rollback backend suite and relevant workflow/browser reconciliation below; cosmetic-only final deltas reuse actual isolated rc8 operation evidence.

| Surface | Shell/layout | Tabler | Search/select | Italian | Human labels | States | Mobile | Keyboard/focus | Debrand | No Desk | Permission-neutral | Business unchanged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Agenda | P | P | P: prenotazione + filtro | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Pazienti | P | P | P: paziente/professionista | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Disponibilità | P | P | P: professionista | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Report | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Notifiche | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Gestione accessi | P | P | P: autorizzati | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Riepilogo | P | P | P: filtri autorizzati | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Fatturepazienti | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: XMLricevuti | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Fatturefornitori | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Banca | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Professionisti | P | P | P: professionista | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: Codaamministrativa | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: SdI | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Finanza: TS | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /professionista | P | P | P: professionista | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /pazienti_report | P | P | P: ricerca autorizzata | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /registro_modifiche | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /validazione | P | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /primo_incontro | P: pubblico/auth/errore | P | P: professionista | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| /login | P: pubblico/auth/errore | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| 404 | P: pubblico/auth/errore | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Errore generico | P: pubblico/auth/errore | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| 403 | P: pubblico/auth/errore | P | N/A | P¹ | P¹ | P² | P | P³ | P | P | P⁴ | P⁵ |
| Logout/session return | P: native + shared login | P | N/A | P | P | P: native session | P | P: native CSRF action | P | P | P⁴ | P⁵ |
| Native invoice print | P: document layout | P: supported print adaptation | N/A | P¹ | P¹ | P: actual authorized200/denied403 | N/A: A4 print media | N/A: noninteractive document | P | P | P⁴ | P: original fields/totals |
| Session print | P: document layout | P: local print stylesheet/table | N/A | P | P | P: guarded response | N/A: document print | N/A: noninteractive document | P | P | P⁴ | P: existing projection |
| Report CSV / fiscal download | N/A: data export | N/A: data function | N/A | P: report headers | P: canonical IDs for trace | P: guarded response | N/A | P: download action | P | P | P⁴ | P: same canonical data |

**Print**: [default + explicit Italian locale](print.json), actual native invoice200, three A/B/C403 with no document disclosure; [print-media screenshots](screenshots/). Native fiscal Customer and amount-in-words are preserved verbatim (some synthetic names/words are technical/English data). No fake identity or accounting rewrite. Session print actual authenticated response/rendering and print-media screenshot are in print.json; permissions and scoped export retain independent positive/negative coverage.

## #77 — server-side permission-neutral gate

[HTTP/direct browser matrix](permissions.json), [complete backend](backend.json), [native print negatives](print.json). All PASS on this candidate. Existing [role matrix](../../uat/FINAL-PERMISSION-MATRIX.md) unchanged: Manager has existing app management scope, not Administrator/System Manager; Secretariat authorized operational/finance, Finance no operational Patient API, Accountant read-only; A/B own professional/patient scope and authored private context, C unassigned no patient/session escalation; Guest controlled public ingress only. No new roles/grants/visibility.

Tests include native/API/fiscal export/query/direct-page/private-note/audit/recovery, foreign center/professional denials, governed membership and patient-assignment revocation inside rollback, unauthorized native invoice print, private payload download and account-switch cache replay. #77's existing supported no-store correction is retained. Counts alone or hidden UI are not accepted proof.

## Regression evidence / commands

All runner scripts are versioned; Playwright **1.58.2** fallback used because Browser plugin is unavailable. Browser suites run serially under host lock, respecting native two-session limit rather than changing user settings. No credentials/raw logs copied here.

| Check | Result | Evidence |
|---|---|---|
| Python AST / JS syntax / browser syntax / vendor integrity | PASS | [static](static.json),166 Python files,13 JS modules,19 browser scripts,24 vendor files |
| Tabler DOM/visual contract, 24 surfaces × desktop/mobile + combobox/modal | PASS | [ui_v1](ui_v1.json), screenshots |
| Native print default/Italian + A/B/C denial | PASS | [print](print.json) |
| Bootstrap error503 × five core paths; native2090 empty financial period | PASS | [states](states.json) |
| End-to-end page walkthrough/login/logout/public/report/audit/finance mobile | PASS | [walkthrough](walkthrough.json) |
| Professional and Patient periods/KPI/drill-down/CSV/native economics | PASS | [professional](professional.json), [patient](patient.json) |
| Audit, expectations, bank amount/document trace, TS review/history, confirmation | PASS | [audit](audit.json), [expectations](expectations.json), [bank](bank_trace.json), [TS](ts_detail.json), [confirmation](confirmation.json) |
| Search/stale and accounting receipts/invoices | PASS | [search](search.json), [accounting](accounting.json) |
| Agenda accepted structure/week/Today/date/filter/detail/private A/B/C/mobile/stale | PASS | [agenda](agenda.json) |
| Full 11-module backend rollback regression | PASS — 262 checks | [backend](backend.json), canonical complete-row hash + counts unchanged |
| Actual isolated booking/reschedule/cancel/private note/assignment/package/revoke/disable/worker notice | PASS — rc8 reused | [isolated workflow](isolated-workflow.json),16 browser checks + real short-worker delivery; final relevant business source unchanged |
| Final server permission matrix | PASS | [permissions](permissions.json), backend final review, print negatives |
| Image/assets/services parity and runtime jobs | PASS | [parity](parity.json), [health](health.json) |
| Owner dataset preserved | PASS | [owner rows](owner-dataset.json), complete-row hashes match pre-workflow baseline |

Principal commands: `node --check`, Python AST parse + vendor SHA256; `infra/uat_candidate.py --source-ref <commit> --name goal02-20261008-rc21 --existing-site-ui` using private env outside Git; `infra/uat_browser_acceptance.py --script <suite>` for14 suites plus `--script uat --agenda-only`; `infra/remediation_acceptance.py`; `infra/image_acceptance.py --source-ref HEAD`; `infra/uat_runtime_health.py`. Authorized Docker group used through `sg docker`; no manual container source patch.

### Dataset and expected/observed reconciliation

Existing Owner changes retained: one performed Alfa session was already moved to14 October16:00. September28–October4 therefore contains **7 Alfa sessions**, not old8, and corresponding expected compensation200 rather than old240. Tests derive exact native IDs/categories/counts and reconcile; data not reset to obsolete fixture assertions. Current Theta deferral and native invoice/payment/payload revisions remain present.

All original rows across32 canonical DocTypes match pre-workflow hash **6d60ef5cc5a73550e935736465269c64fea283bdbe5e61cc1e966db9f4bf2d58**. Isolated fixture cleaned via existing versioned harness; **five append-only audit events of that fixture are deliberately retained**, not deleted. Only their exact fixture actor prefix is excluded from Owner-row comparison; total audit200→205, Owner audit200 unchanged. No Owner row excluded. Backend tests roll back mutations and verify full persistent-row hashes independently.

## Adaptations / residual limits / handoff

Approved equivalent combobox (not Tom Select dependency), native dialog adapted to Tabler, calendar geometry retained, native auth and print supported-hook/CSS adaptations are documented v1 fits. No unapproved framework/plugin, new logo or permission/API delta. No new Owner decision is needed for implementation. **Owner must still visually validate** the24 surfaces, search, native print and authorized role views before acceptance; technical checks are not that decision.

Screen checks target Chromium1536×1024 /390×844; tablet benefits responsive rules but no exhaustive device/browser, screen-reader, performance/load, PDF-printer or compliance certification. Retained customized native print labels outside tested pinned format may need explicit presentation mapping if another format is later selected. Provider/SdI/TS remain simulated only. DEV/UAT guide is intentionally denser. No live transport, production or GOAL-03.

#76 implementation: **TECHNICAL PASS / READY_FOR_OWNER_UAT**. #77 final-candidate permission-neutral gate: **TECHNICAL PASS**, Owner review required. #75 true conformity matrix: **TECHNICAL PASS / READY_FOR_OWNER_UAT**, **OWNER VISUAL ACCEPTANCE PENDING**. All issues OPEN, all PRs draft, no merge.

Final print QA also rejects an unstyled preview: it asserts the local teal token and real Tabler table padding before capturing print media. Native-state lookup occurs on the authenticated origin, not after an isolated preview navigation. Initial test assumptions about Closed, preview-origin reads/styles and mixed result-schema assertions were corrected in QA only; app bytes/image unchanged after rc21.
