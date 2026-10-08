# Agenda grid alignment — Owner UAT corrective checkpoint, 2026-10-08

**TECHNICAL PASS / READY_FOR_OWNER_RETEST.** Issue #75 OPEN; PR #94 draft/unmerged, stacked on #93. Owner visual retest remains required. No Owner acceptance or GOAL-03 authorization.

## Runtime and scope

Branch `issue-75/final-client-ux-review`. Product fix `f06acca4f6c2ac757dbd3e187709f94b18554b65`; geometry-test correction `ef28441` updates canonical date lookup when switching weeks. Candidate `goal02-20261008-rc22`, exact git archive of fix commit, local image ID `sha256:4ce7cbb0bcfbfb9062d4c086e5f0fb8ff51e5025647df4265b4d5630efd97b8c`. Application bytes match all 239 tracked files; manifest `e113cdf211b2ffdb73e8391f514cb1a1c1b853f954e205d2300163baf3595164`. No source overlays/manual container patches. Frappe 16.31.0, ERPNext 16.32.0, Marley 16.5.2, Builder 1.33.0, Tabler Core 1.6.1 unchanged.

Only product change: `public/css/workspace.css`. Added versioned Playwright geometry test and its runner/Dockerfile wiring. No API, JavaScript product, backend, data model, permissions, accounting or lifecycle change. Existing-site versioned UI deployment; no migration/reset/seed. #92/#93 heads unchanged.

## Verified cause and shared geometry

Pinned Tabler stylesheet loads after workspace CSS. Its `.calendar-body,.calendar-header { display:flex; flex-wrap:wrap; justify-content:start; padding:var(--tblr-calendar-padding-y) 0 }` overrides the equally specific workspace header grid declaration; row remains grid. Before fix, actual computed header `flex`, row `grid`, maximum coordinate drift **817.03125 CSS px**. Prior broad conformance checks did not measure day/header coordinates; Owner observation supersedes their Agenda geometry coverage.

The existing calendar shell now owns one `--cc-calendar-columns` template: `var(--cc-calendar-professional-track) repeat(7,minmax(var(--cc-calendar-day-min),1fr))`. Both direct-child header and rows use this exact template through one scoped selector, whose specificity prevents the upstream class collision. Their minimum width derives from the same variables. Desktop professional track remains 116px, narrow track 100px, day minimum 136px; one breakpoint changes only the professional variable. Duplicated old track declarations removed. Native calendar padding removed within this scoped component, with no compensating offsets.

Official references: [Tabler page layouts](https://docs.tabler.io/ui/layout/page-layouts), [CSS grid-template-columns](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/grid-template-columns). Verified cause comes from pinned local Tabler source and runtime computed styles, rather than an inferred documentation guarantee.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| Header/body tracks | Identical professional + seven days | PASS, identical computed track strings |
| Corresponding cell coordinates | Coincident | PASS, maximum drift **0 px** in all samples |
| Seven equal days | Equal within fractional rendering | PASS, maximum spread 0.015625px |
| Desktop/resize/tablet/mobile | No drift or document overflow | PASS at 1536, 1280, 1024, 768, 390px; return to desktop |
| Internal horizontal scroll | Header/body scroll together | PASS, all narrow viewports, sticky professional column retained |
| Session day | Canonical appointment date matches cell/header | PASS, eight existing sessions in 28 Sep–4 Oct; subsequent 5–11 Oct sample also checked |
| Detail panel resize / practitioner filter | Same tracks retained | PASS, one/two rows and detail panel |
| Existing Owner dataset | Unchanged | PASS, before/after canonical fingerprint identical |

Tolerance 0.75 CSS px; actual maximum drift zero. Read-only browser verifies session dates against authorized live agenda API for each sampled week. An initial test-only failure used the preceding week's date map for the next week; corrected in test only, then rerun PASS. No application fix was needed for that test failure.

## Tests and evidence

- `node --check infra/browser/agenda_geometry.cjs`, `git diff --check`: PASS.
- `infra/uat_browser_acceptance.py --script agenda_geometry`: PASS; desktop/resize/scroll/mobile/week navigation/filters/session detail/booking modal. No booking submitted.
- `infra/uat_browser_acceptance.py --script uat --agenda-only`: PASS, 12 checks; A/B/C direct API segregation, secretariat private-note denial, week/Today/date picker, availability, filters, mobile, stale-response protection.
- Versioned `remediation_acceptance` runner restricted to `operations.integration_acceptance`: PASS, **189** backend checks including booking/reschedule/cancel, accounting integration and server-side security; full rollback with persistent counts and canonical-row hashes unchanged.
- `infra/image_acceptance.py --source-ref HEAD`: PASS, 239 files / six application services / no source overlays.
- `infra/uat_runtime_health.py`: PASS, nine services, HTTP/assets, websocket upgrade, two workers, fresh short/long jobs, scheduler enabled.
- Owner dataset read-only fingerprint before/after: identical `6d60ef5cc5a73550e935736465269c64fea283bdbe5e61cc1e966db9f4bf2d58`. Existing five isolated earlier workflow audit rows excluded consistently from Owner fingerprint; retained, not deleted. New backend fixtures fully rolled back.

Normalized JSON: [before FAIL](agenda-grid/before.json), [after PASS](agenda-grid/after.json), [Agenda regression](agenda-grid/agenda-regression.json), [backend regression](agenda-grid/operations-regression.json), [image parity](agenda-grid/parity.json), [health](agenda-grid/health.json), [dataset before](agenda-grid/dataset-before.json), [dataset after](agenda-grid/dataset-after.json).

Screenshots inspected: [desktop with sessions](agenda-grid/geometry-desktop.png), [narrow viewport with session](agenda-grid/geometry-mobile.png), [Owner-reported week](agenda-grid/geometry-owner-week.png). Desktop example: Beta patient at Monday 28 Sep 10:00 beneath Monday header; professional row Alfa. Patient name and professional name represent different identities.

## Owner retest

Open **http://localhost:8082/centrochange** through existing SSH tunnel. Verify header alignment in 5–11 October, then 28 September–4 October with visible sessions; resize and scroll calendar horizontally. Technical PASS does not replace Owner visual acceptance. Dataset retained, runtime running. Only limitation: final Owner retest pending. No merge.
