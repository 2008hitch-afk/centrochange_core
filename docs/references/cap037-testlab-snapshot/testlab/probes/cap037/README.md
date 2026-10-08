# CC-CAP-037 — isolated upgrade / migration rehearsal

Tracking: #65, coordinator #56.

## Purpose

Prove upgrade/migration safety for the pinned Centro Change stack without upgrading the shared `centrochange-dev` runtime.

The rehearsal covers Frappe + ERPNext + Builder + Marley Health + `centrochange_core` and must produce enough evidence to classify CC-CAP-037 technically. It is a testlab artifact only: no product implementation, upstream patch, canonical capability-matrix edit, or `docs/DECISIONS.md` edit belongs here.

## Safety invariants

- Shared Compose project `centrochange-dev`, site `centrochange.local`, network and volumes are source-only and MUST NOT be migration targets.
- Upgrade commands run only against a separately named project/site/volume set.
- Synthetic data only.
- Secrets, DB dumps, file archives, backup artifacts and raw logs stay outside Git.
- The target is immutable: image `tag@sha256` plus exact app commits. Floating `main`, `develop`, `version-*` or tag-only targets are non-probative.
- No manual edit inside a running container may be used to make the rehearsal pass.
- No uncommitted patch/worktree edit may be used to make the rehearsal pass.
- `tasks/pending` is coordinator-owned; this rehearsal is a Codex isolated-environment handoff, not a shared-runtime runner task.

## Inputs

1. Clean checkout of `centrochange_core` at the exact **current** commit used as the source definition.
2. A target manifest copied from `target-manifest.example.json` with every `REQUIRED_*` value replaced by an immutable pin.
3. A separately named working directory outside the repositories, e.g. `/tmp/centrochange-cap037-<run-id>`.
4. Local secrets supplied only through an external env file; never copy them into this repository.
5. Synthetic source-state material sufficient to reproduce the current site on the isolated project. This may be an authorized external backup/snapshot or an independently bootstrapped synthetic site. Do not require a new shared-runtime mutation merely to start this rehearsal.

## Required topology

Suggested defaults (may be changed, but must remain disjoint from the shared runtime):

- Compose project: `centrochange-cap037-<run-id>`
- Site: `centrochange-cap037.local`
- HTTP: localhost port different from `8082`
- Volumes/networks: names derived only from the isolated project
- Work area / checkpoints: outside Git

Before any migration, record `docker compose config`, `docker ps`, volume names and network names and assert that none resolves to `centrochange-dev-*`.

## Rehearsal phases

### 0 — pin inventory and fail-closed target validation

Record current runtime facts from the isolated **current** clone:

- `bench version` for Frappe/ERPNext/Builder/Marley/centrochange_core;
- `git -C apps/<app> rev-parse HEAD` for every Git app;
- image ID/digest used by the current clone;
- clean Git status for the `centrochange_core` checkout and all app trees that are expected to be immutable.

Validate target manifest:

- every target app commit is a 40-hex SHA;
- every image is `tag@sha256:<64 hex>`;
- no placeholder remains;
- target is not identical to current on all stack components;
- Frappe/ERPNext compatibility is explicitly represented by one controlled target image/ref set;
- Builder and Marley target commits are explicit and asserted after fetch/build.

If the target is not fully immutable, result is `BLOCKED`, not `PASS` or `PARTIAL`.

### 1 — isolated current-state clone

Create/start the isolated project on the current pins. Seed only synthetic state. Verify:

- ping/login health;
- installed apps list includes all five stack components where applicable;
- baseline schema/custom fields are readable;
- hooks import successfully;
- workers and scheduler are healthy;
- regression smoke suite passes on current pins.

Capture a **pre-upgrade checkpoint from this isolated clone**. The checkpoint must include DB + public/private files + site config material required for restore, remain outside Git, and have SHA-256 hashes recorded in the run evidence. This satisfies the rehearsal checkpoint requirement without upgrading the shared runtime.

### 2 — target build and pin assertion

Build or obtain the target image only from the manifest. Before migration, assert inside the target image/worktree that Frappe, ERPNext, Builder, Marley and `centrochange_core` resolve to the declared exact commits/versions.

A target build that silently resolves a different commit is `FAIL`.

### 3 — migration

Point only the isolated project at the target image and execute the normal supported migration path. At minimum capture:

- start/end timestamps and exit status;
- `bench --site <isolated-site> migrate` result;
- installed-app versions/SHAs after migration;
- patch log / migration state sufficient to prove supported migrations ran;
- no ad-hoc SQL, console mutation, manual file copy into app source, or unversioned patch was required.

### 4 — schema and custom-field verification

Compare pre/post normalized inventories, not raw DB dumps. At minimum:

- DocType names expected by Centro Change;
- custom fields (doctype, fieldname, fieldtype, options, mandatory/read-only flags where material);
- Custom DocPerm / permission metadata used by the current implementation;
- `centrochange_core` patches declared in `patches.txt` and their applied state;
- required fixtures/configuration records that are intended to survive migration.

