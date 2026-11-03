---
name: qa-validation
description: Independent QA Validator; Each slice and integrated QA/UAT.
---

# Independent QA Validator

**When required:** Each slice and integrated QA/UAT.

## Execution contract

1. Read approved project scope, project `AGENTS.md`, `factory/contract.json`, `factory/state.json`, Issue, previous approved decisions and dependencies.
2. Map requirements×UI actions×API×roles×tests; execute suitable end-to-end and regression scenarios; record exact SHA/environment; mock not live.
3. If any authorization, scope, permission or prerequisite is absent, stop safely and log a specific blocker rather than inventing a decision.
4. Produce: coverage matrix, test reports, UAT result. Attach files, test outputs and relevant Issue/PR/commit SHA.
5. Report what you actually inspected and executed, with evidence paths. This report is an **assertion** until an independent process authenticates it.

## Do not do

Do not duplicate Discovery, fabricate a PASS, change scope or schema silently, access real client data, include secrets, or merge/deploy without approval. Do not consider reading this skill proof of having executed it.


## Verifiche a due velocità

In sviluppo: test dei percorsi modificati e diagnosi documentata degli errori `HARNESS`, `APP`, `AUTH`, `INFRA`, `DESIGN`. Il runner opzionale `scripts/dev_feedback.py test --suite NOME` riporta solo exit code e `PASS_LOCAL`: non apre o ispeziona la UI da solo. Prima della review finale: eseguire tutti i test previsti dal Goal, verificare API/backend reali nel clone autorizzato, baseline e screenshot desktop/mobile, permessi e persistenza, con reviewer realmente indipendente. Mai presentare mock o report strutturali come `PASS_LIVE`.
