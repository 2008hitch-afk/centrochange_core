# UAT-AGENDA-01 — second visual iteration

**TECHNICAL PASS != OWNER VISUAL ACCEPTANCE.**

**READY_FOR_OWNER_VISUAL_UAT: YES. OWNER VISUAL UAT: REQUIRED.** Issue #63 remains OPEN; PR #65 remains DRAFT / UNMERGED. Explicit criterion added to #63: “OWNER VISUAL UAT against client reference required.” No GOAL-03 authorization.

## Scope and deployed identity

Same branch `issue-63/agenda-calendar`, reusing the functional weekly planner, native API and operational detail panel. Deployed commit **82d9c16241c914880ab5fb317f3fbeb16d72e10a**, candidate **goal02-20261006-rc8**, local image ID **sha256:ea32b7eb9a2f53f97fec6b75c3e974eba320f1af970a82514eed792025014c71**. Subsequent evidence-only commits do not alter deployed app code.

Only presentation files `workspace.css`, `workspace.js`, `centrochange.html` and browser checks changed from previous verified iteration. No API/backend, data model, permissions, booking/reschedule/cancel logic, notes, Finance or accounting changes. CSS refinements are scoped to `.agenda-page`; Finance styles are unaffected.

Preflight: clean worktree on the requested branch, healthy DEV runtime, existing synthetic demo. Deployment used exact git archive and the versioned `uat_candidate.py --existing-site-ui` path. No configurator/migrate, volume destruction, source overlay or manual container patch. Six app services share the new image; tracked app parity and served JS/CSS match. Pinned upstream dependencies/Dockerfile are unchanged from the previous official-source/runtime verification.

## Visual changes

| UAT observation | Second iteration |
|---|---|
| Wide sidebar | 104 px desktop rail, icon + readable short labels; operational navigation preserved |
| Large heading/header | 21 px Agenda title, small synthetic-environment banner |
| Heavy form toolbar | Compact Oggi / previous / Italian period / next / professionals / Settimana / + Prenota; center secondary |
| American visible date | Italian period label; native date input remains operable under the label, visually transparent and keyboard accessible |
| Technical synthetic names | Client-side display labels Alfa/Beta, clean patient/service names and Centro A; original canonical IDs and dataset untouched; real names remain unchanged |
| Table-like professional rows | Fixed 116 px column, initials/avatar, vertical label; display-name order only |
| Administrative event cards | Compact time → patient → service/state, lighter border/color cues, no repeated technical prefix |
| Repeated availability text | Free/blocked background areas; native hours retained in DOM for assistive technology rather than repeated primary text |
| Strong blocked pattern | Subtle background/pattern; no dominant Non disponibile text |
| Unused viewport | Calendar takes available viewport height and scrolls internally; header/practitioner column stay sticky |
| Technical practitioner filter | Compact popup, clear checkboxes/all/none and discreet count, readable display labels |
| Detail/responsive | Existing Seduta / Storico / Note panel retained; mobile internal planner scroll and no document overflow |

No drag/drop, resize, month view, configurable colors or professional statistics were added. This is a refinement against the described client-reference characteristics; it is not a pixel-perfect reproduction or a claim that the Owner accepted the result.

## Final runtime verification

- JavaScript syntax/static and Git whitespace: **PASS**.
- [Build](uat-agenda-visual-02/build.json), [image parity](uat-agenda-visual-02/image.json), [served assets / preservation](uat-agenda-visual-02/assets-and-preservation.json): **PASS**.
- [Agenda browser](uat-agenda-visual-02/agenda-browser.json): **12 groups PASS**. A/B/C isolation, direct read/mutation denials, Secretariat private-note boundary, one/multiple/all/none practitioner filters, previous/next/Oggi/date selection, native availability/unavailability, card detail/history/notes, stale-response regression, no JS exceptions, desktop/mobile no document overflow. New visual assertions check rail width, planner height, cleaned labels and Italian visible period.
- [Operational browser](uat-agenda-visual-02/operational-browser.json): **16 groups + actual worker PASS**. Real + Prenota, canonical appointment, move, cancellation, future-close denial, notes, report, native absence rendering, synthetic intake/package/access lifecycle; exact temporary-fixture cleanup PASS.
- Browser fallback: existing Playwright **1.58.2** pinned container; Browser plugin unavailable. Chromium desktop **1536×1024**, mobile **390×844**. Rendered screenshots reviewed: meaningful page, no framework overlay, clean toolbar/calendar, functioning controls.

Commands:

```sh
python3 infra/uat_candidate.py --source-ref 82d9c16 --name goal02-20261006-rc8 --env-file /external/runtime.env --existing-site-ui
python3 infra/image_acceptance.py --source-ref 82d9c16
python3 infra/uat_browser_acceptance.py --agenda-only --output-dir /tmp/cc-visual-final-uat
python3 infra/browser_acceptance.py --operational-only --env-file /external/runtime.env --output-dir /tmp/cc-visual-final-flows
```

No UAT reset/seed. Original manifest IDs unchanged and isolated smoke cleaned up. Previous UAT edits are preserved; this does not restore the historical seed-initial Finance assertions. Raw credentials/logs remain outside Git. Only synthetic DEV data, no provider/production/real fiscal traffic.

## Owner handoff and limits

Runtime remains accessible at **http://localhost:8082/centrochange** through the existing SSH tunnel, server binding **127.0.0.1:8082**. Select **28/09/2026** using the period date picker to inspect historical cards, **12/10/2026** for the future Alfa card, or **Oggi**. Review toolbar, density, practitioner readability, event blocks and free/blocked area treatment against the client reference.

Owner visual acceptance remains pending; automatic checks are functional evidence only. Chromium/two synthetic professionals tested; other engines, large-roster load and exact client-screen fidelity are not qualified. Events retain chronological day cells, not an hour-scaled vertical axis. No new business behavior is inferred.

[Desktop screenshot](uat-agenda-visual-02/desktop.png) · [Mobile screenshot](uat-agenda-visual-02/mobile.png)
