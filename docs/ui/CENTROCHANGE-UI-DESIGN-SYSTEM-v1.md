# Centro Change UI Design System v1 — Owner revision 2026-10-12

**Status:** OWNER APPROVED — revised UI implementation direction (2026-10-12)  
**Original visual direction approved:** 2026-10-08  
**Current implementation/acceptance:** TARGET DOCUMENTED; PR #126 visual review NOT ACCEPTED / remediation pending. No OWNER VISUAL PASS and no final GOAL-02 acceptance.  
**Interpretation:** This revision supersedes every earlier v1 statement that treats Tabler, Tabler classes, Bootstrap semantics, or Tabler Core 1.6.1 as mandatory implementation technology. It does not retrospectively validate or reject every existing implementation detail.
**Issue:** #76  
**Final visual gate:** #75  
**Permission gate:** #77

## 1. Purpose

This document is the authoritative UI direction for the Centro Change client-facing web application.

The goal is to stop page-by-page visual improvisation and provide one reusable, deterministic design system for all current and future Centro Change application surfaces.

This specification governs presentation and interaction patterns. It does **not** authorize changes to business logic, data model, permission model, accounting semantics, clinical confidentiality, provider integrations, production scope or GOAL-03.

## 2. Approved foundation

Centro Change UI v1 is based on:

- **Frappe/ERPNext native customization first.** Prefer supported DocType configuration, Customize Form/Property Setter/Custom Field, List View settings, Form/Client Scripts, translations, Workspace/Page interfaces and versioned app hooks, according to the needs of the view. Preserve standard Frappe lifecycle and upgradeability.
- **Dedicated client-facing UI only when needed.** Custom Frappe pages/client views are appropriate for workflows that native configuration cannot express well (e.g. calendar, operational dashboards or complex cross-DocType workflows); avoid duplicating native ERPNext data, permissions, services or business rules.
- **Tabler as visual inspiration only**: clear hierarchy, compact meaningful cards, readable forms/tables, left navigation, icons, whitespace, color and responsive layout. **Do not require installing or importing Tabler Core, Tabler CSS/JS, Bootstrap semantics, or Tabler-specific classes.**
- Reuse supported Frappe-compatible client widgets, including an appropriate searchable selector when necessary. The interaction requirement is authoritative; **Tom Select is optional, not prescribed**.
- Existing Centro Change server-side APIs, guards, authorization boundaries and business workflows remain canonical.

### 2.1 Asset policy

- Runtime client assets MUST be served locally/versioned with the application. No runtime dependency on a public CDN.
- **No Tabler package is required.** If an existing implementation already includes Tabler 1.6.1, that asset is a legacy implementation fact, not a new mandate. Its retention, simplification or removal requires an impact/regression review; do not uninstall it automatically just because this document changes.
- Any optional third-party dependency MUST be pinned to the exact tested version and lockfile/vendor evidence committed with the implementation.
- Third-party licenses MUST be preserved and recorded.
- Prefer the smallest stable Frappe-supported extension; do not impose a second UI framework, a Tabler demo/plugin stack, or new charting packages just for visual imitation.

### 2.2 Reference sources

**Frappe implementation references (native mechanisms):**
- Frappe Framework documentation: https://docs.frappe.io/framework
- Frappe customizations and Customize Form: https://docs.frappe.io/framework/user/en/customize-erpnext
- Frappe Form Scripts: https://docs.frappe.io/framework/user/en/api/form
- Frappe List View: https://docs.frappe.io/framework/user/en/api/list
- Frappe hooks: https://docs.frappe.io/framework/user/en/python-api/hooks

**Visual moodboard only (not implementation authority):**
- Tabler page layouts: https://docs.tabler.io/ui/layout/page-layouts
- Tabler UI patterns: https://docs.tabler.io/ui

Official Frappe version-pinned source and documentation remain decisive for available hooks, permissions and lifecycle.

