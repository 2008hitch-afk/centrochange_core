# Missione C #109 — parità GOAL-02 e confine Desk cliente

**Stato:** `MISSION-C: PARTIAL`, `READY_FOR_OWNER_UAT: NO`. Prodotto PR DRAFT #112, stacked sulla PR DRAFT #107. La demo C109 già attiva usa la revisione UI precedente `6c837042`; il delta di questo rapporto è **offline** e non va attribuito alla sua immagine. RC22 rimane il riferimento GOAL-02 e non è stato modificato.

La matrice C1 in `C1-NATIVE-FIRST-REALIGNMENT-REVIEW.md` documenta il fit dei componenti ufficiali Frappe/ERPNext/Healthcare pinned. Questa tabella registra la parità applicativa, la scelta Desk e la prova ancora richiesta. `PARTIAL` significa che codice o risultati storici esistono, ma la versione finale non è stata collaudata integralmente.

| # | Area GOAL-02 / riferimento RC22 | Scelta nel Desk Centro Change | Parità sulla HEAD #112 | Prova finale ancora necessaria |
| --- | --- | --- | --- | --- |
| 1 | Agenda settimanale multi-professionista | Page custom CC; List Appointment nativa non rende la griglia autorizzata | PARTIAL | browser 7 giorni, A/B/C, geometria e direct API |
| 2 | Prenota, sposta, cancella | Dialog CC e servizio booking canonico, non save nativo | PARTIAL | tre mutazioni, collisione, snapshot prezzo, audit |
| 3 | Seduta, storico, note | Pannello CC con guard note | PARTIAL | dettaglio e negative private note A/B/C/Segreteria |
| 4 | Pazienti | Patient List/Form nativi per Manager; ricerca CC scoped per altri | PARTIAL | List/Form/direct/query/export/print per ruolo |
| 5 | Professionisti | Healthcare Practitioner List/Form per Manager/self; selettore CC scoped | PARTIAL | self, Segreteria, C senza assegnazioni |
| 6 | Disponibilità | Editor CC; native schedule in sola lettura dove autorizzata | PARTIAL | modifica, assenze e direct-write denied |
| 7 | Catalogo, tariffe, pacchetti | Item/Item Price/Appointment Type e DocType CC nativi per Manager; ledger CC | PARTIAL | prezzi, pacchetti, route negative |
| 8 | Contabilità e registri | List/Form ERPNext dove i guard CC consentono | PARTIAL | cross-center/query/export/print |
| 9 | Fatture paziente e professionista | Sales/Purchase Invoice native read; servizi CC per mutazioni | PARTIAL | emetti, paga, rettifica, annulla, negative |
| 10 | Incassi e pagamenti | Payment Entry nativo; creazione via servizi CC | PARTIAL | documenti canonici, actor, residuo, negative |
| 11 | Banca | Bank Transaction/Account native read; riconciliazione CC | PARTIAL | reconcile/undo/idempotenza |
| 12 | Report Centro/Professionisti/Pazienti | Page custom CC per proiezioni e drill-down scoped | PARTIAL | KPI=record, payer condiviso, periodi/export |
| 13 | Report ERPNext generici | 403 dei guard CC per non Manager | DECISION GATE | negative HTTP/query/export; nessun nuovo grant |
| 14 | SdI simulato | DocType CC native read e azioni CC | PARTIAL | versioni/attempt append-only, no provider |
| 15 | TS simulato | DocType CC native read e azioni CC | PARTIAL | eligibility/correction chain, no provider |
| 16 | Audit | CC Audit Event List/Form nativa Manager | PARTIAL | campi, append-only, direct/export negativi |
| 17 | Gestione accessi e centri | Workflow CC; non esporre User/Role generici | PARTIAL | revoca immediata, direct API negative |
| 18 | Compensi e coda amministrativa | DocType CC native read + override/compare CC | PARTIAL | soglia, sospensione, Manager vs Finance |
| 19 | Notifiche e job | Coda CC custom | PARTIAL | retry/idempotenza e destinazione |
| 20 | Login/logout | Auth Frappe nativa, branding versionato | PARTIAL | sette ruoli, Guest, 403 e logout sulla build finale |
| 21 | Primo incontro pubblico | Sito Frappe separato dal Desk | PRESERVED | Guest bounded sul sito; nessun bridge Desk |
| 22 | Stampa ed export | Print/List native autorizzate, export CC scoped | PARTIAL | output e negative cross-center/private note |
| 23 | Validazione DEV | Pagina tecnica separata | PRESERVED | esclusione da navigazione cliente |
| 24 | Identità/cutover | Desk sperimentale; RC22 primaria | OWNER DECISION | confronto C3, nessun cutover automatico |

## Delta implementato offline

- `app_include_js` e `app_include_css` Frappe caricano una barra Centro Change anche quando l'utente attraversa List/Form native. La barra è differenziata per i cinque ruoli CC, mostra nomi italiani e non si applica a `Administrator`, `Guest` o utenti con ruolo tecnico. Gli asset sono locali e versionati. Il contenuto nativo List/Form resta nativo.
- Un controllo sintetico read-only `security.desk_boundary_acceptance.run` verifica per sette utenti l'assenza di `System Manager`/`Website Manager`, l'impossibilità di leggere Builder e di mutare DocType di configurazione. È **preparato**, non eseguito sul runtime finale; accessi diretti HTTP/API/query/export/print richiedono prove aggiuntive. Il menu è presentazione, non un permission guard.
- La Page Desk conserva i quattro workflow custom già motivati in C1 e l'Audit List nativa. I servizi, documenti, contabilità e dataset sono invariati.

## Evidenza e limiti

`node infra/mission_c_desk_shell_offline.cjs` → **PASS**, sette profili simulati; `PYTHONPATH=infra python3 -m unittest discover -s infra -p 'test_c109_*.py'` → **44/44 PASS**; `node --check` → **PASS**; `python3 -m py_compile` → **PASS**; `git diff --check` → **PASS**. Il browser QA esistente ora acquisisce barra/route native per ruolo, ma **non è stato eseguito** sulla nuova immagine. Questi controlli offline non dimostrano la resa visuale, l'autenticazione reale o la protezione server-side. La demo C109 precedente ha confermato solo ping, login tecnico e caricamento della Page sulla sua immagine, non il nuovo shell né la parità funzionale.

Per `READY_FOR_OWNER_UAT` serve una nuova finestra operativa che copra build/deploy isolati e la matrice discriminante sulla **stessa immagine**: sette profili cliente più Guest e Administrator HITCH, native List/Form, quattro workflow custom, API/direct/query/export/print, desktop/mobile, contabilità, C3 con RC22 senza mutarlo. Devono restare 2 GiB runtime + 512 MiB QA, watchdog, limiti PSI/OOM/I/O, stop al primo guardrail e rollback verificabile. La finestra visuale 09:39–13:39 UTC non autorizza questo collaudo.

**Gate materiale residuo:** autorizzazione separata della finestra di collaudo C109 della nuova immagine. Nessun merge, cutover o cambio di policy autorizzativa è incluso.
