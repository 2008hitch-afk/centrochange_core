# Centro Change — Missione A e roadmap verso Unified Desk

**Data:** 2026-10-08
**Cliente:** HC-0005 — Centro Change
**CASE / RUN:** CASE-001 / IMPLEMENTATION-001
**Stato documento:** PIANO VERSIONATO — PROPOSTO; **MISSIONE A (audit e documentazione) AUTORIZZATA dall'Owner 2026-10-08**
**Autorizzazione operativa:** SOLO audit in lettura e registrazione GitHub del programma; **NO MERGE, NO UPGRADE, NO RUNTIME MUTATION, NO PROD**
**Tracker:** [Issue #95](https://github.com/2008hitch-afk/centrochange_core/issues/95)
**Coordinamento UAT:** [Issue #75](https://github.com/2008hitch-afk/centrochange_core/issues/75), [PR #94](https://github.com/2008hitch-afk/centrochange_core/pull/94)

> Questo e' un programma di lavoro e di decisioni future, **non** una nuova decisione architetturale approvata.
> Restano vigenti HC-0005 DECISION-004 (webapp operativa primaria), DECISION-056 (GOAL-02 autorizzato), i divieti di dati reali, provider reali, GOAL-03 e produzione. Per adottare Unified Desk occorrera' una nuova decisione Owner formale.

## 1. Obiettivo approvato della Missione A

Riprendere il lavoro esistente **senza perdita di codice, PR o evidenze**; revisionare la catena di 34 PR GOAL-01/GOAL-02 e predisporre una procedura di integrazione controllata in `main`.

Non confondere:
- **GitHub attuale:** i commit sono su branch/PR draft, NON ancora integrati in `main`.
- **Runtime UAT RC22:** il prodotto e' tecnicamente provato, ma **Owner visual retest Agenda PENDING**.
- **Status GOAL-02:** percorso UAT ancora aperto per accettazione Owner; lo stato issue tecnica #23 (closed) non trasforma #75 in Owner accepted.

## 2. Stato delle evidenze al 2026-10-08 (osservazioni, non supposizioni)

| Item | Stato GitHub osservato |
|---|---|
| `main` | `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`; branch protection riportata **false** |
| PR tecniche aperte | 34, tutte `OPEN` / `DRAFT`, catena dal #27 al #94 |
| Branch terminale UAT | `issue-75/final-client-ux-review` |
| HEAD del branch con test/evidenze | `84e9df1ebf80aab9905cdfc08df598a07bef0f3a` |
| Candidato UAT runtime | `goal02-20261008-rc22` |
| **Esatto commit source RC22** | `f06acca4f6c2ac757dbd3e187709f94b18554b65` |
| Fix geometria Agenda | `f06acca` CSS; 7 colonne giorni e riga professionista allineate |
| Test correttivo RC22 | geometria 0 px su 5 viewport, 12 browser, 189 backend rollback; health/parita' PASS |
| Proprietà dei dati | Dataset Owner conservato; nessun migrate/reset/seed sul correttivo RC22 |
| Owner UAT | `READY_FOR_OWNER_RETEST`, NON accepted |
| PR #94 | draft/non merged, head sopra #93; #92/#93 non modificate dal fix |
| Stack UAT pinned | Frappe 16.31.0, ERPNext 16.32.0, Marley 16.5.2, Builder 1.33.0 |
| CI `main` | non considerare copertura automatica dimostrata; verificare actions/workflow e status richiesti prima dei merge |

**Evidenza RC22 primaria:**
[Agenda grid alignment 2026-10-08](https://github.com/2008hitch-afk/centrochange_core/blob/issue-75/final-client-ux-review/docs/evidence/ui-design-system-v1/AGENDA-GRID-ALIGNMENT-2026-10-08.md),
[UAT candidate](https://github.com/2008hitch-afk/centrochange_core/blob/issue-75/final-client-ux-review/docs/uat/UAT-CANDIDATE.json),
[PR #94](https://github.com/2008hitch-afk/centrochange_core/pull/94).

**Limite dell'evidenza:** stato di GitHub e report di test versionati; non e' un'osservazione Sysadmin nuova del filesystem live. Prima di operare sul server Codex/Sysadmin dovra' produrre il preflight mirato, confrontandolo con questa baseline.

## 3. Dipendenze esatte PR — ordine candidato bottom-up

Il seguente elenco e' una **fotografia GitHub verificata**; ogni PR ha come base il branch della precedente, salvo #27 -> `main`. Ricontrollare head SHA/base prima del lavoro.

| Ordine candidato | PR | Tema sintetico |
|---:|---:|---|
| 01 | [#27](https://github.com/2008hitch-afk/centrochange_core/pull/27) | WP-00 runtime riproducibile |
| 02 | [#30](https://github.com/2008hitch-afk/centrochange_core/pull/30) | Identita' e sicurezza |
| 03 | [#32](https://github.com/2008hitch-afk/centrochange_core/pull/32) | Booking / primo incontro |
| 04 | [#34](https://github.com/2008hitch-afk/centrochange_core/pull/34) | Sedute, note, chiusure |
| 05 | [#36](https://github.com/2008hitch-afk/centrochange_core/pull/36) | Webapp operativa, comunicazioni, report |
| 06 | [#38](https://github.com/2008hitch-afk/centrochange_core/pull/38) | Bridge finance/master |
| 07 | [#40](https://github.com/2008hitch-afk/centrochange_core/pull/40) | Crediti, incassi, correzioni |
| 08 | [#42](https://github.com/2008hitch-afk/centrochange_core/pull/42) | Banca, riconciliazione |
| 09 | [#44](https://github.com/2008hitch-afk/centrochange_core/pull/44) | XML fornitori / fatture passive |
| 10 | [#47](https://github.com/2008hitch-afk/centrochange_core/pull/47) | Economia professionisti/coda |
| 11 | [#48](https://github.com/2008hitch-afk/centrochange_core/pull/48) | Finance reporting |
| 12 | [#50](https://github.com/2008hitch-afk/centrochange_core/pull/50) | Simulazione SdI |
| 13 | [#52](https://github.com/2008hitch-afk/centrochange_core/pull/52) | Simulazione TS |
| 14 | [#54](https://github.com/2008hitch-afk/centrochange_core/pull/54) | GOAL-01 integrazione |
| 15 | [#56](https://github.com/2008hitch-afk/centrochange_core/pull/56) | Policy soglia sedute insolute |
| 16 | [#57](https://github.com/2008hitch-afk/centrochange_core/pull/57) | Learning extraction |
| 17 | [#60](https://github.com/2008hitch-afk/centrochange_core/pull/60) | Protezione risposte stale |
| 18 | [#61](https://github.com/2008hitch-afk/centrochange_core/pull/61) | UAT package |
| 19 | [#65](https://github.com/2008hitch-afk/centrochange_core/pull/65) | Agenda multi-professionista |
| 20 | [#67](https://github.com/2008hitch-afk/centrochange_core/pull/67) | Report professionista |
| 21 | [#70](https://github.com/2008hitch-afk/centrochange_core/pull/70) | Report paziente/fiscale |
| 22 | [#82](https://github.com/2008hitch-afk/centrochange_core/pull/82) | Registro modifiche |
| 23 | [#83](https://github.com/2008hitch-afk/centrochange_core/pull/83) | Riapertura e spostamento seduta |
| 24 | [#84](https://github.com/2008hitch-afk/centrochange_core/pull/84) | Etichette attese professionisti |
| 25 | [#85](https://github.com/2008hitch-afk/centrochange_core/pull/85) | Tracciabilita' riconciliazione |
| 26 | [#86](https://github.com/2008hitch-afk/centrochange_core/pull/86) | Dettaglio TS revisionato |
| 27 | [#87](https://github.com/2008hitch-afk/centrochange_core/pull/87) | Conferma primo incontro |
| 28 | [#88](https://github.com/2008hitch-afk/centrochange_core/pull/88) | Ricerca pazienti autorizzata |
| 29 | [#89](https://github.com/2008hitch-afk/centrochange_core/pull/89) | Select Pazienti/Professionisti |
| 30 | [#90](https://github.com/2008hitch-afk/centrochange_core/pull/90) | Etichette contabili italiane |
| 31 | [#91](https://github.com/2008hitch-afk/centrochange_core/pull/91) | Profilo Direzione |
| 32 | [#92](https://github.com/2008hitch-afk/centrochange_core/pull/92) | Tabler Design System v1 |
| 33 | [#93](https://github.com/2008hitch-afk/centrochange_core/pull/93) | Review permessi/cache |
| 34 | [#94](https://github.com/2008hitch-afk/centrochange_core/pull/94) | Owner UX finale + Agenda RC22 |

**Cautela stacked PR:** `mergeable=true` non equivale a `PASS`. Le PR hanno base una sull'altra: merge casuali su `main`, squash o retarget/rebase non verificati possono perdere differenze, duplicare patch o falsare il diff. Prima di eseguire, Codex deve presentare una strategia di **merge-commit/rebase/retarget controllata**, con prova su clone e conferma che ciascuna PR abbia diff atteso. Nessun force push o delete del ramo UAT per semplificare.

## 4. Piano di esecuzione della Missione A

### A0 — Freeze informativo e checkpoint di codice (ChatGPT/HITCH; AUTORIZZATO)

1. Rileggere GH PR/commit/tags/branch rules, revisioni, commenti ed evidenze; annotare HEAD e possibili divergenze.
2. Confrontare candidato RC22 e ultimo HEAD: `source_commit` != `review HEAD`, ma gli artifact di source parity identificano i file app esatti. Non usare ciecamente HEAD docs come image source.
3. Confermare lo stato #75 e retest Owner, inclusa Agenda 5–11 ottobre e 28 settembre–4 ottobre, scroll mobile/resize.
4. Produrre audit con per-PR `PASS / PARTIAL / BLOCKED`, lacune, test e ordine di integrazione.
5. Proporre checkpoint/tag release semantico e protezione `main`, senza crearli/imporli automaticamente.

**Gate A0:** audit scritto, blocker evidenziati, Owner retest registrato o esplicitamente pendente. Se retest non completato: **NO MERGE della catena finale**.

### A1 — Piano di merge, preflight e autorizzazione (ChatGPT/HITCH + Owner)

1. Definire metodo Git adatto alle PR stacked, mantenendo la storia; con `merge commit` bottom-up e retarget verso `main` solo a diff verificato; alternative ammesse solo dopo prova.
2. Documentare eventuali conflitti, modifiche CI/CD e protezione branch; verificare che merge su `main` non comporti deploy inatteso.
3. Verificare che tutte le PR siano davvero incluse in baseline proposta, con stato recensioni e test decisivi.
4. Preparare mandato Codex con input SHA, comandi/test, stop conditions, rollback **del codice** e rapporto finale.
5. Ottenere **una distinta approvazione Owner per i merge**.

**Gate A1:** `OWNER APPROVED MERGE EXECUTION` separato dal presente documento.

### A2 — Integrazione tecnica (Codex; **NON ANCORA AUTORIZZATA**)

1. Partire dal ramo `main` e dalla lista PR/SHA bloccata; effettuare un rehearsal isolato prima di scrivere su `main`.
2. Eseguire sequenza approvata; dopo ogni PR verificare head/base e che il diff netto corrisponda a quello atteso; nessuna modifica a runtime UAT.
3. Alla fine clean checkout, build reproducibility, regressioni operative/finance, Agenda geometry, permessi per ruoli, API dirette, export/print, public ingress, workers e asset parity.
4. Confrontare tree app finale rispetto al candidato prodotto RC22 e registrare eventuali delta attesi; la verifica non e' sostituita dalla sola compilazione.
5. Proporre un tag stabile con SHA finale e manifest versionato, subordinato a controllo evidence e Owner.
6. Se `PARTIAL/FAIL`, fermarsi con rapporto e proposta correttiva: **no promozione di `main` a baseline accettata**.

### A3 — Handoff e decisione per fase B (ChatGPT/HITCH + Owner)

Consegnare: PR list merged/reconciled, commit finale, eventuale tag, UAT status, test/evidenze, problematiche residue, modalita' di recovery del codice, decisione richiesta per upgrade isolato. Non autorizza automaticamente B.

## 5. Roadmap del programma complessivo (PROPOSTA, non decisione vigente)

| Macro-obiettivo | ChatGPT/HITCH | Codex, solo se autorizzato | Owner gate |
|---|---|---|---|
| **A GitHub Stable** | audit PR, piano, review, verifica outcome | rehearsal merge, merge e test | autorizza merge e accetta baseline |
| **B Upgrade target v16.50 da verificare** | verifica docs ufficiali, version matrix Frappe/ERPNext/Marley/Builder, test spec, rischi | backup & restore **isolati**, upgrade clone, regression, performance | approva target e execution |
| **C Unified Desk** | architettura per ruoli, mappa schermate -> Desk nativo/custom, criteri UX+permessi | Workspace, forms, Agenda Page custom riusando JS/backend, Finance, TS/SdI | approva cambio decisione architetturale e risultato UAT |
| **D Cutover** | disegno cutover/rollback, evidenze parita', UAT Owner | implementazione decommission UI interna, smoke, restore rehearsal | approva esclusivamente cutover finale |

### Target funzionale desiderato, NON approvato come nuova decisione

- **Interno:** un solo Desk Centro Change, incluse Agenda multi-professionista, appuntamenti/chiusure/note, Pazienti, Finance/Admin, report, SdI/TS, menu per ruolo.
- **Pubblico:** Frappe Website e primo incontro restano pubblici, separati dal Desk e mantenuti.
- **Dati:** un solo DB operativo finale, senza doppia contabilità; DB clone temporaneo per test e migration.
- **Riutilizzo:** integrare backend `centrochange_core` e security guards esistenti; mai nascondere accesso UI come unica barriera, verificare server permissions in Desk/REST/report/export/print.
- **Grafica:** Frappe Desk nativo con tema Centro Change e Tabler localizzato nelle custom Page, evitando patch upstream/override invasivi.
- **Reversibilita':** checkpoint A preupgrade (app+DB+file+config), B postupgrade/pre-Desk, rehearsal restore; GitHub non e' backup dati.
- **Attivazione:** solo dopo prove su copia, UAT completa e approvazioni; mantenere una via di recupero fino a stabilizzazione.
- **Upgrade target:** 16.50 e' un'ipotesi di target da risolvere con tag/rilasci e compatibilita' pinned ufficiale; nessun upgrade automatico.

## 6. RACI e carico di Codex

- **Owner (A):** autorizza cambio architettura/target, merge, interventi server e cutover; valida Agenda e il prodotto.
- **ChatGPT/HITCH (R sul piano):** analizza GH, scrive issue/doc, produce checklists, controlla chiusure, tiene la memoria nel repo. Non effettua merge di propria iniziativa.
- **Codex (R tecnico sul mandato):** soltanto lavori che richiedono filesystem, runtime, test/build o codice; non ridiscute autonomamente l'architettura.
- **HITCH Sysadmin (osservatore):** evidenze live in sola lettura dove servono, senza modificare.
- **Separazione temporale:** una sola missione tecnica autorizzata attiva a Codex; A prima di B; B prima di C; C prima di D.

## 7. Data boundaries, STOP e recovery

- Solo DEV/UAT **sintetico**. Niente dati sanitari reali, backup/dump/secret nel repository; niente real SdI/TS e nessuna autorizzazione produzione.
- Non fare merge/deploy via PR/Action senza controllare eventuale deploy automatico.
- Niente `git reset --hard` sui branch condivisi, force push, delete/clean dei volumi, migration sul sito condiviso.
- Se emerge una differenza sostanziale nei permessi, nel document model, nelle scritture o nel percorso di merge, tornare all'Owner: **DECISIONE RICHIESTA**.
- Lo stato approvato HITCH e i Goal restano immutati finché non vengono aggiornati con una decisione formale separata.

## 8. Prossima consegna

**ChatGPT/HITCH:** audit PR completo e piano di merge chiuso con candidate diff, controlli e blocker.  
**Owner:** retest visivo Agenda RC22 e validazione della strategia proposta.  
**Codex:** nessun merge finché Owner non avra' dato il via libera specifico.

Questo documento e la issue #95 sono tracciamento e proposta; non sostituiscono il registro decisionale HITCH `clients/HC-0005/`.

## Aggiornamento audit 2026-10-08 — HOLD merge della catena

**Nuovo gate da audit di codice:** [#97](https://github.com/2008hitch-afk/centrochange_core/issues/97) — nel `hooks.py` esatto RC22 un secondo assegnamento a `before_request` rimuove dall'elenco dichiarato quattro request guard originari. Impatto HTTP **da verificare in clone/runtime isolato**; nessuna prova di data leak dichiarata. **NON proporre merge della catena #27→#94 né la promozione a baseline stabile** finché l'anomalia non e' verificata e, se confermata, corretta con test e PR separata autorizzata.

**Altri controlli conclusi:** main contiene 6 commit di governance/GOAL-02 non presenti nella catena UAT; il piano merge deve preservarli. L'HEAD #94 e' 2 commit oltre il source RC22, con solo 18 file docs e 1 infra cambiati e nessun file app. Le 34 PR non hanno review submission formalmente registrate tramite GitHub; i test runtime restano separatamente documentati. Il modulo `finance.install.configure` riscrive `Custom DocPerm` durante `after_migrate`: fare rehearsal d'idempotenza/permessi su clone prima di upgrade e non assumere harmless.

**Priorita' immediata:** completare la review del potenziale blocco #97 con una **missione tecnica limitata Codex da autorizzare separatamente** (lettura effettivi hook/HTTP negative su clone, eventuale fix minimo in PR, regressioni). Il retest visivo Owner dell'Agenda #75 resta distinto e pendente. Sono esclusi merge e interventi diretti al runtime condiviso.

## Missione Codex #97 autorizzata dall'Owner — 2026-10-08

L'Owner ha esplicitamente autorizzato **solo** la verifica della sovrascrittura `before_request` sul **clone isolato**, con eventuale fix minimo, regressione, PR DRAFT e report. Documento esecutivo: [MISSIONE-CODEX-097-BEFORE-REQUEST-GUARDS-2026-10-08.md](MISSIONE-CODEX-097-BEFORE-REQUEST-GUARDS-2026-10-08.md); [issue #97](https://github.com/2008hitch-afk/centrochange_core/issues/97).

**Non autorizzati:** runtime UAT RC22 condiviso, dati originali, merge di qualunque PR, `main`, upgrade Frappe/ERPNext, cambi schema/permessi o produzione. Il risultato atteso e' `READY_FOR_OWNER_REVIEW` oppure `DECISIONE RICHIESTA`, non un merge. L'autorizzazione e la consegna del mandato **non attestano l'avvio di Codex**; l'operatore avvia Codex con la issue e il documento specifici.

## Snapshot 2026-10-08 — Next gate 35 PR, rehearsal Git proposta

Dopo la review tecnica della correzione #97 [PR #98](https://github.com/2008hitch-afk/centrochange_core/pull/98), la catena stacked ora comprende **35 PR prodotto** #27→#98, mentre la PR #96 del piano rimane distinta. Il diff applicativo #98 e' minimo e tecnicamente rivisto, ma non merged. **Documento operativo congelato con le 35 SHA e un'unica procedura:** [MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md](MISSION-A-35-PR-CONSOLIDATION-REHEARSAL-PLAN-2026-10-08.md).

**Controllo GitHub**: main SHA `a3c34a7`, branch prodotto #98 SHA `9d12f5e`; storia divergente 159 commit prodotto/6 commit main, tutti da conservare. Nessun workflow GitHub Actions nel tree di main o #98; eventuali automazioni esterne restano da verificare prima di **merge remoto**. Proposta: prova `git merge --no-ff` 35/35 su branch locale temporaneo, senza push, solo dopo autorizzazione Owner alla rehearsal; poi piano di merge remoto separato e successiva approvazione.

**Owner Agenda retest #75 ancora PENDING nel repo.** L'autorizzazione a proseguire nella preparazione non e' un'approvazione visiva, non e' autorizzazione a merge o a Codex rehearsal, e non chiude il goal.
