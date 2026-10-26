# Missione Codex #97 — Verifica e ripristino di `before_request`

**Cliente:** HC-0005 — Centro Change  
**Autorita':** Owner ha esplicitamente **autorizzato** in chat 2026-10-08 questa **singola missione tecnica limitata**: prove in ambiente isolato; fix minimo se il problema e' confermato; nuova PR e regressioni.  
**Issue autoritativa:** [#97](https://github.com/2008hitch-afk/centrochange_core/issues/97)  
**Programma/controllo:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95); [Piano Missione A](CENTROCHANGE-MISSION-A-AND-UNIFIED-DESK-ROADMAP-2026-10-08.md)  
**Stato:** `OWNER_AUTHORIZED_FOR_CODEX`; esecuzione **non attestata** finche' Codex non restituisce evidenze/PR.  
**Durata:** questa sola esecuzione, fino a consegna `READY_FOR_REVIEW` o `DECISIONE RICHIESTA`; nessuna delega permanente.  
**Writer:** Codex; ChatGPT/HITCH coordina e verifica, non modifica il runtime.

## 1. Contesto esatto di partenza

Repo: `2008hitch-afk/centrochange_core`.  
Branch prodotto da cui partire: `issue-75/final-client-ux-review`.  
HEAD osservato: `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`. Prima di creare il branch rileggerlo e fermarsi se cambiato senza documentare/riconciliare le differenze.  
Immagine UAT corrente da **non toccare**: `centrochange-uat:goal02-20261008-rc22`; source commit `f06acca4f6c2ac757dbd3e187709f94b18554b65`; Owner retest #75 ancora pending.  
Stack corrente pinned: Frappe 16.31.0, ERPNext 16.32.0, Marley 16.5.2, Builder 1.33.0.

**Anomalia statica confermata** nel file `app/centrochange_core/centrochange_core/hooks.py`:
- riga 13: `before_request` ha quattro guard: `finance.request_guard.before_request`, `security.diagnostics.before_request`, `security.api.before_request`, `operations.notes.request_guard`;
- riga 151: la variabile `before_request` viene **riassegnata** a `[operations.website_brand.client_language]`, eliminando le quattro entries nella configurazione di modulo finale;
- riga 154: `before_request.append(operations.website_brand.login_language)` aggiunge solo il secondo hook di presentazione.

La riassegnazione compare in #92, resta in #93 e #94. **NON dedurre da questo, da solo, la sfruttabilita' runtime o fuga dati**.

## 2. Scope esatto — ordine di esecuzione

### FASE 0 — Preflight senza scritture

