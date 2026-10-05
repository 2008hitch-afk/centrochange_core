# MVP GOAL COMPLETION REPORT — GOAL-01 (#22)

**GOAL-01 DONE / PASS — reproducible isolated synthetic DEV MVP.**

PARTIAL remains only for the explicit business, real fiscal, UAT and production gates below. No MATERIAL BLOCKER remains in the authorized DEV scope.

DEV-only corrected candidate `issue-55/unpaid-session-threshold`, application source `ba45816`, unchanged deployment recipe from `43d24bb`; integrated draft #54 followed by corrective draft #56 / issue #55, authoritative HC-0005 DECISION-054. Existing work is retained, with all draft PRs awaiting review; no merge or production release is claimed.

## Capability audit

The 44 active capabilities (34 operational and 10 Finance/Admin) were audited against the approved scope and exercised on both fresh-runtime cycles. Deferred 021/031/032/036/037 remain excluded; historical 015 is replaced by the approved Finance/Admin 041–050.

| Capability | Approved requirement | Implementation / regression | PR | Final DEV result |
|---|---|---|---|---|
| CC-CAP-001 | Runtime foundation e isolamento DEV | Pinned Compose, runtime acceptance, fresh build and destroy/recreate | #27 / 54 | PASS |
| CC-CAP-002 | Identita professionista | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-003 | Anagrafica paziente | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-004 | Assegnazione paziente-professionista | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-005 | Segregazione appuntamenti per professionista | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-006 | Appuntamento/seduta | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-007 | Disponibilita professionista | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-008 | No double booking / slot concurrency | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-009 | Primo incontro pubblico solo Marco/Francesca | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-010 | Sedute successive solo backend | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-011 | Prestazioni / catalogo servizi | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-012 | Prezzi | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-013 | Snapshot storico servizio/durata/prezzo sulla seduta | Native scheduling/catalog snapshots/public ingress; direct, HTTP concurrency and browser | #32 | PASS |
| CC-CAP-014 | Pagato Si/No + metodo informativo MVP | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-016 | Pacchetti | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-017 | Note organizzative | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-018 | Note professionali riservate | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-019 | Scheda paziente unificata | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-020 | Patient history / clinical feed | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-022 | Chiusura giornaliera sedute | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-023 | Reminder 21:00 | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-024 | Auto-lock 07:00 giorno successivo | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-025 | Regola 48h | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-026 | Sblocco/correzione chiusure | Operational settlements/packages/notes/closure; direct, HTTP and browser | #34 | PASS |
| CC-CAP-027 | Email / Communication / Notification | Native notification delivery, scoped reporting/export/dashboard; encrypted native backup | #36 / 54 | PASS |
| CC-CAP-028 | Reporting operativo | Native notification delivery, scoped reporting/export/dashboard; encrypted native backup | #36 / 54 | PASS |
| CC-CAP-029 | Export/print/email document surfaces | Native notification delivery, scoped reporting/export/dashboard; encrypted native backup | #36 / 54 | PASS |
| CC-CAP-030 | Dashboard direzionale | Native notification delivery, scoped reporting/export/dashboard; encrypted native backup | #36 / 54 | PASS |
| CC-CAP-033 | Permission model generale | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-034 | Audit business | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-035 | Backup | Native notification delivery, scoped reporting/export/dashboard; encrypted native backup | #36 / 54 | PASS |
| CC-CAP-038 | API/web endpoint authorization | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-039 | Direct/query/report leakage regression suite | Security/lifecycle/audit; direct and HTTP permission regression; patient intake | #30 / 54 | PASS |
| CC-CAP-040 | Operational deploy reproducibility | Pinned Compose, runtime acceptance, fresh build and destroy/recreate | #27 / 54 | PASS |
| CC-CAP-041 | Finance domain bridge and native master mapping | Native accounting links and immutable source snapshots | #38 | PASS |
| CC-CAP-042 | Native receivables/payment/corrections | Sales Invoice, Payment Entry, GL and Payment Ledger | #40 | PASS |
| CC-CAP-043 | Bank import/reconciliation and overdue controls | Native Bank Transaction; explicit reconciliation, retained debt and audited extension | #42 | PASS |
| CC-CAP-044 | Incoming XML and native payable lifecycle | Private intake/review; Purchase Invoice, payments, cancel/amend | #44 | PASS |
| CC-CAP-045 | Professional expected/received economics | Explicit parametric rules; unknown remains unknown; native Supplier comparison | #47 / 56 | PASS — DECISION-054 threshold policy |
| CC-CAP-046 | Administrative exception queue | Assignment, priority, due/defer, reappearance, condition-based auto-close | #47 / 56 | PASS |
| CC-CAP-047 | Finance reporting, permissions and audit | Scoped native accounting totals; Accountant readonly; finance browser | #48 / 56 | PASS |
| CC-CAP-048 | Provider-neutral SdI adapter | Private payload/attempts/protocol; actual worker, simulated outcome and bounded retry | #50 | PASS simulated / PARTIAL real fiscal route |
| CC-CAP-049 | Independent provider-neutral TS adapter | Explicit synthetic opposition/eligibility snapshots; correction chain and actual worker | #52 | PASS simulated / PARTIAL real fiscal rules |
| CC-CAP-050 | Integrated verification/UAT/release readiness | Sequential integrated suites, immutable fresh/recreate proof and this report | #54 / 56 | PASS integrated DEV / PARTIAL later UAT/release |

