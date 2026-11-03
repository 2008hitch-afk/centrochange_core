# Experience-first delivery — user outcome before database structure

## Decision

EMPV applications must be designed around **the people who use them and what they need to accomplish**, not around tables, DocTypes or form fields. A technically correct app that is hard for an operator to understand is **not** ready for Owner UAT.

**Mandatory order for UI-impacting work:**

1. **Business outcome and actor.** Who is doing what, in what context? Derive this from the authorized handoff/brief, not by inventing a customer persona.
2. **Task journey.** Entry point → actions in ordinary language → necessary inputs and defaults → success confirmation → exceptions and recovery. Distinguish frequent quick actions from advanced configuration.
3. **Interaction and visual design.** Compose the page for that journey using the already-approved Product Identity; reuse controls, not every form layout. Modern aesthetics support clarity but cannot substitute for it.
4. **Backend mapping.** Identify native DocTypes/APIs, permissions, validation and money/ledger sources **behind** the experience. Frappe/ERPNext, Laravel or other approved systems remain authoritative; do not duplicate data or bypass invariants.
5. **User-task test.** A real/browser simulation of the task with meaningful user actions and correct readback. Test negative conditions; a green unit test, a beautiful screenshot or a JSON declaration alone cannot certify usability.
6. **Independent UX review.** A reviewer separate from the implementer verifies real task completion, labels, progressive disclosure, required-input burden, navigation and error recovery. Fix until the Goal is genuinely ready; the Founder accepts it in one walkthrough.

## Required per-interface contract

Within the approved design contract, each relevant interface must include:

- `user_role`: authorized operator/persona in the brief (not a guessed demographic)
- `user_goal`: desired result as the operator would describe it
- `entry_point`: where the task begins
- `primary_action`: what the user wants to do
- `success_outcome`: observable user result, linked to persisted backend state when relevant
- `journey_steps`: ordered, human-readable interactions (minimum two)
- `backend_mapping`: where records, validation, permissions and authoritative values live
- `technical_fields_policy`: which system-only fields are hidden/defaulted/advanced and why

Existing design evidence (`reference_screenshot`, `reference_mobile_screenshot`, `layout_rationale`, `visual_identity` and `user_journey`) remains required. For each `uat_results`, provide `user_task_test` with `status=PASS`, a user-language `scenario`, and a real `evidence` path. The independent `design_review.checks` must also PASS `user_task_completed`, `plain_language`, `minimum_user_input`, `backend_complexity_hidden` and `error_recovery`.

**Fail when:** only database fields are listed; an ordinary operator must type native record IDs/account codes without task justification; a known customer workflow (e.g. uploading a finished PDF) is not represented; a financial status is misleading; the user sees generic CRUD instead of the required task; or usability is marked PASS without an actual task scenario and evidence.

## Example: client offer workflow

`Customer wants to register an already prepared official offer PDF` is a different task from `Salesperson wants to create a native Quotation`. The UI may offer both paths. The first can attach a private native Frappe File to the relevant authorized document without pretending that an upload created a submitted Quotation. The second uses the native Quotation workflow. Neither should require the operator to know internal customer IDs or tax-template names just to start.

## Avoid both extremes

- **Not database-first:** do not equate a native backend DocType with a UI form.
- **Not arbitrary custom backend:** user-friendly frontend does not justify bypassing a native workflow, permission or accounting rule.
- **Not anti-table:** lists and tables are valid for comparison/bulk tasks, but should not be the only interface for every kind of job.
- **Not approval-heavy:** the Founder approves initial design identity and genuine scope changes; the agent handles ordinary screen decisions, review and retests autonomously.

## Honest enforcement

The Factory CLI and CI validate declared contract fields, file existence, PASS results and reviewer-name separation. They **cannot** establish that a real human completed a task, that a reviewer was genuinely independent, or that a screen is aesthetically good. External trusted review, branch protections and Owner UAT remain required. For projects bootstrapped before this revision, migrate explicitly instead of silently overwriting a project's configuration.