Unexpected loss, duplicate field creation, type drift or missing permission metadata is `FAIL` unless the target change explicitly and versionably declares the migration.

### 5 — hooks and assets

Verify:

- `centrochange_core.hooks` imports;
- configured hooks resolve to importable callables/modules where applicable;
- no stale override path points to removed upstream code;
- `bench build` succeeds for Builder and `centrochange_core`;
- generated assets are served by the isolated frontend;
- Builder/public pages needed by the current regression surface render without asset 404s attributable to the upgrade.

### 6 — workers and scheduler

Verify after migration/restart:

- backend/frontend/websocket running;
- short/long workers online;
- scheduler enabled and healthy;
- queue connectivity works;
- no repeated import/migration error appears in the bounded post-start log sample.

### 7 — regression suite

Run the currently approved non-destructive/read-only regression set plus any isolated synthetic mutation tests selected by the coordinator for the release candidate. The minimum suite must cover:

- site/app health;
- permission-sensitive smoke paths already proven relevant to Centro Change;
- Builder/public surface smoke;
- custom hooks/imports;
- database/schema integrity checks.

Do not reinterpret unrelated capability failures as upgrade success. Any regression introduced only after the target migration is evidence against CC-CAP-037 PASS.

### 8 — rollback rehearsal

Rollback is a real restore test, not a written promise:

1. stop/remove the isolated target project/volumes only;
2. reconstruct the isolated project on the exact **current** pins;
3. restore the pre-upgrade checkpoint captured in phase 1;
4. run the supported current-version restore/migrate path only as required for that checkpoint;
5. rerun baseline integrity + health + regression smoke;
6. verify checkpoint hashes and key normalized inventories against the pre-upgrade record.

Never roll back the shared runtime as part of this capability rehearsal.

### 9 — unversioned-fix guard

Before classifying the run, prove:

- `git status --porcelain` is empty in the source and target `centrochange_core` checkout(s);
- app HEADs still match the declared current/target commits;
- no extra patch/module was introduced in a container layer or bind mount;
- the exact command sequence needed to pass is represented by this runbook/harness or versioned product migration code already in the target commit.

If a manual SQL/file/container fix was necessary, the run is `FAIL` for upgrade safety even if the final site becomes healthy.

## Evidence contract

Sanitized result should record:

- run id and timestamps;
- current pins observed;
- target manifest digest and target pins;
- isolated project/site identifiers;
- checkpoint SHA-256 hashes (not the checkpoint files);
- migration exit status/duration;
- normalized schema/custom-field before/after deltas;
- hook/assets/worker/scheduler checks;
- regression summary;
- rollback result;
- repo-cleanliness/unversioned-fix checks;
- `cleanup.verified=true` only when isolated target resources are removed or intentionally preserved with explicit handoff and no shared resource was touched.

Never commit backup paths containing secrets, site config contents, DB dumps, archive payloads or raw logs.

## Outcome rules

- `PASS`: immutable current/target pins; isolated clone; checkpoint; supported migration; schema/hooks/assets/workers/scheduler/regression all pass; real rollback passes; no unversioned fix; shared runtime untouched.
- `PARTIAL`: migration succeeds but one non-critical required verification is genuinely non-discriminating/incomplete while rollback and safety invariants remain proven. Must name the missing evidence.
- `FAIL`: target pin mismatch, migration/schema/regression failure, rollback failure, manual/unversioned fix required, or shared-runtime resource targeted.
- `BLOCKED`: immutable target not supplied, source checkpoint/seed unavailable, isolation cannot be proven before mutation, or required credentials/runtime prerequisites are unavailable.

A `PASS` supports a technical recommendation; it does not itself edit the canonical matrix or approve a production upgrade.

## Codex handoff

1. Create a target manifest with immutable refs.
2. Use `rehearsal_probe.py validate-target <manifest>` before provisioning anything.
3. Provision a uniquely named isolated clone outside the shared project.
4. Run each phase above, using `rehearsal_probe.py` for normalized inventories and guards.
5. Save raw evidence outside Git; commit only a sanitized result/evidence summary if/when the coordinator asks.
6. Post `RUNTIME_DONE` + outcome to #65 and `CLASSIFICATION_READY` or `BLOCKED` to #56.

## Reproducible runtime inputs

`runtime-inputs.current-v16.32.0.json` is the versioned non-secret source definition for a new CAP037 run. It pins the core checkout, Compose path, current base image, target image ID, and required external environment variable *names*. Create a new work area by cloning the declared repository at its commit, then combine its declared Compose file with `fixtures/cap040/compose.rehearsal.override.yaml` and `fixtures/cap037/compose.no-build.override.yaml`. Supply a chmod-600 external env file matching `runtime.env.example`; its values are not recoverable from Docker and must be supplied by an authorized operator.

Before `up`, assert the generated project/site are disjoint from the shared names and that no resolved resource begins `centrochange-dev-`. The lifecycle is: fresh CURRENT bootstrap, baseline verification, external checkpoint with hashes, switch only CAP037 to the manifest target, one observable migrate, post-checks, recreate CURRENT, supported restore, post-rollback checks, then CAP037-only cleanup.