### 2.3 Native-first implementation decision rule — OWNER APPROVED 2026-10-12

For every client-facing area, decide and document which of these three outcomes applies:

1. **NATIVE_CUSTOMIZE** — Use supported Frappe/ERPNext List/Form/DocType/Workspace customization when it meets the workflow. Apply client-friendly labels, fields, ordering, list settings, translations, buttons and styling via supported extension points. Do not rely on DOM text rewriting or broad CSS overrides as the main product architecture.
2. **NATIVE_WITH_CLIENT_PRESENTATION** — Preserve the native function, rendering and security while applying bounded client brand/visual conventions and a coherent navigation entry. Test transitions, roles and upstream updates.
3. **DEDICATED_FRAPPE_PAGE** — Implement a purpose-built interface only if native capabilities are insufficient for the validated user task, reusing the same server APIs and permission boundaries. Avoid copying Frappe models or business logic.

Record a rationale and upgrade/regression consequence for any dedicated interface. Do not create a second site, database or frontend stack.

**No mandatory Tabler import, package, CSS classes or technical compliance test.** Acceptance depends on the user's visual/operational experience and functional integrity, not DOM class names or framework installation.

## 3. Brand and visual principles

### 3.1 Identity

The product must present as **Centro Change**, never as an ERPNext/Frappe installation.

Until a separate logo asset is explicitly approved:

- use the text identity **Centro Change**;
- do not invent a replacement logo;
- do not use ERPNext or Frappe logos, names or `Powered by` branding on client-facing surfaces.

### 3.2 Primary color

Retain the already accepted Centro Change primary teal:

`#12665F`

Use it through Centro Change/Frappe-supported theme tokens or local styling for primary actions, active navigation and focus/accent states; no Tabler CSS variable is mandatory.

Do not create page-specific primary colors.

### 3.3 Neutral palette

Use a stable Centro Change neutral palette inspired by Tabler references, implemented via supported/native tokens wherever possible for page backgrounds, surfaces, borders, muted text and disabled controls.

Do not introduce arbitrary greys per page.

### 3.4 Typography

Use an accessible, consistent system sans-serif stack inspired by Tabler's visual proportions; prefer the Frappe-native stack when compatible.

Rules:

- one consistent type scale;
- page title clearly dominant but not oversized;
- section headings below page title;
- field labels and table headings consistent;
- secondary IDs/references visually subordinate;
- no custom web font in v1 unless separately approved.

### 3.5 Spacing and radius

Use consistent Centro Change spacing, radius and sizing tokens inspired by Tabler, implemented through Frappe/native or scoped product styles.

Do not create ad-hoc padding, radius or control heights per page unless required by the calendar geometry and documented.

## 4. Application shell

All authenticated client-facing application surfaces should converge on one consistent **Centro Change experience**, using supported Frappe native shell/Workspace/page mechanisms where possible and dedicated page layouts only where necessary:

- persistent client navigation on the left (role-aware, no duplicate horizontal app menu);
- one unobtrusive brand/account header with a distinct contextual page title (no duplicated "Centro Change");
- a stable main content region and optional local detail region;
- no overlapping Frappe dock, native sidebar or upstream launcher in client-facing workflows;
- transitions, refresh, back/forward and responsive breakpoints without shell jumps, clipped menu or upstream branding flash;
- print hides navigation and preserves the printable data;
- Administrator/technical ERPNext remains independently accessible.

**Do not require Tabler DOM structure/classes such as `.page`, `.navbar.navbar-vertical`, `.page-wrapper` or `main.page-body`.** Native Frappe markup may remain native when properly customized.

### 4.1 Sidebar

Primary navigation groups are role-aware but visually consistent.

Candidate information architecture:

**Operatività**
- Agenda
- Pazienti
- Disponibilità

**Controllo**
- Report
- Finanza

**Amministrazione** where authorized
- Notifiche
- Registro modifiche

