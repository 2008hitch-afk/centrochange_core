# DEV-first safety stop — 19 October 2026

**Outcome: `ROLLBACK_FAILED`; no further DEV installation or fixture run.** The controlled update at `20261019T195731Z-3443828` reached candidate startup, then failed the essential HTTP health check. The executor restored the previous Compose overlay and six application images, but its data fingerprint check failed. Private evidence is retained at `~/.local/state/centrochange-single/issue139-install-runs/20261019T195731Z-3443828/report.json`.

## Cause and scope

The candidate image `sha256:68063d5042ab37099feb44a85d5418e9a0da7bc747ba2789640fecaedb4dac3b` contained `/templates/nginx/frappe.conf.template` as `root:root 0600`; the prior image has the same file as `root:root 0644`. The frontend runs `nginx-entrypoint.sh` as `frappe` and reads the template with `envsubst` before starting Nginx. A read-only container check reproduced `Permission denied` for `frappe` on the candidate and successful reading on the prior image. The build copied a template from a private `0700` context without setting its mode. A previous probe used root, so it checked content but missed runtime readability. This is the concrete cause of the frontend health failure; no application or POS test was reached.

Local executor correction: copy the template with `--chmod=0644` and verify its bytes in an isolated read-only container **as `frappe`**. The correction has not been built or installed on DEV. The targeted offline executor suite passed 13/13. That is not evidence of a working candidate image.

## Recovered runtime and data delta

After the single rollback, the nine `centrochange-dev` services are up, MariaDB and Redis report healthy, the six application services use the previous `centrochange-single:mvp-devfirst-17100e6` image (`sha256:47d753955c81033b11317381b5fdc63aa5e438cec304e57e93a0b6c0215b6758`), and `/api/method/ping` responds HTTP 200. The active Compose overlay was restored. The checks for six hooks, permissions, center A active/B inactive, Communication and database identity matched the checkpoint.

The Owner/data fingerprint did **not** match: the audit count changed from 138 to 139. During the brief candidate run, its scheduler closed the already identified synthetic orphan `CC Admin Exception p4331eu4v5` and wrote one `CC Audit Event 8taij6e6q0` (`ADMIN_EXCEPTION_AUTO_CLOSED`). The source `CC Incoming Invoice oqgogla0e5` remains absent. The queue closure and audit event remained after image rollback; they were not silently deleted or reversed. No other data divergence was identified in the read-only comparison, but exact checkpoint restoration is not proven. This is why the outcome remains `ROLLBACK_FAILED` despite an accessible demo.

## Capability status and next gate

The last evidenced matrix remains **44/46 PASS**. `CC-CAP-042` (POS) is BLOCKED and `CC-CAP-050` (fixture readiness) remains PARTIAL; the intended POS proof was not run. The other 40 historical results are not reclassified as new live tests. No additional DEV mutation, deploy, restore, fixture or retry is authorized by this stopped gate. Before another update, a new Owner decision must acknowledge the retained audited queue closure and authorize a **new single controlled attempt** using a newly pinned image and executor, with a pre-activation frontend readability check and a fresh checkpoint. The present gate is consumed.