## Stack and historical evidence

| Work | Issue | Draft PR | Implementation commit | Evidence |
|---|---|---|---|---|
| WP-00 | #21 | [#27](https://github.com/2008hitch-afk/centrochange_core/pull/27) | `b87da21` | [WP-00](evidence/WP-00-2026-10-04.md) |
| Wave 1 | #28 | [#30](https://github.com/2008hitch-afk/centrochange_core/pull/30) | `24e9c9c` | [Wave 1](evidence/WAVE-01-2026-10-04.md) |
| Wave 2 | #31 | [#32](https://github.com/2008hitch-afk/centrochange_core/pull/32) | `43f69b3` | [Wave 2](evidence/WAVE-02-2026-10-04.md) |
| Wave 3 | #33 | [#34](https://github.com/2008hitch-afk/centrochange_core/pull/34) | `fcaaee0` | [Wave 3](evidence/WAVE-03-2026-10-04.md) |
| Wave 4 | #35 | [#36](https://github.com/2008hitch-afk/centrochange_core/pull/36) | `6e20e96` | [Wave 4](evidence/WAVE-04-2026-10-05.md) |
| WP-01 | #37 | [#38](https://github.com/2008hitch-afk/centrochange_core/pull/38) | `7e55f5c` | [WP-01](evidence/WP-01-2026-10-05.md) |
| WP-02 | #39 | [#40](https://github.com/2008hitch-afk/centrochange_core/pull/40) | `72cccb3` | [WP-02](evidence/WP-02-2026-10-05.md) |
| WP-03 | #41 | [#42](https://github.com/2008hitch-afk/centrochange_core/pull/42) | `595fb06` | [WP-03](evidence/WP-03-2026-10-05.md) |
| WP-04 | #43 | [#44](https://github.com/2008hitch-afk/centrochange_core/pull/44) | `ff999cd` | [WP-04](evidence/WP-04-2026-10-05.md) |
| WP-05 | #45 | [#47](https://github.com/2008hitch-afk/centrochange_core/pull/47) | `227cf66` | [WP-05](evidence/WP-05-2026-10-05.md) |
| WP-06 | #46 | [#48](https://github.com/2008hitch-afk/centrochange_core/pull/48) | `fed8605` | [WP-06](evidence/WP-06-2026-10-05.md) |
| WP-07 | #49 | [#50](https://github.com/2008hitch-afk/centrochange_core/pull/50) | `b5fd72e` | [WP-07](evidence/WP-07-2026-10-05.md) |
| WP-08 | #51 | [#52](https://github.com/2008hitch-afk/centrochange_core/pull/52) | `b5db852` | [WP-08](evidence/WP-08-2026-10-05.md) |
| WP-09 | #53 | [#54](https://github.com/2008hitch-afk/centrochange_core/pull/54) | `816119e` → `6eb3972` | [WP-09](evidence/WP-09-2026-10-05.md) |
| DECISION-054 corrective WP-05 delta | #55 | [#56](https://github.com/2008hitch-afk/centrochange_core/pull/56) | `ba45816` | [DECISION-054](evidence/DECISION-054-2026-10-05.md) |

## Original immutable foundation evidence — retained

Immutable image `sha256:bd1ac57f9c95df0daf48e20db226965eb0e4ccee91d93393a81fc3a7cfc4a7a5`, built without cache from committed application source `6743131`, uses deployment/QA recipe `43d24bb`. All six application services use this image and named volumes, without source overlays. Exact parity covers 162 tracked app files; manifest SHA-256 `9f2044282e039f4bdc2ef10d0f67de62755f51c10b8c90208656035bcd2c3e54`.

Both final fresh cycles PASS: site creation, native ERPNext setup, Healthcare/Marley, Builder and centrochange_core installation, migrate/assets, health/login/Desk, WebSocket 101, enabled scheduler and actual short/long workers, native synthetic Patient/Practitioner/Appointment smoke, and negative bootstrap guards. The second cycle follows destruction of only the dedicated DEV project/network/four volumes. Both metadata snapshots contain 976 DocTypes and have normalized baseline SHA-256 `98b1192ffada845219e4f9cc796cf4ef9ef2e1ef6c65663a9bf67f6622fc30c1`.

