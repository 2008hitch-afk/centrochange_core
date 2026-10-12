# Centro Change — Owner-selected premium visual direction (2026-10-12)

**State:** `OWNER_APPROVED_VISUAL_DIRECTION` for the visual approach; **NOT** `OWNER_VISUAL_PASS`, **NOT** GOAL-02 closure or PR merge approval.

**Trace:** Issue #75; PR #126 DRAFT; earlier Owner approval of native Frappe customization first, dedicated Frappe UI only when justified, Tabler as visual reference only; Owner visual review in the conversation of 2026-10-12. The Owner selected the latest **"Frappe native + real Nexus CSS extracts"** prototype and said **"Sì procediamo per questa strada"**. Older freehand "Nexus Studio" and "Solvronix" mockups were explicitly *not* accepted as a sound implementation model because they lacked reused library code.

## 1. Non-negotiable implementation decision

Implement Centro Change as an **extension of its already-pinned Frappe/ERPNext app**, not a fork or replacement frontend. Prefer native DocType Form/List, Customize Form / bounded Property Setter, `doctype_js`, `doctype_list_js`, translations, supported hooks and Desk Pages. Use a dedicated Frappe Page only if the native interaction genuinely cannot deliver the authorized workflow, preserving the canonical API, data and permissions. No new Bench/Site/DB or parallel frontend.

**Use real, selected, Frappe-compatible CSS from the Nexus Theme codebase where it helps**—especially palette/theme tokens, focus/shadow tokens and native Frappe field/list density. Do not install all of Nexus Theme and do not add its alternate navigation, command palette, theme editor, sounds, permission inspector, `Theme User` role, app launcher or hooks. It is a **source for selected components and styles** to be reviewed and adapted, not an authorization to install the third-party Frappe app.

