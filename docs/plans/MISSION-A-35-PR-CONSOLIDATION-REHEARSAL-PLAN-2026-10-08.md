# Missione A — Consolidamento sicuro delle 35 PR (piano di rehearsal)

**Data:** 2026-10-08  
**Stato:** PROPOSTO / **PRE-MERGE GATE** — analisi e documentazione autorizzate; **rehearsal tecnico Codex, merge e runtime non ancora autorizzati da questo documento**.  
**Tracker:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95); blocco #97 corretto tecnicamente [PR #98](https://github.com/2008hitch-afk/centrochange_core/pull/98); programma [Missione A](CENTROCHANGE-MISSION-A-AND-UNIFIED-DESK-ROADMAP-2026-10-08.md).  
**Autorità:** Owner, secondo governance HITCH; `AGENTS.md` e decisioni correnti.  
**Ambiente interessato:** esclusivamente prova Git su checkout/clonazione isolata *se e quando autorizzata*. **Nessuna operazione sul server o database**.

## 1. Stato GitHub verificato al momento della stesura

| Riferimento | SHA / condizione |
|---|---|
| `main` | `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`, `protected=false` |
| `#27` prima PR | branch `issue-21/reproducible-clean-runtime`, basato su predecessore storico `a648323d645517154cf2e8f7a21e5387e412f47e` |
| `#94` UAT | `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`, review HEAD; RC22 app source `f06acca4f6c2ac757dbd3e187709f94b18554b65` |
| `#98` fix guard | `9d12f5e06df92ed35de843b882f3a40e82c02b19`, base #94 |
| `#98` image-source | `ee0573a42d631d97ccd5a77567ae3961de6a926c`; successivo commit diff solo docs + infra (no app delta) |
| Catena | **35/35 PR OPEN/DRAFT**, da #27 a #98; 36a PR aperta #96 e' **solo documentazione di piano**, NON parte della catena |
| Compare `main...#98` | 159 commit sul branch prodotto non raggiungibili da main; 6 commit propri di main non sul branch; merge base `a648323d645517154cf2e8f7a21e5387e412f47e` |
| GitHub CI | Non risultano file `.github/workflows/` nel tree di main o #98; verifiche GitHub Actions/branch-protection **non forniscono un gate automatico noto**. Eventuali webhooks o CI esterni **non verificati** |
| Test #98 | review HITCH dei file ed evidenze: [review tecnica](MISSION-A-ISSUE97-TECHNICAL-REVIEW-2026-10-08.md). 55 HTTP + 240 backend dichiarati PASS in lab, con limiti per fixture storiche |
| Owner UAT Agenda #75 | Ancora da registrare formalmente come conferma visiva; **non inferire dalla parola "procediamo"** |
| Prod/GOAL-03 | Non autorizzati |

## 2. Catena bloccata per la simulazione (ordine bottom-up)

**Manifest per riferimento, NON un ordine di merge gia' autorizzato.** Prima dell'esecuzione ricontrollare che le SHA/head/base non siano cambiate; in caso di divergenza interrompere e rigenerare il manifest in review.

