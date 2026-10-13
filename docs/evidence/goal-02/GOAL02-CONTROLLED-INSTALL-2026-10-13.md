# GOAL-02 A+B+C controlled DEV installation — executor preparation

Status: **BLOCKED / waiting for one Owner interactive-sudo command**. No build, deployment, restart, Site or database write was performed by Codex. Ordinary `docker ps` returned `permission denied while trying to connect to the docker API`; this is the access gate explicitly covered by the Owner's authorization in issue #69 comment `6154887590`.

## Authorized candidate and observed read-only state

- Candidate PR #132 DRAFT: `90817de65312becb6888ef60a8caa5c679248fb0`. #129 is an ancestor; #128 is not. Application source diff since #129 is exactly five public JS/CSS files: `workspace.css`, `audit_view.js`, `finance_workspace.js`, `ui_labels.js`, `workspace.js`. The authorized #79 Page CSS remains in the candidate.
- `/tmp/centrochange-goal02-package-c` was clean at the candidate commit. This executor is developed in a separate worktree/branch and builds application files from the immutable candidate commit, not from the server checkout on #78.
- The private `runtime.env` hash was `d2e2e2849b0507f9bcfe8de78d48dc81cdb59d705aa62a765e96eea60429f080`; the three deployed Compose file hashes match their recorded #79 baselines. The private #79 override exists. Current containers, images, Site, database, hooks and records **could not be inspected** without interactive sudo; the executor gates them before build.
- Host had 53 GiB free disk and approximately 5.15 GiB MemAvailable at preparation time. The executor rechecks current values.

## One-command procedure

The versioned `infra/goal02_install_one_command.py` takes the expected SHA-256 of its own bytes. The Owner should first compare the command and hash in the PR with the local file. It runs on `srv2033673` in the Owner's SSH session through ordinary interactive `sudo`; it does not use `sudo -n`, change access control, fetch remote code or rely on `/tmp/centrochange-issue124` application checkout.

1. Read-only Gate 0: exact source ancestry/delta, clean checkout, env/Compose precedence and hashes, Docker image mapping and nine services, single Site, synthetic flag and record fingerprint, six effective hooks, installed #79 CSS, browser dependencies, disk/memory and evidence permissions. It also compares the old five files in the running backend and served assets with #129, so unexpected ancestral/runtime drift blocks the build.
2. Checkpoint: private copies and hashes of current Compose/env, snapshot of images/mounts/records and individually verified rollback tags for the six application services. Database and Redis services are never selected for recreation.
3. Build: the immutable #79 CSS image is the local base; only five candidate JS/CSS files are copied from commit `90817de...`; `bench build --force` runs inside the new image. No migration, seed, grant, upstream patch or source checkout switch. The candidate image files and label are verified.
4. Activation: a persistent, versioned six-service Compose override replaces only the fourth `COMPOSE_FILE` entry. The prior #79 override remains intact. A resolved-config comparison requires that only six `image` fields change. Only those six services are recreated with `--no-deps --no-build`.
5. Live checks: HTTP/served asset hashes, nine-service health, image/mount integrity, six hooks, synthetic fingerprint, #79 selector Chromium test, seven-role plus Administrator Chromium checks on real routes, security acceptance with booking/operations and rollback-only targeted regression. Browser scripts use no CSS injection or API mocks. Private screenshots and detailed report remain under the protected runtime state.
6. On the first post-activation failure, the executor restores the exact original env/Compose config and recreates the six application services once. It checks old image IDs, technical service IDs, mounts, #79 CSS, hooks, HTTP/assets and record fingerprint. No retry follows. It reports `ROLLED_BACK` or `ROLLBACK_FAILED`; a failure before activation reports `BLOCKED`.

The live tests and rollback have **not** run. A static pass cannot be called `LIVE_TECHNICAL_PASS` or Owner acceptance. If Gate 0 blocks, inspect the private report and stop; do not edit its checks or rerun the attempt without a new decision.

## Static verification

- `python3 -m unittest infra/tests/test_goal02_install.py` — 3 PASS.
- `python3 -m py_compile infra/goal02_install_one_command.py` — PASS.
- `node --check` for the new live browser harness and modified #79 harness — PASS.
- `git diff --check` — PASS.
- `--dry-run` with exact script SHA — pending final commit and hash, then run before Owner command.

## Scope and residual limits

The #79 harness uses roles m/s/a/b for its modal checks; Package B intentionally removes unusable **+ Prenota** from unassigned role c. The new live harness verifies c's empty state and all seven role landings. Browser checks are read-only. The existing security fixture suite creates only its own synthetic rows and cleans them; the executor compares persistent fingerprints afterward. The Administrator browser check uses the existing private DEV credential and deletes its temporary fixture immediately. Credential validity, record counts, current image IDs and post-switch results remain unverified until the Owner command executes.

This PR is an executor stacked on #132, not a merge request for the candidate itself. The GOAL-02 final Owner gate remains separate.
