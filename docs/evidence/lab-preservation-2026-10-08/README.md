# Lab evidence preservation — 2026-10-08

Owner authority: issue #99 comment 6069524416. Documentation/evidence only; no new regression execution or merge.

G2D full report and 39-suite matrix, phase/retest results, seven-module backend review, 55 HTTP hook result references, parity/inventories/static/health and browser summaries retained. Existing failures and later PASS are distinguished. Two reviewed synthetic Agenda screenshots preserved. M97 23 canonical evidence files copied with path/credential-field sanitization; one reviewed synthetic screenshot and local HTTP fixture metadata variant retained. Remaining 204 G2D and 76 M97 screenshots remain in original locations; curated package preserves discriminating examples, not every redundant image. Raw logs, env/config secrets, cookies, passwords and DB exports are excluded.

This package is technical evidence, not a restorable database backup, bit-identical image archive or Owner acceptance. Existing images, containers and volumes remain unchanged; CURRENT G2D/QA images needed by B99 remain referenced/present. Provisioner recipes are already versioned (M97) or retained locally (G2D); reviewed external wrapper/diff preserved. No hidden source binds observed. Image pruning after future container deletion remains a separate retention risk.

Stop gate BLOCKED: four other visible Codex sessions have inaccessible cwd/open-file metadata; non-use of the labs cannot be certified. No stop commands issued. Owner must establish/release competing lab usage before an already-authorized stop can proceed. No new stop authorization is requested.

Restart after a future stop: use the exact existing container IDs in preservation-state.json. Start lab DB/Redis first and wait healthy; start backend/websocket, then frontend/queue workers/scheduler. Never start exited configurator. Use docker start only on validated IDs/labels; do not use up/recreate/build/migrate. RC22 must keep identical IDs/image/start/restart/mount/ports and return 200 on ping/login before and after. Retain all volumes/images. This is a procedure, not executed now.
