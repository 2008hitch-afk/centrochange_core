# MISSION-B-R5-VALIDATION: PASS

Owner authority: https://github.com/2008hitch-afk/centrochange_core/issues/99#issuecomment-6083231999

Bounded continuation started 2026-10-09 around 14:47 UTC, real rollback begun
14:56 UTC and final controlled stop completed 14:58:10 UTC (16:58 Rome), before
the 18:47 rollback and 21:47 hard-stop limits. Prior R5 PSI stops and blocked
manifest remain preserved; a distinct versioned activation/result records this run.

## Exact code and reuse

Final corrected application revision:
`8639b7982255446eacf0147ae952346442849f1b` (product draft #107).
Actual Docker image:
`sha256:342dd48b649aae93fe2e9cc080e44b1ff622b11c900bd084b636af3f2e4624a7`.
Image was already imported: **no build, dependency upgrade or re-import**.
OCI manifest/config/correction-layer hashes and final correction file bytes were
verified against Git; runtime hashes of all eight changed application files
matched that exact revision. Original base archive evidence was reused; no claim
of a newly repeated full base archive scan. Product PR head may contain later
documentation only; tested application bytes remain the revision above.

Reused consistent stopped R5 TARGET clone and assets. No schema changes in these
fixes: the already completed TARGET migration was not repeated. Final live
TARGET inventory exactly matches the migrated R3 TARGET for schema, all 53 cc_
custom fields, canonical CC/native critical permission rows, installed apps,
core patch list and pins. See target-integrity.json.

Effective versions: Frappe 16.50.0 / ERPNext 16.50.0 / Healthcare 16.6.1 /
Builder 1.35.1. Healthcare SHA dda107b26e3a0fe1dbd65c7257371235de054a04;
Builder SHA 37e958bc4f801d06d0438c21b97b42c45c4eaa51. Official base omits Frappe/
ERPNext .git: immutable base image and previously verified official release
pins f20f92d29706510551b4438cc196b0323a7f1a92 and
7474d9e786277383de1242ab882f16856d17a9c9 are retained; runtime versions verified.
MariaDB/Redis image digests unchanged from R5/R4 baseline.

## Actual suite results on final image

| Finance suite | Result |
|---|---|
| security | PASS |
| finance | PASS |
| receivables | PASS |
| banking | PASS |
| incoming | PASS |
| professional | PASS |
| reporting | PASS |
| sdi | PASS |
| ts | PASS |

| Browser suite | Result |
|---|---|
| uat | PASS |
| professional | PASS |
| patient | PASS |
| expectations | PASS |
| ts_detail | PASS |
| confirmation | PASS |
| search | PASS |
| accounting | PASS |
| permissions | PASS |
| walkthrough | PASS |
| ui_v1 | PASS |
| print | PASS |
| states | PASS |
| agenda_geometry | PASS |

| Additional gate | Result |
|---|---|
| Native adapter/XML actual-actor acceptance | PASS — 11 checks |
| Backend designated seven-module suite | PASS — 240 checks |
| Real HTTP before_request regression | PASS — 55 checks |
| Effective six app before_request hooks | PASS — all 6 invoked |
| Extended HTTP security/booking/operations | PASS — 38 checks |
| Actual code hash and effective dependency versions | PASS |
| TARGET schema/custom fields/critical permissions/apps/pins | PASS |
| Native CURRENT restore | PASS |
| Exact CURRENT schema/metadata/business/files/apps/pins reconciliation | PASS |
| Restored CURRENT demo validation | PASS |
| Restored CURRENT operational regression | PASS — 189 checks |
| Restored CURRENT HTTP | PASS — 200 |
| RC22 and all 110 protected containers | PASS — unchanged |

The 240 backend checks are the existing designated suite, not a claim that every
historical test module was rerun. No R3/R4 PASS substitutes for any listed R5
regression. Migration itself is explicitly reused, with live integrity verified.

## Security and XML evidence

Actual Finance retains no generic Payment Entry create or fiscal-template select
grant. Scoped factories authorize the real actor and canonical invoice center/
company/read, reject A/B/C/accountant, revoked center, forged in-memory invoice,
invalid/nonfinite/over-balance amounts; native posting, idempotence and before/
after audit actor/owner match. XML submit works under Finance; direct generic
parent write, public XML and premature delete are rejected.

Finance receivables proves native draft/submit/receipt/credit/correction and
negative actor/center/REST access. SdI proves actual Secretariat cancellation,
amendment/correction and original private payload retention/download, simulated
worker processing/retries and unauthorized API/query/export/intake negatives.
No role grants, policy changes, user impersonation in application services,
upstream patches or provider traffic. Administrator appears only in the already
versioned fixture setup/recovery and read-only inventory harness.

## Supplemental harness failures retained transparently

The first optional extended security run failed before tests because its fixed
Marco route collides with the preserved demo. A proposed temporary unique alias
was correctly rejected by the unchanged approved-alias validator. Neither result
was classified as product PASS or as an application defect.

The final wrapper uses **Francesca**, an existing approved alias verified absent
before fixture setup. Only the test-process fixture's route constant and matching
client payload/name change; application files, approved aliases, permissions and
all assertions remain intact. All 38 checks pass and fixture recovery removes
only its owned records. Marco is retained. Other harness adaptations remain the
existing explicit R5 backend/site/port mapping, pinned QA reuse, native login
submit-button selector and current exact idempotent confirmation response shape.
See orchestration/run_suite.py and code-checks-initial-attempts.json. No tests were
weakened to force PASS.

## Real rollback

Stopped final TARGET, retained its volumes, and restored the original complete
CURRENT checkpoint through native bench restore into separate R5 rollback
volumes/network. Restored public/private files, original configs/apps and the
integrity-checked private UAT supplement. No source archive or checkpoint changed.

Full schema, metadata, canonical business rows, files, installed apps and pins
match the original CURRENT inventory exactly. Restored CURRENT Frappe16.31.0 /
ERPNext16.32.0 / Healthcare16.5.2 / Builder1.33.0 uses immutable CURRENT image
sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80.
Demo semantic validation PASS; 189 operational checks PASS; HTTP200. R5 TARGET and
restored CURRENT now stopped reversibly; images, volumes, archives and checkpoints
preserved. No prune, deletion, build or mutation of other labs.

## Resource and isolation results

This authorized continuation: no guardrail trip, host/local OOM delta **0**;
memory full PSI peak **0.00%**, some **0.18%**; I/O full peak **21.70%** during
serial tests/restore. All existing PSI/MemAvailable/OOM triggers stayed active and
unchanged. No heavy overlap. Runtime+QA cap max 2,684,354,560 bytes (2.5 GiB);
sampled aggregate usage peak 1,631,252,480 bytes (~1.52 GiB). Minimum host available
RAM 4,683,841,536 bytes (~4.36 GiB). No new builder.

Final available RAM 5,782,061,056 bytes (~5.39 GiB); disk 13,831,942,144 bytes
(~12.88 GiB), ~0.47 GiB incremental from preflight, within 2 GiB budget and 4 GiB
safety reserve. No R5 container running or OOMKilled. Retained prior stops are not
removed or relabeled: this continuation avoided the prior heavy image import.

All **110 non-R5 pre-existing containers** retain image, state/start timestamp,
restart count, mounts and networks. This includes RC22 and R1–R4. Protected event
monitor reports no changes; RC22 ping **HTTP200** before/during/after. Original
checkout remains clean. Existing UAT resources and databases were not touched.

## Visual evidence and retained artifacts

Screenshots reviewed: login desktop and Agenda desktop with nine cards under the
correct days; mobile evidence also retained. Geometry measurements report zero
header/body drift, no wrong-day cards and no document overflow across tested
resizes/scroll. See screenshots/ and browser/agenda-geometry-measurements.json.
Per-suite structured outputs and reproducible host wrappers are adjacent.
Full private logs and original runtime evidence remain outside Git at
`/home/empv26/.local/state/centrochange-b99-r5-final-20261009`.
No credentials, dumps, private fixture config or raw response bodies published.

## Outcome boundary

Technical final validation PASS; #107 and #108 remain DRAFT, no merge. This does
not authorize UAT upgrade, production, GOAL-03 or Owner acceptance of GOAL-02.
Next step is HITCH/Owner review of the scoped fixes and this evidence before any
separately authorized integration/promotion gate.
