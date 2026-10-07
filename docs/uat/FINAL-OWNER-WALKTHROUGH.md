# Final Owner walkthrough — #75

Technical review is distinct from Owner visual acceptance. No new identity is applied before #76 decision. Retain accepted Agenda layout; targeted Italian presentation/search/debranding fixes only.

1. Login/logout/error and missing pages: Centro Change or neutral identity, no upstream logos or Powered by; no navigation to technical Desk.
2. Agenda: existing accepted weekly planner, all/one/multiple professionals, navigation/date, readable names, detail Seduta/Storico/Note and searchable +Prenota.
3. Patients: authorized name/UID search, exact/empty results, assignment selector; UID kept for operational traceability, not renamed in data.
4. Finance: all invoice/XML/bank/economics/queue/SdI/TS surfaces; states/account labels Italian, cancelled invoice history clear, matched bank invoice/amount retained, reviewed TS inputs visible; only simulated invii.
5. Professional/Patient reports: both entries, periods/presets, KPI=records, canonical documents/payment/outstanding reconciliation; fiscal subject sharing explicit and unallocated.
6. Direction: membership account names, Attivo/Disattivo, reason-based controls, audit read-only before/after, first-meeting failure recovery.
7. Public first meeting: readable dates/service/duration, confirmation email simulation, no real provider; stale route/date result cannot enable wrong-slot submission.
8. Desktop and 390px mobile: no document overflow; bounded internal table/planner scroll; modal labels/actions within viewport.

Remaining gates: Owner #76 identity decision, #64 explicit profile/exclusions review, #77 role matrix review and final visual #75 walkthrough. Existing document numbers, UID, audit facts and fiscal payloads retain canonical technical identifiers when required for traceability. Technical UAT guide and operator evidence can contain DEV/SYNTHETIC labels; client pages use plain-language invented-data/simulation warning. Provider delivery remains unavailable by authorized design.