Rules:

- icon + readable Italian text;
- active state always visible;
- no raw technical route names;
- no client-facing link to ERPNext/Frappe Desk where a Centro Change surface exists;
- mobile navigation must be accessible and stable, using a supported native pattern or equivalent behavior inspired by Tabler;
- user/logout area remains visually separated from primary navigation;
- `Direzione completa` may be shown as profile context, not as a technical role name.

## 5. Core component contract

Every client-facing interactive control must be styled coherently using native Frappe features or a supported scoped custom view, visually inspired by Tabler. A matching Tabler DOM component or installed Tabler package is not required.

Every applicable component must define and test:

- default;
- hover;
- keyboard focus;
- active/selected;
- disabled;
- loading;
- empty/no-results;
- error/invalid.

## 6. Buttons and actions

Use one hierarchy everywhere:

### Primary
For the main positive action of the current context.

Examples:
- Prenota
- Conferma
- Salva
- Registra

### Secondary
For non-destructive alternative actions.

Examples:
- Annulla
- Chiudi
- Torna indietro
- Aggiorna

### Ghost/icon
For compact contextual actions where the meaning is clear and accessible.

### Danger
Only for destructive/reversal actions.

Rules:

- one visually dominant primary action per action group;
- destructive actions must not visually resemble normal navigation;
- icon-only buttons require accessible names/tooltips;
- no one-off button shapes, heights or colors.

## 7. Search and searchable selection

This is a mandatory v1 rule.

### 7.1 Search input

Use a compact, accessible native Frappe or dedicated search control visually inspired by Tabler with:

- search icon;
- clear placeholder in Italian;
- visible focus;
- loading state;
- no-results state;
- error state;
- debounced remote search where required.

### 7.2 Searchable select

Patient and professional selection MUST be a **single interaction control**.

Approved behavior:

1. user focuses one field;
2. user types part of name/authorized identifier;
3. authorized matches appear immediately in the same dropdown;
4. click or Enter selects the item;
5. selected human-readable label remains visible;
6. canonical server identifier remains the submitted value;
7. no separate "search field + second native dropdown click" workflow.

For remote patient search:

- server remains authoritative for authorization;
- no permission bypass;
- bounded results;
- stale async responses must not overwrite current context;
- "Nessun risultato autorizzato" is explicit.

For professionals:

- search only the already-authorized professional projection for the current role/center.

If Tom Select is used, configure it as a controlled selector, not as a free-form tag creator.

## 8. Forms

All forms use consistent, supported native Frappe controls first, customized as needed for Centro Change; dedicated controls only when native ones cannot meet the accepted task.

Required rules:

- label above control;
- optional helper text below;
- required state communicated semantically;
- validation next to the relevant control;
- no technical exception text exposed as primary user copy;
- sensitive operations retain required reason/motivation;
- date input may remain native/ISO internally while visible surrounding copy is Italian;
- money shown in Italian EUR format where currency is EUR;
- controls align to a common grid on desktop and stack on mobile.

## 9. Modals

All application modals follow one contract:

- supported Frappe-native dialog/modal structure first, or dedicated modal structure when necessary, with consistent Centro Change styling inspired by Tabler;
- clear title;
- body grouped by task;
- validation/error area close to affected fields;
- footer with secondary action then primary action;
- danger confirmation clearly distinguished;
- width determined by content category, not arbitrary per modal;
- mobile modal stays inside viewport;
- focus enters modal and keyboard navigation remains usable.

Searchable selectors inside a modal must use the single-control rule from section 7.

## 10. Tables and lists

Use native List View configuration wherever suitable, with consistent Centro Change table/list styling inspired by Tabler. Use dedicated tables only for workflows the native list cannot fulfill.

Rules:

