# Centro Change — Client Demo Readiness Report, 19 October 2026

**Esito: `CLIENT_DEMO_READY: NO`; Owner screen-share walkthrough possible with disclosed visual limits.** Functional MVP is documented as 46/46 technical PASS, but visual acceptance is open. This report does not change the installed DEV or claim customer approval.

## Baseline and publication

- Branch `audit/mvp-functional-completion`, original local HEAD `b0e14e0be22ee5c431ad4abb74fb931634335276`; PR #141 remains DRAFT and depends on #140 DRAFT. The original HEAD and the [functional completion report](../mvp-functional-audit/CENTROCHANGE-MVP-DEV-FIRST-COMPLETION-2026-10-19.md) were published without force push or merge.
- Installed DEV source `a03386c41a78692fd4b6d370ec56b1d21d613841`; six application services use `centrochange-single:mvp-devfirst-a03386c-v3`, image `sha256:e2df539cc99fee6965102f539c0969dbec98d2ad59bf7c0d9631d4e03774acdb`. Nine services running, HTTP ping 200. No installation, restart, migration or data mutation was performed for this report.
- The [completion matrix](../mvp-functional-audit/capability-matrix-completion.csv) has six prior PARTIAL entries now evidenced PASS; 40 older PASS retain their original evidence. The 46 functions were not rerun as a new campaign.

## Current Chromium evidence

The existing read-only Owner UAT sweep was run against the actually served DEV with a new Chromium context and private demo accounts. Eight role/viewport combinations covered Direzione desktop/mobile, Segreteria mobile, Professionista Alfa mobile, Beta desktop, C mobile, Finance desktop and Commercialista desktop. **87/87 route renders passed the existing structural checks**; zero unexpected mutations, JavaScript errors, missing CSS/JS assets, blank main regions, oversized icons, clipped status badges or horizontal page overflow. JSON and full-page screenshots are retained privately at `~/.local/state/centrochange-single/browser-evidence/client-demo-20261019/`. This is navigation/rendering evidence, not a new functional write test.

Representative synthetic screenshots: [Agenda desktop](agenda-desktop-before.png), [Agenda mobile](agenda-mobile-before.png), [Fatture pazienti](fatture-native-before.png), [Banca](banca-desktop.png), [Ricerca pazienti mobile](ricerca-professionista-mobile.png). Screenshots were inspected visually in addition to automated DOM checks.

### Observed limits

1. **Sidebar active state, confirmed:** Agenda highlights both «Inizio» and «Agenda». The same duplicate destination exists for finance-only home. Cause: both links share one URL and the renderer marks every matching link active. A source-only correction now gives the destination a single active state and uses its title; the new sweep assertion fails if the active count differs from one. `node --check` and `git diff --check` pass. **This correction is not installed on DEV and has no live PASS yet.**
2. **Native invoice list, confirmed:** the recent canceled POS fixture rows show `CC-MVP-POS-*` as prominent names; search controls expose `ID` and comparison symbols, and a date header is truncated at 1440 px. This does not break accounting or access but is unsuitable as the opening customer finance example. Show human-readable Beta/Gamma/Theta examples and keep canceled test history for audit. A presentation-only native customization and fresh visual verification are still needed before declaring polished demo readiness; do not rename or delete accounting history merely to improve a screenshot.
3. **Mobile Agenda, review item:** the weekly grid is horizontally scrollable at 390 px and initially displays only the first two day columns. No document-level overflow was measured, but the client should confirm that this interaction is understandable.
4. **Italian/localization, PARTIAL visual review:** current representative custom screens use Italian dates, labels and 24-hour times; existing live CSV tests covered six exports. A full customer-facing copy review across every native form, error, empty state and print/export view was not completed in this pass. Technical IDs remain visible in the native invoice list. Issue #134 and #75 acceptance remain open.

## Demo workflow coverage

The [runbook](../../uat/CLIENT-DEMO-RUNBOOK-2026-10-19.md) specifies 12 linked scenarios and their roles. Current Chromium read-only navigation reached the relevant top-level screens; earlier capability evidence documents underlying functional operations, including POS partial payment, private attachment persistence and server-side role denial. **12/12 scenarios have a documented route and functional evidence path; 0/12 were re-executed end-to-end as fresh write workflows in this demo-readiness pass.** This distinction prevents route PASS from being mistaken for current-session business-process PASS. A guided Owner screen-share can use the existing synthetic records and prior evidence without changing Owner data.

## Decision and next gate

The DEV is accessible now to the Owner through the existing private SSH tunnel, but this report does **not** declare a polished direct client demo ready. A single cumulative UI candidate is required for the one-active-link correction and any agreed native-list presentation refinement. Its installation needs one separate operational authorization, followed by targeted Chromium visual checks; no new full 46-capability campaign is indicated. Direct client login additionally needs a separate security/access decision. PR #141 remains DRAFT; no merge, production, GOAL-03 or customer acceptance is implied.
