# #76 — Client debranding and proposed identity

## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

Authorized neutral debranding PASS across login/logout/404/app/print. Versioned clear-cache fixes persisted old website hook cache. UI-IDENTITY-PROPOSAL remains PROPOSED, not approved or applied transversally.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

PARTIAL: authorized neutral debranding implemented; browser acceptance pending; identity proposal explicitly awaits Owner decision before transversal application. docs/uat/UI-IDENTITY-PROPOSAL.md.

Native-first supported `update_website_context`, web_include_css and app website templates. Pinned Frappe 16.31.0 `BaseTemplatePage.post_process_context` calls hook after native login context, so logo/name overrides do not require login/auth patches. Native error rendering uses app templates and retains HTTP status. No core changes, auth changes or grant. Technical asset paths remain implementation dependencies, not visible product branding. Native Desk is not rebranded; client-facing links removed. No new print/export rights; direct unauthorized print/download tested in #77.

Official reference: https://docs.frappe.io/framework/user/en/python-api/hooks and https://docs.frappe.io/framework/user/en/portal-pages ; pinned source checked for website context, native login and error template resolution. Browser/runtime is discriminating proof.

Runtime rc26 first browser probe detected persistent Redis hook cache retaining prior login branding despite matching image bytes. The versioned candidate deployment now runs native bench clear-cache after controlled application restart; no schema migration or manual patch. Recheck required on rc27.
