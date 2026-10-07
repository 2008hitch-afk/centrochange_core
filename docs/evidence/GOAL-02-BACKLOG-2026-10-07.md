# GOAL-02 backlog checkpoint — 2026-10-07

TECHNICAL PASS for the implemented/tested deltas. Overall acceptance PARTIAL: Owner rechecks, identity decision and final reviews remain pending. No issue closed, no PR merged, no Owner acceptance or GOAL-03 authorization.

## Issue / draft PR / Owner gate

| Issue | Draft PR | Tested delta | Pending Owner check |
|---|---|---|---|
| #71 | [#82](https://github.com/2008hitch-afk/centrochange_core/pull/82) | [Audit register](goal02-remediation/ISSUE-71.md) — technical PASS | UAT-08 |
| #78 | [#83](https://github.com/2008hitch-afk/centrochange_core/pull/83) | [Governed reopened reschedule](goal02-remediation/ISSUE-78.md) — technical PASS | UAT-11 |
| #81 | [#84](https://github.com/2008hitch-afk/centrochange_core/pull/84) | [Readable expectation comparison](goal02-remediation/ISSUE-81.md) — technical PASS | UAT-15 |
| #62 | [#85](https://github.com/2008hitch-afk/centrochange_core/pull/85) | [Native bank allocation trace](goal02-remediation/ISSUE-62.md) — technical PASS | Bank reconciliation |
| #72 | [#86](https://github.com/2008hitch-afk/centrochange_core/pull/86) | [Reviewed TS snapshot detail](goal02-remediation/ISSUE-72.md) — technical PASS | TS review |
| #73 | [#87](https://github.com/2008hitch-afk/centrochange_core/pull/87) | [First-meeting synthetic confirmation](goal02-remediation/ISSUE-73.md) — technical PASS | First meeting/retry |
| #74 | [#88](https://github.com/2008hitch-afk/centrochange_core/pull/88) | [Authorized name/UID search](goal02-remediation/ISSUE-74.md) — technical PASS | Patient search |
| #79 | [#89](https://github.com/2008hitch-afk/centrochange_core/pull/89) | [Searchable canonical selectors](goal02-remediation/ISSUE-79.md) — technical PASS | Booking/assignment/report |
| #80 | [#90](https://github.com/2008hitch-afk/centrochange_core/pull/90) | [Italian accounting labels](goal02-remediation/ISSUE-80.md) — technical PASS | Finance walkthrough |
| #64 | [#91](https://github.com/2008hitch-afk/centrochange_core/pull/91) | [Existing application Direction profile](goal02-remediation/ISSUE-64.md) — technical PASS | Profile definition/exclusions |
| #76 | [#92](https://github.com/2008hitch-afk/centrochange_core/pull/92) | [Neutral debranding and identity proposal](goal02-remediation/ISSUE-76.md) — technical PASS | Explicit identity decision |
| #77 | [#93](https://github.com/2008hitch-afk/centrochange_core/pull/93) | [Final permission matrix/cache isolation](goal02-remediation/ISSUE-77.md) — technical PASS | Final Owner matrix review |
| #75 | [#94](https://github.com/2008hitch-afk/centrochange_core/pull/94) | [Final existing UI polish/walkthrough](goal02-remediation/ISSUE-75.md) — technical PASS | Final visual Owner walkthrough |

Reviewed synthetic screenshots: [login](goal02-remediation/client-login.png), [access management](goal02-remediation/client-Gestioneaccessi.png), [Finance](goal02-remediation/client-finance.png), [public mobile](goal02-remediation/client-public-mobile.png). Raw logs and credentials remain outside Git.

## Exact runtime and source

Named candidate **goal02-20261007-rc31**, git-archive source `2a8a37b3fc3526d5bd6b12e8e23d351d234fc1df`, image `centrochange-uat:goal02-20261007-rc31`, local image ID `sha256:905a46a5c307dd1ae12dd8077383028419c5791885fcffd463b1dbb1a08b48ea` (not a registry digest). Branch `issue-75/final-client-ux-review` is the tip of thirteen dedicated stacked branches; each PR base is its immediate predecessor. Subsequent test/evidence-only commits do not change these app bytes.
208 tracked app files; manifest `af9653a56eef6db582a28dff951b4118c103501aebb0b7b8650a22b036c71137`; six app services share one image, no source bind/manual overlay. Nine services running. Frontend bound only to 127.0.0.1:8082; Owner tunnel URL http://localhost:8082/centrochange.

Pinned Frappe 16.31.0 / `6a329d068416768ec47ccd3326b9cc95a8d7bf99`; ERPNext 16.32.0 / `81a6f97566b83609c3917404a560b673050e907d`; Marley 16.5.2 / `934d6c162868139dfbe80c23d6102adb7ec25adb`; Builder 1.33.0 / `41987c064da4650e6901b5da82b7c76add452ebf`. Core unmodified.

Only #73 introduced schema: versioned CC Booking Confirmation migration applied on rc24. Later builds reuse existing volumes without migration. Native app/website cache invalidation is in the deploy recipe; no manual container patch.

## Discriminating validation

