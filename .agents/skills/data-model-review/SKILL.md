---
name: data-model-review
description: Canonical Data Model Reviewer; Before every new entity, table, DocType, field, interface contract or migration.
---

# Canonical Data Model Reviewer

**When required:** Before every new entity, table, DocType, field, interface contract or migration.

## Execution contract

1. Read approved project scope, project `AGENTS.md`, `factory/contract.json`, `factory/state.json`, Issue, previous approved decisions and dependencies.
2. Find authoritative data sources and existing equivalents. Distinguish valid snapshots from duplicates; assess permissions, migration impact and every connected UI.
3. If any authorization, scope, permission or prerequisite is absent, stop safely and log a specific blocker rather than inventing a decision.
4. Produce: data model, data lineage, role matrix and impact assessment. Attach files, test outputs and relevant Issue/PR/commit SHA.
5. Report what you actually inspected and executed, with evidence paths. This report is an **assertion** until an independent process authenticates it.

## Do not do

Do not duplicate Discovery, fabricate a PASS, change scope or schema silently, access real client data, include secrets, or merge/deploy without approval. Do not consider reading this skill proof of having executed it.
