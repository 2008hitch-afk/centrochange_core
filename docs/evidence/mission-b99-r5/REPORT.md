# MISSION-B-R5: BLOCKED

## Authority and scope

Owner issue #99 comment 6080880107; R4 evidence PR #106. Execution window
2026-10-09: rollback by 16:47 UTC, hard stop 19:47 UTC. Stopped at 12:59 UTC,
well before either deadline. No main merge, UAT deployment, provider traffic or
production work. Original operational checkout remains unchanged and clean.

Product branch: `issue-99/erpnext1650-compatibility-r5` (final docs/test/code
commit 625292c). Runtime-tested app revision: f80cf534fd071d283cb2c8efc6fe3f1fbd0cb920.
Final packaged revision: 8639b7982255 (see full immutable image proof); this
revision was **not started or runtime accepted**. Evidence branch:
`issue-99/isolated-upgrade-r5`.

## Work actually executed

Reused R4's stopped, already migrated TARGET through read-only source mounts into
exclusive R5 db/sites/assets volumes. Redis, credentials context, project and
networks remained isolated from RC22. Compose caps 2 GiB plus QA 512 MiB; build
helper 2 GiB, CPU 1, serialized. No dependency build or schema migration repeated.
Eight versioned application files were packaged as COPY-only OCI layers over the
verified TARGET; no running container code patch or source bind mount.

Docker initially failed tag lookup despite successful OCI load; immutable manifest
lookup worked. Concurrent initial volume copy-up caused a symlink collision;
R5 configuration now uses volume nocopy. Only the new R5 copy-up assets directory
was renamed/preserved. Completed database copy was reused; R4 was not changed.
Stopped copy helpers' read-only source and exclusive anonymous volumes were
explicitly verified by the isolation wrapper. Early harness-only failures were
not counted as product regressions or PASS.

## Versions

Frappe 16.50.0 f20f92d29706510551b4438cc196b0323a7f1a92;
ERPNext 16.50.0 7474d9e786277383de1242ab882f16856d17a9c9;
Healthcare 16.6.1 dda107b26e3a0fe1dbd65c7257371235de054a04;
Builder 1.35.1 37e958bc4f801d06d0438c21b97b42c45c4eaa51.
Base TARGET image sha256:10e701947cccc377dc1d3c2082a03ef69b81d14da8e08fac75f07e78bcf974ce.
MariaDB 11.8.8 sha256:24e76fcec8c003a0362d0dd53f4806e7e79458d7fdeaf47437760e19496f5a9c;
Redis 8.6.5 alpine sha256:cd218f4b106a332c5c992e38a9480bfb9d7e9f8f7b0ec9a0023bfa36d9a408f9.
Dependency pins were reused, not upgraded again.

## Actual results, without substituting historical PASS

| Suite | R5 observed result |
|---|---|
| Scoped native adapter, f80cf53 | PASS, 10 discriminating checks |
| Finance security | PASS |
| Finance bridge | PASS |
| Receivables | FAIL at native Italy XML submit |
| Banking/reconciliation | PASS |
| Incoming invoices/payment | PASS |
| Professional economics | PASS |
| Reporting | PASS |
| SdI simulated | FAIL at native XML cancellation |
| TS simulated | PASS |
| Expanded XML adapter acceptance, final image | NOT EXECUTED |
| Browser uat/professional/patient/expectations/ts_detail/confirmation/search | NOT EXECUTED |
| Browser accounting/permissions/walkthrough/ui_v1/print/states/agenda_geometry | NOT EXECUTED |
| Backend 240 | NOT EXECUTED on R5 final image; prior evidence retained |
| HTTP 55 | NOT EXECUTED on R5 final image; prior evidence retained |
| Hooks 6 | NOT EXECUTED on R5 final image; prior evidence retained |
| Python syntax / JS syntax / git diff whitespace | PASS |
| TARGET migration/schema integrity | Historical R3/R4 PASS reused; no new migration |
| R5 real CURRENT rollback | NOT EXECUTED |

7/9 Finance passed on the first app image. No final 9/9 or 14/14 claim.
The initial adapter test proves actual actor, no native create/select grants,
negative role/center tests, canonical invoice reload, native partial posting,
idempotency and before/after audit. Final XML correction remains unvalidated.

## Verified residual defect fixes

The first two fixes (configured native tax projection and scoped unsaved payment
factory) enabled seven Finance suites. Additional submit failure was traced to
Frappe File.validate_attachment_references, which demands generic parent write
when the native Italy submit hook creates XML. SdI cancellation separately failed
in native File delete permission under the actual Secretariat actor.

The draft extends the existing FinancialFileMixin only inside the already guarded
accounting service: actual Finance write, canonical center/company/read, synthetic
profile, private local XML; deletion only for native XML of a cancelled invoice.
No role grants, global permission flags or Administrator impersonation were added.
Retained CC Fiscal Transaction payloads are excluded. Expanded tests were committed
but could not execute. Login native submit markup/shared footer assets were also
corrected but browser acceptance remains outstanding.

Official pinned sources:
- https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/core/doctype/file/file.py
- https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/regional/italy/utils.py
- https://github.com/frappe/erpnext/blob/7474d9e786277383de1242ab882f16856d17a9c9/erpnext/accounts/doctype/payment_entry/payment_entry.py

## Safety stop and resource evidence

Two unchanged PSI guard stops are retained. Initial packaging segment stopped
before import/clone; after sustained recovery a separately versioned validation
segment reused the completed archive. The validation segment stopped again after
loading the final XML-fix image and before restarting R5. It was not reset/restarted.
At the second stop memory full PSI had exceeded 1% for three samples; peak 3.58%
in that event. Aggregate R5 peak 10.85% full / 12% some, including the first stop.
High I/O PSI included throttled copy/archive operations; max full 86.72%.
The actual causal writer of the host memory pressure is NOT conclusively verified.
No local or host OOM delta. Minimum host available RAM 4,933,087,232 bytes.
Sampled own usage peak 2,048,970,752 bytes, within the 2 GiB build cap.
Final available RAM 5,857,435,648 bytes (~5.46 GiB);
final disk available 14,338,179,072 bytes (~13.35 GiB).

All R5 containers stopped. 112 pre-existing containers have unchanged image,
start/running/paused state, restart count, mounts and networks; RC22 ping HTTP 200.
CURRENT checkpoint, supplementary private fixture configuration and CURRENT/QA/
base TARGET images are retained. R5 TARGET volumes with synthetic test changes
remain stopped and preserved. No destructive cleanup or protected-runtime mutation.

The safety stop prevented R5 real rollback: prior R3/R4 rollback PASS is not
represented as R5 rollback. Checkpoint remains usable; no UAT data was at risk.
No screenshots exist for R5 because browser tests were not reached.

## Remaining gate

A safe explicitly authorized restart must address repeated host PSI during Docker
image import without weakening existing thresholds, then run the final-image XML
positive/negative tests, all Finance/browser/security suites and real CURRENT
restore/reconciliation. This draft is not READY for merge, UAT upgrade or promotion.


## Subsequent authorized final validation

The historical BLOCKED result above is retained. Owner comment 6083231999
authorized a distinct continuation: [Final validation report](final-validation/REPORT.md)
records PASS on the actual final image, including real CURRENT rollback.
