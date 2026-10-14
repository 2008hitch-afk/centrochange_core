# GOAL-02 rollback recovery plan — 2026-10-14

Status: **READY_FOR_OWNER_CLEANUP (plan only; no deletion executed)**. The Owner asked for a plan concerning two synthetic records. Dependency inspection found a third test-created `Communication`; the Owner authorized preparation of a **three-record plan**, not execution. A fresh explicit approval of this exact deletion remains required. PR #133 stays DRAFT. No new installation, database deletion, migration, reseed or merge was performed.

## Read-only DEV state

Host `srv2033673`, project `centrochange-dev`: nine running healthy services; all nine image IDs match the pre-attempt report, including backend #79; original `runtime.env` and resolved Compose image mapping; six request/language hooks; accepted #79 CSS. One Site `centrochange.local`, synthetic flags present. The inactive candidate override file remains on disk but is not in the resolved configuration. Current 11-DocType fingerprint is `19814e964a8b19ac8ebe1d4444a18b5ba2bc309e00bbe77425c2e06ddfa6ef10`, versus pre-attempt `0454ed99df64c29a6d1c81e033b560d8fe96cf98826ab3d96ecdf52f4e21944a`.

## Exact proposed deletion set

| DocType | Exact name | Provenance and dependency |
|---|---|---|
| `CC Booking Confirmation` | `nq7fe9a7te` | Created 2026-10-14 09:31:57 local time by the synthetic HTTP fixture, center `CC-HTTP-9277857997 A`; references now-deleted appointment `HLC-APP-2026-00026` and Communication below. |
| `CC Audit Event` | `nq7cpubodl` | Created 2026-10-14 09:31:57 local time; type `BOOKING_CONFIRMATION_SIMULATED`; references exactly confirmation `nq7fe9a7te`. |
| `Communication` | `nq7pmkk53k` | Created 2026-10-14 09:31:57 local time by the simulated `example.invalid` sink; references exactly deleted appointment `HLC-APP-2026-00026`; confirmation links to it. |

The appointment and fixture center no longer exist. Read-only checks found no File, Comment, DocShare or Version attachments to the three rows; no Email Queue, CC Payment Notice or reply references to the Communication. The only Link reference to it is the listed confirmation. Native Link metadata showed no other matching row for these IDs. Excluding the confirmation and audit event **in memory only** from the 11-DocType fingerprint reproduces the checkpoint exactly. The previous fingerprint did not include `Communication`; its provenance follows from exact appointment link, synthetic recipient/sender and matching creation time. This limits the scope of the restoration claim.

## Proposed one-time cleanup, pending Owner approval

Versioned procedure: `infra/goal02_orphan_cleanup.py`. `--inspect` is read-only and has passed on the current DEV. After approval, use the same checked-out commit and run an unchanged-state `--inspect`, then `--apply` **once** with `sudo -n python3 -I`. The script requires root on the named host, synthetic DEV flags, exact names/relationships, missing fixture appointment and center, no other related records in the checked classes, current fingerprint and projected checkpoint fingerprint. Any drift blocks before deletion.

`--apply` first writes all three complete rows to a new private 0600 snapshot under `/home/empv26/.local/state/centrochange-single/goal02-cleanup/`, records its SHA-256 and fsyncs it. It then checks that the rows still match the snapshot, deletes **only** the three exact names within one database transaction, verifies absence and the original 11-DocType fingerprint before commit. On an exception before commit it rolls back. After success, run the read-only `--verify-clean` mode, then repeat the nine-service/asset/hook check. Keep the snapshot and its SHA private; never commit it to Git.

The versioned `--restore <private-snapshot> --snapshot-sha256 <digest>` path is reserved for a recovery decision. It requires all three IDs absent and the checkpoint fingerprint, reinserts only the three saved rows in one transaction, verifies the pre-cleanup fingerprint and commits. Do not invoke it automatically; a failed or uncertain cleanup is a stop for inspection. Both apply and restore are **unexecuted** and their database effects cannot be claimed PASS from offline tests.

## Procedure fixes and verification

- `infra/goal02_targeted_regression.py` no longer overwrites a shared `/tmp` log. On failure it creates a unique 0600 diagnostic in the private run directory; the Docker exec uses the correct Sites working directory and absolute Bench interpreter. The executor reports a bounded private diagnostic path and requires the integrity flag in the regression result.
- The HTTP fixture teardown now discovers confirmations linked to its exact appointments, their simulated Communications, and audit events referencing those records. The pure ownership helper rejects out-of-fixture appointments/centers/recipients and missing linked Communications. Existing permission and business code is unchanged.
- 17 offline Python contract tests passed; Python compile and `git diff --check` passed; the cleanup script's live `--inspect` passed read-only. No destructive or fixture runtime regression was run on the persistent DEV. The application fixture fix is source-only and **not installed**; the previously authorized application commit `90817de` remains unchanged on the server. Because PR #133 now contains an application-source correction, its former executor static gate intentionally blocks a further install until a separately approved candidate/source pin and procedure update are prepared. No new deploy is authorized by this plan.

The next Owner gate is approval of the **three exact rows above** for deletion and of the private snapshot/restore procedure. A future installation remains a distinct authorization after cleanup verification and candidate pinning.
