# Centro Change — Missione A: gate pre-merge G2 per le 35 PR

**Data:** 2026-10-08  
**Stato:** `PLAN_READY / OWNER_GATES_PENDING / NO_MERGE_AUTHORIZATION`.  
**Scopo di questa versione:** predisporre il passaggio operativo da simulazione locale PASS a consolidamento remoto CONTROLLATO. Questa preparazione **non autorizza merge** né modifica runtime/server/site/DB.  
**Tracker:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95).  
**Simulazione autorizzata e conclusa:** [Codex 35/35 report](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6065380981), [HITCH review](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6065479993).  
**Manifest statico SHA e piano trial:** [MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md](MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md).

## 1. Snapshot verificato dopo la rehearsal

| Controllo | Stato |
|---|---|
| 35 PR prodotto stacked | #27 → #98 tutte OPEN/DRAFT, nessuna merged |
| PR documentale #96 | OPEN/DRAFT; da gestire **separatamente** |
| `main` | SHA `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`; repository private, `protected=false` |
| HEAD ultima PR #98 | `9d12f5e06df92ed35de843b882f3a40e82c02b19` |
| Rehearsal Codex solo locale | 35/35 PASS, product tree finale `5eb8051fe36eabcf7a897e2f91d8a97e6918298c`, uguale a `app/centrochange_core/centrochange_core` su #98 e verificato con API tree GitHub |
| Sei commit unici di main | PRESERVATI secondo ancestry riferita da Codex, da verificare anche nel merge effettivo |
| App security fix #97 | Presente nella #98; sei before_request app guards, nessuna duplicazione (test del Codex) |
| GH Actions | Nessun `.github/workflows/` nel tree osservato; `check-runs` su HEAD #98 = 0 |
| Webhooks / CI esterna / autodeploy | **NON VERIFICATO**. API GitHub dei hooks non disponibile dal connettore di questa chat; va verificato via ambiente host/CLI autorizzato o UI proprietario prima di qualsiasi push/merge |
| Gate Agenda RC22 Owner #75 | **PENDING**, ultimo commento richiede retest visivo settimane 5–11 ottobre e 28 settembre–4 ottobre, desktop e scroll |
| Build/runtime post-merge | **NON PROVATI** dalla rehearsal Git (solo static checks) |
| Owner autorizzazione merge | **NON CONCESSA**; “ok procediamo” in chat avvia questo preflight, non e' approvazione finale di un merge remoto |

## 2. Preflight operativo consentito: READ-ONLY remoto + locale isolato

L'Owner ha chiesto di procedere al prossimo passo. Prima dei merge effettivi si raccomanda una missione Codex che non esegue ne' muta PR, main, server o UAT. Il mandato per il preflight non estende alcuna precedente autorizzazione.

1. **Git provenance:** `git status`, branch attuale, remotes, SHA di main/#94/#98 e di ciascun HEAD delle 35 PR. Fermarsi se qualunque SHA cambia. Non fare `git reset` o modificare il checkout operativo.
2. **Remote-trigger audit:** dall'host Codex, con `gh api` READ-ONLY se permessi disponibili, verificare webhooks repository (`GET repos/2008hitch-afk/centrochange_core/hooks`), GitHub Actions workflows/runs, branch protections/rulesets nei limiti del piano GitHub, e ogni automation esterna conosciuta. Non divulgare URL webhook sensibili, token o secret. Se un'automazione al push/merge può fare deploy o toccare dati, **STOP** finché il proprietario non ne approva una mitigazione.
3. **Conflitti/governance:** rileggere i due documenti risolti in clone durante #54/#61; produrre il patch report esatto. Preservare `AGENTS.md` main, DECISION-055/056, overlay dei learning APPROVATO, verifiche upstream, GOAL-03 ancora chiuso.
4. **Review PR:** controllare recensioni richieste/stati del repository e potenziali policy, senza assumere approvazione dall'assenza di check. Evidenziare PR obsolete o non pertinenti prima dei merge.
5. **Attestare gate UAT Owner:** #75 non e' Owner-accepted in GitHub. Preparare istruzioni brevi per la verifica visiva RC22; non cambiare il candidato e non dichiarare “accettato” senza esplicita conferma Owner.
6. **Release plan:** elaborare uno script/checklist dei merge GitHub in ordine #27→#98 come merge commits `no-ff` (no squash/rebase/force), con SHA re-check/remote deploy gate e checkpoint dopo ogni step. Per i branch stacked, verificare che il cambio di base della PR successiva sia coerente con l'antecedente; non applicare operazioni sui PR remoti in questa missione.
7. **Safety after merge:** definire verifica HEAD/ancestry, confronto Git tree app= #98, conservazione six main commits, diff governance, clean clone static/CI dove disponibile e test runtime in **ambiente isolato** con dati sintetici e credenziali distinte solo dietro successiva autorizzazione. Un merge Git non produce automaticamente una release runtime.
8. **Rollback Git:** non usare force-push/reset su main. Prevedere revert di merge governati nel caso si renda necessario, e salvare SHA del main prima di tutto.

**Output richiesto:** una relazione unica `PREMERGE_GATE_PASS/PARTIAL/FAIL` con verifica remote-trigger, SHA, Owner UAT e precisa proposta di procedura. Le azioni server/build/DB **restano escluse**. Se i controlli remoto non sono disponibili, `PARTIAL` con motivo.

## 3. Sequenza autorizzativa — separazione obbligatoria

**G2A — prima di ogni merge:** (a) report remote-trigger audit con assenza o mitigazione di deploy automatico, (b) conferma Owner walkthrough Agenda RC22 con esito e difetti, (c) validazione esatta del manifest/primo staging path. **Non confondere il TECHNICAL PASS dell'Agenda con Owner acceptance.**

**G2B — decisione Owner di esecuzione:** presentare un'unica proposta a obiettivo per le 35 PR in ordine, guardrail stop/revert e test di non regressione, con una sola richiesta di autorizzazione. Questa decisione e' distinta dalla precedente autorizzazione alla sola rehearsal; nessun merge remoto finché non esiste.

**G2C — soltanto dopo decisione esplicita:** Codex implementa l'integrazione in `main` secondo procedura verificata, rallentando solo su anomalie materiali. PR #96 documentale e' separata; non inglobarla automaticamente.

**G2D — build/runtime separata:** dopo l'integrazione e previa autorizzazione, fresh checkout/build e test isolati, poi eventuale promozione UAT; non sostituire RC22 senza Owner OK.

**G3, successivo:** backup/rehearsal upgrade Frappe/ERPNext + Healthcare/Builder versione target controllata, senza cambiare GOAL-03 o architettura Desk implicitamente.

## 4. STOP conditions

Fermarsi su: UAT Owner negativa o non eseguita se richiesta per G2B; webhook/auto-deploy sconosciuto; main/prodotto SHA divergenti; difetti permessi; conflitti governance non ricomponibili; richiesta di migrazione/runtime/DB condiviso; branch incongruente; approvazione o protezione GitHub incerta; impossibilità di provare rollback.

**Decisione da raccogliere:** non basta il PASS della rehearsal. Serve Owner UAT visivo e successiva autorizzazione **esplicita, circoscritta ai merge reali**. Il prossimo passo consigliato e' l'audit read-only dei trigger GitHub in parallelo al walkthrough Owner Agenda.
