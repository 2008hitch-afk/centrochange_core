# UI Quality Gate v1.1 — mandatory for UI-impacting Goals

## Purpose
Prevent a shipped feature from quietly replacing an Owner-approved experience with generic CRUD/forms. UI is the frontend experience; a native backend (such as Frappe/ERPNext) remains authoritative for data and operations. Native-first does **not** mean rendering the native database schema as the primary user interface.

This gate applies to every `ui_impact=YES` Goal (FOUNDATION, FEATURE, MAINTENANCE, RELEASE) before `READY_FOR_REVIEW`; it introduces **no per-screen Founder micro-approvals**.

## Experience First: non-negotiable

The task journey must be derived from a real user role and business outcome **before** deciding which Frappe/ERPNext DocType fields are visible. Each interface contract additionally declares `user_role`, `user_goal`, `entry_point`, `primary_action`, `success_outcome`, `journey_steps` (at least two), `backend_mapping` and `technical_fields_policy`. See [Experience First](EXPERIENCE-FIRST.md). A design reference alone cannot prove a flow is understandable or useful.

## Before implementation
- Enumerate affected routes/screens and the actual user task for each.
- Record an Owner-approved design baseline in a versioned JSON file inside the project. Set `goal.ui_design_contract` to this file, `goal.ui_interfaces` to the impacted screen IDs.
- The contract must include `status: APPROVED`, `approval_ref`, `design_id` and `interfaces` containing `interface_id`, real `reference_screenshot` and `reference_mobile_screenshot` paths, `user_journey`, `layout_rationale`, and `visual_identity`. Screens not affected by this Goal may also be present.
- Art direction is Founder-approved **once**, and subsequent features reuse the baseline. If the identity must change, set `ui_identity_change=YES`, document the new Owner approval in `approvals.ui_identity_change`, update the baseline approval reference and execute `product-art-director`.
- Until design has been approved, do not assert `READY_FOR_REVIEW`. A proposed concept is not an approved reference.
- UI should be task-centred: use compositional screens for dashboard, customer, quotes, projects, calendar etc. Shared low-level inputs/tables are encouraged; a universal database-field form is not sufficient for a task workflow unless independently justified.

### Approved design baseline example (synthetic paths only)
```json
{
  "status": "APPROVED",
  "approval_ref": "decision:founder-design-001",
  "design_id": "studio-v1",
  "interfaces": [
    {
      "interface_id": "quotation",
      "reference_screenshot": "design/approved/quotation-desktop.png",
      "reference_mobile_screenshot": "design/approved/quotation-mobile.png",
      "user_journey": "Find the client by name, upload official PDF or compose native quotation without ERP IDs",
      "layout_rationale": "Two clearly distinguished entry paths, contextual customer summary and natural-language fields",
      "visual_identity": "Approved Studio typography, navigation, spacing and hierarchy",
      "user_role": "Commercial operator",
      "user_goal": "Record an official client quotation without ERP training",
      "entry_point": "Client page",
      "primary_action": "Upload a prepared PDF or create an offer",
      "success_outcome": "Offer document is stored and visible under the authorized client",
      "journey_steps": ["Find a client by name", "Choose upload or guided creation", "Confirm and open the saved result"],
      "backend_mapping": "Frappe Customer, private File and Quotation when a native quotation is created",
      "technical_fields_policy": "Customer IDs, internal price list and account mappings are not routine user inputs"
    }
  ]
}
```
The screenshot must actually exist; merely writing this example is not evidence.

