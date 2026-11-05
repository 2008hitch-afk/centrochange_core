# Mission B R2 — BLOCKED

Owner authority: https://github.com/2008hitch-afk/centrochange_core/issues/99#issuecomment-6076948191

Source: `e85fce588de6012a47da302710b9f9c615211279`. R2 activation commit: `5eef9cdc32fce1317721f2cff8d3384e6e3bfb29`. Operational branch: `issue-99/isolated-upgrade-r2`. No main merge or product change.

## Actual results

| Phase | Result |
|---|---|
| CURRENT fresh install and migrate | PASS |
| CURRENT synthetic demo validation, worker simulations | PASS |
| CURRENT backend regression | PASS — 7 modules, 240 checks; canonical rows and persistent counts unchanged |
| CURRENT six before_request guards | PASS — effective pinned WSGI hook invocation |
| CURRENT real HTTP security checks | PASS — 55 positive/negative cases, isolated principal disable restored |
| External complete CURRENT checkpoint | PASS — native unfiltered DB backup, public/private files, site configuration and common configuration; hashes, gzip/tar readability, encrypted archive decrypt equality |
| Complete CURRENT/QA image archive | PASS — existing complete archive SHA verified, prior image load verification reused |
| TARGET build | STOPPED — memory PSI guardrail during pinned base-image extraction |
| TARGET migrate / schema / functional and browser regression | NOT EXECUTED |
| Real CURRENT rollback | NOT EXECUTED — TARGET never migrated the CURRENT database |

CURRENT observed: Frappe 16.31.0, ERPNext 16.32.0, Builder `41987c064da4650e6901b5da82b7c76add452ebf`, Healthcare `934d6c162868139dfbe80c23d6102adb7ec25adb`; all five apps installed. Official Frappe/ERPNext image omits Git metadata; image digest and package versions recorded, not invented Git HEADs.

TARGET attempted: Frappe/ERPNext 16.50.0 base `sha256:833bceb57233908cbc949d7aa533942b18e54b329d846b933b66937c62b7e4ae`. Builder `37e958bc4f801d06d0438c21b97b42c45c4eaa51`, Healthcare `dda107b26e3a0fe1dbd65c7257371235de054a04` were intended pins only: their build stages were not reached. No completed TARGET application image, no compatibility conclusion.

## Safety stop

The actual PSI stop was at 2026-10-09T08:21:27Z. Memory full avg10 reached the >=1% threshold for three consecutive samples. At the stop: full 2.35%, some 2.42%; no OOM and host MemAvailable about 5.48 GiB. BuildKit maximum sampled memory.peak 1,746,731,008 bytes (1.63 GiB), with enforced parent cgroup memory.max 2,147,483,648 and swap.max 0. Overall sampled maxima: memory full 4.01%, some 4.20%, I/O full 7.02%, some 7.72%. This proves sustained memory pressure correlated with image download/extraction, not its ultimate cause. No threshold was disabled or raised.

An earlier monitor-only false positive was corrected: BuildKit's `init` child has unlimited local memory.max, while its enclosing Docker scope enforces the 2 GiB cap. The supervisor now checks the verified container scope, covering descendants. This correction did not change resource limits. Evidence of both stops is retained.

Build and lab/browser never overlapped; no heavy image archive ran concurrently. CURRENT app services were stopped before checkpoint; queues were empty. All R2 lab containers and the dedicated builder are stopped. New R2 volumes and checkpoint retained; R1 resources untouched.

## Orchestration adaptations

- Distinct r2 service keys and new volumes, preserving R1 partial state.
- Demo requires cc_uat_demo and explicit synthetic Administrator; used existing versioned fixture with no grant change.
- One-off Python logging uses FRAPPE_STREAM_LOGGING, as existing G2D harness.
- CURRENT inventory records absent upstream Git metadata instead of falsely claiming HEADs.
- Frontend-only dedicated bridge exposes localhost:8099; app/DB/Redis remain on internal network.
- Watchdog stops only R2 if monitor heartbeat is lost.

## Final protected state and resources

All 14 protected container identities, images, starts, running states and restart counts match preflight (RC22 plus stopped R1). RC22 ping on localhost:8082 is HTTP 200. Original checkout is clean. No changes to UAT databases, code, settings, production, removed laboratories or Docker global configuration.

Disk free: initial 44,730,351,616 bytes; final snapshot 39,899,607,040 bytes (37.16 GiB); host-level consumption about 4.50 GiB, not an exclusive per-layer allocation. Final MemAvailable about 5.6 GiB, swap absent. No cleanup performed. Offline CURRENT/QA archive and all checkpoints retained privately; secrets, dumps, configurations and raw logs are not committed.

## Handoff

Manifest is now OWNER_AUTHORIZED_R2_STOPPED_BLOCKED with execution_allowed_now=false; historical activation retained. Do not restart R2 automatically. Next decision requires a targeted resource/PSI remediation proposal and explicit authorization for another attempt, preserving existing thresholds. Build, TARGET regressions and real rollback remain mandatory and unproven. Technical PASS or UAT upgrade is not asserted.
