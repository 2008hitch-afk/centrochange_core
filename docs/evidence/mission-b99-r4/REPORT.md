# Missione B R4 — PARTIAL

Owner authorization: [issue99 comment6080248134](https://github.com/2008hitch-afk/centrochange_core/issues/99#issuecomment-6080248134).
Application source remains `e85fce588de6012a47da302710b9f9c615211279`; no product patch, main merge, UAT deploy or permission grant. Operational branch: `issue-99/isolated-upgrade-r4`. Activation commit: `ea85ffc`.

## Reused proof and isolation

R3 TARGET image `sha256:10e701947cccc377dc1d3c2082a03ef69b81d14da8e08fac75f07e78bcf974ce` reused without rebuild. Frappe/ERPNext16.50.0, Builder1.35.1, Healthcare16.6.1; exact commits in inherited R3 evidence and target-image.json. R3 240 backend checks,55 HTTP checks,6 hooks retained as REUSED PASS, not claimed rerun.

New Compose project `centrochange-b99-r4`, exclusive r4-fit database/sites/assets/Redis volumes and networks, synthetic site b99.local, local8099. Original R1/R2/R3 and RC22 resources preserved. New clone restored from verified R2 checkpoint and migrated natively; repeat migration necessary to isolate R4 changes from retained R3 state, no fresh bootstrap. Runtime/browser configured caps2048+512MiB, no simultaneous build. Incremental disk budget3GiB; actual consumption1,167,577,088bytes. No cleanup was required; no resource deletion was performed. Existing CURRENT/QA/TARGET images and verified external checkpoints/archives retained. Build cache was deliberately preserved because its dependency classification was not needed to meet this small incremental budget.

## Asset404 — VERIFIED ROOT CAUSE, FIX PASS

`sites/assets` is a symlink to bench/assets outside the sites volume. Native cached bundling in a one-off container updated that container's writable image layer; the running frontend continued using the original incomplete image asset map. R3's image map contained only Healthcare, despite native Frappe/ERPNext built files being present.

Reproducible R4 correction: dedicated assets volume mounted at `/home/frappe/frappe-bench/assets` in all app services and native one-offs; run supported `bench build --using-cached --apps frappe,erpnext,builder,healthcare,centrochange_core`, then clear-cache. No compilation, core patch, manual assets.json mutation or app-code bind mount. Initial login4 native asset404; after correction8/8 linked JS/CSS HTTP200. Native login, navigation and actual browser interactions work.

Official pinned [Frappe cached asset implementation](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/esbuild/esbuild.js) supports reconstructing mapping from built artifacts. Procedure is versioned in orchestration/start-target.py and shared-volume configs.

## Browser / synthetic fixture discrimination

13/14 browser suites PASS after two explicit fixture corrections; see browser-final-results.json. Agenda geometry PASS desktop1536,resize1280/1024,mobile390,internal horizontal scroll, professional filtering/week switching/detail panel and booking modal. Maximum header/body drift0px, wrong-day cards0, document overflowfalse. Patient/professional reports, permissions across m/s/f/t/a/b/c, search including stale response, confirmation, walkthrough, print and empty/error states PASS.

TS detail initially required a Beta correction absent from the baseline checkpoint; accounting display required a cancelled Purchase Invoice absent from that same checkpoint. Added only these scenarios on R4 through canonical TS/incoming services, under existing Manager: Beta original ELIGIBILITY_PENDING retained, READY successor with zero attempts, and a new synthetic cancelled invoice while original retained. Both browser retries PASS. No reset, no seed and no provider submission.

UI design conformance suite FAIL at native login: new Frappe16.50 `es-button` markup lacks Tabler .btn and native login head_include overrides the shared head assets inclusion. This is a presentation compatibility defect, not an authentication failure. Native login selector adaptation is test-only. No test expectation weakened to hide this finding. Other UI surfaces had progressed through screenshot checks before this failure; the entire conformance suite is NOT PASS.

Browser plugin unavailable; existing pinned Playwright1.58.2 QA image used. Screenshots in this directory are synthetic. Console/security results are retained in the private evidence tree.

## Finance403 — VERIFIED COMPATIBILITY DEFECTS, UNRESOLVED

Nine real HTTP acceptance suites executed. Security, finance bridge and TS PASS. Receivables, banking, incoming, professional, reporting and SdI FAIL; see finance-results.json. Non-public disposable fixtures explicitly use the supported public_route=False option, avoiding collision with the persistent demo Marco route; product code/route behavior unchanged. Security suite was run without optional public-booking/operations expansion; those optional historical scenarios are not newly claimed PASS.

Finance principal has CC Finance plus standard All/Guest/Desk User, with native Sales Invoice/Payment Entry read access. It lacks template select and direct Payment Entry create by design. No wrong principal or missing configured role was found.

1. Receivable draft fails inside ERPNext16.50 get_taxes_and_charges: new require_permission(template,select). CURRENT16.32 helper did not perform this check.
2. Payment/reconciliation paths fail inside ERPNext16.50 get_payment_entry: new Payment Entry create check. CURRENT16.32 factory did not perform this check. Incoming/professional/reporting suites reach this same failure; they are not independent proofs of six different root causes.
3. SdI suite advances through simulated attempts and then fails positive native invoice cancellation403; precise internal cancellation cause remains NOT VERIFIED, not assumed to be the payment factory.

Official sources compared: [TARGET tax helper](https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/controllers/accounts_controller.py), [TARGET payment factory](https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/accounts/doctype/payment_entry/payment_entry.py), and corresponding CURRENT v16.32.0 source. No grant expansion, Administrator impersonation, monkeypatch or upstream permission bypass was applied.

This leaves a security-sensitive compatibility decision: the existing service-only accounting design cannot satisfy the new native UI factory create/select checks with its current role grants. A reviewed internal adapter preserving scoped service authorization and audit attribution is the recommended direction; broad native grants or principal elevation are not an acceptable automatic fix. No untested product fix is claimed or deployed.

## Real rollback — PASS

Native bench restore of original CURRENT database/public/private files into separate new r4-fit-rollback volumes, plus verified private UAT orchestration manifest supplement. Full schema,metadata,business,files,installed apps,pins match baseline exactly. Demo validation PASS,189 operational acceptance checks PASS, restored HTTP200. CURRENT image `sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80` (Frappe16.31.0/ERPNext16.32.0) restored; no TARGET promotion.

## Resources / final protection

No new OOM: host counter5→5 and monitored cgroups without OOM events. Memory PSI full max0.18%; I/O full max22.21% recorded separately, without relaxing memory PSI thresholds. Minimum MemAvailable4,705,128,448bytes; sampled aggregate cgroup peak1,281,216,512bytes (sampled value, not an absolute instantaneous bound). No safety-stop. Final disk16,765,829,120bytes (~15.61GiB). All R4 containers STOPPED, volumes retained for diagnosis. All85 preexisting containers' ID,image,state,start time,restart count,mounts,networks,ports unchanged; RC22 ping200. No changes to RC22,main,global Docker configuration or production. No GOAL-03.

Private evidence: `/home/empv26/.local/state/centrochange-b99-r4-20261009/`; secrets/checkpoints/runtime.env are excluded from Git. R4 activation is closed with execution_allowed_now=false. No automatic continuation or merge. Final result PARTIAL because Finance and native login design compatibility remain unresolved, despite asset repair, broad browser coverage and verified rollback.
