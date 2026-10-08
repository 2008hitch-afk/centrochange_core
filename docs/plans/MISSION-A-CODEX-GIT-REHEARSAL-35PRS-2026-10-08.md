# Centro Change — Mandato Codex, simulazione Git delle 35 PR

**Data autorizzazione Owner:** 2026-10-08 (chat Centro Change: «AUTORIZZO» alla domanda «Autorizzi Codex a eseguire questa simulazione Git isolata, senza effettuare merge reali?»).  
**Stato:** `OWNER_AUTHORIZED_FOR_GIT_REHEARSAL_ONLY` — mandato pronto; non indica che Codex abbia gia' eseguito la missione.  
**Issue coordinatrice:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95).  
**Piano e manifest delle 35 PR:** [MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md](MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md).  
**Repo:** `2008hitch-afk/centrochange_core`.  
**Durata/ambito:** una sola simulazione isolata di integrazione codice Git, senza pubblicazione dei merge, senza scritture ai rami GitHub e senza toccare server applicativo, container, immagini UAT o DB.

## Obiettivo (GOAL A, rehearsal — non merge)

Dimostrare, tramite 35 merge **solo locali su un clone temporaneo**, che la catena stacked `#27 -> ... -> #94 -> #98` puo' essere integrata partendo da `main` senza perdere i sei commit di governance aggiuntivi, la storia PR e la correzione dei guard di sicurezza #98. Qualora sorgano conflitti non banali o incongruenze di codice, arrestarsi con evidenza esatta; non improvvisare.

## Preflight obbligatorio (senza scritture sul repository di lavoro o GitHub)

1. Leggere `AGENTS.md`, i documenti di architettura e sicurezza e l'issue #95; consultare la roadmap sopra e la review PR #98. La missione **non riapre il design Desk** e non introduce nuove feature.
2. Nel clone/checkout preesistente eseguire **solo letture** di `git branch --show-current`, `git status --short`, `git log -n 5 --oneline`, `git remote -v`. Non alterare branch o file non committati; se lo stato locale e' sporco, lasciarlo intatto.
3. Creare un clone indipendente in directory nuova temporanea a nome identificabile (`mission-a-git-rehearsal`), con oggetti e working tree propri, evitando worktree che usino/rifacciano checkout del runtime condiviso. Non usare `/mnt/data` per segreti, non scrivere dump o credenziali nel repo.
4. Rileggere dal remoto tutte le PR, confrontare `head SHA`, `base branch`, stato `DRAFT` e `main` con il manifest congelato nel piano. **Fermarsi** se un commit non coincide; richiedere riconciliazione, non scegliere automaticamente il nuovo HEAD.

### Baseline congelata alla registrazione (2026-10-08)