| Ordine | PR | HEAD SHA da verificare | BASE BRANCH attuale |
|---:|---:|---|---|
| 01 | [#27](https://github.com/2008hitch-afk/centrochange_core/pull/27) | `b87da2173fd73185537ade389fddb087af7d29cd` | `main` |
| 02 | [#30](https://github.com/2008hitch-afk/centrochange_core/pull/30) | `24e9c9c2425081a36174c9c0fd098cc6e1ae27a2` | `issue-21/reproducible-clean-runtime` |
| 03 | [#32](https://github.com/2008hitch-afk/centrochange_core/pull/32) | `43f69b31d864564b7969407dba4ed51b7b95c0b3` | `issue-28/security-identities-audit` |
| 04 | [#34](https://github.com/2008hitch-afk/centrochange_core/pull/34) | `fcaaee0a7e7597f4713398d09ce3a0299d80313d` | `issue-31/scheduling-services-ingress` |
| 05 | [#36](https://github.com/2008hitch-afk/centrochange_core/pull/36) | `6e20e96d4c23659aba11dabc1e4b53b04cea3712` | `issue-33/operations-ledger-notes-closure` |
| 06 | [#38](https://github.com/2008hitch-afk/centrochange_core/pull/38) | `7e55f5cb016bc5a90d3c58c1bf28d1199f1db447` | `issue-35/communication-reporting-workspace` |
| 07 | [#40](https://github.com/2008hitch-afk/centrochange_core/pull/40) | `72cccb341061cb335898b8c4f07a1ea3cab3b2b1` | `issue-37/finance-master-source-bridge` |
| 08 | [#42](https://github.com/2008hitch-afk/centrochange_core/pull/42) | `595fb06b157e195b012c407c432c5b25196cc335` | `issue-39/native-receivables-payments-corrections` |
| 09 | [#44](https://github.com/2008hitch-afk/centrochange_core/pull/44) | `ff999cd3f68a2545d5b6cf4899af241eda8310bd` | `issue-41/bank-import-reconciliation-overdue` |
| 10 | [#47](https://github.com/2008hitch-afk/centrochange_core/pull/47) | `227cf66a981433b029e6fb390a64ffd54ad31df7` | `issue-43/incoming-xml-reviewed-payables` |
| 11 | [#48](https://github.com/2008hitch-afk/centrochange_core/pull/48) | `fed86055ca8e7ce52a316935d7f4d7829f1c9486` | `issue-45/professional-economics-admin-queue` |
| 12 | [#50](https://github.com/2008hitch-afk/centrochange_core/pull/50) | `b5fd72ee42702fc16ee4597e60a1c2a715ddbce2` | `issue-46/finance-reporting-workspace` |
| 13 | [#52](https://github.com/2008hitch-afk/centrochange_core/pull/52) | `b5db852d98fb152529e83b9c1e31e76dcd2ab6b7` | `issue-49/simulated-sdi-adapter` |
| 14 | [#54](https://github.com/2008hitch-afk/centrochange_core/pull/54) | `6eb39728fa8732d64893a4ca72b4bd2a824a8f44` | `issue-51/simulated-ts-adapter` |
| 15 | [#56](https://github.com/2008hitch-afk/centrochange_core/pull/56) | `8efa6c44b3550efe29362ce470282f82476ea37d` | `issue-53/integrated-mvp-acceptance` |
| 16 | [#57](https://github.com/2008hitch-afk/centrochange_core/pull/57) | `ff693c61746d7caf673a30f1bb302d05f941dc63` | `issue-55/unpaid-session-threshold` |
| 17 | [#60](https://github.com/2008hitch-afk/centrochange_core/pull/60) | `2f905ef526e9b0c6049ad7cb2a879054a929c3db` | `issue-22/goal-learning-extraction` |
| 18 | [#61](https://github.com/2008hitch-afk/centrochange_core/pull/61) | `1678406d803264068972786fdb8a5b189395b50a` | `issue-59/stale-operational-view` |
| 19 | [#65](https://github.com/2008hitch-afk/centrochange_core/pull/65) | `8562dbb10bb16c25f6d1d2376f5ecdae1874a986` | `issue-58/uat-candidate-package` |
| 20 | [#67](https://github.com/2008hitch-afk/centrochange_core/pull/67) | `43bdaee10b3527cce2bcd44787c6012b4a17609f` | `issue-63/agenda-calendar` |
| 21 | [#70](https://github.com/2008hitch-afk/centrochange_core/pull/70) | `9eaa4f93ac0d49b00c21157cd7181f31041f09b3` | `issue-66/professional-view` |
| 22 | [#82](https://github.com/2008hitch-afk/centrochange_core/pull/82) | `1ce40d8ace0a23cade6000c52dd32b87a5bca8fe` | `issue-68/patient-customer-view` |
| 23 | [#83](https://github.com/2008hitch-afk/centrochange_core/pull/83) | `d3da0ca162d01dd51658623fefab761a546c8e40` | `issue-71/audit-register` |
| 24 | [#84](https://github.com/2008hitch-afk/centrochange_core/pull/84) | `014fe883f59a78d26dca597a5b5ef8bbd2231d8b` | `issue-78/governed-reschedule` |
| 25 | [#85](https://github.com/2008hitch-afk/centrochange_core/pull/85) | `23702596fe2d1e470e789c2e33f3c53ea743ba78` | `issue-81/readable-expectations` |
| 26 | [#86](https://github.com/2008hitch-afk/centrochange_core/pull/86) | `1352df5254da8f88259df45c17d23d3b414be4e9` | `issue-62/bank-reconciliation-trace` |
| 27 | [#87](https://github.com/2008hitch-afk/centrochange_core/pull/87) | `1745ee4416f960423ffc08eed96dbd66be2054ad` | `issue-72/ts-reviewed-detail` |
| 28 | [#88](https://github.com/2008hitch-afk/centrochange_core/pull/88) | `d2ce53bfeffb0948f71aab4e9b18d634204823f3` | `issue-73/first-meeting-confirmation` |
| 29 | [#89](https://github.com/2008hitch-afk/centrochange_core/pull/89) | `4342fef81272e0693c52e1edd63bafd51bf9bc1e` | `issue-74/authorized-patient-search` |
| 30 | [#90](https://github.com/2008hitch-afk/centrochange_core/pull/90) | `a1f32f714f197bb56256f1fe97dbb2e679c39274` | `issue-79/searchable-selectors` |
| 31 | [#91](https://github.com/2008hitch-afk/centrochange_core/pull/91) | `c6625c9ff1918a47406bdf5b5e1c157f225eb218` | `issue-80/italian-accounting-ui` |
| 32 | [#92](https://github.com/2008hitch-afk/centrochange_core/pull/92) | `793b2eb830879815ae1e39c86ce7c1cc505afe62` | `issue-64/application-direction-profile` |
| 33 | [#93](https://github.com/2008hitch-afk/centrochange_core/pull/93) | `e687e259825b8bc5178fe2a9df86a28e4ce12c6b` | `issue-76/client-identity-boundary` |
| 34 | [#94](https://github.com/2008hitch-afk/centrochange_core/pull/94) | `84e9df1ebf80aab9905cdfc08df598a07bef0f3a` | `issue-77/final-permission-review` |
| 35 | [#98](https://github.com/2008hitch-afk/centrochange_core/pull/98) | `9d12f5e06df92ed35de843b882f3a40e82c02b19` | `issue-75/final-client-ux-review` |

La PR #96 documentale sul branch `plan/mission-a-goal02-stabilization-20261008` va gestita separatamente; non anticiparne il merge mentre si congelano e confrontano i branch prodotto.

## 3. Perche' non fare un merge diretto e indifferenziato

Le 35 PR sono *stacked*: ciascun branch dipende dal precedente. Le sei variazioni di `main` contengono istruzioni/roadmap che devono sopravvivere all'integrazione. Uno squash, rebase non pianificato, force-push, o singola PR "tutto prodotto" possono perdere tracciabilita' e cambiare il diff delle revisioni.

**Strategia candidata preferita:**
1. **Rehearsal Git in una worktree/clone isolata e pulita**, creata esattamente dal `main` SHA verificato; NON creare site o DB e NON toccare volumi Docker.
2. Verificare `git status` e tutte le SHA/parent-child; salvare log/manifest. Nessun `git reset --hard` su branch condivisi, no force-push/no delete di branch.
3. Creare **branch locale temporaneo** di rehearsal partendo da `main`; in ordine #27→#98 eseguire merge commits locali (`--no-ff`) dai commit SHA bloccati. Se appare un conflitto non banale, fermarsi, documentare il punto esatto e formulare una proposta; non risolvere con `ours`/`theirs` globale o scelte silenziose.
4. Dopo ogni step assicurare che i precedenti SHA siano antenati del trial HEAD e che restino i sei commit di main; nessun push remote. Controllare diff e file di governance (soprattutto `AGENTS.md`, `docs/MVP-GOAL-ROADMAP-v0.1.md`).
5. Al termine, verificare l'identita' (contenuto/tree) di `app/centrochange_core` con il branch #98 **nella sua versione dopo il fix**; il trial deve incorporare tutto il prodotto e i controlli. Verificare `git diff --check` e regressioni **che non richiedano il runtime**, riusando test versionati non distruttivi. Segnalare eventuali cambi di docs/governance attesi.
6. Preparare un piano di integrazione **35 PR GitHub** che faccia merge di #27 per prima e, ogni volta, aggiorni la base della successiva a `main` **solo se il diff e' verificato**, preservando i commit con merge commit. Non cancellare i branch stacked fino a operazione completa. GitHub puo' aggiornare automaticamente le basi in alcune circostanze: rileggere i metadati ad ogni step.
7. Per il merge futuro, predisporre snapshot SHA `main` prima/dopo, prova permessi e ambiente/test runtime separata. **Il rehearsal deve terminare senza nessun merge remoto**.

**Alternativa:** consolidare con PR di integrazione dedicata costruita dal tree completo preservando commit/storia, e chiudere/riconciliare individualmente le PR precedenti secondo un registro verificato. E' piu' semplice lato numero di click ma piu' complesso quanto a tracciabilita' degli acceptance per-PR; **non raccomandata senza motivo concreto**.

## 4. Deliverable atteso dalla rehearsal (Codex, solo dopo nuova autorizzazione)

- `PASS/PARTIAL/FAIL` sulla rehearsal completa 35/35.
- Nuova SHA locale del trial branch (non pubblicata prima della review), lista degli step e diff/conflict report; verifica che nessuna delle sei revisioni `main` sia perduta.
- Confronto del product tree rispetto a #98 e verifica che `hooks.py` mantenga i 6 hooks.
- Distinzione test statica/CI di repo/runtime; lista test supplementari necessari al gate post-merge. Nessuna dichiarazione di UAT Owner accepted.
- Proposta di procedura esecutiva per GitHub, con strategia reversibilita' e stop condition.
- **Nessun aggiornamento al runtime RC22, nessuna nuova RC/UAT**, DB o configurazioni.

## 5. Gate successivi e assenza di autorizzazione implicita

**Gate G1, ora da richiedere:** Owner autorizza Codex a svolgere **solo rehearsal Git isolata e read-only su remoto**. Lo sviluppo locale avviene su clone/worktree temporaneo; no push e no server.

**Gate G2, futuro:** dopo PASS rehearsal e Owner visual review #75, Owner autorizza separatamente l'**esecuzione dei merge** su main con scope, SHA e rollback definiti. La conferma G1 non autorizza G2.

**Gate G3, futuro:** solo dopo che `main` e' riproducibile e testato, proposta per backup/upgrade isolato Frappe+ERPNext/Marley/Builder. Non autorizzare automaticamente GOAL-03, alcun provider reale o cutover.

**Checkpoint dati:** nessun database viene toccato durante G1/G2 se restano operazioni Git; un eventuale aggiornamento dell'installazione esistente e' separato e richiede backup/restore verificati.

## 6. Rischi e STOP

- SHA `main`, #94 o #98 divergente / uno dei 35 rami non piu' raggiungibile.
- Conflitti in `AGENTS.md`, roadmap, permission hooks, migrations o `docs/DECISIONS.md` non riconciliabili senza decisione.
- Merge comporterebbe un workflow automatizzato di deploy inatteso (webhook/integrazione non verificata): stop prima di un merge remoto.
- Perdita/differenza del codice applicativo rispetto a #98 o mancata preservazione dei sei commit di `main`.
- Run di test non fattibili senza mutare runtime/DB condiviso; fermarsi e progettare una prova isolata separata.
- Qualsiasi richiesta di `reset --hard`, force-push, drop DB, modifica UAT, update ERPNext, merge di branch non approvato o GOAL-03.

**Stato:** `READY_FOR_OWNER_REHEARSAL_AUTHORIZATION`; questo file non esegue e non autorizza alcuna integrazione.
