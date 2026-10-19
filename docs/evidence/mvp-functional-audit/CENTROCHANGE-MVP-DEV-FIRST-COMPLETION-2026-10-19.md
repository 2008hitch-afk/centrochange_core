# Centro Change MVP — DEV-first functional completion, 19 October 2026

**Technical result: 46/46 documented MVP capabilities PASS, subject to Owner review.** This combines the 40 previously evidenced functional PASS with six previously PARTIAL rows in `capability-matrix-completion.csv`. It is not a claim that all 46 were rerun today, and it is not GOAL-02 Owner acceptance.

## Installed baseline and controlled update

- One `centrochange-dev` project, one Site `centrochange.local`, nine active services. Frappe and ERPNext `16.50.0`, Builder `1.35.1`, Healthcare `16.6.1`.
- Installed application source `a03386c41a78692fd4b6d370ec56b1d21d613841`, six-service image `sha256:e2df539cc99fee6965102f539c0969dbec98d2ad59bf7c0d9631d4e03774acdb`, tag `centrochange-single:mvp-devfirst-a03386c-v3`.
- Versioned executor at local commit `468debd89565ab5e05b0005af3af57960de19ff3`, SHA-256 `c6905c90221ea8e3774dad712898c9bb74c41bf9b53fa4f0419ffa9c7df58b6d`. Private Owner gate started `2026-10-19T20:14:14Z`; operations end `2026-10-20T00:14:14Z`, recovery end `2026-10-20T01:14:14Z`.
- Private run `issue139-install-runs/20261019T201455Z-3466982`: `DEV_UPDATED_WITH_GAPS`, essential installation checks PASS, four encrypted backup parts verified, candidate image/source/assets/realtime proxy/Administrator/essential browser authorization PASS. The executor intentionally left the separate mutative finance/security suites BLOCKED. No second DEV update or rollback occurred. HTTP ping returned 200 after installation and again after POS testing.
- The first executor invocation stopped before any DEV mutation because the isolated Nginx rehearsal had already occupied the candidate image tag. After confirming no container used that tag, it was removed; the same gate then performed the **single** DEV update. This was a preflight packaging issue, not an additional installation.

## Error → cause → fix → proof

| Error | Cause and correction | Local commit and verification |
|---|---|---|
| Frontend health failure in previous attempt | Private build context gave the Nginx template mode `0600`; `frappe` could not read it. `COPY --chmod=0644`, read as `frappe`, `nginx -t`, and isolated startup now run before stopping DEV. | `f4b85fd`, `468debd`; isolated read/config/start PASS; live frontend healthy. |
| Previous rollback data fingerprint differed | Candidate scheduler legitimately closed one synthetic orphan administrative condition and appended one audit event. Read-only reconciliation found exact `Open`→`Closed` event, retained missing-source reference, and zero new GL/Payment Ledger/invoices/payments. No audit deletion. | `468debd`; reconciled fingerprint `f5cea384c350dc8780818ccec752a314885085b8f14afb49a9c34115fa68b517` used as new pre-update checkpoint. |
| POS browser first stopped at login | Frappe 16.50 login uses the form submit button, not `.btn-login`. | `90c6811`; live read-only login PASS. |
| Synthetic accounting fixture reused an occupied slot | Native canceled history retains the first appointment. Fixture now chooses the first free Monday from a bounded synthetic range, while booking collision guards remain active. | `90c6811`; read-only preflight selected distinct dates before each new fixture. |
| Permission fingerprint changed after synthetic assignment | `set_assignment()` creates exactly two authorized shares on the new synthetic Patient. Host control now proves the complete **preexisting** permission fingerprint unchanged after excluding only this exact tagged Patient, and validates the two expected shares. No existing Patient permission changed. | `90c6811`; exact hash matched the pretest baseline and fixture-share checks PASS. |
| Browser payment proof failed after refresh | The detail pane loads asynchronously; immediate text assertion raced its fetch. The test now waits for the invoice and uses a separate session for the unauthorized professional. | `b3887c7`; targeted live browser PASS, professional direct API `403`, zero JS errors. |

## CC-CAP-042 — card/POS

Private evidence `browser-evidence/mvp-pos-20261019T202356Z/`: a new synthetic Patient, appointment and EUR 100 Sales Invoice were created in operational Centro A. Finance used a native Bank/POS Mode of Payment to record a EUR 5 partial Payment Entry against that invoice. The Frappe backend verified the EUR 95 outstanding amount and native invoice/payment link; Chromium verified the document after refresh and denied the direct Finance API to a Professional (`403`). The payment and invoice were then natively canceled. Both vouchers retain four GL rows each with zero net account effect; Payment Ledger and historical links were not directly deleted. Browser, native reversal and all seven host integrity controls reported PASS. Screenshots `before.png` and `after-refresh.png` remain in that private evidence directory. No external card transaction occurred.

Two preceding tests diagnosed browser-only failures. Their synthetic invoices and any created payments were also natively canceled. Three uniquely tagged accounting chains, their Patients/appointments/methods and legitimate canceled accounting/audit history remain traceable; this is intentional retention, not an active customer payment. All preexisting monitored Owner records, database identity, Communication and preexisting permissions stayed unchanged. The fresh final run passed.

## CC-CAP-050 — fixture and integrated readiness

Preconditions were checked before writing: synthetic Site flags, one active center, company/cost center, EUR bank account, service/price/tax mappings, valid native payment mode, free slot, no prior invoice for the new appointment, and absence of unknown orphan queue references. Unique tags and request keys prevent accidental reuse. The fixture uses native cancellation and retains balanced GL history; it does not delete posted ledger rows or change Accounts Settings. The final runner confirmed the preexisting document snapshot and permission fingerprint unchanged, expected synthetic shares only, unchanged Communication and DB identity, nine services and six hooks. The previously passing 38 HTTP security controls and 189 integrated checks remain historical evidence; current installation also passed essential browser authorization and Administrator checks. The unrelated 128-route campaign was not repeated.

Offline suite after test corrections: **108/108 PASS**. The earlier MariaDB `1020` error did **not recur** with native reversal. Its exact historical row-contention cause remains undetermined; the old direct-ledger-delete cleanup path was removed from this proof.

## Access and residual limits

The demo is accessible through the Owner's SSH tunnel: `ssh -N -L 8082:127.0.0.1:8082 empv26@srv2033673`, then open `http://127.0.0.1:8082/app/cc-unified-desk?cc_view=agenda`. Use the existing private demo credentials; none are recorded here.

The six completion rows are PASS; the 40 earlier rows retain their prior evidence rather than being silently relabeled as fresh runtime tests. Owner functional/visual acceptance of GOAL-02, production readiness and GOAL-03 remain separate. PR #140 and #141 remain DRAFT; no merge or GitHub publication was performed in this mandate.
