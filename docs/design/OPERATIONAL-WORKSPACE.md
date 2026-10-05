# Operational workspace — DEV implementation spec

HC-0005 DECISION-004 governs: dedicated authenticated Centro Change web app, native Frappe foundation, Desk for administration. No independent application stack or branded public website (deferred CC-CAP-031). `/centrochange` uses supported Frappe website routing and versioned app assets; `/primo_incontro` is the narrow fixed-route first-meeting transaction surface.

The concept is `operational-workspace-concept.png`, generated using the built-in Image Gen tool as the primary-screen implementation reference. Brief: Italian operational agenda, left navigation, center/date filters, table with session state, selected-patient detail, closure/payment/reason, move/cancel, history/notes tabs; true white, restrained teal, no marketing/images/metrics.

Tokens: white `#fff`, sidebar `#f6f8f9`, primary `#12665f`, text `#1c2d38`, muted `#63757e`, line `#dfe6e9`, selected `#e2f5f2`, radius 6px. Sans-serif UI: 48px page title, 32px patient title, 20px detail facts, 16px controls/navigation, 15px table/tabs, 14px utility text. Native code text, controls and outline navigation icons; no raster screenshot masquerading as UI.

Responsive: desktop 224px navigation, open table and 450px detail; narrow screens stack navigation/content/detail, horizontally scroll the table inside its region, and place date controls in two columns with a separate update row. Native Frappe services enforce all authority; UI visibility is only presentation.

Intentional functional deviations from the generated reference: actual runtime fixtures determine row count/names/state; future Pending sessions display Prenotata; business reason is mandatory, overriding the concept's optional placeholder; guarded print control and authorized reopen/waiver actions implement approved capabilities; success/denial banners reflect real API results. Date formatting follows browser locale. Patient/package dropdowns use labels and available balance, not raw implementation identifiers.

Verification uses Playwright because the Browser plugin is unavailable. The QA image is pinned `mcr.microsoft.com/playwright:v1.58.2-noble@sha256:6446946a1d9fd62d9ae501312a2d76a43ee688542b21622056a372959b65d63d`. It supplies browser libraries absent from the host; it is a test tool, not an application dependency.

Fidelity ledger: sidebar width/background and navigation alignment preserved; white/teal palette preserved; 48px title and 32px detail hierarchy preserved; table/detail divider and selected-row treatment preserved; primary/header/button anatomy preserved; desktop and 390px mobile inspected with `view_image`. Fixes made: header/table/detail alignment, mobile grid minimum-width overflow, unclipped mobile date controls, padded times, cryptographic idempotency key on HTTP DEV origins. Native-size comparison: 1536×1024. Dynamic rows and added supported actions are the intentional deviations above.
