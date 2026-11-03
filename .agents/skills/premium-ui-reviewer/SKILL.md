---
name: premium-ui-reviewer
description: Premium UI Independent Reviewer; During prototype validation and every relevant vertical slice, independently of developer.
---

# Premium UI Independent Reviewer

**When required:** During prototype validation and every relevant vertical slice, independently of developer.

## Execution contract

1. Read approved project scope, project `AGENTS.md`, `factory/contract.json`, `factory/state.json`, Issue, previous approved decisions and dependencies.
2. First independently execute the intended user's main task (not just compare screenshots). Check the actor/goal/journey from the approved Experience-First Contract against the real page and authorized backend; inspect required input burden, plain-language labels, defaults, hidden internal IDs, errors and recovery. Then check real work hierarchy, Founder-approved design references, task workflows, identity consistency, density, keyboard contrast, mobile, error/loading/empty, microinteractions and realistic long data. Reject generic CRUD/table/form-driven UI when it bypasses user workflow (not merely generic cards). Compare the actual desktop/mobile screenshots for each affected interface against approved baselines and record significant differences, acceptance and fixes.
3. If any authorization, scope, permission or prerequisite is absent, stop safely and log a specific blocker rather than inventing a decision.
4. Produce: independent, per-interface accessibility, task-fit and visual regression findings with comparison evidence, tested SHA and ten check results: visual/workflow (workflow_fit, approved_visual_fidelity, information_hierarchy, user_friendly_forms, responsive_quality) plus experience (user_task_completed, plain_language, minimum_user_input, backend_complexity_hidden, error_recovery). Attach files, test outputs and relevant Issue/PR/commit SHA.
5. Report what you actually inspected and executed, with evidence paths. This report is an **assertion** until an independent process authenticates it.

## Do not do

Do not duplicate Discovery, fabricate a PASS, change scope or schema silently, access real client data, include secrets, or merge/deploy without approval. Do not consider reading this skill proof of having executed it.
