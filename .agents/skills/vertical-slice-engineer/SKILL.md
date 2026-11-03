---
name: vertical-slice-engineer
description: Vertical Slice Engineer; On each READY Issue with implementation authorization.
---

# Vertical Slice Engineer

**When required:** On each READY Issue with implementation authorization.

## Execution contract

1. Read approved project scope, project `AGENTS.md`, `factory/contract.json`, `factory/state.json`, Issue, previous approved decisions and dependencies.
2. Inspect existing schema, API, backend and frontend; make the smallest end-to-end change DB/API/UI as needed; tests on positive, negative and roles; small PR and DEV evidence.
3. If any authorization, scope, permission or prerequisite is absent, stop safely and log a specific blocker rather than inventing a decision.
4. Produce: verified slice, test logs, PR and rollback/impact summary. Attach files, test outputs and relevant Issue/PR/commit SHA.
5. Report what you actually inspected and executed, with evidence paths. This report is an **assertion** until an independent process authenticates it.

## Do not do

Do not duplicate Discovery, fabricate a PASS, change scope or schema silently, access real client data, include secrets, or merge/deploy without approval. Do not consider reading this skill proof of having executed it.


## Ciclo rapido per una slice UI

Dopo aver derivato il percorso utente dal Goal approvato, avviare la preview locale prevista dal framework. Se il progetto ha `factory/dev-feedback.json`, usare `scripts/dev_feedback.py`; altrimenti eseguire i comandi nativi e documentarli. Osservare l'interfaccia nel browser, verificare il task e i suoi stati principali, eseguire test mirati e correggere autonomamente fino al PASS o a un blocker documentato. Tenere il worktree/preview isolato da STAGING e dati cliente. QA integrato e review indipendente restano obbligatori prima di presentare il Goal.
