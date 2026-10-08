# #77 — Final permissions

## Superseding checkpoint — 2026-10-08

**TECHNICAL PASS / READY_FOR_OWNER_UAT. OWNER VISUAL ACCEPTANCE PENDING.** Final-candidate server-side positive/negative permission-neutral matrix; seven roles + Guest, direct/API/query/export/native-print/cache-switch and rollback revocation.

Candidate `goal02-20261008-rc21`, source `c51a9e7a1f887b87c0b06872a8d3e94f2e7249f5`; PRs #92 → #93 → #94 are draft/unmerged and all issues remain OPEN. No permission/business/schema delta or dataset reset.

See [complete conformity and runtime evidence](../ui-design-system-v1/CONFORMANCE.md). Earlier checkpoints below are historical; identity-pending claims are superseded by Owner-approved Design System v1, not by a new branding inference. No GOAL-03.


## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

10 rollback security checks and 8 browser checks PASS for seven roles and Guest, API/query/direct/export/print/private notes, membership/assignment revocation. Private download cache replay fixed with supported after_request no-store policy; permission delta NONE.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

PARTIAL pending integrated runtime/HTTP matrix and Owner review. Branch `issue-77/final-permission-review`, base #76. Versioned final role matrix and rollback-only governed revocation tests added. No permission-model change. docs/uat/FINAL-PERMISSION-MATRIX.md. Native API/query/export/print/download and UI probes included in browser review; no hiding-only authorization claims. No real transport or dataset reset.

Verified runtime cache regression: after Manager fetched a retained TS payload, the same browser cache returned HTTP 200 after switching to Professional. Repeating with `fetch(cache:no-store)` reached the server and correctly returned 403. Pinned native `frappe/utils/response.py:send_private_file` deliberately sets `private,max-age=3600,stale-while-revalidate=86400` for X-Accel downloads. The supported after_request hook now sets no-store for private downloads and scoped API/pages. This preserves native authorization decisions; NO role, grant, scope or permission-model delta. Default-cache browser account-switch replay is now a required regression. Native source and docs https://docs.frappe.io/framework/user/en/python-api/hooks (after_request), runtime discriminant recorded.
