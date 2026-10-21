# Security results — #148

Status: **PARTIAL / NOT_VERIFIED for live authorization**. No real patient data, provider or shared Site was accessed. No backend security or schema code was altered.

| Control | Evidence | Status |
|---|---|---|
| Frappe page Guest gate | `www/premium.py` redirects Guest to login; source inspection only | NOT_VERIFIED live |
| Operational or finance role page gate | controller checks `require_actor()` or finance `allowed()` | NOT_VERIFIED live |
| CSRF / same-origin POST | `src/api.ts`, synthetic Playwright asserts header and payload | PASS mocked; live NOT_VERIFIED |
| UI route hides unauthorized finance | finance bootstrap 403 synthetic; direct `#Finanza` synthetic test | PASS mocked; server API NOT_VERIFIED |
| Center/patient/practitioner/notes isolation | existing domain endpoints invoked | NOT_VERIFIED on React candidate |
| Generic `/api/resource` writes | none in React source; network test sees none | PASS on synthetic tested paths |
| Finance, CSV/export, direct URL negatives | #139 historical tests available | NOT_VERIFIED on React candidate |
| Provider calls | none added; only fiscal status read, no send action | PASS source review; runtime NOT_VERIFIED |
| Dependency vulnerabilities | npm audit snapshot: 0 | PASS snapshot only |
| Client error rendering | React escapes string content; server HTML stripped in API error string | source review; hostile-data test NOT_VERIFIED |
| Public first meeting | React sends only route, slot and identity to existing rate-limited Guest service; no patient/practitioner identifiers | PASS synthetic payload; live rate limit, identity matching and permissions NOT_VERIFIED |

The UI never grants permissions by hiding controls. `finance.reporting.bootstrap` and all mutation services must be tested server-side for each role and cross-center attempt before READY. The existing `frappe.client.get_list` notifications projection needs direct permission review. #139's 38/38 is historical and must be rerun against the installed React candidate in an Owner-authorized isolated environment, with synthetic fixture fingerprint and cleanup.