- `main` `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`.
- `#94` `84e9df1ebf80aab9905cdfc08df598a07bef0f3a` (RC22 Owner UAT).
- `#98` `9d12f5e06df92ed35de843b882f3a40e82c02b19` (guard fix).
- Sei commit propri di `main` da preservare: `1f951b7`, `12f010b`, `912a64a`, `176a690`, `c83431c`, `a3c34a7`. Non ignorare `AGENTS.md` e `docs/MVP-GOAL-ROADMAP-v0.1.md`.
- 35 PR di prodotto; PR #96 solo documentale e **esclusa dalla simulazione del codice**.
- Documento di riferimento contiene numeri, ordine e SHA completi di tutte le 35 PR (non ricostruire l'elenco a memoria).

## Simulazione locale (nessun push/merge GitHub)

1. Nel clone **separato**, creare un solo branch locale `rehearsal/mission-a-35-prs` dall'esatto `main` SHA, senza pubblicarlo.
2. Per ciascuna PR in ordine bottom-up #27 -> #98, usare il relativo **commit SHA del manifest**, preferibilmente `git merge --no-ff --no-edit <sha>`, e registrare: PR, head SHA usato, tipo/risultato merge, conflict, tree SHA risultante e controllo di ancestry. I merge locali sono previsti/autorizzati; i merge GitHub no.
3. In caso di conflitti non banali, documentare file/blocco/conflitto e alternative, eseguire `git merge --abort` **solo sul clone temporaneo** e terminare `PARTIAL — DECISIONE RICHIESTA`. Non usare `-X ours`, `-X theirs`, `git reset --hard` su checkout originali, squash/rebase/force push, eliminazione branch UAT o editing dei container.
4. Dopo ciascuna PR confermare che nessun commit originario e' perso: `git merge-base --is-ancestor` sui relativi head; registrare le differenze e lo stato.
5. Dopo tutti i 35 merge simulati: verificare ancestry dei sei commit `main`, ricostruire un tree/diff leggibile, comparare il **tree dell'app** a `#98` e, soprattutto, il file `hooks.py` con la correzione #97. Verificare che `AGENTS.md` e roadmap GOAL-02 mantengano le modifiche correnti di `main` e nessuna regola sovrascritta da vecchi branch.
6. Controlli di sola filesystem Git (compilazione/test statici se eseguibili nel clone **senza avviare servizi/installazioni sul runtime condiviso**), `git diff --check`, assenza di conflitti residui, assenza di secret/dump accidentalmente aggiunti.
7. **Niente build Docker, migrazione, database, servizi, backup, reboot, porta o UAT** durante questa rehearsal. La CI e il runtime saranno verificati a parte prima dell'effettiva integrazione.
8. Produrre un report sintetico con `PASS`, `PARTIAL` o `FAIL`, numero merge completati, SHAs, file conflittuali se presenti, diff tree app, conservazione dei sei commit `main`, eventuali divergenze semantiche, elenco dei passi necessari prima del merge remoto.
9. Consegnare il report e la proposta di procedura **senza eseguire alcun push**. Aggiornare la issue GitHub #95 con un **commento riepilogativo di soli risultati/scrittura documentale**, se possibile, senza pubblicare rami di simulazione. Non chiudere issue, non approvare PR, non cambiare stati.
10. Riportare `READY_FOR_OWNER_MERGE_DECISION` solo se la prova Git 35/35 e i controlli di integrita' sono PASS; altrimenti `DECISIONE RICHIESTA` con problemi concreti.

## Limiti di autorita' / stop conditions

- **AUTORIZZATO:** Git read/search/fetch, clone temporaneo indipendente, commit di merge **solo locali** in tale clone, controlli statici, report e commento di stato in #95.
- **VIETATO:** `git push` verso qualunque branch, retarget PR, merge remoto, cancellazione branch/commit, modifiche `main`, editing di codice sul branch prodotto, runtime/app/server/DB, UAT RC22, upgrade v16.50, Unified Desk, GOAL-03, gestione di dati reali o segreti.
- Stop su cambio delle 35 HEAD SHA / `main`, conflitto non banale, alterazione del tree finale, governance persa, necessità di intervenire sul prodotto per sbloccare la prova, o richieste di accesso al runtime per test supplementari.
- Il retest visuale Agenda #75 da parte dell'Owner resta **PENDING** e non e' condizione per eseguire **solo la prova Git**, ma e' requisito prima di promuovere la nuova baseline UAT.
- **I merge reali saranno una decisione Owner separata** a valle della relazione; l'autorizzazione attuale non permette neppure un primo merge in `main`.

## Deliverable atteso

Un solo report conclusivo (non una sequenza di microrichieste): branch/clone isolato, 35 merge Git con esito per PR, verifica dei sei commit, diff/identita' del prodotto finale, limiti e proposta di esecuzione futura. Se `PASS`, attendere nuova approvazione dell'Owner prima di qualsiasi modifica al repository remoto.


## ADDENDUM — OWNER AUTHORIZED RESUMPTION AFTER PR #54 CONFLICT (2026-10-08)

**Explicit new approval:** Owner has confirmed the bounded proposal to resolve the PR #54 roadmap conflict **only on the temporary local rehearsal clone**, preserving `main`'s formally authorized GOAL status, then resume the 35-PR rehearsal. This approval extends the earlier rehearsal authorization **only for the specific local conflict and its safe continuation**. It does NOT authorize any remote merge, branch mutation/push, production activity, server or database operation.

### Results already recorded by Codex (not yet final)
- GitHub #95 [Codex partial report](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6064657947): manifest 35/35 SHA/base verified; 13 local no-ff merges PASS #27→#52.
- Step14 / PR #54: merge stopped in `docs/MVP-GOAL-ROADMAP-v0.1.md`, and safely aborted on clone only.
- Isolated clone recorded: `/tmp/mission-a-git-rehearsal-2qp6b5l1/clone`, local branch `rehearsal/mission-a-35-prs`; checkpoint trial HEAD `1095447fb6aba93133b001d8cce0ac4bb84d0e9c`, tree `5490ca59a0c3524cc78aec9f42099966aa4feb02`. Verify these exist and are unmodified on disk. If no longer available, reconstruct ONLY in a new isolated clone from pinned manifest; do not pretend to resume an absent checkpoint.
- All six of `main`'s private commits are present at this checkpoint. No remote changes, no app runtime or DB touched. Final 35/35 tree parity has NOT been established.

### Specific resolution to use at PR #54
The conflict arises between:
- `main` status: `GOAL-01 — OWNER ACCEPTED / DEV PASS — DECISION-055`; `GOAL-02 — ACTIVE / AUTHORIZED — DECISION-056`.
- Historical #54 status: `GOAL-01 — DONE / DEV PASS`; `GOAL-02 — QUEUED`, which is obsolete and would roll back Owner authorization.

**Resolve only the two conflicting status rows** to preserve the authority of `main` for GOAL-01 acceptance and GOAL-02 authorization. Keep DECISION-055/056 links and do NOT demote GOAL-02 to QUEUED. If the incoming branch also contributes independent, noncontradictory technical-evidence links, retain those links or explain any omission. Do NOT overwrite the rest of the roadmap with `--ours` / `--theirs`. The authorized official status remains ACTIVE/AUTHORIZED even if a separate technical report says the UAT candidate is READY; Owner acceptance remains pending.

### Resume procedure
1. Recheck `git status`, HEAD `1095447...`, tree, remote SHA lock, and that the original checkout is unchanged; no force-reset. If diverged, **STOP** and report.
2. In the clone only, repeat/continue local merge of PR #54 from its pinned SHA, resolve the specific document conflict as above, stage exactly the resolved file, complete the local merge commit with both parents. Ensure no conflict markers remain.
3. Resume the rest of the 35 PRs through #98 using the already-approved local rehearsal procedure and pinned manifest. Document per-step tree SHA and all ancestry checks.
4. **Stop on any new substantive conflict**, especially governance, security, app code, migrations or loss of approved decisions. Only mechanical/nonmaterial edits (e.g. whitespace) may be handled locally with full recorded proof; never choose between opposing business/security authorities without Owner decision.
5. After step35, independently verify six commits `main` remain ancestors, product app tree equals #98 (including six restored before_request hooks), `AGENTS.md`/goal roadmap preserve `main` authorities, no dropped product commits or unexpected changes, no uncommitted files; finish `PASS / READY_FOR_OWNER_MERGE_DECISION` only on full 35/35 checks.
6. Update issue #95 with a new comment linking the former partial result, specifying the approved resolution and final PASS or PARTIAL with detailed discrepancies. Any report/file creation must stay local; no GitHub pushes or changed branch/PR metadata.

**Absolute boundaries unchanged:** no `git push`, no actual PR merge/retarget, no `main` changes, no Docker/runtime/UAT RC22/DB/upgrade/Desk, no old checkout changes. Owner Agenda visual UAT #75 is a separate pending approval gate. This addendum does not authorize actual merges.


## ADDENDUM #2 — OWNER AUTHORIZED LOCAL PR #61 CONFLICT RESOLUTION (2026-10-08)

**Decisione Owner nel progetto Centro Change:** "autorizzo", in risposta alla proposta esplicita di **risoluzione additiva locale del conflitto #61** in \`AGENTS.md\` e \`docs/MVP-GOAL-ROADMAP-v0.1.md\`, conservando tutte le istruzioni vigenti in \`main\` e i riferimenti tecnici non contraddittori. Autorizzata la **sola continuazione della rehearsal Git isolata** fino a #98; non sono autorizzati merge remoti, modifiche ad altri branch, runtime, DB, UAT, upgrade o produzione. Interrompersi su ulteriori conflitti materiali.

### Checkpoint verificabile sul vero host Codex

- Clone dichiarato: \`/tmp/mission-a-git-rehearsal-2qp6b5l1/clone\`.
- Branch solo locale: \`rehearsal/mission-a-35-prs\`.
- Ultimo HEAD pulito dopo 17 PR: \`d0913e743af401de35d454b4349b4131ffb7042b\`; tree atteso \`ddd261622e58706c41cc6de66a77be6f235c77c7\`.
- Le PR simulate e preservate come antenati: #27, #30, #32, #34, #36, #38, #40, #42, #44, #47, #48, #50, #52, #54, #56, #57, #60.
- PR successiva #61, SHA \`1678406d803264068972786fdb8a5b189395b50a\`.
- \`main\` remoto congelato \`a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b\`; ultimo HEAD #98 \`9d12f5e06df92ed35de843b882f3a40e82c02b19\`.
- Fonte evidenza: [issue #95, report Codex](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6065022441); [riesame host](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6065175424); [review HITCH](https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6065288565).

**Prima di procedere:** ricontrollare esistenza clone, \`git status\` clean, HEAD e tree attesi, integrità checkpoint e corrispondenza 35 SHA/base, sei commit main antenati. Se manca/invalido, fermarsi e non fingere una ripresa: solo ricostruzione isolata nei limiti del mandato originale, con rapporto esplicito.

### Risoluzione additiva di PR #61 AUTORIZZATA nel solo clone

1. \`AGENTS.md\`: conservare integralmente gli obblighi correnti di \`main\`, incluso workflow macro-goal, Goal Learning Extraction cross-client, consultazione solo generalized learnings APPROVATO, documentazione e sorgente ufficiale upstream pinned, dataset sintetico, limiti GOAL-03/provider/prod e senza stack merge automatico. Aggiungere dal ramo storico soltanto formulazioni compatibili sul GOAL-01 formalmente accepted via DECISION-055 e GOAL-02 authorized via DECISION-056, senza togliere né rilassare alcun requisito.
2. \`docs/MVP-GOAL-ROADMAP-v0.1.md\`, tabella: mantenere come *status formale* GOAL-01 \`OWNER ACCEPTED / DEV PASS\` (DECISION-055) e GOAL-02 \`ACTIVE / AUTHORIZED\` (DECISION-056), non sostituirli con status tecnico. Incorporare come *evidenza tecnica distinta* GOAL-01 Completion Report, GOAL-02 Completion Report e \`TECHNICAL DONE / UAT READY\` con esplicita nota \`Owner visual UAT / final acceptance pending\`. Nessun GOAL-03 o merge implicito.
3. Sezione \`Current command for Codex\`: comporre testo unico che conserva per intero i requisiti di \`main\` (APPROVATO, official upstream, pinned source/runtime, guardrails, autonomia solo nel GOAL autorizzato) e aggiunge soltanto gli output tecnici compatibili (named candidate, client validation, completion report, extraction). Non riscrivere la decisione HITCH o dichiarare GOAL-02 formalmente accepted.
4. Risolvere i **soli conflitti identificati** in questi file, senza \`--ours\`/\`--theirs\` sull'intero file. Documentare il diff e motivare ogni scelta. Se emergono conflitti ulteriori o la risoluzione richiede una scelta di authority, **STOP**.
5. Completare #61 come *merge commit locale a due genitori*, verificare tutti gli antenati e proseguire nell'ordine previsto fino a #98. Ripetere controlli source tree, hook #97, sei commit main, governance, \`git diff --check\`, stato clean e rapportare eventuali limitazioni. Nuovi conflitti sostanziali non sono autorizzati: \`PARTIAL — DECISIONE RICHIESTA\`.

### Perimetro immutato

Consentiti: simulazione in clone Git indipendente, risoluzione locale additiva del conflitto PR #61, report ed eventuale commento su issue #95.  
Vietati: \`git push\`, merge reali, retarget PR, update di \`main\` o branch condivisi, interventi al server, Docker, UAT RC22, dati, upgrade Frappe/ERPNext, Desk/cutover.  
L'autorizzazione non equivale alla verifica di avvenuta esecuzione; Codex deve riportare dati effettivamente controllati. Il gate visivo Owner Agenda #75 resta distinto e aperto.

**Output:** solo a simulazione completa e verificata 35/35: \`READY_FOR_OWNER_MERGE_DECISION\`; in ogni altro caso \`PARTIAL / FAIL — DECISIONE RICHIESTA\`.
