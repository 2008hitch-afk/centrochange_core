# Centro Change UI Design System v1

**Status:** OWNER APPROVED — design direction  
**Owner decision date:** 2026-10-08  
**Implementation status:** TRANSVERSELY APPLIED — TECHNICAL PASS / READY_FOR_OWNER_UAT (2026-10-08); OWNER VISUAL ACCEPTANCE PENDING
**Issue:** #76  
**Final visual gate:** #75  
**Permission gate:** #77

## 1. Purpose

This document is the authoritative UI direction for the Centro Change client-facing web application.

The goal is to stop page-by-page visual improvisation and provide one reusable, deterministic design system for all current and future Centro Change application surfaces.

This specification governs presentation and interaction patterns. It does **not** authorize changes to business logic, data model, permission model, accounting semantics, clinical confidentiality, provider integrations, production scope or GOAL-03.

## 2. Approved foundation

Centro Change UI v1 is based on:

- **Tabler Core 1.6.1** as the UI framework/reference baseline.
- **Bootstrap semantics used by Tabler**, without introducing React or a separate SPA architecture.
- **Tabler Icons** for client-facing iconography.
- **Tom Select or an equivalent Tabler-compatible searchable-select control** only where native Tabler/Bootstrap select behavior cannot satisfy the approved single-control search-and-select requirement.
- Existing Centro Change server-side APIs, guards, authorization boundaries and business workflows remain canonical.

### 2.1 Asset policy

- Runtime client assets MUST be served locally/versioned with the application. No runtime dependency on a public CDN.
- `@tabler/core` is pinned to **1.6.1**. No `latest` dependency.
- Any optional third-party dependency MUST be pinned to the exact tested version and lockfile/vendor evidence committed with the implementation.
- Third-party licenses MUST be preserved and recorded.
- Do not import the complete Tabler demo/plugin stack by default. Include only assets/components actually used.
- No charting/plugin package is approved merely because Tabler demos include it.

### 2.2 Reference sources

- Tabler releases: https://github.com/tabler/tabler/releases
- Tabler page layouts: https://docs.tabler.io/ui/layout/page-layouts
- Tabler UI documentation: https://docs.tabler.io/ui
- Tabler third-party references: https://docs.tabler.io/ui/getting-started/references
- Tabler license: https://github.com/tabler/tabler/blob/dev/LICENSE
- Tom Select: https://tom-select.js.org/

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

Use it through Tabler/Bootstrap theme variables for primary actions, active navigation and focus/accent states.

Do not create page-specific primary colors.

### 3.3 Neutral palette

Use Tabler's neutral palette and semantic variables for page backgrounds, surfaces, borders, muted text and disabled controls.

Do not introduce arbitrary greys per page.

### 3.4 Typography

Use the Tabler/system sans-serif stack.

Rules:

- one consistent type scale;
- page title clearly dominant but not oversized;
- section headings below page title;
- field labels and table headings consistent;
- secondary IDs/references visually subordinate;
- no custom web font in v1 unless separately approved.

### 3.5 Spacing and radius

Use Tabler/Bootstrap spacing tokens and component sizing.

Do not create ad-hoc padding, radius or control heights per page unless required by the calendar geometry and documented.

## 4. Application shell

All authenticated client-facing application surfaces should converge on the same shell:

- `.page`
- vertical responsive navigation based on `.navbar.navbar-vertical`
- `.page-wrapper`
- semantic page header
- one `main.page-body`
- optional secondary/detail region inside the page body
- navigation hidden from print with `d-print-none`

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
- mobile uses Tabler responsive/collapse behavior;
- user/logout area remains visually separated from primary navigation;
- `Direzione completa` may be shown as profile context, not as a technical role name.

## 5. Core component contract

No client-facing interactive control should remain as visually raw HTML when an appropriate Tabler pattern exists or can be adapted without changing business semantics.

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

Use a Tabler-style input group/search control with:

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

All forms use consistent Tabler form controls.

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

- Tabler modal structure;
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

Use Tabler table/list patterns.

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

Patient/session/invoice/reconciliation/audit detail should use Tabler cards and/or data-grid patterns rather than unstructured key-value paragraphs.

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

Use consistent Tabler alert/toast/empty/loading patterns.

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
- Tabler page header;
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

Public page uses Centro Change identity and Tabler form/card conventions.

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

Apply Centro Change/neutral Tabler authentication pattern.

Must not show:

- ERPNext logo;
- Frappe logo;
- `Powered by`;
- framework/product names not needed by the client.

Authentication implementation remains native unless a separate technical decision authorizes change.

### 14.13 403 / 404 / generic error

Use a Centro Change/neutral Tabler empty/error page with:

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

- sidebar collapses/behaves through Tabler responsive navbar rules;
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

1. shared Tabler assets/theme variables and base shell;
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
| Tabler component conformity | PASS |
| Search/select behavior | PASS where applicable |
| Italian client language | PASS |
| Human label > technical ID | PASS |
| Loading/empty/error states | PASS |
| Responsive/mobile | PASS |
| Keyboard/focus baseline | PASS |
| ERPNext/Frappe debranding | PASS |
| No Desk leakage | PASS |
| Permission-neutral regression | PASS via #77 |
| Business behavior unchanged | PASS |

A screen is not accepted merely because it "looks better"; it must conform to the component and interaction rules above.

## 22. Known UAT observations absorbed into this design system

The following previously observed UX issues are explicitly addressed by this specification:

- patient/professional search requiring a second native dropdown click;
- technical English status/notification vocabulary;
- raw event names and boolean values in audit views;
- technical IDs dominating human labels;
- ambiguous bank reconciliation amount wording;
- raw/simple lists without a coherent component treatment;
- inconsistent controls across Agenda, Finance and reports;
- ERPNext/Frappe branding leakage.

These are design-system requirements, not invitations to change the underlying business rules.

## 23. Governance state

Owner approved the Tabler-based direction on **2026-10-08**.

This approval authorizes the **design direction and specification**.

It does **not** by itself authorize:

- merge of PR #92 or any stacked PR;
- production deployment;
- permission changes;
- GOAL-03;
- unreviewed cross-application implementation.

Implementation remains subject to the current GOAL-02 governance, dedicated branch/PR workflow, technical regression evidence, #77 permission review and #75 final Owner visual acceptance.