1. Leggere `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `docs/DECISIONS.md`, `docs/RUNTIME-BASELINE.md` e issue #97.
2. Verificare branch UAT, commit sorgente, stato immagini e servizi; **non cambiare** branch/volumi/site/image del candidato RC22 condiviso.
3. Creare branch di lavoro dedicato `issue-97/before-request-guards` dal HEAD esatto del prodotto `issue-75/final-client-ux-review` (o interrompere se un altro writer ha modificato il source HEAD).
4. Identificare runtime **isolato**, nome Compose/site/porte/volumi distinti, dataset sintetico riproducibile, senza riutilizzare mount DB/volumi/credenziali del corrente UAT. Se isolamento non dimostrabile, `DECISIONE RICHIESTA` e non avviare servizi o migrazioni.

### FASE 1 — Prova discriminante, prima di correggere

1. Consultare sorgente ufficiale Frappe **pinned** per semantica `before_request`, esecuzione ordine hook ed eventuali contributi di altre app. Registrare riferimento upstream esatto.
2. Sul clone isolato, verificare il valore reale di `frappe.get_hooks('before_request')` e il percorso delle quattro funzioni originali; distinguere contenuto di `hooks.py`, risoluzione hook e invocazione HTTP.
3. Eseguire richieste HTTP realmente autorizzate e vietate, senza usare dati reali: professionista assegnato/non assegnato, segreteria, Finance, accountant, Manager e Guest. Testare in modo particolare:
   - endpoint/report nativi contabili che `finance.request_guard.before_request` dovrebbe bloccare per non-manager (compresi report `frappe.desk.query_report` e metodi ERPNext pertinenti);
   - API e endpoint che usano `security.api.before_request`, `security.diagnostics.before_request` e `operations.notes.request_guard`;
   - print/export, lista/diretto/documento, cross-center e privacy delle note, con negative **HTTP**, non solo menu UI;
   - funzionamento di login e selezione lingua che devono rimanere attivi.
4. Registrare **BEFORE** con prova oggettiva e precisa: `CONFIRMED_RUNTIME_GAP`, `NO_RUNTIME_IMPACT` o `INCONCLUSIVE`. Una prova di bypass va trattata con minimi dettagli necessari nel report e nessun dato paziente.

### FASE 2 — Fix minimo solo se confermato o se il difetto di configurazione e' riproducibile

1. Correggere il doppio assegnamento `before_request` componendo **una lista unica con tutti i guard originali + `client_language` + `login_language`**, nell'ordine motivato dai controlli e dalla versione pinned; non duplicare hook.
2. Non modificare modello dati, ruoli, API, finanza, logica appuntamenti o provider se non indispensabile; qualsiasi estensione sostanziale richiede `DECISIONE RICHIESTA`.
3. Aggiungere un test di regressione che fallisca se la composizione hook torna a essere sovrascritta; preferire assert sui hook reali della app più una discriminazione HTTP.
4. Niente core patch Frappe/ERPNext/Healthcare/Builder, monkeypatch permanente, overlay non versionato o editing nei container running.
5. **Se la prova smentisce il difetto operativo**: non eseguire un fix superfluo; presentare evidenze `NO_RUNTIME_IMPACT` e una motivazione di conservazione/correzione opzionale separata, poi fermarsi per review.

### FASE 3 — Verifica e consegna

1. Ricostruire una immagine **isolata** e ripetibile dai commit esatti della PR proposta.
2. Ripetere `frappe.get_hooks`, prove HTTP positive/negative, #77 permission matrix, suite Finance, Agenda, Website pubblico/login, report/export/print e cache boundary; test su ruoli e centri.
3. Controllare che dati e contatori del clone rimangano invariati dopo i test (rollback completo), e che **dataset RC22 e runtime UAT originale non siano stati mutati**.
4. Eseguire `git diff --check`, controlli sintattici e per-file, clean source/image parity e health dei servizi isolati.
5. Aprire una **PR tecnica DRAFT** da `issue-97/before-request-guards` verso `issue-75/final-client-ux-review` (NON verso `main`, la catena stacked deve restare integra), collegata a #97 e #95. Indicare SHA base/head, diff esatto, `PASS/PARTIAL/FAIL`, scenario before/after, prove e rischi.
6. Non fare merge, non modificare `main`, non cambiare la PR #94 o i branch #92/#93, non creare nuovo RC/tag/deploy sul runtime UAT, non chiudere #97.
7. Restituire `READY_FOR_OWNER_REVIEW` **solo** se prove discriminanti e regressioni PASS; altrimenti `PARTIAL/FAIL — DECISIONE RICHIESTA`.

## 3. Condizioni tassative di arresto

- Isolamento ambientale insufficiente, necessità di usare volumi o account attuali, dato reale o segreto, interferenza con UAT RC22.
- Problema più ampio di un fix minimo dei hook, incompatibilità upstream o differenza materiale di permessi/contabilità/schema.
- Necessità di `migrate` / `restore` / `reset` **nel runtime condiviso**; stop.
- Test HTTP mostra dati sensibili o accessi inattesi: documentare in modo riservato e fermarsi per review; non esplorare altre esposizioni senza nuovo scope.
- HEAD prodotto cambiato e non riconciliato, conflitti Git, necessità di force push o merge.
- Non entrare in GOAL-03, upgrade 16.50 o migrazione Desk.

## 4. Deliverables e criteri di accettazione

- Report `#97 — before/after` con identificazione dei hook effettivi, Frappe pinned source, test HTTP e ruolo per ruolo.
- Una PR DRAFT minima oppure un rapporto discriminante `NO_RUNTIME_IMPACT` senza fix, se la questione è falsificata.
- Prove versione/build e non-interferenza con RC22.
- Stato finale aggiornato sulla issue #97 e nel collegamento a #95.
- Nessuna modifica sul ramo `main`, sulla chain #27→#94 o sul runtime RC22. Nessuna approvazione Owner simulata.

**Autorizzazione:** l'Owner ha approvato il mandato limitato; gli step eccedenti questa descrizione NON sono autorizzati. Si applicano `AGENTS.md` e governance HITCH corrente.
