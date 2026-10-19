# Reconciliation before the next DEV-first update

Read-only verification on the existing `centrochange-dev` Site at 19 October 2026. This does not rewrite the previous `ROLLBACK_FAILED` result.

- `CC Admin Exception p4331eu4v5` is `Closed`, with its historical `CC Incoming Invoice oqgogla0e5` reference retained. That synthetic source is absent. The resolution timestamp is 20:00:04 UTC and the reason explicitly identifies the absent source.
- `CC Audit Event 8taij6e6q0` is `ADMIN_EXCEPTION_AUTO_CLOSED`, authored by the synthetic automation service. Its recorded transition is `Open` → `Closed` for that exact queue document. The event timestamp is 22:00:04 in the Site's local time.
- Zero new `GL Entry`, `Payment Ledger Entry`, `Sales Invoice`, `Purchase Invoice` and `Payment Entry` records were created since the failed update started at 19:57:31 UTC. The earlier comparison also found unchanged Communication, database identity, schema, permissions, six hooks and operational center states. No unexplained difference was found in the monitored data.
- Current Owner/data fingerprint is `f5cea384c350dc8780818ccec752a314885085b8f14afb49a9c34115fa68b517`. It supersedes the old fingerprint **only as the verified starting checkpoint for the newly authorized update**. The audit event is preserved.

The corrected candidate is based on application commit `a03386c41a78692fd4b6d370ec56b1d21d613841`. The executor now copies the Nginx template as `0644`, proves it readable by `frappe`, validates `nginx -t`, and confirms an isolated frontend remains running before any DEV service is stopped. The isolation uses no network, shared volume, Site data or published port. The old `0600` image fails the runtime-user read; the old baseline and corrected image pass. This is a preflight proof, not a live installation result.
