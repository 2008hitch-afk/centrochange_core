# #76 — Client debranding and proposed identity

PARTIAL: authorized neutral debranding implemented; browser acceptance pending; identity proposal explicitly awaits Owner decision before transversal application. docs/uat/UI-IDENTITY-PROPOSAL.md.

Native-first supported `update_website_context`, web_include_css and app website templates. Pinned Frappe 16.31.0 `BaseTemplatePage.post_process_context` calls hook after native login context, so logo/name overrides do not require login/auth patches. Native error rendering uses app templates and retains HTTP status. No core changes, auth changes or grant. Technical asset paths remain implementation dependencies, not visible product branding. Native Desk is not rebranded; client-facing links removed. No new print/export rights; direct unauthorized print/download tested in #77.

Official reference: https://docs.frappe.io/framework/user/en/python-api/hooks and https://docs.frappe.io/framework/user/en/portal-pages ; pinned source checked for website context, native login and error template resolution. Browser/runtime is discriminating proof.