- consistent header;
- readable row density;
- hover/selection feedback where rows are interactive;
- numeric/money columns right-aligned where useful;
- date/time formatting consistent;
- status represented with text plus semantic badge/status treatment;
- row actions grouped consistently;
- human-readable name is primary;
- canonical ID/document number is secondary where traceability is required;
- responsive behavior uses bounded table scrolling, not whole-page horizontal overflow;
- empty table uses an explicit empty state, not a blank area.

## 11. Cards, details and data grids

Patient/session/invoice/reconciliation/audit detail should use meaningful, compact native Form sections or cards/data-grid patterns visually inspired by Tabler rather than unstructured key-value paragraphs or oversized empty panels.

Typical structure:

- title / identity;
- important status;
- grouped key-value fields;
- relevant financial totals;
- contextual actions;
- expandable technical/audit detail only where needed.

Technical identifiers should not compete visually with human labels.

## 12. Status vocabulary

Status uses text + semantic visual treatment. Never color alone.

Client-facing labels are Italian.

Examples include:

- Prenotata
- Da chiudere
- Chiusa
- Riaperta
- Cancellata
- Pagata
- Non pagata
- Annullata
- Da verificare
- Riconciliata
- In attesa
- Conferma registrata in simulazione

Backend canonical values may remain English/technical internally.

Do not expose values such as `Pending`, `Closed`, `CENTER_MEMBERSHIP`, raw booleans such as `active 0/1`, or equivalent technical vocabulary as the primary client label.

## 13. Alerts, feedback and system states

Use consistent native Frappe feedback/alert/empty/loading patterns, visually inspired by Tabler and localized for Centro Change.

### Success
Short user-oriented confirmation.

### Warning
Actionable and specific.

### Error
Italian, understandable, with next useful action when possible.

### Loading
Use spinner/placeholder/skeleton appropriate to the surface. Do not leave stale data without a loading indication.

### Empty state
Explain what is empty and, where authorized, the next action.

DEV/UAT simulation warnings remain explicit and visually separate from production-like content.

## 14. Page-to-component map

### 14.1 `/centrochange` — Agenda

Keep the accepted functional calendar model.

Apply:

- shared application shell;
- a compact semantic page header with styling inspired by Tabler;
- primary `+ Prenota` button;
- compact toolbar for center/week/view;
- professional picker/search following searchable-control rules;
- calendar controls using consistent buttons/button groups;
- session state chips/statuses;
- selected session detail in card/data-grid structure;
- action groups consistent with section 6;
- no business-rule change to closure/reopen/reschedule.

### 14.2 `/centrochange` — Pazienti subview

Apply:

- standard page/subview header;
- search input;
- data table/list;
- searchable patient/professional controls in creation/assignment flows;
- action buttons using standard hierarchy;
- explicit no-results and loading states;
- economic report link visually secondary to operational identity.

### 14.3 `/centrochange` — Disponibilità subview

Apply:

- card/form structure;
- standard date/time controls;
- consistent switches/check states;
- compact explanatory text;
- standard save/confirm feedback.

### 14.4 `/centrochange` — Notifiche subview

Apply:

- list/table pattern;
- recipient, date/time and state readable at scan speed;
- failure/retry uses semantic status and clear action;
- first-meeting confirmation entries shown without technical implementation vocabulary.

### 14.5 `/finanza`

Apply shared shell plus role-authorized finance navigation.

For each finance view:

- toolbar/filter row;
- KPI/summary cards where useful;
- standard data table;
- status badges;
- selected row opens a coherent detail card/panel;
- action modal follows common modal contract.

Do not expose accounting implementation details unless necessary for traceability.

### 14.6 Finance — Bank reconciliation

Detail must clearly distinguish:

- movement amount;
- reconciled amount;
- remaining/unallocated amount;
- reconciled document;
- fiscal subject;
- reconciled amount per document.

Avoid ambiguous headings such as a generic `Riconciliato · 0,00 €` when 0 means remaining rather than reconciled.

### 14.7 Finance — simulated TS/SdI

Use:

- prominent simulation status;
- explicit "nessun invio reale" notice in DEV/UAT;
- status badge;
- data-grid presentation for reviewed inputs;
- human labels before technical snapshot/version identifiers.

### 14.8 `/professionista`

Apply:

- shared report shell;
- single searchable professional selector;
- period filters;
- metric cards;
- session table;
- compensation/expectation detail cards;
- readable expected vs received comparison;
- Italian operational/accounting labels.

### 14.9 `/pazienti_report`

Apply:

- shared report shell;
- search;
- date/center filters;
- responsive financial table;
- patient/fiscal-subject labels clearly separated;
- drill-down detail card;
- CSV export as secondary action.

### 14.10 `/registro_modifiche`

Apply:

- read-only audit table;
- filters;
- humanized event type;
- actor shown as readable identity where available;
- timestamp;
- reference;
- reason;
- expandable Before/After using data-grid/card;
- canonical IDs secondary;
- no raw `active: 0 -> 1` as the only explanation: pair with human meaning such as `Accesso: Disattivato -> Attivo`.

### 14.11 `/primo_incontro`

Public page uses Centro Change identity and clear native/custom form/card conventions visually inspired by Tabler.

Apply:

- simple public header/brand;
- readable professional/service selection;
- slot selection;
- personal-data form;
- clear validation;
- success state with booked date/time;
- simulated confirmation notice only in DEV/UAT;
- no ERPNext/Frappe branding.

### 14.12 Login / logout / session states

Apply Centro Change-branded, native-compatible authentication styling inspired by Tabler; do not replace the authentication implementation.

Must not show:

- ERPNext logo;
- Frappe logo;
- `Powered by`;
- framework/product names not needed by the client.

Authentication implementation remains native unless a separate technical decision authorizes change.

### 14.13 403 / 404 / generic error

Use Centro Change-branded native or dedicated empty/error page styling inspired by Tabler with:

- simple human title;
- short explanation;
- one useful recovery action;
- correct HTTP status retained;
- no upstream product branding.

### 14.14 `/validazione`

This is a UAT/DEV support surface, not a production client workflow.

It should still use the shared visual primitives where practical, but its testing content may remain denser than the end-user application.

## 15. Responsive rules

Desktop, tablet and mobile behavior is part of component acceptance, not later polish.

Minimum rules:

- sidebar behaves responsively and accessibly through native Frappe layout features or a scoped equivalent, without a Tabler dependency;
- controls wrap/stack without overlap;
- primary action remains reachable;
- modal stays within viewport;
- tables scroll inside their own container when necessary;
- no page-level horizontal overflow at the target mobile viewport;
- cards become single-column when width requires it;
- labels remain visible;
- touch targets remain usable.

## 16. Accessibility baseline

Required:

- semantic landmarks;
- one main content region per page;
- skip-to-content where shared shell supports it;
- labelled navigation regions;
- form labels tied to controls;
- visible keyboard focus;
- keyboard-operable menus, modals and searchable selects;
- status not communicated by color alone;
- accessible name for icon-only controls;
- useful `aria-live`/status behavior for async search and operation feedback;
- reasonable contrast using framework semantic variables.

## 17. Print/export presentation

Client-facing print views should:

- hide navigation and interactive actions;
- preserve document title/context;
- preserve important status and amounts;
- avoid clipped tables;
- not expose ERPNext/Frappe branding;
- not expose technical controls or URLs as primary content.

Exports remain data functions; this design system does not change export authorization.

## 18. Debranding contract

Client-facing UI acceptance fails if any of the following are visible where not explicitly required:

- ERPNext logo;
- Frappe logo;
- `Powered by ERPNext`;
- `Powered by Frappe`;
- Desk navigation when a Centro Change equivalent exists;
- raw framework page chrome on client workflows.

Technical/admin-only infrastructure may retain native branding outside the client navigation boundary.

## 19. Permission-neutral implementation contract

