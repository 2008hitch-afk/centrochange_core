# Missione A — Primo audit metadata PR (2026-10-08)

**Status:** READ-ONLY METADATA AUDIT COMPLETATO; **CODE/DIFF AUDIT NON COMPLETATO**; merge NON autorizzato.
**Tracker:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95) • **Plan:** [Roadmap](CENTROCHANGE-MISSION-A-AND-UNIFIED-DESK-ROADMAP-2026-10-08.md)

## Risultati osservati in GitHub

- **34/34 PR** aperte, **34/34 draft**, **34/34 metadata `mergeable=true`** al momento dell'osservazione. Questo non dimostra che siano pronte al merge, né che i permessi e i test siano sicuri.
- Catena base/head consecutiva verificata dall'ultima **#94** fino alla prima **#27 -> main**. L'ordine documentato nel piano e' la sequenza candidata bottom-up.
- `main` osservato a `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`, segnalato non protetto.
- HEAD ultimo branch PR #94 `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`; immagine prodotto RC22 si riferisce invece al **source commit** `f06acca4f6c2ac757dbd3e187709f94b18554b65`. Distinguere source version e review/docs version.
- Per HEAD #94, **0 statuses (combined status) e 0 workflow runs PR-triggered** restituiti da GitHub. Non confondere l'assenza di check GH con l'assenza dei test riportati nelle evidenze runtime; tuttavia sono da convalidare CI/release/rebuild indipendentemente.
- [#75](https://github.com/2008hitch-afk/centrochange_core/issues/75): Owner Agenda visual retest ancora PENDING. **NO MERGE #94** prima dell'esito e dell'autorizzazione.
- #94 ha **173 changed files, 39 commits** rispetto alla sua base #93: di questi 173, **133 file sotto `docs/evidence/`**, 7 `docs/uat/`, 15 `infra/`, 16 `app/`, 2 altra documentazione. Volume di diff dovuto in larga parte a evidenze, ma **scope delle 16 modifiche app deve essere revisionato prima del merge**.
- #92 ha 57 changed files e 27 commits; include local Tabler v1 e implementazione trasversale. Controllare licenze/asset, accesso Frappe nativo, sessioni e report, come gia' rilevato dagli UAT. Anche #65 (Agenda) ha numerosi commit di rifinitura; non sovrapporre in modo cieco ulteriori fix.

## Elenco completo metadata PR

Numeri di file/commit sono **relativi al diff di ciascuna PR sulla propria base**, non vanno sommati per ottenere dimensioni del prodotto. Osservazione puntuale 2026-10-08.

| Sequenza dal basso | PR | File | Commit | Metadata mergeable |
|---:|---:|---:|---:|---|
| 1 | #27 | 7 | 4 | true |
| 2 | #30 | 23 | 1 | true |
| 3 | #32 | 22 | 3 | true |
| 4 | #34 | 43 | 1 | true |
| 5 | #36 | 33 | 2 | true |
| 6 | #38 | 18 | 1 | true |
| 7 | #40 | 12 | 1 | true |
| 8 | #42 | 26 | 1 | true |
| 9 | #44 | 15 | 1 | true |
| 10 | #47 | 20 | 1 | true |
| 11 | #48 | 14 | 1 | true |
| 12 | #50 | 21 | 1 | true |
| 13 | #52 | 14 | 1 | true |
| 14 | #54 | 26 | 6 | true |
| 15 | #56 | 44 | 4 | true |
| 16 | #57 | 1 | 1 | true |
| 17 | #60 | 1 | 1 | true |
| 18 | #61 | 51 | 2 | true |
| 19 | #65 | 30 | 14 | true |
| 20 | #67 | 23 | 3 | true |
| 21 | #70 | 34 | 10 | true |
| 22 | #82 | 12 | 4 | true |
| 23 | #83 | 4 | 3 | true |
| 24 | #84 | 8 | 4 | true |
| 25 | #85 | 7 | 2 | true |
| 26 | #86 | 5 | 3 | true |
| 27 | #87 | 14 | 2 | true |
| 28 | #88 | 6 | 3 | true |
| 29 | #89 | 9 | 2 | true |
| 30 | #90 | 7 | 3 | true |
| 31 | #91 | 6 | 1 | true |
| 32 | #92 | 57 | 27 | true |
| 33 | #93 | 8 | 2 | true |
| 34 | #94 | 173 | 39 | true |

## Blocchi per la review di codice e merge (ancora da eseguire)

1. **Security:** focus PR #30/#32/#34, finance #38–#54, #93 e #94; permessi `has_permission`/`permission_query_conditions`, print/export/query/report, accesso diretto, confidenzialita' note.
2. **Runtime:** garantire no source overlay/manual patch e clean build; controllare se merge su main aziona un deployment automatico.
3. **Integrity:** confrontare app tree di `main` candidato finale con esatto git archive RC22; differenza attesa solo file evidenze/test/doc, salvo motivazioni esplicite.
4. **UAT:** non dichiarare #75 completata o passare a GOAL-03; prima retest Owner.
5. **Git stack:** provare sequenza in clone, preservando tutte le PR/commits e confronto diff prima/dopo retarget; decidere metodo di merge prima di modificare `main`.
6. **CI:** validare test su branch di integrazione pulito e documentare perche' non risultano status/workflow nel commit #94; i test manuali e runtime sono evidenza, non sostituto automatico dei gate di repo.
7. **Backup:** GitHub non e' database backup; Missione A non modifica DB. Piano di DR operativo e upgrade solo nelle successive missioni autorizzate.

## Handoff da preparare a Codex (non ancora avvio esecuzione)

Una sola missione **`integrate-stacked-prs-safely`**, con lista PR/SHA fissa, rehearsal non distruttivo, verifica dei diff, nessun `force-push`, nessun patch al runtime UAT e stop su qualunque contenuto o conflitto non previsto. **Emissione dell'incarico solo dopo approvazione Owner del piano di merge.**

**Criterio d'uscita Missione A:** audit e strategia testati per iscritto + Owner retest (#75) + decisione esplicita sul merge. Non significa GOAL-02 accepted.

## Supplemento di verifica: review GitHub campionate (2026-10-08)

Sono state lette le review PR tramite l'API GitHub per **17 PR campionate**: #27, #30, #32, #34, #38, #40, #42, #44, #47, #50, #54, #56, #61, #65, #92, #93, #94. La risposta per ognuna riporta **zero review submission registrate**. Questo non elimina le evidenze dei test, le discussioni PR o l'accettazione Owner di GOAL-01, ma conferma che **non si puo' assumere che il processo di code review GitHub sia gia' completato**. Non estrapolare a tutte le 34 PR: il controllo non e' esaustivo.

**Decisione tecnica ancora da preparare:** approvazione per una prima review aggregata del prodotto da HEAD #94 verso main o merge sequenziale delle 34 PR preservando tracciabilita'. Va simulato su clone e analizzata la parita' dei commit/finali prima di scegliere. La scelta non e' automatica e non va delegata implicitamente a Codex.

## CRITICAL REVIEW GATE — Hook `before_request` potentially overwritten (#97)

**Blocco audit con codice verificato; impatto runtime ancora NON dimostrato.** [Issue tecnica #97](https://github.com/2008hitch-afk/centrochange_core/issues/97).

Nel file `app/centrochange_core/centrochange_core/hooks.py` del candidato **RC22 source `f06acca...`**:
- linea 13: `before_request` e' definito con quattro guard originari (finance, diagnostics, security API, note);
- linea 151: `before_request = ["centrochange_core.operations.website_brand.client_language"]` **sovrascrive la lista** invece di estenderla;
- linea 154: un `.append(login_language)` estende solo la nuova lista.

Il primo overwrite compare nella PR **#92** (non presente nell'head #91) e rimane nei successivi #93/#94. **Questo fatto e' staticamente certo per la semantica di Python**, ma il grado di protezione effettivo di ciascuna route HTTP richiede un test reale Frappe, con `frappe.get_hooks('before_request')` e prove negative di accesso. Non affermiamo che esista un exploit reale senza prova.

**Disposizione di audit: HOLD qualsiasi merge/promotion della catena di prodotto** fino al controllo mirato e, se confermato, correzione in PR con regressione #77 e controllo backend/API/print/report. **Questa Missione A non autorizza il fix, l'accesso al runtime o un deploy**; per questi serve mandato tecnico distinto.

### Divergenza del ramo principale rispetto a RC22

Il compare GitHub `main` vs HEAD #94 ha dato: **155 commit avanti sul ramo prodotto, ma 6 commit di main assenti dal ramo UAT**; merge-base `a648323d645517154cf2e8f7a21e5387e412f47e`. I sei commit aggiungono aggiornamenti di governance e GOAL-02: `1f951b7`, `12f010b`, `912a64a`, `176a690`, `c83431c`, `a3c34a7`. Sono modifiche da **conservare e conciliare**, non da sovrascrivere con un reset o force push. Almeno `AGENTS.md` e `docs/MVP-GOAL-ROADMAP-v0.1.md` risultano tra i file modificati da main rispetto al branch prodotto.

**Strategia candidata, non autorizzata al merge:** provare localmente la sequenza bottom-up **merge commits** #27→#94, con `main` come base finale e retarget controllato di ciascuna PR dopo il predecessore; **evitare squash/rebase/force-push indiscriminati** che perdano comparabilita' del diff stacked. Dopo trial confrontare tree di prodotto con RC22 e `AGENTS.md`/roadmap con la governance main. La strategia deve essere verificata prima di ogni merge e potra' essere rivista in base all'esito.

### Tracciabilita' versione fonte / review HEAD

Compare `f06acca4...` → `84e9df1e...`: **solo 2 commit, 19 file**: 18 sotto `docs/`, 1 sotto `infra/`, **nessun file `app/` modificato**. Quindi il problema hook e' presente anche nell'esatto archivio applicativo di RC22, non soltanto nel branch review.

### Review complete (metadata)

API GitHub `list_pull_request_reviews` interrogata per **tutte e 34 le PR prodotto**: **zero review submissions registrate per 34/34**. Le evidenze/test runtime sono separate e restano da correlare; questa osservazione non e' da sola un verdetto sulla qualita' del prodotto. La review dei **diff e dei guard** e' ancora parziale e NON deve essere dichiarata completa.

### Rischio migrazioni future — ciclo `after_migrate`

La funzione `centrochange_core.finance.install.configure` e' configurata in `hooks.py` anche come `after_migrate` e cancella/ricrea `Custom DocPerm` su docTypes finanziari e master contabili. Non e' un difetto provato, ma crea un **gate di verifica su aggiornamento e ripetibilita' migrazioni**: verificare che refresh dei permessi resti intenzionale/idempotente e non espanda grants durante upgrade verso versione nuova, sempre su clone isolato. Non correggere in Missione A.
