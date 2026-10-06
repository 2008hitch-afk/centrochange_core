# UAT-PATIENT-REPORT-01 — TECHNICAL PASS / READY_FOR_OWNER_UAT

## Requirement and authority

Issue #68 records the approved HC-0005 Discovery/Secretariat §4.3 Patient View, consolidated Center/Professional/Patient reporting, DECISION-033 CORE classification, Executable Solution Baseline and approved quote. This is the remaining core implementation gap under GOAL-02 #23, following Owner acceptance of Professional View #66. Local implementation baseline/capability map CC-CAP-047 and accepted financial/security behavior are reused. No new commercial scope, accounting/pricing/role policy, DECISION-054 change or GOAL-03.

This is technical readiness only. **Owner manual UAT REQUIRED; #68 remains OPEN.** Draft stacked PR #70 remains unmerged; no automatic acceptance or stack merge.

## Branch, candidate and runtime

`issue-68/patient-customer-view`, created from exactly `43bdaee10b3527cce2bcd44787c6012b4a17609f`, the remote/local current head of accepted `issue-66/professional-view`. PR base is that branch, not Agenda. Preflight worktree was clean.

Deployed application commit **`17691a75163fde9f4d89a77ecfd3f07ac6e124c7`**; named candidate **`goal02-20261006-rc17`**; image **`sha256:8e410aa770b353410c917c806225b4e88f7f6777e0c1c00e8586547f341adec8`**. Subsequent evidence-only commit leaves deployed app bytes unchanged. Exact `git archive` image build via versioned `infra/uat_candidate.py --existing-site-ui`, supported build/assets and controlled app service recreation. **No migrate/schema change, dataset reset/seed, source bind or manual container patch.**

Source parity PASS: 183 tracked app files, six app services on the same immutable image with volume mounts only. Nine services running, HTTP ping 200, Redis/DB healthy; bench doctor reports two online workers. Frontend only `127.0.0.1:8082`; Owner tunnel URL http://localhost:8082/centrochange.

