---
name: ux-prototyping
description: Experience-first, task-centred UX Prototyper; before implementation or choosing UI field layout.
---

# Experience-first UX Prototyper

**When required:** For every UI-impacting Goal. Start from the user task **before** finalizing UI layout or mapping backend DocType fields to visible controls. The approved product identity is reused; no new Founder decision for each screen.

## Guiding principle

**User outcome → real-world journey → UI composition → authoritative backend mapping.** Never start from the database schema to decide what the user sees. A native Frappe/ERPNext backend is the source of truth, **not** the frontend design system. Shared controls and tables are welcome when appropriate, but an auto-generated CRUD page is not by itself a good experience.

## Execution contract

1. Read the handoff, business goals, roles, real daily activities, approved decisions, product identity and relevant constraints (`AGENTS.md`, Factory contract/state, Goal Issue and dependencies). If the Owner has already supplied the workflow, **do not ask again**.
2. For each affected workflow, create an **Experience-First Contract** before JSX/forms: `user_role`, `user_goal`, `entry_point`, `primary_action`, `success_outcome`, human-readable `journey_steps`, `backend_mapping` and `technical_fields_policy`. Preserve the approved baseline's `user_journey`, `layout_rationale` and visual identity. Use one reusable contract per screen, not a new approval for every field.
3. Explain in task language what the user must know, what can be inferred/defaulted, and which technical fields may be hidden, automated or exposed only in an advanced view. **Never silently bypass server validations, DocPerm, financial semantics or legal requirements.** Avoid exposing internal record IDs, exchange-rate/account mappings or configuration as routine operator inputs unless a genuine workflow requires them.
4. Build representative clickable task flows with realistic synthetic data and success/error/empty/loading states; account for dense long records, desktop/mobile, accessibility and recovery from mistakes. Use progressive disclosure, contextual defaults and user-language labels. Do not turn all business pages into the same generic table or form.
5. Derive UAT scenarios **from the customer's intended task, independently of the implementation**. Record the actions a nontechnical user can take, expected business outcome and test evidence. Test at least one complete primary journey per affected screen against the authorized environment, including data persistence/readback when applicable. Review confusing required fields and avoidable steps.
6. Deliver a concise workflow report with the experience contract, prototype, evidence paths and relevant commit/Issue/PR. An independent `premium-ui-reviewer` assesses actual usability as well as visual fidelity. The validator sees only structural evidence; it does **not** independently verify test authenticity or subjective UX quality.

## Example: quotation handling

- Bad: render Quotation.party_name, selling_price_list, company, tax template and Item codes as a raw ERP form.
- Task: "I have a signed-off offer PDF; register it against a client", or "I need to prepare an offer".
- UI: search client by name, choose upload versus guided creation, prefill safe defaults, preview outcome, confirm and open the saved native record.
- Backend: use Frappe File and native Quotation where appropriate, permissions and server-side validation.
- Test: a business operator completes the flow without knowing an ERP record ID; stored links and visibility are verified on Frappe.

## Do not do

Do not fabricate customer requirements, hide legally important data, duplicate Discovery, change approved Product Identity without a decision, treat screenshots as usability proof, fake test PASS, alter scope/schema, access real customer data without authorization, expose secrets, or merge/deploy without approval. Reading this skill is not evidence that the workflow has been executed.


## Preview rapida di pattern UX

Se il framework supporta Live Preview, mostrare e verificare un percorso rappresentativo sul browser prima di propagare un nuovo pattern a molte interfacce. Controllare casi lunghi, error/empty/loading, mobile e confronto con la Product Identity approvata. La preview riduce il rework, ma non sostituisce la design review indipendente né richiede nuove micro-approvazioni Founder per ogni controllo visivo ordinario.
