# #139 — Third DEV installation readiness — 14/10/2026

**Result: `FULL_END_TO_END_REHEARSAL_PASS`. Third DEV installation: `NOT_AUTHORIZED / NOT_STARTED`.** PR #140 remains DRAFT. This report covers a complete rehearsal with the real installation executor on an isolated clone; it does not mark the shared DEV as updated or GOAL-02 as Owner accepted.

## Exact sources and shared DEV baseline

- Application candidate remains `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f` (57 application paths; no #78/#128). Executor `infra/issue139_install_gate.py` SHA-256: `ca6df1016d2876da959745366ca7f4fb90b6c3d9b3a13067aec09a6c0340fc5b`. Full rehearsal driver SHA-256 at execution: `51f5f7da15f27ff6d564134b5b76203eae262db0be956f065866b70bce1d7471`; final driver with exact temporary-image and network cleanup: `741dd8e09613b5064c54d443df2fa50af8b32e182c0883b3e63c0410ef17504b`. The later cleanup addition does not alter the executor or the successful installation/rollback trace.
- Before and after, read-only executor `--dry-run` returned `DRY_RUN_PASS`: one `centrochange-dev` project, nine services, six application services on `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`, two demo centers, six security/language hooks, accepted #79 CSS, pinned Compose/env and Site checks. Owner dataset fingerprint `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3` was unchanged. No shared DEV container, database, Site, volume, env or service was modified or restarted.
- Host gate before clone: at least 8 GiB Docker disk reserve and 3 GiB MemAvailable. Clone used its own named network and volumes, private log volumes, and `127.0.0.2:8082 → frontend:8080`. The command router rejects shared `centrochange-dev` targets, Compose/env outside the private clone root, Docker copies outside the clone, mounts in executor `docker run`, and unapproved child commands. The nested security runner is admitted only as the exact clone-targeted `python -I` invocation. Positive/negative routing tests passed.

## End-to-end matrix

| Gate on isolated clone | Result | Evidence |
| --- | --- | --- |
| Restore real synthetic Site backup | **PASS** | Verified DB, public/private files and Site config backup hashes; restored nine-service baseline with the same Owner/Communication fingerprint as DEV. |
| Actual executor preflight, checkpoint and encrypted backup | **PASS** | Executor SHA and dependency hashes verified; private checkpoint and four-part encrypted native backup verified before installation. |
| Candidate build/install/migrate | **PASS** | Actual `execute()` path built image `sha256:a3b11fe1caca0fb324a01e9d05d4dcf1073506e8af45c8746f0a7efcf2140544`, installed six application services, preserved three technical services and migrated clone Site. |
| Center state and audit | **PASS** | Both centers failed closed after migration; Centro A activated once through the governed method with Administrator audit; Centro B remained inactive. |
| Assets and realtime | **PASS** | 11 served asset SHA checks, 69 manifest mappings; browser/public Socket.IO canonical and tunnel Origin 200, foreign/mismatched Origin 403; pinned proxy uses internal 8080 behind public 8082. |
| Seven demo roles, desktop/mobile | **PASS** | Chromium `128/128` route checks; 14 role/viewport sweeps, zero route failures or unexpected mutations. |
| Native List/Form | **PASS** | 11/11 pairs at 1440 px and 11/11 pairs at 390 px; real rendering checked, not HTTP status alone. |
| Administrator and Guest boundary | **PASS** | Administrator Desk browser check; Guest/public route constraints included in security suite. |
| Centro Change security suite | **PASS** | Actual nested `python -I` runner executed **38/38** checks: REST/list/query/export scope, cross-professional data, direct API denial, Guest routes, booking race/idempotence, private notes, reassignment and disabled sessions. Synthetic fixture cleanup `PASS`; Owner/Communication fingerprints and service snapshot unchanged. This is not a claim of full Frappe security certification. |
| Actual executor rollback after successful W5 | **PASS** | Real `restore_services()` consumed the encrypted checkpoint once; original images, DB/files/config, schema, roles/permissions, six hooks, Owner/Communication fingerprint and HTTP readiness returned to baseline. |
| Clone disposal and DEV integrity | **PASS** | Clone containers, named volumes and exact temporary image tags removed. Independent shared DEV snapshot before/after was identical; final read-only dry-run passed. |
| Third shared DEV installation | **BLOCKED BY OWNER GATE** | Not executed; prior two installation authorizations were consumed by their rollbacks. |

Relevant offline verification after the run: 39 #139 Python unit tests, 5 Rome date/DST cases, 4 fiscal outcome states, 7 session-action cases, `git diff --check`, and DEV read-only `--dry-run` passed. The previous two isolated rehearsal interruptions were test-environment issues: anonymous image log volumes failed the clone ownership guard, then browser fixture traversal and the strict child-command router blocked W5. Each clone was rolled back/removed; the final run used named private log volumes, an explicit browser-user access probe, and the exact `python -I` child allowlist. No failed DEV installation was retried.

Reproduction command for this clone-only rehearsal, after verifying the exact branch/backup and host resources: `sudo -n python3 -I infra/issue139_full_rehearsal.py`. The driver fails closed if clone resources already exist and checks DEV read-only before/after; it cannot authorize or invoke a shared DEV installation.

Representative real Chromium screenshots from the final run: [Agenda desktop](screenshots/w5-e2e-agenda-desktop.png), [Agenda mobile](screenshots/w5-e2e-agenda-mobile.png), [Sales Invoice Form desktop](screenshots/w5-e2e-sales-invoice-form-desktop.png), [Sales Invoice Form mobile](screenshots/w5-e2e-sales-invoice-form-mobile.png). Raw test reports, screenshots and encrypted backup evidence remain private under `~/.local/state/centrochange-single/issue139-full-rehearsal/20261014T223115Z-3472891/`; no credentials, dumps or raw private logs were committed.

## Residual limits and single next gate

This PASS proves the **mechanism on an isolated clone**. The shared DEV still serves the restored baseline; W5 and the 38 security controls have not passed on a third DEV installation. Screenshots also retain Owner-review UX items: the Agenda landing shows both «Inizio» and «Agenda» active, synthetic technical identifiers are visually prominent in the invoice, and some native invoice labels remain untranslated. Browser route PASS does not settle visual acceptance or every accounting workflow.

**One Owner decision required for any next mutation:** authorize a **third, single controlled installation** on the existing `centrochange-dev`, pinned to application `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f` and executor SHA-256 `ca6df1016d2876da959745366ca7f4fb90b6c3d9b3a13067aec09a6c0340fc5b`, with a fresh private UTC gate generated at actual start (maximum four operational hours plus one recovery hour), fresh preflight/checkpoint/encrypted backup, full W5 on DEV and at most one verified rollback. The rehearsal authorization does not authorize this installation. No merge, production, GOAL-03 or Owner acceptance follows automatically.
