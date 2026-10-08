# #76 — UI identity proposal — decision recorded

Status: **SUPERSEDED BY OWNER-APPROVED DESIGN DIRECTION** on 2026-10-08.

The authoritative design specification is now `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md`: **Tabler-based Centro Change UI v1**, retaining the existing Centro Change teal, using consistent Tabler components and a single-control searchable-select pattern, with client-facing ERPNext/Frappe debranding. This records a design decision only; transversal implementation, merge and final acceptance remain pending.

Authorized neutral removal of upstream logos/Powered by and technical Desk links remains implemented separately using supported website hooks and native authentication.

Proposed basis: retain the already visually accepted weekly Agenda. Use its existing restrained teal actions, neutral white/grey surfaces, current sans-serif stack and operational density as the reference, with readable Italian names/dates/money. No replacement logo is proposed: retain the existing Centro Change text until Owner supplies/approves brand assets.

| Component | Proposed rule / existing reference |
|---|---|
| Navigation | Compact Agenda rail; consistent links back to Agenda/Finance/report levels |
| Typography | Existing system sans-serif; compact page title; secondary muted context |
| Palette | Existing Agenda teal for primary actions; neutral backgrounds; color supplemented by status text |
| Density | Dominant planning viewport; bounded scroll tables; compact horizontal filters on desktop |
| Forms | Explicit labels, canonical values hidden from primary labels; modal action + reason for sensitive changes |
| State | Specific Italian empty/loading/success/error messages, status text and accessible announcements |
| Identity | Readable display name primary; document number/UID secondary only when traceability requires it |
| Dates/money | Italian visible formatting; technical date inputs remain ISO internally; EUR formatting |
| Mobile | No document overflow; internal planner/table scrolling; modals within viewport |
| Accessibility | Labelled controls, keyboard buttons, native selects, no color-only information |

Existing examples for review: accepted Agenda, Italian account-label modal (#80), authorized selector search (#79), patient fiscal report (#68), and audit register (#71). These functional/clarity fixes do not constitute acceptance of a new design system.

Decision outcome: Owner selected **Tabler** as the cross-application visual baseline on 2026-10-08. The detailed rules, page-to-component map, responsive/accessibility contract and acceptance matrix are defined in `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md`.

Full identity application and #75 visual completion remain pending. Native infrastructure/administrative tools remain separate from client navigation; no permission alteration.
