# Functional coverage — #148

`PRESENTE` below means source/UI and synthetic browser path exist; real Frappe behavior remains `NOT_VERIFIED`. Scope is from #148 and `PREMIUM-FRONTEND-MACRO-GOAL-v1.md`.

| Area | React candidate | State / remaining work |
|---|---|---|
| Shell and Agenda landing | single `/premium` shell, responsive menu, center selector, logout | PRESENTE; real role/login UAT NOT_VERIFIED |
| Agenda calendar | day practitioner lanes, week view, filter, date nav, event/slot selection | PRESENTE; collision, DST, 48h server tests NOT_VERIFIED |
| Booking and session actions | book, move, cancel, close, reopen, waive; action buttons reflect current server state | PRESENTE; booking and cancelled-state presentation mocked; other mutations NOT_VERIFIED |
| Patient overview | permission-aware search, history, packages, organizational note revision groups | PRESENTE; pagination/truncation and all patient permissions NOT_VERIFIED |
| Private notes | professional tab, create and append-only correction with grouped history | PRESENTE; synthetic correction/history PASS, server isolation NOT_VERIFIED |
| Availability | schedule/absence read and forms | PRESENTE; actual mutation NOT_VERIFIED |
| Operational report | summary and CSV link | PRESENTE; export permissions NOT_VERIFIED |
| Finance overview and drill-down | accounting summary; fiscal Customer groups and professional period report with sessions, invoices/payments or expectation comparisons, plus CSV | PRESENTE with synthetic browser checks; full field parity and live totals NOT_VERIFIED |
| Finance lists | sales, incoming XML, purchase, bank, expected compensation, admin queue, SdI, TS | PRESENTE as read-only tables; list/form parity NOT_VERIFIED |
| Finance mutations | sales draft/submit/pay/credit/amend, supplier submit/pay/cancel/amend, bank import/reconcile/cancel, admin queue, professional rule/threshold/capture/compare/override/reevaluate, SdI/TS simulated prepare/queue, incoming XML intake/supplier bind/classify/draft | PRESENTE in React; representative draft/payment/rule/capture/compare/XML classification mocked, live NOT_VERIFIED; fiscal review UI incomplete |
| Access | memberships read, membership/practitioner state actions | PRESENTE; synthetic membership POST PASS, live revocation NOT_VERIFIED |
| Audit | manager-only list, period/reference filters, event detail with actor, reason and before/after | PRESENTE; synthetic read-only desktop/mobile PASS, live audit permission NOT_VERIFIED |
| Notifications | list | PRESENTE via native read permission; live role check NOT_VERIFIED |
| Public first encounter | new React `/premium-primo-incontro` using existing guarded Guest services | PRESENTE; synthetic desktop/mobile booking PASS, live Guest UAT NOT_VERIFIED |
| Catalog, packages, assignments | read-only center service/practitioner directory; package issue/adjust and patient assignment/reassignment through existing audited services; searchable long selectors | PARTIAL; master catalog editor and full 11 list/form equivalents not built, server role checks NOT_VERIFIED |
| Technical Desk | existing Frappe/ERPNext/Marley | 11×2 disposition mapped in `NATIVE-ROUTE-DISPOSITION.md`; direct URL/role separation and Owner decision NOT_VERIFIED |
| Seven roles + Guest | existing #139 historical suite | this candidate tested manager-like synthetic and one finance-denied synthetic role only; full matrix NOT_VERIFIED |

The #139 branch contains broad backend and test changes. Its third DEV installation reported 128/128 role×route×viewport, 22/22 native list/form and 38/38 security on its own candidate. This branch does **not** merge it blindly. Those results are historical evidence and cannot be counted toward React acceptance. Its route/security test structure is retained as the future live comparison plan.
