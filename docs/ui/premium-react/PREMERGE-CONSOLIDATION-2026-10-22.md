# #150 — Pre-merge consolidation checkpoint (22/10/2026)

**Scope:** review and offline CI only. PR #150 remains DRAFT; no merge, DEV deploy, migrate, schema/role change or primary-UI switch is authorized by #156. Distinguish source tests from live Frappe evidence and Owner acceptance.

## CI contract

`.github/workflows/premerge.yml` runs only on same-repository PRs or manual dispatch; avoiding duplicate push and PR runs conserves the account's included minutes. It uses a read-only token, commit-pinned checkout/setup actions, no secrets, private fixture, DEV URL, Docker service or `pull_request_target`. The backend job verifies the complete source manifest, pinned image recipe, Python syntax and 44 offline regression tests. The frontend job uses the committed npm lockfile, typechecks, rebuilds, compares tracked assets to the manifest, and runs both Playwright suites against local Vite and **synthetic intercepted API responses** at 1440×900 and 390×844. These jobs cannot prove Frappe permissions, schema migration or restore. Actual run status is reported on the PR, not inferred from this file.

The Owner has selected the local VPS pre-merge suite while GitHub Actions is unavailable. Run `python3 infra/premerge_local.py --ref <candidate-sha> --report /tmp/cc-premerge-<candidate-sha>.json` from a clean #150 worktree. The command creates a disposable detached Git worktree, installs only lockfile-pinned frontend packages there, runs the source manifest, Python regressions, React typecheck/build, asset parity and both synthetic Playwright suites, and writes a machine-readable report outside Git. It does not access Docker, a Frappe Site or the DEV. A local PASS is **not** GitHub CI PASS or live Frappe PASS. The existing workflow remains available but is not a consolidation dependency.

## Reviewed high-risk surfaces

| Surface | Source / effect | Required integration gate |
|---|---|---|
| `hooks.py` | `after_migrate` calls security/operations/finance configure and `configure_existing_users`; User hooks, client routing, before/after request and DocType permission hooks also change | Compare hook lists on final tree; isolated migration rehearsal, roles/Custom DocPerm/User.default_app and route checks before any DEV migrate |
| `security/install.py` | `Branch.cc_operational` Custom Field, configured master permissions, Property Setter and unique constraints | Confirm existing Site metadata, duplicate data and pre/post schema/permissions on isolated clone; any unapproved delta blocks |
| `patches.txt` / `issue75_native_filters.py` | New post-model-sync Property Setter for Healthcare Practitioner standard filter | Confirm Patch Log state; execute once on isolated clone and compare metadata |
| Backend API/finance guards | DECISION-063 scoped reads and approved writes, negative role/center boundary and audit | Python offline plus final tree and Frappe live positive/negative matrix; no generic CRUD or broadened permission |
| Docker/Compose/asset manifest | Complete pinned app image; generated React/Frappe assets; historical overlay remains in repository | Source/image parity and 9-service Compose review, no overlay or historical configurator deployment |

No new DocType JSON or DocPerm JSON is added by #150 relative to #149, but the install hooks above can still mutate metadata and permissions during `migrate`.

## Dependency on #146

The app tree at #146 HEAD `83f1cb17bb213b47c256781b346ee434c0f23a4b` is byte-identical to its earlier commit `1f88207c6a71c4bf0252b912fe83313337cab16f`; later #146 changes are documentation, browser probes, an installer and an infra test. #150 pins the entire backend app from `1f88207` plus an explicit allowlist of reviewed React/API changes and verifies every file hash. **This is source equivalence, not Git ancestry or approval of #146's historical installer.** Do not apply both installer paths to DEV or merge #146 blindly with #150; review its base chain and decide whether to integrate, supersede or retain its non-overlapping evidence before product merge. No duplicate DocType or alternate runtime is proposed.

Read-only `git merge-tree --write-tree` between #146 `83f1cb17` and #150 reports six textual/add-add conflicts. Each #146 blob matches the approved `1f88207` backend baseline byte for byte; each #150 blob differs because of later reviewed changes. The proposed resolution for every conflict is the **#150 blob**, subject to final-tree tests. This preserves the baseline and the subsequent React/API/security changes; it does not merge or rebase either PR.

| Conflicting path under `app/centrochange_core/centrochange_core/` unless stated | #146 = baseline `1f88207` blob | Proposed #150 blob |
|---|---|---|
| `finance/reporting.py` | `ec525765` | `86c2220d` |
| `finance/reporting_acceptance.py` | `670ad6df` | `9080750e` |
| `operations/client_landing.py` | `662f95ca` | `6ea164a9` |
| `security/dev_acceptance.py` | `f6b18439` | `862c99e3` |
| `security/fixture_cleanup.py` | `d16f0cec` | `72a81f3a` |
| `infra/security_acceptance.py` | `b32c8213` | `371d9c2b` |

The #146 historical installer and its two passing unit tests remain evidence, not a second runtime installation path. Before any later authorized merge, recheck these blob identities at the then-current HEADs and run the local full-source suite on the final candidate. Do not mechanically take the #146 side or discard its documentary evidence.

## Isolated migration rehearsal — prepared, not executed by this checkpoint

1. Obtain a specific gate for migration of a **temporary isolated** Site/DB clone, naming its container, DB, volumes, network, data classification and cleanup. DECISION-066 explicitly records `schema_migration_authorized: false`; its restore/test authorization does **not** cover a new pre-merge `migrate` rehearsal. Confirm the clone is synthetic, owns its fixture, cannot reach or mount the live DEV database/Site, and uses private configuration outside Git. If these facts cannot be proved, stop this activity.
2. Before mutation, capture sanitized inventories/hashes of installed apps, Patch Log, schema columns/indexes, Custom Field, Custom DocPerm, Role, Property Setter, `User.default_app` distribution and critical table counts. No user names, patient rows, secrets or raw dumps in Git/logs. Confirm backup/restore of this exact clone.
3. Run the final candidate's `bench --site <TEMP_SITE> migrate` **only in that isolated clone**. Record exit status, patch executions and after_migrate effects; fail on unexpected permission expansion, schema difference, unique-constraint failure, real mail/provider traffic or data loss. Compare the same inventories and ownership/fixture counts after migration, then rerun to check idempotency. Exercise role/center/direct API negatives. Keep the DEV untouched.
4. Restore the clone to its checkpoint and verify the original fingerprints before disposing only the named temporary resources. A rehearsal PASS requires full evidence; no static test or historic restore is a substitute.

**Current gate:** no isolated clone identity, migration-specific authority or pre/post inventories have been established for this pre-merge action; DECISION-066 explicitly withholds schema migration authorization. Therefore `MIGRATION_REHEARSAL=NOT_EXECUTED`, `AFTER_MIGRATE_LIVE=NOT_VERIFIED`. Final merge review must see the actual rehearsal under a new gate or an explicit Owner disposition of this risk.