**Provenance and license (must retain in redistributed derivatives):**
- Nexus Theme v16 repository: https://github.com/abbas0444/nexus_theme/tree/version-16
- Reference branch commit at selection: `5e6615bf759b8cae80fb52c6e4249eeb45133940`.
- CSS sources examined: `nexus_theme/public/css/theme_variables.bundle.css`, `nexus_theme/public/css/density.bundle.css` and `nexus_theme/public/css/sidebar_skin.bundle.css` (the sidebar skin targets native `.body-sidebar` and **must not** simply be dropped over Centro Change's own sidebar).
- MIT copyright 2026 Abbas Raza; carry upstream copyright, attribution and complete required MIT notice for any adapted portions.
- Do **not** require Tabler installation, CSS classes or JS; Tabler remains a moodboard only.

## 2. Approved visual reference and fidelity

The approved reference is the interactive HTML artifact from the Owner/ChatGPT visual review, titled **"Centro Change · Prototipo Frappe nativo + Nexus CSS"**. It is a **local conversation artifact**, not yet a code implementation or GitHub file. Retrieve the source HTML and images from the Owner's Codex handoff if they are supplied; **do not pretend to have opened an inaccessible sandbox URL**. This document contains enough constraints to implement the same direction on real Form/List views.

Selected appearance:
- A dark, quiet forest-green **single left sidebar**, with visible, restrained role-appropriate Italian navigation and meaningful selected-state contrast.
- Light grey/neutral canvas; disciplined white surfaces with subtle borders and almost no decorative shadows.
- Typography with distinct title/section/field hierarchy; compact functional controls; no oversized KPI cards, cartoon-style decoration, glossy gradients or generic dashboard kits.
- Centro Change institutional accent **`#12665F`**; do not introduce additional unrelated brand colours or fake client logos.
- One minimal upper line for context/account, no double app bar and no duplicate "Centro Change" label.
- High-density but readable forms and tables; **Comfortable** baseline, optional **Compact/Spacious** if compatible with Frappe and accepted; use genuinely supported Frappe design tokens/selectors where possible.
- Responsive screen composition including a clear mobile menu without horizontal overflow.
- Technical Administrator Desk remains separately usable. No ERPNext/Frappe/Marley logo flashing before/during navigation for client roles.

**Design anatomy: real Item / Servizio form**
1. Small route/back link: `Catalogo servizi › Seduta`.
2. Readable human label **Seduta**, status **Abilitato**, compact contextual edit action. Raw `CC-HTTP-UAT...` identifier only in a secondary, deliberate technical-details disclosure; never replace canonical stored IDs.
3. Few contextual tabs: **Dettagli**, **Tariffe**, **Collegamenti**—only if each represents real authorized data/functions; don't create a tab with non-functional placeholders.
4. Main native Form column with **Informazioni principali**: service name, relevant category, state, useful description, and duration **only if the canonical data actually provides it**. Use actual DocType fieldnames and supported Form layout controls.
5. **Utilizzo nel centro** groups existing relationships to `Appointment Type`, `CC Center Service` and canonical `Item Price` where valid and authorized. Do not fabricate relationships or alter scheduling/price rules to fill the screen.
6. Right summary **Riepilogo / Strumenti**, available only where useful and robust on native Form; on smaller widths it may stack instead.
7. Avoid upstream Item's irrelevant stock movement heatmap, Accounting, Tax, Purchasing, Quality, raw Sales/Buy workspace tabs, technical assignments/timeline or tag/share chrome in routine client views **when business relevance and role checks confirm they are unnecessary**. Do not remove ERPNext data, fields needed for validation, underlying documents or functions needed by authorized Finance/Administrator users. Prefer native configuration, scoped supported client scripts and defensive, non-global presentation refinements. Document any structural form limitation that genuinely requires a dedicated page.
8. When editing and saving, the **real native Frappe form** must continue to use the canonical lifecycle, mandatory fields, validations, audit, document permissions and backend.

**Design anatomy: Catalogo servizi native List**
- Clear title and compact action; native search/filter/sort and keyboard accessibility.
- Consistent row density; readable Italian human labels; status and price/related data only if they are authorized and actually present.
- Open a genuine Item Form and return to list, respecting history/refresh.
- Preserve native create/edit permissions; no fake buttons.

**Do not turn reference mock values into implementation facts.** Example patient/service counts, sample prices, duration and demo identifiers from the prototype were illustrative.

## 3. Rollout within the existing approved issue scope

1. **Prove the reference first on real Frappe**: Item native List **and** Item native Form for the roles that legitimately see them; preserve the current sidebar and app data. Use the exact design language above, rather than drawing another standalone HTML app.
2. **Apply the same design rules to the other already-approved native surfaces in issue #75:** Item Price; Patient; Healthcare Practitioner; appointment/service/package configuration only when exposed; Sales/Purchase Invoice; Payment Entry; Bank Transaction. Per-role presentation must respect business needs, not blindly suppress financial/clinical/administrative fields. If a field is required to save, it cannot be hidden as a workaround.
3. Keep the existing dedicated Agenda, Finance, reporting and Home pages; normalize shared look/feel where necessary, **without rewriting operational UI solely to adopt a third-party component**.
4. Include the separately recorded **upstream ERPNext/Frappe branding flash defect** from #75: fix the actual early-loading origin; add browser video/trace coverage from before initial document creation. Existing post-shell DOM assertions are insufficient. Do not mask loading with a blank overlay.
5. Write source attribution for MIT-derived CSS, pin provenance; test against pinned Frappe/ERPNext 16.50.0 and Healthcare 16.6.1, preserving deploy reproducibility.

## 4. Visual and functional acceptance evidence

On the sole existing `centrochange-dev` stack (1 Bench, 1 Site, 1 DB, demo synthetic records unchanged):
- Screenshot/video and real browser steps for **List → Item Form → authorized Edit → Save → List**, including tabs, responsive layout, keyboard focus, error/empty/loading states and role differences.
- Before/after comparisons for the specific clutter reported by the Owner (ERPNext Item stock activity, useless tabs, user actions/sidebar, technical IDs), **not just a final DOM pass**.
- Test Administrator native technical access separately; no new permissions, shortcuts around authorizations or cross-role leaks.
- Record each native form's actual fields, what was shown/hidden for each role, and why; validate financial and medical permission boundaries.
- Trace early-loading brand leak with captures from navigation start, SPA transitions, redirects and reloads, not only post-render screenshots.
- Preserve runtime services, package pin, synthetic dataset integrity; no reset, no production, no real SdI/TS, no new app install, **no merge**.
- Update issue #75 and PR #126 DRAFT with evidence, truthful residuals, commit/deployed image SHA.

**Completion label:** `CENTROCHANGE_PREMIUM_NATIVE_UI_READY_FOR_OWNER_REVIEW` only after implementation on the real Site and passing relevant tests. **Never** declare `OWNER_VISUAL_PASS` or GOAL-02 complete without subsequent explicit Owner acceptance.

## 5. Decision boundary

The Owner has approved **this visual direction and an implementation path using existing/native Frappe plus selected Nexus-derived styling**. This does **not** authorize wholesale Nexus installation, new Frappe roles, replacing finance/security workflows, hidden state changes, merging existing draft PR chains, or changing source ERPNext code directly. If substantial scope/permission changes become necessary, document alternatives and ask the Owner.
