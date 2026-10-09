# Mission B R3 — PARTIAL

Source: `e85fce588de6012a47da302710b9f9c615211279`. Owner authorization: issue99 comment6077401448. No merge or UAT deployment.

## Actual results

| Check | Result |
|---|---|
| TARGET image build/import | PASS; immutable image recorded in target-image.json |
| Frappe/ERPNext16.50.0, Builder1.35.1, Healthcare16.6.1 | PASS; pinned commits verified;239 application files and7 official source fingerprints reconciled |
| CURRENT clone from R2 native checkpoint | PASS; full schema/metadata/business/upload files/apps identical |
| TARGET native migrate | PASS after isolated DB/cache memory redistribution |
| Custom fields/custom permissions/User Permission | PASS |
| User role assignments | PASS;16 new non-user native Has Role rows, no removed rows; see role delta |
| Backend regression | PASS:240 checks in7 modules |
| before_request security hooks | PASS:6 hooks |
| Real HTTP regression | PASS:55 checks |
| Additional historical acceptance harnesses | FAIL: fixture route Marco collision; receivables/banking positive role permissions also returned403; these failures are retained and unresolved |
| Browser regression | FAIL/INCOMPLETE: old login selector adapted, then missing Frappe asset map caused404 and no navigation; cached-native mapping rebuild stopped by PSI before completion |
| Real rollback CURRENT | PASS: native checkpoint restore, full schema/metadata/business/files/apps/pins equality, private synthetic UAT manifest supplement, demo validation,189 operational checks, HTTP200 |
| Protected30 containers | PASS: no ID/image/start/restart/mount/network/port/state differences; RC22 HTTP200 |

## Operational findings

R2 base-extraction blocker was overcome with a dedicated builder cgroup (2GiB, no swap, one CPU, BuildKit parallelism1, read8MiB/s/write4MiB/s), cached dependency transport and Cypress cache permissions. Native Builder and Healthcare built successfully. Heavy phases were serialized.

The 2GiB memory.max was enforced, but kernel memory.peak briefly exceeded it; exact sampled peaks are in resource-summary.json. OOM counter increased0→5 across failed segments: confirmed DB384MiB, worker192MiB and scheduler128MiB failures; some increments were between monitor samples. No claim of an OOM-free mission. Fail-closed stops retained; no thresholds relaxed. Docker pause/freezer drift and teardown-cgroup monitor races were corrected only in orchestration.

Final proposed runtime cap was services2048MiB + QA512MiB=2560MiB: backend640, DB512 with bounded native caches, worker384 serving long/default/short, scheduler256, Redis64 each, websocket96, frontend32. All current R3 containers are STOPPED. TARGET migrated volumes, rollback CURRENT volumes, archives and R1/R2 resources remain preserved. No cleanup/prune.

The native backup covers private/files, not private/uat/demo.json. The original synthetic manifest was read from the stopped R2 container and restored privately, with checksum recorded; no credentials committed. Future checkpoint procedure must explicitly include this private orchestration artifact.

## Blocking remainder

Full browser/regression acceptance is not demonstrated. Latest native cached asset-map build again tripped unchanged PSI full>=1% for3 samples despite >5GiB available. Do not restart or relax protection automatically. Review the measured resource/PSI boundary and unresolved403 positive cases before a new execution authorization. Last successful real rollback is preserved; no TARGET promotion is authorized.

Private evidence roots: `/home/empv26/.local/state/centrochange-b99-r3*-20261009/`. These contain confidential synthetic credentials/checkpoints and are NOT Git artifacts. Only sanitized summaries and orchestration are included here.

Official source used: [Frappe pinned bundler](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/bundler.py), [pinned login](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/www/login.html), [native worker queues](https://docs.frappe.io/framework/user/en/api/background_jobs), [cgroup memory.max semantics](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files).