## Implementation and review
- Apply `ux-prototyping` and `premium-ui-reviewer` to **every UI-impacting Goal**, not only FOUNDATION. Record execution evidence for both. `product-art-director` is required for changed identity; FOUNDATION also retains its existing required skills.
- Run per-interface UAT against relevant backend/API, desktop/mobile, states and permissions as already defined in `docs/AUTOMATED-OWNER-UAT.md`.
- For every `uat_results[]` entry add `design_review` with `status=PASS`, `commit_sha`, independent `reviewer`, `evidence`, `comparison` report (approved references versus actual desktop/mobile screenshots), plus `screenshot` and `mobile_screenshot` in the UAT entry and all five PASS checks:
  `workflow_fit`, `approved_visual_fidelity`, `information_hierarchy`, `user_friendly_forms`, `responsive_quality` plus experience checks `user_task_completed`, `plain_language`, `minimum_user_input`, `backend_complexity_hidden`, `error_recovery`. Each UAT entry also needs `user_task_test: {status: PASS, scenario: ..., evidence: ...}` showing a complete user-facing task.
- The reviewer must verify the user can complete the intended outcome without ERP field knowledge unless the workflow genuinely requires it, and must be separate from the implementer and must **reject** generic admin tables/forms that hide the intended user journey, missing upload workflows, untranslated technical fields, visually regressed layouts or fake financial metrics.
- Comparisons must document significant differences, what was accepted, and what was fixed. Pixel-perfect equality alone is neither necessary nor sufficient; human visual judgement is essential.

## Enforcement and limits
- `scripts/goal_factory.py validate-goal --root . --goal GOAL-ID` fails structurally when the baseline, references, UI skill claims, independent design reviews or comparisons are missing, mismatched, or not PASS.
- The generated-project CI runs `validate-project`, covering Goals in READY_FOR_REVIEW/VERIFIED. On a PR, `scripts/verify_ui_diff.py` compares changed source files to the base commit and **rejects React/CSS/UI source changes unless at least one UI-impact Goal is READY_FOR_REVIEW/VERIFIED**. The filename heuristic is intentionally conservative and does not prove exact route-to-Goal traceability.
- This is a **fail-closed structural gate**, not a visual AI evaluator. A file containing fictitious text still passes file-existence checks. A claimed second reviewer can be fake. Real screenshots, authentic approval and reviewer independence must be verified externally.
- Required GitHub branch protections, trusted CI and actual reviewer identities are NOT configured by bootstrapping. Project owner must enable them for mandatory pre-merge enforcement.
- `PASS_OFFLINE` or `PASS_LIVE` is not `OWNER_ACCEPTED`; only the Founder accepts the work, with one walkthrough per Goal. No automatic merge, production deploy, VPS changes, or access to real data.
- An existing project bootstrapped before this change needs an **explicit migration** of the new contract/schema, instructions and scripts, reviewed on a branch; never overwrite its project-specific decisions or sources automatically.


## Separazione del gate durante sviluppo e integrazione

`verify_ui_diff.py --stage draft` permette una normale PR Draft con UI modificata se esiste almeno un Goal UI in `ACTIVE` o successivo. Il test strutturale del Goal finale e la prova del design **non devono bloccare ogni modifica intermedia**.

`verify_ui_diff.py --stage ready` richiede invece un Goal UI in `READY_FOR_REVIEW`/`VERIFIED`. Il workflow generato esegue questo passaggio alla conversione Draft → Ready. Senza required checks attendibili e branch protection, la CI non impedisce tecnicamente il merge. Questo controllo è euristico sui percorsi e non verifica la corrispondenza esatta fra file modificato e Goal; la review indipendente rimane necessaria.

## Limite di tracciabilità del controllo file UI

Il controllo `verify_ui_diff.py` verifica attualmente **l'esistenza di almeno un Goal UI eleggibile**, non che ogni file React/CSS modificato sia davvero assegnato a quel Goal. Per una PR con più Goal questa è una lacuna di tracciabilità e non va presentata come controllo completo del perimetro: il reviewer deve confrontare il diff effettivo con l'inventario delle interfacce, i requisiti e gli `uat_results`. Un futuro gate per-file richiede un'associazione verificabile fra path e Goal, senza false approvazioni sintetiche.
