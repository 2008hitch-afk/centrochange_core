# Design System v1 — implementation, 8 October 2026

Authority: `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md`, Owner authorization under #76. PR #92 supplies shared UI; #93 and #94 remain stacked, draft, unmerged. Technical acceptance is distinct from Owner UAT.

## Shared implementation

Local Tabler Core **1.6.1**, Icons **3.35.0**. `public/vendor/MANIFEST.json` records exact npm versions, integrity and 24 file SHA256 values. No runtime CDN, downloaded fonts or demo/plugin stack. Core package declares MIT but excludes LICENSE: official repository license provenance is explicitly recorded; Icons LICENSE comes from the exact archive.

`cc_ui_assets.html`, `cc_ui_sidebar.html`, `cc_web_base.html`, `ui_v1.css`, `ui_v1.js`: shared page/navbar/page-wrapper/page-body shell; compact headers; teal primary token `#12665f`; system font; Tabler buttons, controls, tables, cards, data-grid, badges, alerts and loading presentation. Sidebar mobile collapse, skip link, visible focus, reduced motion and internal table/planner scroll. Existing authorized navigation projections remain authoritative.

Native `<dialog>` is retained for focus confinement/Escape, using Tabler modal-content/header/body/footer styling and focus return. This is an explicit supported adaptation, not a custom replacement of the lifecycle. Calendar geometry stays custom: continuous professional rows/weekly columns and event blocks; toolbar and panels use shared primitives. No drag/drop, resize or month view.

`search_select.js` is the equivalent single-input ARIA combobox permitted by v1. Focus/type/dropdown/click or keyboard Enter; Arrow keys/Escape; required selection; bounded remote Patient projection through the **existing** authorized endpoint; local Professional options from the **existing** authorized context. Canonical hidden select remains the submitted field; free text is never a canonical selection. Generation invalidation, disconnected-element checks, pending/error/retry and immediate stale-option clearing. No new API/grant/visibility.

Presentation labels use existing authorized names, synthetic aliases and Italian status/date/time labels. Audit original event codes/snapshots stay secondary and unmodified. Accounting values, dates, native status and references stay canonical. Technical source/document numbers stay available where traceability is relevant. Stored service names, addresses, reason text and native amount-in-words remain original data, not silently rewritten.

Supported website context/CSS hooks debrand native authentication/errors. Existing native authentication is retained. A supported `get_print_format_template` hook sets the print translator to explicit Italian after native print permission validation, returning `None` to retain the native format, fields and totals. App `translations/it.csv` fills translated labels. The selected native image invoice format and Letter Head also contain hardcoded English labels: supported website context post-processing translates only `.invoice-title` and `.title .info-text` label nodes with an exact allowlist. Data nodes and document language/data remain unchanged. BeautifulSoup is already provided by pinned Frappe; no new dependency. Operational session print keeps its original authorization/projection and receives local print styles only.

## Upstream/source verification

- [Tabler layouts](https://docs.tabler.io/ui/layout/page-layouts), [Tabler components](https://docs.tabler.io/ui).
- [Tom Select interaction documentation](https://tom-select.js.org/docs/): consulted for selector interaction; no Tom Select dependency introduced.
- [Frappe supported hooks](https://docs.frappe.io/framework/user/en/python-api/hooks), [ERPNext printing](https://docs.frappe.io/erpnext/printing).
- Runtime pinned Frappe `6a329d068416768ec47ccd3326b9cc95a8d7bf99`: `www/printview.py` validates native print permissions **before** invoking `get_print_format_template`; returning no replacement retains the native renderer. `utils/safe_exec.py`, `utils/jinja.py`, `translate.py`, `utils/translations.py` checked for locale/rendering behavior. Upstream incomplete Italian labels supplemented only in the app.
- ERPNext `81a6f97566b83609c3917404a560b673050e907d`; Marley `934d6c162868139dfbe80c23d6102adb7ec25adb`; Builder `41987c064da4650e6901b5da82b7c76add452ebf`. Versions/commits remain pinned by the existing immutable image path.

## Diagnostic fixes and discarded attempts

Generic `.btn` flex geometry initially flattened event cards: explicit block adaptation preserves calendar geometry. Native login `page-card` conflicted with Tabler page min-height: auth-card override confines this supported upstream markup. Debounced search initially left earlier options visible: now immediately invalidated before the next request. Request-local language alone did not translate hardcoded template/Letter Head labels. The rendering hook translates gettext labels; constrained post-render label localization completes the native format. Real browser default/explicit-locale print and A/B/C denial are the discriminating evidence.

Several old QA assertions assumed eight September sessions and one wholly future October session. Owner had already moved one performed session to October; regression now reconciles native records/categories instead of resetting data to old expectations. These are QA changes, not reporting or lifecycle changes.

Full results, matrix and screenshots: `CONFORMANCE.md` and sibling normalized JSON/PNG evidence. No production, real data, real providers, real fiscal traffic, upstream edits or permission-model change. Owner visual acceptance remains required.

## Final runtime corrections

Text+semantic Tabler badges also cover dynamic table states. History/notes/notifications use shared `card-body` spacing; public/error primary actions explicitly retain the teal token against native CSS. Existing generated notification labels and collection amounts receive Italian presentation, with original records untouched. Finance practitioner/supplier aliases use only the existing authorized boot context.

The actual native403 path is `NotPermittedPage` → `www/message.html`. The supported context hook reads the existing response action before native late context merge and selects `cc_error_page.html`; native status/grant/action remain unchanged. Shared error card uses the base template's `content` block. Real403,404 and generic error layout are tested; earlier blank-template/late-context attempts were rejected, not marked PASS.

The final session-print adaptation keeps the same existing API, native read guard and fields; only Italian state/date and synthetic name presentation changes. Actual canonical `Reopened` is displayed `Riaperta`, reconciled in the browser instead of assuming Closed. Real authorized HTML is rendered in a browser setContent on the existing authenticated origin (no added server route) and print-media screenshot. Final runtime/source/parity/permissions are rc21; unchanged rc20 surface evidence is explicitly reused with source-diff provenance.
