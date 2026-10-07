# #75 — Final cross-application UI/UX pass

PARTIAL: targeted readability changes implemented; final browser/runtime walkthrough pending. No new transversal identity before #76 Owner decision. Existing accepted Agenda preserved. Italian dates/states/days/accounts, readable demo account labels and explicit empty search states; no canonical ID or economic rewrite. Plain-language simulation warnings retained. Public first-meeting route/date response generation prevents stale slot selection. Versioned walkthrough: docs/uat/FINAL-OWNER-WALKTHROUGH.md.

Owner visual walkthrough and #76 identity decision required; do not equate technical PASS with Owner acceptance.

Critical-suite harness correction: old operations/master-bridge tests asserted globally empty accounting tables. This is invalid on persistent accepted Owner data. They now assert the document counts are unchanged during their operations (no automatic posting), preserving the original discriminating assertion without destroying data. Professional comparison regression selects the current submitted supplier invoice rather than the Owner-cancelled original. Product accounting/permission logic unchanged.

Visual inspection found Chromium displaying native date inputs in US format even with it-IT locale. Added a visible Italian date label over the retained native date input/picker, preserving canonical ISO values, keyboard focus and test selectors; labels refresh after programmatic presets and API refresh. No schema/booking date logic changed. Actual screenshots and input/date-change browser regressions required.

Pinned upstream Italian login PO strings include untranslated entries. Native login is retained; app-owned Italian CSV translations (explicitly supported by Frappe 16) plus request-local login language provide readable labels, without changing any User/System Settings or authentication operation. Official reference https://docs.frappe.io/framework/user/en/bench/frappe-commands ; pinned `frappe.translate.get_translations_from_apps` loads app CSV then MO; native login context/JS and form IDs unchanged. No upstream file modified.

`infra/remediation_acceptance.py` composes 11 versioned runtime suites sequentially with full rollback after each and unchanged persistent document counts, preventing callback leakage and avoiding browser/revocation races. Dedicated native modules are executed from the immutable runtime image; no source overlay or container file writes.
