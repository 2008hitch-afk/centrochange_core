# Functional coverage — #148

`PRESENTE` below means source/UI and synthetic browser path exist; real Frappe behavior remains `NOT_VERIFIED`. Scope is from #148 and `PREMIUM-FRONTEND-MACRO-GOAL-v1.md`.

| Area | React candidate | State / remaining work |
|---|---|---|
| Shell and Agenda landing | single `/premium` shell, responsive menu, center selector, logout | PRESENTE; real role/login UAT NOT_VERIFIED |
| Agenda calendar | day practitioner lanes, week view, filter, date nav, event/slot selection | PRESENTE; collision, DST, 48h server tests NOT_VERIFIED |
| Booking and session actions | book, move, cancel, close, reopen, waive | PRESENTE; only booking mocked; other mutations NOT_VERIFIED |
| Patient overview | permission-aware search, history, packages, organizational notes | PRESENTE; pagination/truncation and all patient permissions NOT_VERIFIED |
| Private notes | professional tab and create | PRESENTE; correction flow UI missing, server isolation NOT_VERIFIED |
| Availability | schedule/absence read and forms | PRESENTE; actual mutation NOT_VERIFIED |
| Operational report | summary and CSV link | PRESENTE; export permissions NOT_VERIFIED |
| Finance overview | accounting summary, debts and expected compensation | PRESENTE; live totals NOT_VERIFIED |
| Finance lists | sales, incoming XML, purchase, bank, expected compensation, admin queue, SdI, TS | PRESENTE as read-only tables; list/form parity NOT_VERIFIED |
| Finance mutations | sales draft/submit/pay/credit, incoming invoice review, bank import/reconcile, professional rule/threshold/compare, SdI/TS simulated prep/retry | BACKEND_AVAILABLE_UI_MISSING; existing domain services identified; no new rule authorized |
| Access | memberships read | PRESENTE; membership/practitioner state actions UI missing |
| Notifications | list | PRESENTE via native read permission; live role check NOT_VERIFIED |
| Public first encounter | existing Frappe page only | BACKEND_AVAILABLE_UI_MISSING in React; Guest UAT NOT_VERIFIED |
| Catalog, packages, assignments | backend and native Desk | BACKEND_AVAILABLE_UI_MISSING; 11 list/form equivalents not built |
| Technical Desk | existing Frappe/ERPNext/Marley | no second native UI developed; 11×2 parity and separation decision NOT_VERIFIED |
| Seven roles + Guest | existing #139 historical suite | this candidate tested manager-like synthetic and one finance-denied synthetic role only; full matrix NOT_VERIFIED |

The #139 branch contains broad backend and test changes. Its third DEV installation reported 128/128 role×route×viewport, 22/22 native list/form and 38/38 security on its own candidate. This branch does **not** merge it blindly. Those results are historical evidence and cannot be counted toward React acceptance. Its route/security test structure is retained as the future live comparison plan.