Each cycle passes all 12 sequential suites: **176 direct checks, 158 HTTP groups and 35 browser checks**, plus actual internal native Notification Log delivery. These are suite check/group counts, not every individual assertion. Authorization, lifecycle, booking concurrency, historical pricing, closure/packages/notes, native receivables/payables/bank reconciliation, professional queue/reporting and simulated fiscal worker paths are covered. Desktop/mobile, public ingress and Accountant readonly browser checks pass with no application JS exceptions. Every owned fixture cleanup passes; final synthetic operational/financial counts are zero. These original cycles preceded the DECISION-054 correction; they remain evidence of the unchanged foundation, not tests of the new application image. Six enabled Centro Change scheduled methods record actual execution in both cycles.

Native backup of database, public/private files and configuration is encrypted with AES-256, verified through decryption/hash/integrity, and raw copies removed. Encrypted archive: 1,178,762 bytes; SHA-256 `2b7414ea62f4a317b4833539bf43882c0c5cd3e4b68996f9c570218073bdcaf4`. Restore was not tested.

Detailed commands, suite counts, resolved defects and screenshots are in [WP-09 evidence](evidence/WP-09-2026-10-05.md) and [sanitized machine-readable evidence](evidence/WP-09/acceptance-summary.json). Temporary raw output, backups and synthetic credentials remain outside Git. Historical PARTIAL results are preserved at their original stack stages; this composed candidate provides final DEV PASS evidence for those stages.

Approved booking policy is retained: native Item Price is resolved on the Europe/Rome booking date, then the session snapshot is immutable through moves/catalog changes. Cancellation is late strictly below 48 hours; exactly 48 hours is timely. HC-0005 DECISION-054 now supplies the unpaid compensation rule; no default threshold or rate is inferred.

## Corrective acceptance — DECISION-054

The targeted immutable-image correction implements configurable N per professional with separate patient/professional counts, first-N maturity, excess suspension, payment-driven deterministic reevaluation and Management-only audited override. Original facts, rule/source snapshots and historical states remain append-only. One deterministic condition per session updates/reopens/closes on replay and native payment reversal. Current projections use per-session sequence; suspended/configuration-missing amounts remain unknown, never final zero.

Current immutable image `sha256:63ab9305015fa9afb63d7665fa79cfee3ea77ea8862f6cc915ca875fc9dd6ff3`; source parity PASS for 166 tracked app files (manifest `36e621b5955859b7847092ed91e601a31f987c578b157caf22014bf968faa13c`), six services without overlays. Supported migration/977-DocType schema and current runtime smoke PASS. The correction passes **189 integrated direct checks, 18 WP-05 HTTP groups, 21 financial/report HTTP groups and 8 focused browser checks**. All owned fixtures clean up; current policy is DECISION-054, with zero threshold/expectation/queue and synthetic clinical/financial fixture rows afterward. Enabled native administrative reconciliation records execution after the correction.

[Delta evidence](evidence/DECISION-054-2026-10-05.md) records the new image, targeted integrated/direct/API/report/export/query/browser checks, migration, cleanup and the scope of reused foundation proof. No new full 12-suite or fresh/destroy/recreate rerun is claimed for the correction. GOAL-02 is not opened or executed.

## Residual policy and later-goal gates

- DECISION-054 closes the former unpaid compensation policy gate. Management must configure each professional threshold explicitly; a missing threshold remains a visible configuration exception, rather than a business-policy unknown. Compensation rates are separately explicit.
- Package units are operational; no package sale price is inferred. Native invoicing rejects unsupported package billing contexts rather than deriving units × session tariff.
- Real fiscal verification, tax population, SdI route/provider and TS subject/transmitter/credentials/opposition treatment are gated. All adapter execution here is SIMULATED, with real internal workers and retained fictional results.
- Patient email overdue notices are local native Communication simulation; no real SMTP or patient delivery is claimed. Internal native Notification Log delivery is exercised.
- Restore/DR, upstream upgrade rehearsal and branded public website remain deferred capabilities, not claimed tests. Backup encryption/integrity does not prove restore or a production RTO.
- Shared fiscal Customer/Supplier totals are reported as shared payer/payee totals; no arbitrary patient/professional attribution or undefined margin is inferred.
- GOAL-02 UAT, final review/merge and production readiness are separate gates. This DEV evidence does not certify fiscal compliance, GDPR compliance or production readiness.

## Next-goal recommendation

Review the stacked draft PRs and the recorded open policies, then explicitly authorize GOAL-02 (#23) for a named UAT candidate, deterministic demo data and client validation guide. No subsequent goal is automatically started.
