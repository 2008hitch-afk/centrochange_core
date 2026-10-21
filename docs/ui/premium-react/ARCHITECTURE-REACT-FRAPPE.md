# React / Frappe architecture — #148

Status: **PARTIAL**, 2026-10-21. Branch `issue-148/premium-react-frontend` from PR #149 (`640b221`). No shared DEV, server clone, production or live data used.

## Boundary

`/premium` is a new Frappe `www` page. Its Python controller checks the Frappe session and operational/finance role before rendering; it provides a CSRF token. `/premium-primo-incontro` is a separate public React shell which uses only the existing guarded Guest first-meeting endpoints. Both HTML pages reference repository assets under `/assets/centrochange_core/premium/`. React calls same-origin `/api/method/centrochange_core.*` domain methods using the Frappe cookie and CSRF header for POST. Frappe, ERPNext, Marley Healthcare and `centrochange_core` remain authoritative. No frontend database, proxy token or generic Doctype write endpoint is introduced. `/centrochange`, `/finanza` and Desk are untouched and are **not** promoted as second product UI.

The Vite source is `frontend/premium/`; `npm ci --ignore-scripts` and `npm run build` reproduce checked-in static assets in `app/centrochange_core/centrochange_core/public/premium/`. Separate `app.js` and `public.js` entries share a generated React chunk; the public first-meeting page does not load the Agenda workspace entry. The local `index.html` and `public.html` are test-only and inject fake CSRF tokens. A production Frappe site did not serve this candidate: page resolution, reverse-proxy caching, Content-Security-Policy, real login redirect and bundled asset delivery are **NOT_VERIFIED**. The `www` convention is supported by [Frappe portal page documentation](https://docs.frappe.io/framework/user/en/portal-pages); that is architectural support, not runtime proof.

## Security and state

- The initial bootstrap calls are independent because finance-only and operations-only roles differ. Only server-permitted sections render. A direct hash such as `#Finanza` falls back when the finance bootstrap fails; this is a UI hint, not an access-control boundary.
- Domain endpoints retain their existing center/patient/finance guards. No server permission or DocType schema was changed. `frappe.client.get_list` remains only for the existing notifications projection and needs live permission review before acceptance.
- Mutations use existing audited service endpoints with CSRF and operation reasons. Booking uses a cryptographic request key. The frontend never sends real provider requests.
- Local time inputs are wall-clock fields; server scheduling remains authority for collisions, 48-hour policy and DST. Display date/time use Italian formatting and Europe/Rome for the current date. True browser/server DST behavior across all roles remains **NOT_VERIFIED**.
- Frontend endpoints are bounded by existing backend limits (agenda 93 days / 200 returned, patient search 50, finance report 500 composing records). The UI surfaces truncation where returned. Some finance records endpoint bounds require live review.

## Deployment and rollback contract

The candidate is source and static assets only. No Docker image, Frappe install, migration, restart or shared runtime mutation has occurred. DECISION-062 targets the single existing `centrochange-dev` deployment; no old laboratory runtime remains. `infra/Dockerfile.premium-single-stack` and `infra/compose.premium-single-stack.yaml` prepare an image-only replacement of the six application containers over the current pinned backend, subject to [the single Owner gate](SINGLE-STACK-EXECUTION-GATE-2026-10-21.md), proven backup and isolated restore. The old `premium148` Docker/Compose files are historical and **not approved**. Runtime rollback is **NOT_VERIFIED** because nothing was installed.

## Architectural gaps

The current SPA has one workspace HTML route plus hash sections and one public first-encounter route. It lacks approved master writers for catalog/tariffs/anagraphics, complete 11 native list/form equivalents, print parity, role-level navigation validation and a live Frappe integration test. `FUNCTIONAL-COVERAGE.md` and `SCOPED-MASTER-API-PROPOSAL.md` record these gaps; they prevent `READY_FOR_OWNER_VISUAL_UAT`.