UI migration must not:

- add or remove roles;
- expand center scope;
- weaken patient/professional segregation;
- bypass server authorization;
- infer access from hidden/disabled buttons;
- expose an endpoint because the UI needs a new component;
- move confidential notes into broader views;
- change accounting or session lifecycle rules.

If a desired UI pattern appears to require a permission or API expansion, implementation MUST stop and request a separate Owner decision.

## 20. Implementation sequence

Recommended implementation order:

1. native Frappe capability map per area; stable single shell and shared Centro Change visual tokens inspired by Tabler;
2. shared primitives: buttons, forms, searchable select, modal, status, table, card, feedback;
3. Agenda and operational subviews;
4. Finance;
5. Professional and Patient reports;
6. Audit register and notifications;
7. public first-meeting and authentication/error surfaces;
8. responsive pass;
9. print pass;
10. #77 permission regression;
11. #75 final visual walkthrough.

Do not perform page-specific cosmetic patches ahead of the shared primitives unless required to unblock implementation.

## 21. Acceptance matrix for #75

Each client-facing surface must be reviewed against:

| Gate | Required |
|---|---|
| Shared shell / layout | PASS |
| Centro Change visual consistency inspired by Tabler (no library/class requirement) | PASS |
| Search/select behavior | PASS where applicable |
| Italian client language | PASS |
| Human label > technical ID | PASS |
| Loading/empty/error states | PASS |
| Responsive/mobile | PASS |
| Keyboard/focus baseline | PASS |
| ERPNext/Frappe debranding including transitory chrome and authorized client entry | PASS |
| No client Desk leakage, shell shift or duplicate navigation | PASS |
| Permission-neutral regression | PASS via #77 |
| Business behavior unchanged | PASS |
| Native-first choice documented for each view; dedicated UI only where justified | PASS |
| Owner visual review against actual screenshots/workflows (not just automated DOM checks) | PASS only after explicit Owner acceptance |

A screen is not accepted merely because it "looks better"; it must conform to the component and interaction rules above.

## 22. Known UAT observations absorbed into this design system

The following previously observed UX issues are explicitly addressed by this specification (including subsequent Owner observations on 2026-10-12):

- patient/professional search requiring a second native dropdown click;
- technical English status/notification vocabulary;
- raw event names and boolean values in audit views;
- technical IDs dominating human labels;
- ambiguous bank reconciliation amount wording;
- raw/simple lists without a coherent component treatment;
- inconsistent controls across Agenda, Finance and reports;
- ERPNext/Frappe branding leakage and upstream loader flash during client page transitions;
- left navigation collapse/overlap, repeated brand in header and unpredictable Frappe dock;
- oversized three-link Home cards and full-width patient actions without useful density;
- unintended upstream Workspace with ERPNext/Marley logos;
- Healthcare Practitioner view triggering Medical Department permission error (technical cause to verify; **no permission widening authorized**).

These are design-system requirements, not invitations to change the underlying business rules.

## 23. Governance state

Owner approved the initial Tabler-inspired visual direction on **2026-10-08** and clarified/approved the **native Frappe-first implementation strategy on 2026-10-12**. This newer decision supersedes the former mandatory Tabler Core 1.6.1 / Tabler-class interpretation. It does not authorize uninstalling assets, redesigning all native screens, changing roles, merging PRs, or deploying to production.

This approval authorizes the **design direction and specification**.

It does **not** by itself authorize:

- merge of PR #92 or any stacked PR;
- production deployment;
- permission changes;
- GOAL-03;
- unreviewed cross-application implementation.

Implementation remains subject to current GOAL-02 governance, dedicated branch/PR workflow, technical and functional regression evidence, #77 permission review and #75 final Owner visual acceptance. PR #126 remains DRAFT and its visual UI acceptance remains **NOT ACCEPTED** until a new Owner review; no merge or server changes are authorized by this document update.
