# #75 — Final cross-application UI/UX pass

## Superseding checkpoint — 2026-10-08

**TECHNICAL PASS / READY_FOR_OWNER_UAT. OWNER VISUAL ACCEPTANCE PENDING.** True twelve-dimension surface conformance matrix, desktop/mobile/keyboard/search/states/debranding/print; Owner visual acceptance remains required.

Candidate `goal02-20261008-rc21`, source `c51a9e7a1f887b87c0b06872a8d3e94f2e7249f5`; PRs #92 → #93 → #94 are draft/unmerged and all issues remain OPEN. No permission/business/schema delta or dataset reset.

See [complete conformity and runtime evidence](../ui-design-system-v1/CONFORMANCE.md). Earlier checkpoints below are historical; identity-pending claims are superseded by Owner-approved Design System v1, not by a new branding inference. No GOAL-03.


## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

Final main-surface desktop/mobile walkthrough, Italian visible dates and states, readable source labels, native login/print/debranding and public stale-route protection tested. Final candidate and screenshot evidence in unified report; no new identity applied.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

PARTIAL: targeted readability changes implemented; final browser/runtime walkthrough pending. No new transversal identity before #76 Owner decision. Existing accepted Agenda preserved. Italian dates/states/days/accounts, readable demo account labels and explicit empty search states; no canonical ID or economic rewrite. Plain-language simulation warnings retained. Public first-meeting route/date response generation prevents stale slot selection. Versioned walkthrough: docs/uat/FINAL-OWNER-WALKTHROUGH.md.

Owner visual walkthrough and #76 identity decision required; do not equate technical PASS with Owner acceptance.

Critical-suite harness correction: old operations/master-bridge tests asserted globally empty accounting tables. This is invalid on persistent accepted Owner data. They now assert the document counts are unchanged during their operations (no automatic posting), preserving the original discriminating assertion without destroying data. Professional comparison regression selects the current submitted supplier invoice rather than the Owner-cancelled original. Product accounting/permission logic unchanged.

Visual inspection found Chromium displaying native date inputs in US format even with it-IT locale. Added a visible Italian date label over the retained native date input/picker, preserving canonical ISO values, keyboard focus and test selectors; labels refresh after programmatic presets and API refresh. No schema/booking date logic changed. Actual screenshots and input/date-change browser regressions required.

Pinned upstream Italian login PO strings include untranslated entries. Native login is retained; app-owned Italian CSV translations (explicitly supported by Frappe 16) plus request-local login language provide readable labels, without changing any User/System Settings or authentication operation. Official reference https://docs.frappe.io/framework/user/en/bench/frappe-commands ; pinned `frappe.translate.get_translations_from_apps` loads app CSV then MO; native login context/JS and form IDs unchanged. No upstream file modified.

`infra/remediation_acceptance.py` composes 11 versioned runtime suites sequentially with full rollback after each and unchanged persistent document counts, preventing callback leakage and avoiding browser/revocation races. Dedicated native modules are executed from the immutable runtime image; no source overlay or container file writes.

Final Finance screenshot review also found technical fixture prefixes and ISO dates in fiscal source labels. Primary source/subject/service labels are now cleaned and Italian-formatted while document IDs remain canonical. Numeric financial cells use Italian EUR formatting. Remaining standard Expense account labels were enumerated read-only from the pinned native chart and explicitly translated; customized unknown accounts are still not guessed. No ledger/account/data rewrite.

Browser orchestration failure was verified against the native User.simultaneous_sessions=2 setting: overlapping suites logged into the same demo principal and evicted an older test session. Professional/expectation reruns execute serially; versioned browser runner now takes a host lock. No session-limit/user/role settings changed. This is an orchestration fix, not a weakened product assertion.
