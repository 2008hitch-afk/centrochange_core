# Component catalog — #148

Components are in `frontend/premium/src/ui.tsx` and assembled in `main.tsx` / `views.tsx`.

| Component | Contract | Current evidence |
|---|---|---|
| Shell/sidebar/topbar | role-aware menu, center switch, logout, search entry, responsive overlay | mocked desktop/mobile browser PASS |
| Heading, Button, Chip | shared visual hierarchy, states, semantic button | screenshot reviewed |
| Metric, DataTable | financial and operational summaries; keyboard rows | mocked browser PASS for Agenda/Finance |
| Modal, Drawer | booking and details, Escape close | booking/drawer browser PASS |
| Field, FormError, useAction | native validation, required reasons, busy/error handling | booking POST/CSRF browser PASS |
| DateInput | Italian `GG/MM/AAAA` text with calendar-date validation; sends ISO to API | invalid/valid date browser PASS; calendar-picker UX remains open |
| Empty/loading/alert | visible empty, loading and request failure states | rendered; full scenario matrix NOT_VERIFIED |
| React Big Calendar | day resources and week overview, click event/slot, local wall time | mocked Agenda desktop/mobile PASS; DST scheduling server NOT_VERIFIED |
| FinanceCreate / FinanceActions | guided accounting actions, request keys stable for identical retries, scoped candidates | synthetic invoice draft/payment PASS; all live accounting outcomes NOT_VERIFIED |
| FirstMeeting | public route, slot-only search, bounded identity form, confirmation | synthetic Guest flow desktop/mobile PASS; live rate limit/permissions NOT_VERIFIED |

Untitled UI React FREE was reviewed as a candidate. Its package distribution is copy-based rather than an npm component library; using it would add Tailwind/React Aria and a second styling system. The candidate therefore uses native semantic controls plus one shared component layer and MIT React Big Calendar. No Untitled PRO or FullCalendar Premium content is used.
