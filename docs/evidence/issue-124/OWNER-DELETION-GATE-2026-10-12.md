# Issue #124 — Owner deletion gate (2026-10-12)

Status: **PARTIAL / awaiting explicit Owner approval of the exact deletion manifest**. No resource in this manifest has been stopped or deleted for issue #124.

## Source and target

- Current GitHub `main`: `2fab181cd61cfc69e341d9fa1849038c6646e87e`.
- PR #107 DRAFT: `d50299f8d9ad32640259ff1c3a1fded47db5c447`.
- PR #112 DRAFT: `6f8a8f5f28ebc39f8e25eecd10086a601fc21419`, stacked on #107. The last application-tree change is `eb3cf092d258448ddc74a5902b7063fb9b95feb0`; the tree under `app/centrochange_core` is unchanged between packaged application revision `e2fd728ecf6acdb0e0ab26379820df6905dd5521` and current #112 HEAD.
- Planned pinned target: Frappe `f20f92d29706510551b4438cc196b0323a7f1a92` and ERPNext `7474d9e786277383de1242ab882f16856d17a9c9` (16.50.0); Healthcare/Marley `dda107b26e3a0fe1dbd65c7257371235de054a04`; Builder `37e958bc4f801d06d0438c21b97b42c45c4eaa51`. Existing local TARGET base image: `sha256:10e701947cccc377dc1d3c2082a03ef69b81d14da8e08fac75f07e78bcf974ce`. Existing C109 application image: `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. The repository's generic `infra/Dockerfile` still pins 16.32.0, so it must not be used as the TARGET build recipe.

## One read-only server inventory

The exact resource list is [`docker-delete-gate-2026-10-12.json`](docker-delete-gate-2026-10-12.json), SHA-256 `2a0e1e51c1ccaeff458b174a3d4711640ab741b07cd1baed3f7443ec4d4d4208`. Each Docker container has a full ID, name, Compose project and state; each volume has its exact name and container references; each network has its exact ID and members. The script `infra/issue124_inventory.py` deliberately does not print environment variables, credentials, site configuration or volume contents.

| Scope | Exact deletion proposal after Owner gate | Preserve |
| --- | --- | --- |
| Containers | 241 named Centro Change containers: 9 running RC22, 27 created, 205 exited; includes old B99, C109 R2–R14 and helpers | No other container exists at inventory time |
| Volumes | 254: 68 named Centro Change demo volumes and 186 anonymous volumes attached exclusively to listed Centro Change containers | 23 unattached/unknown or buildx volumes; ownership not proven, excluded |
| Networks | 28 `centrochange-*` networks; no foreign container member | Docker `bridge`, `host`, `none` |
| State paths | 36 exact `/home/empv26/.local/state/centrochange*` paths in manifest, including private demo data, checkpoint archives and old lab configuration | 3 clean local source repositories in that tree, plus `/home/empv26/src/centrochange_core`, `/tmp/centrochange-c109-r13`, `/tmp/centrochange-issue124` |
| Images | None in this gate; 23 Centro Change tags / 14 unique image IDs retained until replacement verified | All image cache, upstream base images and unknown images |
| Host | No OS, SSH, Nginx, listener 80/443, tmux session, GPG agent or unrelated `/tmp` path in deletion scope | All host services and unclear resources |

All 241 listed containers have Centro Change names or Compose ownership. All 254 listed volumes have Centro Change names or are referenced only by listed Centro Change containers. The 28 listed networks are Centro Change named. The active `centrochange-dev` site self-reports `cc_synthetic_dev=1`, company `Centro Change SYNTHETIC DEV`, and completed synthetic setup. Historical B99/C109 volume provenance and test reports are in the repository; **the contents of stopped databases were not opened**. If a pre-delete check finds a foreign mount, unexpected dataset, changed ownership or new resource, stop and return to Owner rather than widen this list.

The server has 42 GiB free disk, 5.4 GiB available RAM and no swap. Only port `127.0.0.1:8082` is bound by the current Centro Change frontend. No Centro Change systemd unit or crontab entry was found. The host's 80/443 service and SSH are excluded.

## Consequence and rebuild contract

Approval of this manifest permits permanent loss of the listed synthetic demo site databases, Redis state, private files, local checkpoint archives and RC22 access. Downtime starts when the 9 RC22 services stop. GitHub history, PR #107/#112, other host services, 23 unowned or buildx volumes and old images are preserved. No global Docker prune or broad path deletion is authorized.

Immediately before deletion, regenerate the inventory and require the proposed deletion ID/name sets to match this committed manifest and require exclusive ownership again. Then stop/remove only listed containers, listed volumes, listed networks and listed state paths. Build a single TARGET application image from the pinned source, create new secrets outside Git, a new isolated Compose project, one fresh site and DB, seed with versioned `centrochange_core.uat.demo`, then verify restart, browser sections and server-side roles. No old demo database is cloned. If any listed resource has drifted or ownership is unclear, stop before deletion.

`CLEAN_SINGLE_STACK_DEV_READY` is not yet met. The next action requiring Owner input is approval of **this exact manifest**. No merge, main update, production cutover or GOAL-03 follows from this gate.
