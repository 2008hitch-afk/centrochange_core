# Centro Change — Mandato operativo Premium React Frontend (macro-goal #148)

**Versione:** 1.0 — 21/10/2026
**Stato storico al 21/10/2026:** OWNER AUTHORIZED, EXECUTION NOT YET STARTED
**Cliente:** HC-0005 / CASE-001 / IMPLEMENTATION-001 / ITERATIVE_BUILD_INTEGRATION
**Goal:** `CENTROCHANGE-PREMIUM-FRONTEND-REBUILD` — [issue #148](https://github.com/2008hitch-afk/centrochange_core/issues/148)
**Autorità:** [HC-0005 DECISION-061](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-061-authorize-premium-react-frontend-macro-goal.md), approvazione Owner 21/10/2026.
**Architettura:** [HC-0005 DECISION-060](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-060-premium-react-frontend-architecture.md).
**Natura:** work package frontend aggregato nel perimetro funzionale MVP approvato, **NON GOAL-03**.

> Aggiornamento 22/10/2026: questo è il mandato iniziale della DECISION-061, conservato per tracciabilità. Le successive DECISION-062–066 e i report di #148/PR #150 documentano single-stack, API, tentativi DEV e correzioni; per autorizzazioni operative usare il mandato corrente dell'issue. Il consolidamento #156 non autorizza nuovi deploy, migrate o merge.

## 1. Risultato

Consegnare un **frontend React dedicato, premium, funzionante e verificato**, con esperienza ispirata ai principi UX di Fresha e **logo/colori originali Centro Change** ricavati dal sito https://www.centrochange.it/, senza copia di asset, marchi o codice Fresha. Deve essere una sola applicazione coerente per tutti i workflow autorizzati, non una dashboard superficiale.

**Frappe, ERPNext, Marley Healthcare e `centrochange_core` restano fonti autorevoli di dati, permessi, processi, audit, documenti clinici e contabilità.** Non replicare motore contabile, database, identità o backend. L'utente deve vedere Centro Change, non Desk tecnico, salvo un'area amministrativa tecnica separata e autorizzata.

`READY_FOR_OWNER_VISUAL_UAT` richiede prove vere sulla build React (copertura funzioni, test mutativi sicuri, protezione dati, fluidità, QA visivo desktop/mobile e riproducibilità). Se un controllo rilevante manca: `PARTIAL` o `BLOCKED`; **non è Owner PASS, merge, cutover, GOAL-02 DONE o produzione**.

## 2. Autorità e priorità

Ordine: governance HITCH > decisioni HC-0005 approvate > issue #148 e `AGENTS.md` > baseline autorizzata, documentazione/sorgente pinned, runtime > skill consultive.

- DECISION-060 sostituisce la **preferenza di frontend nativo Frappe** del 12/10 per la UX cliente; il principio native-first **rimane per backend/ERP/Marley/DocTypes**.
- DECISION-061 autorizza lavoro isolato su branch/worktree, skill FOSS selezionate dopo verifica e test non distruttivi; **non** una nuova installazione DEV condivisa, attivazione server, nuova licenza, merge di prodotto o cutover.
- #139 è il precedente workstream remediation Frappe-first: riusare diagnosi, test e fix pertinenti, instradare **solo la UI sovrapposta** al nuovo frontend React, preservando #139 come archivio/tracker del rehearsal. Non eseguire due UI finali in parallelo.
- PR #133/#138/#140: leggere gli HEAD attuali, dipendenze e prove, riusare soltanto contributi tecnicamente verificati; nessun merge o reset automatico. Missione C #109 e PR #112 restano sospesi/DRAFT.
- Issue GOAL-02 #23 risulta `closed` su GitHub, ma manifest/run cliente ancora `AUTHORIZED_ACTIVE`. Registrare la discordanza, **non correggerla implicitamente**. GOAL-03 non autorizzato.
- Nessuna modifica automatica di `main`; creare un solo ramo implementativo principale e PR DRAFT collegata a #148 (o stack ordinato giustificato).

## 3. Architettura target (da dimostrare tecnicamente)

```text
Centro Change React (client-facing, stessa origine preferita)
   └─ HTTPS / Frappe session + CSRF / API di dominio autorizzate
       └─ sito Frappe esistente (backend canonico)
           ├─ centrochange_core
           ├─ Marley Healthcare
           ├─ ERPNext
           └─ DB / scheduler / workers / audit già previsti
```

**Same-origin React integrato nel sito Frappe** è preferenza architetturale, non fattibilità data per dimostrata: verificare versioni Frappe pinned, layout assets/bundle, routing e refresh URL diretti, login/logout, cookie/SameSite/CSRF, CORS, gestione errori, websocket, manifest/hash/cache, stabilità e upgrade. Non introdurre automaticamente un secondo sito, database, server auth o un ERP parallelo.

Ogni screen/azione usa endpoint di dominio con **permessi server-side** verificati: non fidarsi della sola UI, del nascondere pulsanti o dei generici endpoint CRUD DocType. Verificare accesso diretto/API/query/list/export/report, scope di centro e paziente/professionista, note cliniche riservate, fatture, banca e audit. Distinguere formattazione/presentazione da nuove business rules e modifiche di schema (stop autorizzativo per le seconde se materiali). Backend e dati canonici invariati.

Lockfile e versioni esatte di librerie, skill e asset, licenze conservate; nessun CDN obbligatorio runtime o patch manuale nei container. Documentare build, rollout potenziale e rollback senza eseguirlo sul DEV condiviso.

## 4. Brand, Fresha e librerie (candidati, non acquisti)

- **Originale Centro Change:** recuperare asset/logo/favicon/varianti e palette CSS effettiva da `centrochange.it`, annotando URL, licenze, qualità e consenso di riuso. Non inventare un logo, non presumere che il vecchio `#12665F` equivalga al brand attuale. Confermare con Owner se risulta ambiguo.
- **Fresha** è benchmark per Agenda protagonista, densità professionale, calendario e viste professionisti, sidebar essenziale, navigazione fluida, ricerca rapida, pannelli/drawer e microinterazioni. Non clonare interfacce proprietarie, brand, codice o screenshot nel prodotto.
- **Una libreria UI principale**, proposta `Untitled UI React` versione FREE se licenza e compatibilità reali consentono; alternativa motivata documentando qualità e costo. `FullCalendar Standard` candidato per calendario; resource views/Scheduler sono premium, **nessun acquisto o uso commerciale non licenziato senza Owner**.
- Skill repo-local `.agents/skills/centrochange-premium-ui/SKILL.md`; Anthropic frontend-design, Vercel react-best-practices, web-design-guidelines, UI/UX Pro Max e OpenAI frontend-testing sono **candidate da revisionare**, non installazioni automatiche. Per ogni skill verificare origine, licenza, commit, script, compatibilità e scope. Non eseguire installer web/remoti, script mutevoli, `npx` indiscriminati o installazioni globali.
- Design tokens versionati (brand, semantici, focus/disabled/hover/selected, font, spacing, radii, breakpoints e z-index). Componenti unici per shell/sidebar/header, toolbar, tabelle, filtri, combobox, form, modal/drawer, feedback, notifiche, status, calendario.
- Agenda è landing per ruoli autorizzati. Nessuna doppia barra, schermata splash superflua, branding Frappe/ERPNext/Marley client-facing, icone enormi o tecnicismi grezzi.
- Lingua italiana ovunque per persone (login, messaggi di validazione/errori, email, report, stampe/esportazioni umane), date **`GG/MM/AAAA`**, orari **`HH:mm`**, Europe/Rome, importi `it-IT` e DST; preservare formato canonico/API/XML/SdI/TS.
- Ricerca e selezione (#79): una combobox verticale ricercabile per entità numerose, bounded server queries, tastiera/mouse/touch, loading/empty; un normale select per pochissime opzioni; niente griglie di pulsanti inutili.

## 5. Matrice obbligatoria (scope invariato)

Inventariare **ogni schermata e ogni azione**:
`route | business task | role | API/method | authoritative Doctype | read/write | permission boundary | test ID | visual baseline | state`. Classificare `PRESENTE`, `BACKEND_AVAILABLE_UI_MISSING`, `GAP_API`, `DEFECT`, `DEFERRED`, `OUT_OF_SCOPE`.

| Area | Copertura da verificare |
|---|---|
| Login/shell | autenticazione, sessione, profilo e ruolo, Agenda landing, logout/error |
| Agenda/Disponibilità | calendario per professionista, prenota/sposta/cancella/chiudi, concorrenza, regola 48h |
| Pazienti/Professionisti | anagrafiche, ricerca, schede, assegnazioni, storico, permessi |
| Primo incontro | flusso pubblico Guest secondo soggetti abilitati e protezioni |
| Sedute/Note/Pacchetti | stati e azioni lecite, note private e rettifiche, storico prima/dopo, saldi |
| Catalogo/Tariffe | Item, Item Price, Appointment Type, servizi centro e modelli pacchetti |
| Finanza | fatture pazienti e professionisti, pagamento, crediti, documenti, contabilità nativa |
| Banca | movimenti, import, riconciliazione assistita, documento riconciliato |
| Economia professionisti | compensi, soglie non incassato, tariffe storiche e report |
| Report/Dashboard | azioni comprensibili, indicatori, export e drill-down autorizzati |
| Admin/Accessi | ruoli, notifiche, eccezioni, audit, gestione e impostazioni permesse |
| Centri | oggi solo Centro A attivo, Centro B futuro inattivo, enforcement server #135 |
| SdI/TS | vista amministrativa chiara, **solo processi simulati**, nessun invio reale |
| Trasversale | italiano, date/orari, error/loading/empty, mobile, stampa e export |

Le **11 liste native + le 11 schede** difettose durante UAT #136 devono avere flussi equivalenti integri nel nuovo frontend o restare confinate a un Desk tecnico separato, con tracciamento per ruolo. Riutilizzare i test storici **128 route×ruolo×device** e **38 test security** (#137/#139), ma **rieseguirli sul candidato React**; un PASS temporaneo prima del rollback non vale come PASS corrente.

**Nessuno scope creep:** non implementare implicitamente capability `DEFERRED` o nuove automazioni fiscalità/commercialista, né cambiare semantica contabile, 48h, note, pacchetti, compensi, privacy e stati storici.

## 6. Un unico macro-goal — W0...W7

### W0 — Preflight Git, runtime e piano by-difference
Rileggere README, ARCHITECTURE, SECURITY, docs/DECISIONS, RUNTIME-BASELINE, AGENTS, decisioni HITCH/run/manifest, #148 e backlog UAT; HEAD/branch/status delle PR DRAFT #133/#138/#140/#112 e worktree non committati. Nessun `reset --hard`, `clean`, cancellazione volumi o perdita demo. Verificare CPU/RAM/PSI/IO/disco/host isolation, backup/rollback; non presumere che `main` = DEV installato. Preflight READ-ONLY verso DEV; se serve accesso ulteriore o clone server, chiedere gate.

### W1 — Supply chain, brand e baseline visuale
Verificare skill e librerie candidate (licenza, SHA, script, accesso repo-local), installare solo quelle gratuite realmente ammissibili in workspace isolato dopo review, niente download non verificati. Brand asset audit originale, reference Fresha-based senza copia, screen/layout riferimento Agenda, Paziente, Finanza desktop/mobile; design contract prima di implementazioni massificate. Pagamenti o dipendenze commerciali = stop.

### W2 — Contratti frontend/backend
Mappare API/funzioni/ruoli/guard con prove; session/cookie/CSRF e routing same-origin realmente supportato; DTO e localizzazione errori; no data leakage. Estensioni minime solo se conformi ad autorizzazione e security review; nuovo paradigma DB/permessi/API = stop.

### W3 — Foundation UI condivisa
App shell unica, sidebar e topbar role-aware, Agenda default, tokens, tipografia, table/form/filter/search-select, drawer/modal, toast, skeleton/loading/empty/error, responsive e accessibilità. Niente page-by-page CSS ad hoc. Verificare una superficie canonica prima del rollout.

### W4 — Agenda e operatività
Agenda multirisorsa se legalmente/tecnicamente disponibile, booking/move/cancel/closure e regressioni, note/history, pazienti/professionisti, disponibilità, pacchetti, catalogo, primo incontro autorizzato. Ogni workflow ha test positivo/negativo e screenshot della build effettiva.

### W5 — Finance, amministrazione e reporting
ERPNext authoritative Sales/Purchase Invoices, Payment Entry e Bank Transaction, riconciliazioni, compensi/soglie, coda eccezioni, centri e accessi, notifiche, audit, report; SdI/TS **simulati**. UI guidata (cosa fare, perché, stato documento) preservando tutti i permessi e documenti nativi.

### W6 — QA e correzioni autonome ordinarie
Typecheck/lint/unit/integration, Playwright su **desktop 1440×900 / mobile 390×844**, almeno matrice storica 7 ruoli + Guest, routing diretto, screenshot/console/errors/empty/loading/focus/keyboard/overflow; test API server-side positivi/negativi per paziente/centro/note/export. Test che mutano dati **solo in fixture isolate, revocabili e fingerprint/cleanup verificati**. Test DST Europe/Rome e formato human vs machine. Performance p50/p95 su navigazione e aggiornamento Agenda, baseline e hardware fissati prima dell'ottimizzazione finale; niente numeri inventati. Zero P0/P1 security/integrity aperti.

### W7 — Candidate e report finale
Una PR implementativa **DRAFT** o stack ordinato giustificato, report completo di diff/commit/build SHA, screenshot sintetici, coverage route/ruolo/API/test, gap, performance p95 e risultati sicurezza. `READY_FOR_OWNER_VISUAL_UAT` solo quando i gate sono realmente PASS; in caso contrario `PARTIAL`/`BLOCKED`. Proprietà Owner per accettazione finale e futuro rilascio.

Le fasi sono **workstream interni**, non goal separati. Continuare sui bug ordinari entro il limite autorizzato, fermarsi solo a gate materiali.

## 7. Definition of Done

1. **Funzioni:** 100% delle schermate/azioni **autorizzate** mappate con evidenza per i ruoli applicabili, senza includere rinvii non approvati.
2. **11+11 UAT:** nessuna UI rotta cliente; componenti CSS/JS/font reali, no HTTP 200 interpretato come rendering PASS; verifiche di liste e form desktop/mobile.
3. **Brand/Design:** logo e palette originali verificati, Fresha-inspired senza copia, componenti uniformi, navigazione fluida senza splash, Agenda prima pagina, screenshot per tutte le aree.
4. **Italiano/Date/Ore:** `it-IT`, `GG/MM/AAAA`, `HH:mm`, `Europe/Rome`, messaggi d'errore contestuali, contratti tecnici intatti.
5. **Sicurezza:** test permission negatives su API/URL dirette/report/export, separazione Centro A/B e note private, nessuna regressione critical/high.
6. **Browser QA:** matrice ruoli/Guest, desktop/mobile, scenari di successo/errore/loading/empty, test integrati realmente eseguiti e screenshot non falsamente accettati.
7. **Performance:** baseline comparabile su hardware/fixture uguale, p95 nav e refresh Agenda, target prefissati e misurati; se assenti `PARTIAL`.
8. **Riproducibilità:** pin, lockfile, licenze, asset autorizzati, build/test/rollback riproducibili, no patch nascoste.
9. **Evidenza:** `PREMIUM-FRONTEND-GOAL-COMPLETION-REPORT.md` con coverage, test ID, SHA, screenshot sanitizzati, benchmark, unknown, known limitations, issues/PR e owner-review checklist.
10. **Stati:** `READY_FOR_OWNER_VISUAL_UAT` != Owner acceptance != GOAL-02 closure != production. Goal Learning Extraction esclusivamente come `CANDIDATE` sanitizzati.

## 8. Stop gates (nessun bypass)

Codex deve fermarsi e formulare una domanda mirata all'Owner, ma continuare ogni attività indipendente e sicura, se occorrono:

- licenza PRO/premium, nuovo fornitore/spesa, asset/logo non riutilizzabile o diritti incerti;
- nuova regola clinica/economica, modifiche materiali di DocType/API/permission/security, incompatibilità architetturale;
- dati reali, secret, provider, traffico SdI/TS/PEC/SMTP reale;
- **installazione, terzo deploy, migrazione, restart, image load, restore o qualunque write al DEV condiviso**;
- creazione/attivazione di clone, nuova topologia o mutazioni host/server senza specifica approvazione target/risorse/rollback;
- rischi RAM/disk/PSI/IO, impossibilità di restore, identità clone incerta o perdita dati;
- merge non documentale delle PR, cutover della UI primaria, GOAL-03, produzione, go-live e Owner PASS;
- informazioni autorevoli mancanti su decisioni materiali.

Il possesso di `sudo` o accesso root **non amplia mai l'autorizzazione**.

## 9. Deliverable obbligatori

`ARCHITECTURE-REACT-FRAPPE.md`; `API-ROLE-CONTRACT-MATRIX`; `BRAND-ASSET-AUDIT.md`; `DESIGN-TOKENS`; `COMPONENT-CATALOG`; `UX-VISUAL-REFERENCE`; `FUNCTIONAL-COVERAGE`; `LICENSE-INVENTORY`; `QA-RESULTS`; `SECURITY-RESULTS`; `PREMIUM-FRONTEND-GOAL-COMPLETION-REPORT.md`.

Riferimenti principali: `AGENTS.md`, `ARCHITECTURE.md`, `SECURITY.md`, `docs/RUNTIME-BASELINE.md`, issue #75/#76/#77/#79/#134/#135/#136/#137/#139/#148, PR #133/#138/#140, HITCH DECISION-060/061; documentazione ufficiale e sorgente **version pinned** di Frappe/ERPNext/Marley. Prima di qualsiasi commit tecnico rileggere lo stato reale del repo e dei target.

**Decisione dell'Owner del 21/10/2026: autorizzazione isolata APPROVATO.** Il testo serve come mandato di esecuzione **solo dopo che Codex è stato esplicitamente avviato dall'Owner e ha risolto la issue #148 e DECISION-061**.
