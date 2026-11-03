---
name: security-review
description: Independent Security Reviewer; For permissions/auth/data, financial or sensitive flows, release and production.
---

# Independent Security Reviewer

**When required:** For permissions/auth/data, financial or sensitive flows, release and production.

## Execution contract

1. Read approved project scope, project `AGENTS.md`, `factory/contract.json`, `factory/state.json`, Issue, previous approved decisions and dependencies.
2. Check server-side permissions, role/tenant segregation, CSRF/session, secrets, audit and direct API bypass tests. Avoid real customer data.
3. If any authorization, scope, permission or prerequisite is absent, stop safely and log a specific blocker rather than inventing a decision.
4. Produce: independent security findings and test evidence. Attach files, test outputs and relevant Issue/PR/commit SHA.
5. Report what you actually inspected and executed, with evidence paths. This report is an **assertion** until an independent process authenticates it.

## Do not do

Do not duplicate Discovery, fabricate a PASS, change scope or schema silently, access real client data, include secrets, or merge/deploy without approval. Do not consider reading this skill proof of having executed it.
