# Final Owner walkthrough — #75

**Current:** Owner-approved Design System v1, implemented transversally in `goal02-20261008-rc21`. **TECHNICAL PASS != OWNER VISUAL ACCEPTANCE.** Issues76/77/75 remain OPEN; drafts92/93/94 unmerged. [Exact conformity matrix/evidence/screenshots](../evidence/ui-design-system-v1/CONFORMANCE.md). Dataset contains existing Owner UAT changes, not the obsolete initial fixture.

1. Login/logout, real403,404 and generic error: Centro Change text brand, Italian recovery, teal action, no upstream chrome or Desk link; native authentication/diniegos unchanged.
2. Agenda: accepted weekly professional-row model; week/Today/date/all/one/multiple filter; readable names and states, event detail Seduta/Storico/Note. +Prenota uses one Patient search-and-select control and one Professional control; click/Arrow/Enter, no-results and retry; canonical selections unchanged.
3. Pazienti/Disponibilità: authorized search and assignment, searchable professional, common cards/forms, human identity beforeUID, Italian dates; no new permissions.
4. Notifiche/access management/audit: readable labels, state badges, dates and role/actor; required reasons retained; audit Before/After human meaning plus expandable canonical originals. Shared card-body spacing.
5. All nine Finance views: common shell/filters/buttons/table/card/modal/alert; receipt/invoice/bank reconciliation amounts remain distinct and canonical; TS/SdI explicitly simulated. Scan human professional/fiscal subject and Italian statuses; no provider actions made real.
6. Professional/Patient reports: both entries, shared periods/presets/search, exact KPI↔records/CSV, canonical accounting sources. Patient identity is distinct from fiscal Customer; shared payer balance not duplicated/allocated.
7. Public first meeting: readable searchable professional, authorized route/service/slot, Italian date/time, validation and dated success; no real delivery. Stale route/date cannot enable old slot.
8. Native invoice and session print: Italian labels, preserved canonical document values, navigation/actions hidden in print, no branding/Desk controls or clipping. Native amount-in-words and legal party identity remain original data. Export remains an authorized data function.
9. Desktop1536px/mobile390px: collapse navigation with click/Space, internally scrollable tables/calendar, visible focus/labels, one main landmark, modal within viewport and Escape/return focus. Review all24 screenshot pairs against the design-system dimensions, not merely whether they look improved.
10. Role validation with existing approved role matrix: Manager, Secretariat, Finance, Accountant, A/B/C and Guest. Server evidence is in #77; hiding buttons is not proof. A/B/C cannot gain another professional/patient/fiscal/private-note scope. No role-model delta.

Record per-surface Owner PASS/FAIL and screenshot/reference. If a visual request requires new API/grant/visibility, pause for an explicit Owner decision; do not infer it. No identity decision remains pending; final visual acceptance, #77 review and final GOAL-02 acceptance are still Owner decisions. No production, real data, providers, real SdI/TS, stack merge or GOAL-03.

## #75 Agenda alignment retest — RC22

Verify 5–11 October and 28 September–4 October with sessions visible: each day header must coincide with its day column; repeat after resize and internal horizontal scroll. Professional column stays distinct. Technical evidence does not replace Owner visual acceptance.