- Static PASS: 165 Python AST parses, 11 app JavaScript module syntax checks, 16 browser scripts.
- Composed runtime backend PASS: **262 checks / 11 versioned suites**, executed from rc29 immutable image; full rollback between suites; before/after Patient, Appointment, Invoice, Payment, GL/PLE, Audit, Communication and confirmation counts unchanged. No seed/reset. Backend unchanged in rc30/rc31.
- rc29 browser PASS: Professional View 18, Patient/Customer View 20, accepted Agenda 12, final seven-role/Guest security 8. Includes exact drill-down reconciliation, period changes, stale-response regression, scoped API/query/export/print/private notes and mobile containment.
- rc30 Finance PASS: readable compensation selection 4, existing native bank allocation trace 1, TS reviewed detail 1, native Italian accounting controls 2. rc31 adds only a public missing-route message; these surfaces unchanged.
- rc31 targeted PASS evidence: final eight-check main-surface walkthrough; name/UID/selector and delayed query regression; three-check synthetic confirmation read-only browser. See machine-readable result files for actual check names.
- Runtime rc31 PASS: HTTP/assets, websocket HTTP101 upgrade, two workers, fresh UUID jobs finished on short and long queues, scheduler enabled, nine services. Scheduler periodic execution is not inferred from enabled status.
- Browser plugin unavailable; pinned Playwright 1.58.2 Chromium used. Browser suites serialized using host lock, preserving native two-session account limits.

Commands (private env/account files not included):

```sh
sg docker -c "python3 infra/remediation_acceptance.py"
sg docker -c "python3 infra/uat_browser_acceptance.py --script <suite> --output-dir <external-results>"
sg docker -c "python3 infra/image_acceptance.py --source-ref HEAD"
sg docker -c "python3 infra/uat_runtime_health.py"
```

## Verified failures and minimal fixes

1. Native Closed appointments cannot be moved; only an explicitly audited Reopened closure now permits governed correction. Closed/cancelled/no-show and future-time restrictions retain negative tests.
2. Native document-scoped Patient access does not imply generic list rights. Operational search uses exact currently authorized Patient/center pairs and fixed identity fields; no permission grants added.
3. Persisted Redis app hooks left old login branding after an image replacement despite asset parity. Supported versioned `bench clear-cache` corrects it.
4. Native private-file cache allowed browser replay after switching principals, while a no-store server call correctly returned403. Supported after_request no-store for protected responses fixes default-cache replay; server permissions unchanged.
5. Native date input rendered US dates despite Italian browser locale. A readable Italian overlay retains native ISO/date picker/keyboard focus and original canonical values.
6. Old regression fixtures assumed globally empty accounting and the original supplier invoice; Owner UAT legitimately posted/amended records. Tests now compare unchanged counts and current submitted native source, preserving their discriminating assertions.
7. Concurrent demo browser logins evicted sessions under native limit2. Test runner serializes suites; no session/user changes.
8. Missing optional public demo route exposed an English native error. A specific presentation mapping now explains unavailable configuration in Italian; no route/data created. Public delayed-route response cannot enable old slots.

## Dataset and economics

Existing Owner UAT data preserved: Beta native invoice/payment/bank allocation; Theta original/effective due dates and Owner override; current amended supplier invoice and historical cancelled original; manual compensation override and its prior suspended expectation; TS version/correction chain. Existing semantic seed hash is historical and is not presented as the current modified dataset hash. No real transmission, SMTP, provider credential or clinical data. Mutating integration checks run in rollback, while browser checks are read-only except native authentication metadata.

## Required decisions / limitations

- #64: existing CC Manager is identified as Direzione completa. No new role, role profile or grant. Current Manager global scope is explicitly documented, not silently narrowed or expanded; native catalog setup remains technical. Owner reviews [profile boundary](../uat/APPLICATION-DIRECTION-PROFILE.md).
- #76: [identity proposal](../uat/UI-IDENTITY-PROPOSAL.md) remains PROPOSED. Authorized debranding is applied and tested. New transversal palette/logo/component identity awaits explicit Owner decision.
- #77: [permission matrix](../uat/FINAL-PERMISSION-MATRIX.md) ready for Owner review, permission-model delta **NONE**. No operational need for Administrator; infrastructure/catalog setup excluded.
- #75: [final walkthrough](../uat/FINAL-OWNER-WALKTHROUGH.md) ready for Owner visual UAT of the existing interface. New identity application and final acceptance remain gated by #76. Technical PASS is not visual acceptance.
- Public demo Marco route exists; optional Francesca route is not configured. UI reports this explicitly; no seed performed. Custom service/account names are retained when translation cannot be inferred.
- Knowledge repository governance remains inaccessible (GitHub repository/AGENTS contents API404 on2026-10-07). Prior GOAL02 CANDIDATE0019/extraction is historical; supplementary cross-client extraction cannot be published or governed until access is restored. No unapproved learning loaded or promoted, and no NO_GENERALIZABLE_LEARNING claim made. This remains a delivery documentation gap before final GOAL02 Done, not a reason to redo accepted product work.

## Upstream references

Official Frappe [Database API](https://docs.frappe.io/framework/user/en/api/database), [REST API](https://docs.frappe.io/framework/user/en/api/rest), [Document API](https://docs.frappe.io/framework/user/en/api/document), [supported hooks](https://docs.frappe.io/framework/user/en/python-api/hooks), [portal pages](https://docs.frappe.io/framework/user/en/portal-pages), [background jobs](https://docs.frappe.io/framework/user/en/api/background_jobs) and [version16 CSV/PO translations](https://docs.frappe.io/framework/user/en/bench/frappe-commands); ERPNext [Bank Transaction](https://docs.frappe.io/erpnext/bank-transaction) and [Payment Reconciliation](https://docs.frappe.io/erpnext/payment-reconciliation). Pinned native source/runtime behavior checked for Marley Closed status, ERPNext allocation references, Communication without mail delivery, Frappe private-file cache/session limit/website hooks and Italian translations. Current pinned runtime evidence takes precedence over assumptions from latest docs.