Pins unchanged: Frappe 16.31.0 / `6a329d068416768ec47ccd3326b9cc95a8d7bf99`; ERPNext 16.32.0 / `81a6f97566b83609c3917404a560b673050e907d`; Marley 16.5.2 / `934d6c162868139dfbe80c23d6102adb7ec25adb`; Builder 1.33 / `41987c064da4650e6901b5da82b7c76add452ebf`. Twelve installed files match official pinned sources. Relevant official guidance: [Sales Invoice](https://docs.frappe.io/erpnext/sales-invoice), [Payment Entry](https://docs.frappe.io/erpnext/payment-entry), [Frappe Database API](https://docs.frappe.io/framework/user/en/api/database). Native invoice/payment source and runtime, rather than a new ledger, govern the projection.

## Implementation and period semantics

`finance.patient_reporting.patient_view` reuses existing `finance.reporting.summary(customer=...)`; `collections.position`, latest overrides and original native due dates supply collections facts. `/pazienti_report` uses the shared Professional View period/metric/table helpers and stylesheet. Report → Pazienti works from operational Report and Finance Riepilogo; permitted operational Patient rows link to the same detail. Professional View remains on the accepted framework, with shared helpers extracted without changing economics.

List: one row per **Customer in the selected center**, showing authorized Patient identities, fiscal identity, sessions, issued gross, net collected, prominent current outstanding, overdue, open deadline and state. An unmapped Patient is separate and has **unknown accounting amounts**, never center totals or invented zero. A shared payer is labeled “Soggetto fiscale condiviso — saldo riferito al Customer”; totals occur once. Invoice line source links show composing Patient/session only where deterministically scoped; no attribution of an entire invoice/payment to a single Patient.

- Sessions: appointment date in the selected interval; exact authorized records and deterministic performed/cancelled/future classification.
- Invoiced: sum of signed submitted native Sales Invoice `grand_total` by posting date in period, including native returns; drafts/cancelled documents excluded.
- Collected: signed native Customer Payment Entry Receive/Pay amounts by posting date; includes advances/refunds, does not infer invoice allocations or change operational Paid.
- Outstanding: **signed current native outstanding** for all nonzero submitted Customer invoices in the center, including open credits and invoices outside the period. This is not a reconstructed period-end balance.
- Overdue: positive open invoice debts past effective end-of-day Europe/Rome deadline; latest approved deferral preserves original due date. Credits are not overdue debts and do not activate an old deferral.
- Operational debts/agreements remain separate, never added to native outstanding. Group block means at least one composing Patient is blocked by `collections.position` in this center; individual Patient flags are shown separately. The existing booking guard may also enforce debts from other centers; this view does not expose foreign-center debt details or claim a global booking clearance.

`collections` adds original deadline to its returned debt dictionaries, including operational agreements, without changing the effective deadline/override rules. Specific-date missing-data behavior is preserved even for legacy overridden inputs. No accounting write occurs in the reporting endpoints; only GET and guarded CSV export are added.

## Dataset and expected versus observed

Persistent synthetic `goal02-demo-v1`, Centro A; period **28/09/2026–31/10/2026**. Current Owner accounting state is preserved, rather than resetting old expectations of Beta's earlier partial balance.

| Case | Expected canonical facts | Observed |
|---|---|---|
| Beta, regular after current Owner receipts | Native submitted invoice/receipts; no remaining balance | Issued 100 EUR, collected 100 EUR, outstanding 0, overdue 0, Regolare |
| Gamma, regular | Native fully received invoice | Issued 100 EUR, collected 100 EUR, outstanding 0, overdue 0, Regolare |
| Theta, open/scaduto/block | Native open invoice and collections position | Issued 100 EUR, collected 0, outstanding 100, overdue 100, 1 open invoice, original/effective due 30/09/2026, block true |
| Extended deadline probe | Debt/original date retained, latest override effective | PASS; outstanding stays 100, deferred invoice excluded from overdue, rollback restores original state |
| Shared payer probe | Two Patient identities, one Customer row; native totals unallocated | PASS; no duplicate position, fiscal records reconcile, scoped source references only |
| Unmapped Patient probe | No inferred fiscal allocation | PASS; monetary position unknown, no center invoice/payment rows |
| Signed credit input probe | Native signed outstanding retained, no positive overdue/deferred classification | PASS; -25 retained, overdue 0, Credito contabile |

The shared mapping, unmapped mapping, extended deadline and signed-field input probes run in a private **versioned savepoint/rollback** acceptance method. They leave no persistent Owner dataset changes. The credit probe tests projection of a signed native field, not creation of a native credit posting; actual invoice/payment/credit posting is covered separately by the receivables regression. Browser uses the preserved Beta/Gamma/Theta dataset, not a fabricated response. No shared payer or deferral is left in the Owner dataset solely for test convenience.

## Drill-down and security

All direct reconciliation PASS for Secretary, Finance, Management and Accountant:

- session KPI equals exact IDs/count and date interval;
- invoiced equals sum of native composing submitted invoices;
- collected equals signed native composing Payment Entries;
- outstanding equals sum of native nonzero outstanding records;
- overdue equals sum of positive genuinely overdue invoice records;
- list totals equal detail totals; no duplicate Customer row;
- original/effective deadlines and block equal collections facts;
- deterministic invoice source links are scoped to center/Customer, with no foreign Patient identity projected.

Browser PASS **20 check groups**: Report entry, current balances/list/detail, each KPI drill-down, native due/block, four presets/custom period, current-vs-period balance, delayed stale response, exact CSV record count, mobile internal scroll/no document overflow, quick operational Patient entry, Finance Riepilogo entry, S/F/M/T permissions and private-note exclusion. Page identity/content, screenshots and absence of application JS exceptions verified. Desktop 1536×1024, mobile 390×844. Browser plugin unavailable: pinned Playwright 1.58.2 fallback.

A/B/C: direct page, new API, existing finance report, export and native Sales Invoice/Payment Entry/Payment Override query denied or permission-filtered empty. Finance: foreign center, foreign Patient and unknown Customer requests/exports denied. Finance/Accountant acquire no operational session detail privilege. Secretary private-note direct read denied; no private professional note body in UI, report or export. Guards run before privileged queries. No new role or self-financial view introduced.

## Regressions, fixes and test provenance

- Professional View #66: **18 browser checks PASS** on `fec6406` / rc16; final rc17 differs only in Patient report labels/per-Patient block display. Professional modules, APIs and shared helpers are byte-identical.
- Agenda #63: **12 checks PASS** on `86dcb92` / rc13: role A/B/C, filtering, availability, navigation/date picker, accepted visual layout, stale response and mobile.
- Booking/sposta/cancella: **16 operational browser checks + actual short-worker Notification Log PASS**, disposable fixture cleanup PASS, on rc13.
- Invoice/payment: **17 HTTP checks PASS**, including native draft/submit/partial/full payment/credit, reversal/amendment, helpers/raw report/export negatives and revocation; cleanup PASS.
- Collections/banking: **16 HTTP checks PASS** on rc13, native allocations, original debt/override/booking block, permission negatives, reversal/replay and cleanup.

The rc13 operational/collections/finance foundation files are unchanged in final rc17; later changes are isolated to the new Patient projection, its presentation and private tests. New Patient browser, canonical tests, upstream and full app parity reran on final rc17. Required JS syntax/Python compile checks PASS; no new dependencies.

Observed failures were resolved: inherited nowrap status caused mobile overflow (specific-page wrapping fix); old financial harness tried to recreate persistent public route Marco (disposable fixtures now use `public_route=False`); signed-credit probe revealed an obsolete override incorrectly marked active (positive-debt predicate fix). One operational fixture startup and one concurrent browser login timed out; serialized reruns passed, and no product cause is asserted for those transient harness failures. An interrupted rc13 Compose deployment left a temporary frontend name; versioned Compose restart/recreation restored normal services/source parity. Final rc17 build/deploy and health PASS. No unversioned container fix or reset was used.

Commands: `infra/uat_candidate.py --existing-site-ui`, `infra/image_acceptance.py`, `infra/upstream_acceptance.py`, private bench `patient_report_acceptance.run`, `infra/uat_browser_acceptance.py --script patient|professional`, `--agenda-only`, `infra/browser_acceptance.py --operational-only`, `infra/receivables_acceptance.py`, `infra/banking_acceptance.py`, `infra/uat_demo.py inspect`, `bench doctor` and HTTP ping. Private credentials/raw traces remain outside Git.

## Preservation and handoff limits

Before/after demo manifests byte-identical; Beta/Gamma/Theta financial cases match first/final canonical runs. Savepoint probes restored mapping/deadline/invoice fields; HTTP fixtures report exact-owned cleanup PASS. No reset/seed, deletion of Owner UAT data or change to prices/business rules.

Manual Owner UAT still required; issue #68 OPEN, PR #70 draft. Bounded 366-day interval / 500 composing records and fiscal subjects; EUR economics only. Collected is the approved Payment Entry cash projection, not an allocation to invoices or a complete qualification of other native receipt channels. Current outstanding/effective due date is not a historical snapshot. Native date picker format follows browser locale; selected period is explicit Italian. Individual collections flags are center-scoped; no cross-center details exposed. No real data/providers, real SdI/TS traffic, production or GOAL-03.

Evidence: [machine reports/screenshots](patient-customer-view-2026-10-06/). Manual scenario: [Client Validation Guide](../uat/CLIENT-VALIDATION-GUIDE.md#uat-patient-report-01--pazienti--soggetti-fiscali).
