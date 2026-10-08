# UAT-PROF-REPORT-01 — TECHNICAL PASS / READY_FOR_OWNER_UAT

Requirement: #66, lifecycle Management Reporting MVP, DECISION-033 CORE reporting and approved views/drill-down. GOAL-02 #23; no new commercial scope or GOAL-03. Manual Owner acceptance remains REQUIRED; #66 OPEN, PR #67 draft, no merges.

## Baseline and runtime

Branch `issue-66/professional-view`, based exactly on accepted Agenda head `8562dbb10bb16c25f6d1d2376f5ecdae1874a986`; stacked base `issue-63/agenda-calendar`. Deployed application commit `3b24b01d9f711eb9824714976e756489e7685e4b`, named build `goal02-20261006-rc10`, image `sha256:cb471fcafa7fa9704077950c5310e1e714ce68773c012c0d5b20461e1d249a2a`. Subsequent evidence-only commit does not alter deployed application bytes.

Versioned `git archive` build/deploy via `infra/uat_candidate.py --existing-site-ui`; no schema migration, volume destruction, dataset reset or manual container patch. Source parity: 176 app files, six services share one immutable image, named volume mounts only. Nine runtime services running, Redis/DB healthy, site ping HTTP 200, frontend only `127.0.0.1:8082`. Owner tunnel URL: http://localhost:8082/centrochange.

Pins unchanged: Frappe 16.31.0 / `6a329d068416768ec47ccd3326b9cc95a8d7bf99`; ERPNext 16.32.0 / `81a6f97566b83609c3917404a560b673050e907d`; Marley 16.5.2 / `934d6c162868139dfbe80c23d6102adb7ec25adb`; Builder 1.33 / `41987c064da4650e6901b5da82b7c76add452ebf`. Twelve installed upstream source files match official pinned sources; see machine evidence. Native guidance: [Frappe Database API](https://docs.frappe.io/framework/user/en/api/database), [ERPNext Purchase Invoice](https://docs.frappe.io/erpnext/purchase-invoice).

## Implementation and semantics

Single guarded `finance.reporting.professional_view`, reusing `summary(center,start,end,practitioner=...)`; single `/professionista` renderer from Agenda name/avatar and Report → Professionisti. Existing appointment click and Seduta/Storico/Note reused; Finance retains its existing absence of operational detail privilege. Secretary/Manager Report includes Centro, Professionisti and existing Patients entry; Finance enters through its existing financial summary.

No booking/pricing/accounting/role/schema/DECISION-054 change. Session price snapshots include cancelled/non-due rows and are explicitly distinct from receivables. Operational Paid/Unpaid is distinct from native patient accounting. Expected compensation follows latest canonical session snapshots, unresolved values remain unknown. Native supplier invoices/payments use posting dates and fiscal supplier; shared amounts are never allocated to an individual. Current invoice outstanding is not a reconstructed historical period-end balance. Canonical comparison drill-down returns whole explicit snapshots only when all composing sessions belong to the selected professional/period, never a split or inferred discrepancy total.

## Expected versus observed

Preserved synthetic `goal02-demo-v1`, Centro A / Alfa, 28/09/2026–04/10/2026.

| Check | Expected | Observed |
|---|---|---|
| Agenda and Report entry | Identical scoped projection after selecting Alfa | PASS, complete projection equal |
| Sedute vs drill-down | Exact canonical IDs/count | 8 / 8; every row Alfa and in period |
| Operational partition | Canonical status and performed facts | 6 performed, 2 cancelled, 0 future/pending/closed-not-performed |
| Historical snapshot | Native row snapshots | 800 EUR (includes cancelled/non-due) |
| Operational settlement | Native Paid flags | 0 Paid, 8 Unpaid; no accounting inference |
| Expected compensation | Canonical latest snapshots | 200 EUR known, 1 suspended, 0 review; total unknown, displayed Da verificare |
| Suspended drill-down | Exact composing expectations | PASS |
| Presets/custom interval | Visible interval reconciles response | Today/week/month/previous-month PASS; 12–18 October = 1 future session |
| Received invoices initial period | Native posting dates | 0; demo invoice posts 5 October |
| Received invoice extended period | Native supplier invoice fields | Net/outstanding/status match native document |
| Comparison/discrepancy | Explicit canonical snapshot, exact references | PASS: expected amount minus native net; excluded outside composing session period |
| Export | Same 8 composing sessions, no note bodies | PASS, header + 8 CSV records |

The positive comparison test invokes the existing comparison service inside a savepoint, verifies returned references/amount/difference and period exclusion, then rolls back comparison/audit writes. Persistent comparison count unchanged. The preserved Owner dataset has no stored comparison; UI honestly shows zero canonical comparisons until an authorized explicit comparison exists. No fabricated invoice allocation or accounting write is introduced.

## Security and regressions

PASS for authorized Secretary, Finance, Management and Accountant reconciliation. Finance cannot acquire operational detail links; its foreign-center request is denied. A/B/C direct page, new API, existing financial report, CSV and native expectation query are denied/empty as appropriate; no financial self-view permission introduced. Existing Agenda tests verify A cannot see B patient/session, B cannot see A, and unlinked C has no patient/session visibility. Secretary direct private-note read denied. No private note body/content in report or export.

Browser PASS: both entries, exact count/records, period presets/custom, detail reuse, suspended drill, delayed stale response, CSV, mobile no document overflow, no JS exceptions. Desktop 1536×1024 and mobile 390×844 screenshots included. Native tables scroll internally. Browser plugin unavailable; pinned Playwright 1.58.2 fallback.

Agenda regression: 12 check groups PASS. Operational regression: 16 checks PASS including booking/move/cancel, permission revocation/restore, private notes and mobile; actual short-worker notification PASS, disposable fixture cleanup PASS. Those regressions ran on `23dcfc6`; final `3b24b01` changes only private acceptance code, harness and documentation, with production UI/backend unchanged. Professional browser and canonical integration reran on final immutable build.

Static: syntax checks for workspace, finance workspace, professional view and browser script; Python compile PASS. Dataset manifest before/after byte-identical; no reset/seed or changes to current Owner accounting state.

Commands: `infra/uat_candidate.py`, `infra/image_acceptance.py`, `infra/upstream_acceptance.py`, private bench `professional_view_acceptance.run`, `infra/uat_browser_acceptance.py --script professional`, `--agenda-only`, `infra/browser_acceptance.py --operational-only`, `infra/uat_demo.py inspect`. Credentials remain external private files and are never included in evidence.

## Residual limits

Manual Owner UAT required. Existing boundaries: no professional financial self-view; Finance has no clinical/operational detail access. Maximum 366-day interval / 500 composing records; EUR economics only. No rankings, forecasting, advanced BI, Patient reporting implementation or artificial supplier allocation. Native date picker presentation follows browser locale; selected period is explicitly Italian. No real providers, SdI/TS traffic, production or real data.

Machine checks and screenshots: [evidence directory](professional-view-2026-10-06/). Client scenario: [guide](../uat/CLIENT-VALIDATION-GUIDE.md#uat-prof-report-01--professional-view).
