# #97 — before_request guards, isolated before/after — 2026-10-08

**TECHNICAL PASS / READY_FOR_OWNER_REVIEW.** #97 remains OPEN. New PR DRAFT stacked on #94; no merge, main change, RC22 deployment, upstream upgrade or GOAL-03. This is a fix of hook composition, not a new permission decision. References #95, #75, #76, #77.

## Authority, exact base and scope

Owner-authorized [issue #97](https://github.com/2008hitch-afk/centrochange_core/issues/97) and [mission plan](https://github.com/2008hitch-afk/centrochange_core/blob/plan/mission-a-goal02-stabilization-20261008/docs/plans/MISSIONE-CODEX-097-BEFORE-REQUEST-GUARDS-2026-10-08.md). Base verified twice: `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`, branch `issue-75/final-client-ux-review`. Work branch `issue-97/before-request-guards`.

Single product delta: `app/centrochange_core/centrochange_core/hooks.py`, destructive second assignment replaced by append, with explanatory comment. Original four guards remain in original order, then client_language and login_language, each once. No change to guard bodies, grants, roles, API, schema, finance, booking or providers. Test infrastructure adds isolated Compose/build orchestration, hook configuration/unit/WSGI trace, socket HTTP probes, parity and reuse of existing regression suites.

## Isolated environment and image

Compose **centrochange-m97-lab**, site **mission97.local**, localhost port **8097**. Separate sites/DB/Redis named volumes and network, fresh random private credentials, no UAT volume/database/account/credential copy. Upstream image declares anonymous logs volumes: each verified exclusive to its isolated container; no binds or shared log volumes. Versioned Compose generated from existing recipe with fixed lab names, site and port; CLI rejects wrong target/image family. Isolation checked before tests and after controlled isolated redeploy. Private files under `/tmp/centrochange-m97-lab` outside Git; credentials never published.

Fresh synthetic `goal02-demo-v1` seeded only in lab. No shared-site seed/reset/backup/restore/migrate/restart. Initial and fixed builds use original bootstrap; later isolated UI-only redeploy skips configurator/migration and invalidates only lab cache. No manual edits in running containers.

Final reproducible image **centrochange-m97:issue97-guards-v3**, exact `git archive` source **ee0573a42d631d97ccd5a77567ae3961de6a926c**, local image ID **sha256:7fc1313f42bada8df12848af9ac94b7e719e3a99265880bcd4239fc3a6c84888** (not registry digest). Parity PASS: 239 tracked app files / six services / no overlays; application manifest **8c5cf4d2a83115c1e59647ced101871b869f6e79dff73003d21cb7f20226653d**. Final docs/test-only additions retain these exact product bytes. Earlier v1/v2 lab images have the identical fixed application manifest; read-only browser coverage from those runs is explicitly reused, while final v3 hook/HTTP/backend/#77/health proofs are rerun. No new UAT RC/tag created.

Pins unchanged: Frappe16.31.0, ERPNext16.32.0, Marley16.5.2, Builder1.33.0; original base image digest retained.

## Verified upstream semantics

Official [Frappe hooks documentation](https://docs.frappe.io/framework/user/en/python-api/hooks). Exact official Frappe `v16.31.0` commit **6a329d068416768ec47ccd3326b9cc95a8d7bf99**: [`frappe/__init__.py`](https://github.com/frappe/frappe/blob/6a329d068416768ec47ccd3326b9cc95a8d7bf99/frappe/__init__.py), [`frappe/app.py`](https://github.com/frappe/frappe/blob/6a329d068416768ec47ccd3326b9cc95a8d7bf99/frappe/app.py). Both runtime source-file SHA256 hashes exactly equal official pinned bytes; see [upstream.json](upstream.json). Base image strips git metadata, so package version plus exact file hash comparison is used, not a fictitious runtime git SHA.

`_load_app_hooks` reads final module attributes, merging installed apps; `get_hooks` uses request/site/client caches; request initialization calls resolved before_request entries sequentially after authentication/form parsing. Four Frappe hook contributions remain first (recorder, monitor, rate limiter, OAuth CORS); other installed apps add no before_request in this lab. After composition the six application functions follow in the preserved original order. Lab cache explicitly cleared on each controlled image switch.

## BEFORE: CONFIRMED_RUNTIME_GAP

[Hook read-back and invocation trace](hooks-before.json): app resolved only **client_language, login_language**; global list included the four Frappe contributions plus those two. None of the four original app guards invoked on HTTP ping.

Trace uses Werkzeug HTTP Client through the actual pinned Frappe WSGI application and real request initialization. Process-local unittest.mock wrappers record original function calls; original bodies execute, no hook replacement or permanent server/core patch. Separate socket HTTP requests against nginx/backend prove externally observed behavior.

[HTTP BEFORE](http-before.json), eight principals, 16 checks: ping 200; deliberately nonexistent native query report returns **404** for A/B/C, Secretariat, Finance, Accountant and Manager; Guest native permission denial 403. This proves non-manager dispatch reached the native report handler instead of the explicit guard. No financial/patient report queried, no successful data payload returned. **No data leak or exploitability is asserted.** The configuration defect and missing guard dispatch are the confirmed findings.

## AFTER: expected hooks and invocation

1. finance.request_guard.before_request
2. security.diagnostics.before_request
3. security.api.before_request
4. operations.notes.request_guard
5. operations.website_brand.client_language
6. operations.website_brand.login_language

[AFTER trace](hooks-after.json): all six resolved and invoked, exactly once/in order, ping 200. Confidential private-note targeted request sets redaction flag before note denial and returns 403; presentation hooks intentionally do not execute after an earlier denial. Actual service principals and a disabled synthetic principal are denied by the original API guard (direct negative probes, disabled-row change rollback-only).

[Socket HTTP AFTER](http-after.json): **55 PASS checks**. Native nonexistent report is 403 for all non-managers; Manager still reaches native 404. Guarded native accounting/regional prefixes, known ERPNext balance helper and form `cmd` routing denied before query. Own clinical-author note read 200; all other listed principals incl Manager/Guest denied with no document payload. Retained-session test: fresh c login/ping200, temporarily disabled isolated User.enabled, same authenticated session ping403; original enabled flag restored in finally without changing modified or any role/grant. This test uses restored isolated fixture writes, distinct from fully rolled-back backend fixtures.

No response bodies, note text, credentials or raw logs published. Matrix labels are synthetic role aliases.

## Regression and genuine limits of fresh-fixture coverage

- Hook composition unit, Python syntax and git diff checks: PASS. Unit asserts exact six ordered entries without duplicates, and would fail on the original two-entry module.
- [Backend](backend.json): **240 PASS checks**, seven modules, including operations.integration_acceptance (189), confirmation, search, professional/patient reporting, final permission review and private UAT boundary. Finance/native invoices/payments/receivables/bank/compensation/fiscal simulation/security/booking/move/cancel/reopen covered by composed integration. Per-module full rollback verifies persistent counters and canonical row hash unchanged.
- [#77 final server matrix](backend.json) and [final HTTP/browser matrix](browser-permissions.json): PASS for Manager, Secretariat, Finance, Accountant, A/B/C, Guest; center/practitioner/patient/native/document/query/export/print/file/direct-page boundaries and private-note exclusion. Server controls, not menu visibility, supply evidence.
- [Agenda](browser-agenda.json): 12 PASS checks incl navigation, availability, A/B/C and stale responses. [Grid geometry](browser-agenda-geometry.json): shared tracks, resize/scroll/mobile/canonical card dates PASS; no product calendar change.
- Professional browser18, Patient browser20, search11, empty/error states6: PASS. Shared UI v1 twelve-surface desktop/mobile suite PASS, including Finance/public/login/debranding/no Desk leakage. Print PASS, localized permitted native/source document presentation, PDF generated externally. Read-only browser scenarios do not submit booking/payment or alter demo business data.
- **Historical fixture-specific attempts did not pass their setup assertions**: security.audit_view_acceptance requires two Owner Oct6/7 reasons, scheduling.reopen_acceptance requires original serial appointment133, finance.expectation_ui_acceptance requires appointment132 overridden40, finance.bank_trace_acceptance requires original reconciled invoice81; browser accounting.cjs requires Owner-cancelled invoice row. None exists in fresh isolated seed, so these historical assertions are NOT APPLICABLE here and are not reported PASS. No copying or fabrication of Owner actions. Equivalent boundaries/business lifecycle, audit authorization, compensation override, native invoice cancel/correction and bank reconciliation are tested by generic rollback integration, final #77 and current view browser suites. Owner-specific historical-state replay remains outside this mission.
- [Health](health.json): PASS, nine isolated services, HTTP/assets, websocket101, two workers, scheduler enabled and fresh short/long jobs finished. No timestamp-only periodic-job inference.

## Dataset and non-interference

[Lab before](lab-before.json) / [after](lab-after.json): identical 31-DocType counters and canonical-row fingerprint **e2dab8007c196043d108dd11744832b32e2c44ea460660bb0a740609c6ab4cf3** after tests and restored enabled fixture. Backend uses additional per-module rollback checks. Auth sessions/last-login and diagnostic logging are runtime metadata, not part of the business-row fingerprint; no claim they remain byte-identical.

[Non-interference](noninterference.json): RC22 Owner-business fingerprint **6d60ef5cc5a73550e935736465269c64fea283bdbe5e61cc1e966db9f4bf2d58** unchanged with all tracked counters; six original app container IDs, images, StartedAt, restart counts and mounts unchanged. Five previously isolated audit rows excluded consistently by existing Owner-fingerprint helper, retained untouched. Commands on shared runtime were only read-only canonical fingerprint and docker inspect; no login/cache clear/job enqueue/restart/migrate there. Port8082 keeps RC22; the isolated lab uses8097.

Original #92/#93/#94 branch chain untouched; original #94 HEAD rechecked84e9df1. main untouched. No merge, production, real data/providers or SdI/TS submission.

## Reproduction commands (Docker-group host)

```
python3 infra/mission97_lab.py up
python3 infra/mission97_lab.py seed
python3 infra/mission97_hooks.py                 # BEFORE on initial RC22-source lab
python3 infra/mission97_http.py --phase before
python3 infra/test_before_request_hooks.py
python3 infra/mission97_lab.py build --source-ref ee0573a42d631d97ccd5a77567ae3961de6a926c --image centrochange-m97:issue97-guards-v3
python3 infra/mission97_lab.py redeploy --image centrochange-m97:issue97-guards-v3
python3 infra/mission97_hooks.py
python3 infra/mission97_http.py --phase after
python3 infra/mission97_parity.py --source-ref ee0573a42d631d97ccd5a77567ae3961de6a926c
python3 infra/mission97_regressions.py backend --output-dir /tmp/cc-m97
python3 infra/mission97_regressions.py browser --script permissions --output-dir /tmp/cc-m97-permissions
python3 infra/mission97_regressions.py browser --script uat --output-dir /tmp/cc-m97-agenda
python3 infra/mission97_regressions.py health --output-dir /tmp/cc-m97
python3 infra/mission97_regressions.py fingerprint --output-dir /tmp/cc-m97
```

Browser plugin unavailable; existing pinned Playwright1.58.2 is used. Host-only driver remaps fixed existing acceptance targets to lab, refuses shared names, and uses separately generated lab credentials. No permission/core monkeypatch in persistent runtime. BEFORE requires the initial lab image, not the fixed image; do not switch shared UAT to reproduce.

## Review gate

**READY_FOR_OWNER_REVIEW**, TECHNICAL PASS within approved mission. Review required before any proposal to replace UAT baseline. Owner-specific historical-fixture replay is not claimed. #97 remains OPEN; PR DRAFT, base #94; no #94/#92/#93 body/branch updates. Lab remains isolated/running for review; shared Owner UAT URL continues to serve unchanged RC22. No acceptance or deployment authorization inferred.
