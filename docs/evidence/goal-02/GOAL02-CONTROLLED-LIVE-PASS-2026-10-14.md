# GOAL-02 controlled DEV installation — live technical result

**Status: LIVE_TECHNICAL_PASS.** Owner authorization: [issue #69 comment 6164303197](https://github.com/2008hitch-afk/centrochange_core/issues/69#issuecomment-6164303197). One authorized attempt was executed on `srv2033673` on 2026-10-14. This is technical evidence, not GOAL-02 Owner acceptance.

## Locked sources and checkpoint

- Application source: `83f8f4f97b74e25e73710b6fc3667be0ae473fce`; it extends the approved A+B/#79 source `90817de65312becb6888ef60a8caa5c679248fb0` with only the two synthetic fixture cleanup files.
- Executor PR #133: `ed0c51d10044f8c4fa7b9b9693b75d756be6bcec`; `infra/goal02_install_one_command.py` SHA-256 `607578830188ab47a5c9d062e0848d5ef2c38c8a5422b503326f30d166592ac5` before execution.
- Read-only gate: clean worktree and exact source ancestry, nine healthy services, one `centrochange.local` Site, six runtime hooks, #79 CSS, served baseline assets, synthetic Site flags, resources and rollback image/configuration all passed. Prior three-record cleanup remained verified.
- Private checkpoint and full report: `/home/empv26/.local/state/centrochange-single/goal02-install-runs/20261014T083657Z-2730740/`. The checkpoint includes the original Compose/env and rollback image tags. Keep this directory private; it contains configuration.
- Newly built image ID: `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`, tag `centrochange-single:goal02-abc-fixture-83f8f4f`.

## Runtime result

The six application services (`backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler`) use the new image through the persistent candidate Compose override. The database and both Redis service image IDs and container identities stayed unchanged. No migration, reset, reseed, permission change, merge, provider call or production action was performed. A separate read-only verification after the executor confirmed nine healthy containers, the six app images, all six hooks, HTTP ping, persistent Compose mapping and exact served A+B asset hashes.

| Live check | Result |
| --- | --- |
| #79 autocomplete on real Agenda route, mouse/keyboard/empty state, desktop/mobile, role isolation | PASS (`m`, `s`, `a`, `b`; mobile `m`) |
| Package A professional invoice comparison UI, Finance role separation | PASS for tested read-only interaction (`f`, `t`) |
| Package B Agenda, TS simulation view, audit, notifications, responsive UI | PASS for tested read-only routes and controls |
| Seven demo roles plus technical Administrator, login/landing, JavaScript errors | PASS; no page errors or browser writes |
| Security acceptance with booking and operations fixtures | PASS |
| Targeted regression with private per-run log and fixture teardown | PASS |
| Served asset SHA and running application file SHA | PASS against exact approved source |
| Synthetic data and Communication fingerprints after all tests | PASS, unchanged |

The 11-DocType fingerprint was `0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a` before and after. The separate `Communication` fingerprint was `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2` before and after. The fixture left no new persistent rows. Chromium screenshots are private under `/home/empv26/.local/state/centrochange-single/browser-evidence/goal02-20261014T083657Z-2730740/`; no credentials or private report content were committed.

## Owner review path

Private tunnel: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, then open `http://127.0.0.1:8082/login`. Demo credentials remain in the Owner's private access channel; none are stored in GitHub.

1. **Package A:** sign in as Finance, open Finanza and `Confronta fattura professionista`; check the exact document selection, expected/actual amounts, message and allowed action. Review the other open UAT scopes for #73/#74 with their assigned roles.
2. **Package B:** sign in as Direzione, traverse Agenda, Notifiche, Registro modifiche and simulated TS; inspect native patient, practitioner and invoice screens at desktop/mobile widths. Sign in as Commercialista and confirm the permitted read-only presentation.
3. Confirm #79 autocomplete still works in Agenda `+ Prenota` for allowed roles. Then record functional and visual acceptance separately on issue #69/#75.

Owner review of the wider workflows and visual quality is pending. #78/#128 remains excluded; Mission C #109 remains suspended. No final GOAL-02 acceptance or merge is implied.
