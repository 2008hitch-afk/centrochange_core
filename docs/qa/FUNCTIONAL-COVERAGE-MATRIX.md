# Centro Change — Matrice requisiti ↔ UI Premium ↔ backend (audit #157)

**Stato:** `AUDIT-00_COMPLETE / BASELINE_OPERATIVA_APPROVATA / PR_159_DRAFT_UNMERGED` — 22/10/2026. L'Owner ha autorizzato l'avvio del ciclo per interfaccia; **non** ha approvato come PASS le singole funzionalità, il merge della PR o il passaggio in produzione.
**Master:** [#156](https://github.com/2008hitch-afk/centrochange_core/issues/156) · **Inventario:** [#157](https://github.com/2008hitch-afk/centrochange_core/issues/157) · **Prima area:** [Login #158](https://github.com/2008hitch-afk/centrochange_core/issues/158).  
**Regola:** questa matrice è un **indice verificabile di ciò che va controllato**, non un certificato di completezza, UAT o conformità. NESSUNA area è ancora `OWNER_DONE`.

**Dettaglio per funzione:** [110 righe CSV](FUNCTIONAL-COVERAGE-DETAIL.csv), con fonte, decisione, perimetro, UI/API/backend separati, DocType, ruoli, dipendenze, prova, stato, issue, gap e approvazione Owner. [Inventario delle schermate, controlli e 11 archivi](PREMIUM-REACT-INTERFACE-INVENTORY.md). I 50 ID originari sono tutti presenti: `CC-CAP-006` è scomposta in prenotazione, spostamento/cancellazione e storico; 28 requisiti/limiti successivi `CC-EXT-*` coprono decisioni, UAT e vincoli che non erano nell'indice iniziale; 30 azioni `CC-ACT-*` scompongono processi composti. **110 righe ≠ 110 nuove funzionalità approvate**: alcune sono escluse, rinviate, gate o verifiche trasversali.

| Stato puntuale | Righe | Significato in questo audit |
|---|---:|---|
| `PASS` | 2 | Solo due percorsi UAT mirati, con prova `LIVE-22` precedente; Owner ancora `PENDING` |
| `PARTIAL` | 61 | Codice e/o prove parziali; manca almeno una verifica del requisito completo |
| `NOT_TESTED` | 35 | Nessuna prova specifica sufficiente per l'azione o il processo |
| `BLOCKED` (storico) | 12 | **8 fuori perimetro/rinviati/sostituiti**, **3 non autorizzati**, **1 gate di attivazione React in attesa Owner**. Nessuno equivale automaticamente a difetto |
| `FAIL` | 0 | Nessun difetto funzionale riprodotto in questo audit documentale |

## A. Fonti e baseline

1. [Discovery — CLIENT-REQUESTS-SNAPSHOT](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/discovery/CLIENT-REQUESTS-SNAPSHOT.md), richieste originali e loro stato; molte voci erano ancora `DA VALIDARE` in discovery.
2. [MVP capability map](../MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml) — scope tecnico, `active`, `deferred`, `historical_replaced` al 03/10; non sostituisce decisioni successive.
3. [Finance/Admin delivery plan](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/delivery/DELIVERY-PLAN-WORK-PACKAGES-001.md) e [solution baseline](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/solution/EXECUTABLE-SOLUTION-BASELINE-001.md), capability 041–050.
4. [React #148](https://github.com/2008hitch-afk/centrochange_core/issues/148) / [PR draft #150](https://github.com/2008hitch-afk/centrochange_core/pull/150) / branch `issue-148/premium-react-frontend`: [React coverage](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/FUNCTIONAL-COVERAGE.md), [API/roles](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/API-ROLE-CONTRACT-MATRIX.md), [11 native list/form](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/NATIVE-ROUTE-DISPOSITION.md).
5. [UAT Owner storica #136](https://github.com/2008hitch-afk/centrochange_core/issues/136), [test UAT #137](https://github.com/2008hitch-afk/centrochange_core/issues/137), [React DEV delivery report](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/DECISION-066-DEV-DELIVERY-REPORT-2026-10-21.md) e [fixes live 22/10](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/UAT-PRIORITY-FIXES-LIVE-2026-10-22.md).
6. [HITCH HC-0005 decisions 003–066](https://github.com/2008hitch-afk/hitch-client-discovery/tree/main/clients/HC-0005/decisions), in particolare 003–012, 018, 027–034, 045, 053–054, 059–066. Discovery è **indice non contrattuale**; decisioni approvate e delivery successiva prevalgono. [AGENTS](../../AGENTS.md), [README](../../README.md), [Architecture](../../ARCHITECTURE.md), [Security](../../SECURITY.md), roadmap e codice API/DocType nella PR #150 completano il tracciato.

### Gerarchia delle decisioni per evitare falsi gap

| Tema | Stato vigente | Fonte |
|---|---|---|
| Primo rilascio operativo completo, una webapp, un modello multi-centro; master centrali Patient/Practitioner; catalogo centrale e tariffa del centro | Approvato | DECISION-003–009 |
| Ledger pacchetti, pagamento operativo distinto dall'accounting, confine 48h esatto in Europe/Rome, visibilità paziente fra centri limitata | Approvato | DECISION-010–012, 018 |
| Finance/Admin core: fatture, banca import manuale, compensi, XML passivi, reporting standard, documenti; SdI/TS con adapter simulati e TS ordinario in core | Approvato nei limiti delle policy, senza provider reale | DECISION-027–034, 045 e delivery 041–050 |
| Snapshot prezzo alla **data prenotazione**; soglia sedute non pagate parametrica per coppia paziente+professionista | Approvato | DECISION-053–054 |
| Correzione retroattiva dell'orario seduta (#78) | Rinviata; DECISION-058 non conferisce più autorità implementativa | DECISION-059 |
| React Premium, una sola installazione DEV; attivazione come interfaccia principale | UI/DEV autorizzati, routing `cc_premium_primary=1` solo dopo accettazione visiva Owner | DECISION-060–062, 064–066 |
| API scoped catalogo, tariffe, template, anagrafiche, pagamenti lettura, stampa | Approvate con whitelist, permessi server, audit; create standalone Patient/Practitioner/Item, Payment Entry allocation e mapping Customer arbitrario non autorizzati | DECISION-063 |
| Sito pubblico completo, provider/POS, payment links, OCR, dashboard di contabilità gestionale avanzata, analytics cliniche | Rinviati/esclusi dal core corrente | Capability map e DECISION-031–034 |

### Baseline e limiti della verifica odierna
- Al checkpoint GitHub di questo audit, la **PR #150 è open/draft/unmerged**, HEAD GitHub `96cecfc746cacba42aa25fbea2170736f6217821` (non dare per scontato che `main` abbia React).
- Il report dell'ultimo fix indica sorgente prodotto installato `749eef346e9d259ce59266a5455311b45d498a76`, immagine `sha256:54db4262375457bee60f497029f8cf05f38e99bfab6ec9caa6762078a5f74b6f`, runtime DEV e QA live **PASS nel perimetro provato**, `cc_premium_primary=0`, PR ancora draft. `git diff 749eef3..96cecfc` mostra solo report, screenshot e `frontend/premium/tests/live.spec.ts`: **nessun file applicativo o asset sorgente differisce** tra image-source e HEAD PR. Il manifest dell’immagine non è stato ricalcolato in AUDIT-00. Lettura locale **non mutativa** del 22/10: nove container `centrochange-dev` attivi, sei applicativi con immagine corrispondente; Site `centrochange.local`, flag sintetico true e `cc_premium_primary=false`. `HEAD /premium` come Guest risponde 301 verso `/login?redirect-to=/premium`. Non sono stati eseguiti login, POST o test funzionali sul runtime in AUDIT-00.
- L'Owner riferisce che la UI Premium è terminata: **dichiarazione di completamento UI**, da distinguere dalla riconciliazione Git/ambiente, dall'audit dei requisiti e dalla formale accettazione di ciascuna interfaccia.
- I report storici che riportano `NOT_VERIFIED` per le suite live precedono la consegna documentata il 22/10; non ricopiare tali limiti come stato corrente senza data/commit. I PASS live globali non provano automaticamente ogni singola riga della presente matrice.

## B. Codici di stato e policy

**Scope:** `BASE` = attivo nella capability map originale; `FIN` = Finance/Admin approvato nella delivery; `DEF` = differito nella baseline originale, da rivalutare con decisioni successive; `SOST` = sostituito; `EXCL` = escluso nell'ambito storico. Le autorità HC-0005 approvate più recenti prevalgono.

**Ricognizione UI:** `INDICATA` = il codice/documentazione React contiene un percorso plausibile, **non** significa funzione approvata; `DA_RICONCILIARE` = esiste flusso limitrofo o report con gap; `NO_UI` = lavoro infrastrutturale/di backend; `NON_RILEVATA` = nessuna corrispondenza puntuale stabilita.

**Separazione fondamentale per ogni prossima interfaccia:** lo **scope del requisito** (`APPROVATO`, `RINVIATO`, `ESCLUSO`, `NON_AUTORIZZATO`, `DA_VALIDARE`) è indipendente dall'**esito della verifica** (`PASS`, `FAIL`, `PARTIAL`, `NOT_TESTED`, `BLOCKED_BY_DEPENDENCY`). Le 12 righe storicamente etichettate `BLOCKED` conservano tale valore nel CSV come dato di AUDIT-00, ma durante l'audit per-area devono essere riportate nel registro di scope appropriato e **non conteggiate come 12 errori**. Le capacità `DA_VALIDARE` non autorizzano implementazioni finché l'Owner non ne conferma il perimetro.

**Verifica:** i prospetti D/E sono l'indice storico, con `AUDIT` come promemoria, non l'esito aggiornato. L'esito puntuale e l'approvazione Owner sono nel CSV. `PASS` vale solo per il controllo esatto associato alla prova indicata; `PARTIAL` include codice presente ma scenario non completamente verificato; `BLOCKED` identifica anche scope formalmente rinviato. Nessun esito `OWNER_DONE` in AUDIT-00.

## C. Indice aree — ordine di lavoro proposto

| Ordine | Interfaccia / area | Traccia React o integrazione | Issue | Stato |
|---:|---|---|---|---|
| 01 | Login e autenticazione | Login nativo Frappe `/login`, sessione e redirect verso `/premium`; logout in `frontend/premium/src/main.tsx` | [#158](https://github.com/2008hitch-afk/centrochange_core/issues/158) | `NEXT / NOT_TESTED` |
| 02 | Shell, navigazione, centro attivo e ricerca | `main.tsx`; shell/sidebar/header e fallback per ruolo | Da creare dopo 01 | `QUEUED` |
| 03 | Agenda e prenotazioni | `views.tsx`; `operations.workspace.*`, `scheduling.booking.*` | Da creare | `QUEUED` |
| 04 | Pazienti, storico, assegnazioni, note e pacchetti | `views.tsx`, `patient_assignments.tsx`, `patient_packages.tsx`, `note_history.tsx` | Da creare | `QUEUED` |
| 05 | Professionisti e accessi per professionista | `views.tsx`, `professional_workflow.tsx` | Da creare | `QUEUED` |
| 06 | Servizi/catalogo, prezzi e disponibilità | `views.tsx`, `scoped_archive.tsx` | Da creare | `QUEUED` |
| 07 | Chiusure seduta, cancellazioni 48h, eccezioni, notifiche | Agenda, lifecycle, Notifiche; verificare i processi anche se distribuiti in più schermate | Da creare | `QUEUED` |
| 08 | Finanza, fatture, incassi e banca | `finance_actions.tsx`, `finance_create.tsx`, `views.tsx` | Da creare | `QUEUED` |
| 09 | Compensi, fatture passive, SdI/TS e coda amministrativa | `finance_actions.tsx`, `finance_reports.tsx`, moduli finance | Da creare | `QUEUED` |
| 10 | Report e dashboard | `views.tsx`, `finance_reports.tsx` | Da creare | `QUEUED` |
| 11 | Archivi 11 liste + 11 schede e master-data editing | `scoped_archive.tsx`, `master_archive.tsx`; verificare permessi e completezza reali | Da creare | `QUEUED` |
| 12 | Gestione accessi e registro modifiche | `views.tsx`, `audit_log.tsx` | Da creare | `QUEUED` |
| 13 | Primo incontro pubblico (Guest) | `/premium-primo-incontro`, `first_meeting.tsx`, `public.tsx` | Da creare | `QUEUED` |
| 14 | Regressioni trasversali + UAT finale | Permessi, multi-centro, privacy, localizzazione, email/export/print, backup, performance | Da creare | `QUEUED` |

L'ordine può essere adattato dall'Owner sulla base delle dipendenze dimostrate; **una sola area ACTIVE** alla volta. Le correzioni a componenti comuni richiedono test sulle altre aree coinvolte.

## D. Matrice delle capability originali (01–40)

Legenda colonne: `Rif.` ID in discovery e/o capability map; `Area` = destinazione per audit, non necessariamente una pagina autonoma; `Fonte` = sistema canonico previsto, da confermare a livello di campo; `UI` = ricognizione documentale preliminare; `Verifica` = NON ancora audit Owner per riga.

| Rif. | Scope | Funzione da dimostrare | Area | Fonte backend / dati candidata | UI | Verifica |
|---|---|---|---|---|---|---|
| CC-CAP-001 | BASE | Ambiente DEV isolato e riproducibile | Trasversale | Frappe/Compose | NO_UI | AUDIT |
| CC-CAP-002 | BASE | Professionisti, identità, stato | Professionisti/Accessi | User + Healthcare Practitioner | INDICATA | AUDIT |
| CC-CAP-003 | BASE | Anagrafica paziente, contatti e riferimenti amministrativi | Pazienti/Archivi | Marley Patient; mapping ERPNext ove previsto | DA_RICONCILIARE | AUDIT |
| CC-CAP-004 | BASE | Assegnazione/revoca/riassegnazione paziente | Pazienti/Accessi | CC Patient Assignment | INDICATA | AUDIT |
| CC-CAP-005 | BASE | Segregazione dati per professionista/centro | Tutte | Permessi Frappe + CC | NO_UI | AUDIT |
| CC-CAP-006 | BASE | Prenotare, spostare, cancellare, storico seduta | Agenda | Patient Appointment | INDICATA | AUDIT |
| CC-CAP-007 | BASE | Orari ricorrenti, ferie, assenze, eccezioni | Disponibilità | Practitioner Schedule/Availability | INDICATA | AUDIT |
| CC-CAP-008 | BASE | No doppia prenotazione stesso slot | Agenda | Booking service, Patient Appointment | INDICATA | AUDIT |
| CC-CAP-009 | BASE | Primo incontro pubblico consentito solo agli autorizzati | Guest | Public booking protetto | INDICATA | AUDIT |
| CC-CAP-010 | BASE | Sedute successive non prenotabili pubblicamente | Guest/Agenda | Public booking policy | INDICATA | AUDIT |
| CC-CAP-011 | BASE | Catalogo prestazioni/servizi | Servizi/Archivi | Item, Appointment Type, Center Service | DA_RICONCILIARE | AUDIT |
| CC-CAP-012 | BASE | Prezzi prestazioni | Servizi/Archivi | ERPNext Item Price | DA_RICONCILIARE | AUDIT |
| CC-CAP-013 | BASE | Snapshot immutabile durata/prezzo/servizio seduta | Agenda/Finanza | Patient Appointment + snapshot CC | INDICATA | AUDIT |
| CC-CAP-014 | BASE | Stato pagamento operativo informativo e metodo | Chiusure/Finanza | Stato seduta/settlement CC; distinto da contabilità | INDICATA | AUDIT |
| CC-CAP-015 | SOST | Percorso futuro verso accounting (baseline storica) | Finanza | Sostituito da 041–050 | NO_UI | SUPERSEDED |
| CC-CAP-016 | BASE | Pacchetti paziente: emissione, consumo, correzione | Pazienti/Pacchetti | CC Patient Package + ledger | INDICATA | AUDIT |
| CC-CAP-017 | BASE | Note organizzative | Pazienti/Agenda | CC Organizational Note | INDICATA | AUDIT |
| CC-CAP-018 | BASE | Note professionali riservate | Pazienti/Agenda | CC Private/Professional Note | INDICATA | AUDIT |
| CC-CAP-019 | BASE | Scheda paziente unificata | Pazienti/Archivi | Patient, appointment, package, note | DA_RICONCILIARE | AUDIT |
| CC-CAP-020 | BASE | Storico paziente e attività | Pazienti/Agenda | Patient Appointment + eventi audit | INDICATA | AUDIT |
| CC-CAP-021 | EXCL | Analytics cliniche / patient progress | Fuori MVP | Decisioni defer/esclusione | NO_UI | OUT_OF_SCOPE |
| CC-CAP-022 | BASE | Chiusura giornaliera, stati e riapertura | Agenda/Chiusure | Patient Appointment + lifecycle | INDICATA | AUDIT |
| CC-CAP-023 | BASE | Reminder sedute pendenti alle 21:00 | Notifiche/Processi | Worker/scheduler CC | DA_RICONCILIARE | AUDIT |
| CC-CAP-024 | BASE | Blocco automatico alle 07:00 | Agenda/Processi | Worker/scheduler CC | NO_UI | AUDIT |
| CC-CAP-025 | BASE | Disdetta entro/oltre 48h, debito e deroga auditata | Agenda/Finanza | Booking + economic disposition | INDICATA | AUDIT |
| CC-CAP-026 | BASE | Correzione/sblocco autorizzati con audit | Agenda/Accessi | Lifecycle + audit | INDICATA | AUDIT |
| CC-CAP-027 | BASE | Comunicazioni, reminder e notifiche operative | Notifiche | CC Notification + worker | INDICATA | AUDIT |
| CC-CAP-028 | BASE | Report operativi per ruolo | Report | Reporting CC | INDICATA | AUDIT |
| CC-CAP-029 | BASE | Export, stampa, email sicuri | Report/Finanza/Trasversale | API export/print/email con permessi | DA_RICONCILIARE | AUDIT |
| CC-CAP-030 | BASE | Dashboard gestionale | Report/Finanza | Aggregazioni autorizzate | INDICATA | AUDIT |
| CC-CAP-031 | DEF | Sito pubblico branded completo | Fuori area Premium / Guest | Website/brand; distinta da primo incontro #009 | DA_RICONCILIARE | SCOPE_REVIEW |
| CC-CAP-032 | DEF | Builder/Git pipeline originale | Trasversale | Build/versionamento | NO_UI | SCOPE_REVIEW |
| CC-CAP-033 | BASE | Permission model globale | Tutte | Permessi Frappe/CC | NO_UI | AUDIT |
| CC-CAP-034 | BASE | Audit immutabile azioni critiche | Registro | CC Audit Event + regole | INDICATA | AUDIT |
| CC-CAP-035 | BASE | Backup dati e configurazione | Trasversale | Backup site/files/config | NO_UI | AUDIT |
| CC-CAP-036 | DEF | Disaster recovery/restore testato | Trasversale | Recovery; report DEV già disponibili | NO_UI | SCOPE_REVIEW |
| CC-CAP-037 | DEF | Upgrade e migrazioni sicure | Trasversale | Frappe migration/rollback | NO_UI | SCOPE_REVIEW |
| CC-CAP-038 | BASE | Autorizzazione API e web endpoint | Tutte | Frappe API server-side | NO_UI | AUDIT |
| CC-CAP-039 | BASE | Anti-leakage API/query/report/export | Tutte | Test security Frappe/CC | NO_UI | AUDIT |
| CC-CAP-040 | BASE | Distribuzione da sorgente riproducibile | Trasversale | CI, immagini/versioni | NO_UI | AUDIT |

## E. Matrice Finance/Admin approvata (41–50)

| Rif. | Scope | Funzione da dimostrare | Area | Fonte backend / dati candidata | UI | Verifica |
|---|---|---|---|---|---|---|
| CC-CAP-041 | FIN | Ponte operativo-economico: paziente/cliente, professionista/fornitore, articoli e link seduta→economia | Finanza/Pazienti | Marley Patient/Appointment ↔ ERPNext Customer/Supplier/Item + CC Economic Link | INDICATA | AUDIT |
| CC-CAP-042 | FIN | Crediti, fatture attive, incassi, note di credito/rettifiche, insoluti | Finanza/Archivi | ERPNext Sales Invoice/Payment Entry | INDICATA | AUDIT |
| CC-CAP-043 | FIN | Import banca, riconciliazione e blocchi scaduti | Finanza/Banca | ERPNext Bank Transaction + regole CC | INDICATA | AUDIT |
| CC-CAP-044 | FIN | XML passivi, fornitori e approvazione controllata fatture passive | Finanza/Archivi | CC Incoming Invoice + ERPNext Purchase Invoice | INDICATA | AUDIT |
| CC-CAP-045 | FIN | Compensi professionisti attesi vs ricevuti, soglie e anomalie | Finanza/Report | CC Professional Expectation + Purchase Invoice | INDICATA | AUDIT |
| CC-CAP-046 | FIN | Coda amministrativa: eccezioni, responsabili, rinvii e audit | Finanza | CC Admin Exception | INDICATA | AUDIT |
| CC-CAP-047 | FIN | Report amministrativi, accessi contabili, audit e segregazione | Report/Finanza/Accessi | ERPNext GL/ledger + report protetti | INDICATA | AUDIT |
| CC-CAP-048 | FIN | Adapter SdI: stati, errori, retry, tracciabilità | Finanza/Trasmissioni | Adapter CC + Sales/Purchase Invoice | INDICATA | AUDIT_SIMULATO; LIVE_GATE |
| CC-CAP-049 | FIN | Adapter TS ordinario, eleggibilità/opposizione, correzioni e traccia | Finanza/Trasmissioni | Adapter CC + documenti fiscali | INDICATA | AUDIT_SIMULATO; LIVE_GATE |
| CC-CAP-050 | FIN | Collaudo finance integrato, UAT e release readiness | Trasversale | Test/recovery/evidenze | NO_UI | AUDIT |

**Nota sulle connessioni:** ad esempio `Patient`, `Customer` e i dati fiscali nelle fatture possono avere semantiche distinte: non aggiungere/duplicare campi senza verificare la fonte autorevole e gli snapshot storici richiesti. La mappatura DocType sopra è concettuale; i campi/API precisi devono essere documentati durante l'audit dell'area.

## F. Dettaglio completato e scheda di prova da allegare per ogni interfaccia

Il [CSV dettagliato](FUNCTIONAL-COVERAGE-DETAIL.csv) contiene già 110 righe, tutti i campi obbligatori e l'issue di provenienza. Le celle `PRESENT` significano presenza nel sorgente esaminato, non autorizzazione dimostrata o collaudo live. `LIMITED` indica solo una parte della funzione; `NONE` assenza di percorso; `N/A` non è un'interfaccia. `LIVE-21` e `LIVE-22` rimandano a report storici nominati nell'[inventario](PREMIUM-REACT-INTERFACE-INVENTORY.md); `MOCK` è solo prova con HTTP intercettato; `SRC` è ispezione statica. I due `PASS` riguardano esclusivamente griglia settimanale e navigazione/scheda professionisti provate nel report `LIVE-22`, sul candidato allora installato. Per questo HEAD il diff dal sorgente dell’immagine installata contiene solo prove/test/documenti; su una build applicativa successiva, riconciliare gli SHA.

Per la revisione di ogni riga, allegare una scheda di prova con:

| Campo | Valore richiesto |
|---|---|
| ID / autorità | Capability + decisione HC-0005 vigente + stato requisito |
| Area / URL / componente | Route reale, file React/controllo, azione operatore |
| Chi può / chi non può | Ruoli, centro, professionista, Guest, direct URL/API |
| Fonte dati | DocType/campo canonico; link tra modelli; snapshot autorizzati |
| Implementazione | UI `PRESENT / MOCK / MISSING`; endpoint `PRESENT / MISSING`; backend `PRESENT / MISSING` |
| Test verificabili | Caso positivo/negativo, device, Frappe live vs mocked, data, ambiente, SHA, logs/screenshot sanitizzati |
| Esito | `PASS / FAIL / PARTIAL / BLOCKED / NOT_TESTED` con motivazione |
| Correzione | Issue dedicata e PR, rischio schema/permessi, dipendenze, regressioni |
| Chiusura | CI PASS, merge autorizzato, build/dev allineati, Owner ACCEPTED |

Non considerare `PASS` un test non eseguito. Un endpoint HTTP 200 o uno screenshot non prova il processo end-to-end.

### Corrispondenza UI non dimostrata o limitata

| Requisito | Esito documentale / decisione necessaria |
|---|---|
| Creazione standalone Patient/Practitioner/Item; allocazione diretta Payment Entry; mapping fiscale Customer arbitrario | `BLOCKED`, fuori dal mandato DECISION-063. Backend può avere un vecchio intake Patient, ma non va esposto come nuovo workflow senza policy approvata. |
| Ricerca completa in ciascuno degli 11 archivi | `NOT_TESTED / DA_VALIDARE`: il filtro React agisce solo sulle pagine già caricate. Verificare aspettativa funzionale dell'Owner durante Archivi, senza inventare nuovo requisito. |
| Scheda completa Sales/Purchase Invoice e Bank Transaction negli Archivi | `NOT_TESTED / DA_VALIDARE`: il drawer usa la proiezione `finance.reporting.records`; le azioni sono nella sezione Finanza. Verificare campi e workflow richiesti nella singola interfaccia. |
| Consegna email/reminder ore 21 e auto-lock ore 07 | API/backend presenti, superficie di monitoraggio parziale. Job reali e confini di tempo `NOT_TESTED` in AUDIT-00. |
| Documenti non strutturati, allegati, handoff commercialista, email e stampe/esportazioni complete | Backend e ambito core previsti da DECISION-034; corrispondenza puntuale dei controlli React `NOT_VERIFIED` finché la relativa interfaccia non è auditata. La preview stampa scoped non copre ogni flusso documentale. |
| Alias demo per quattro Patient storici non nel manifest | `PARTIAL`, evidenza `LIVE-22`; non riscrivere ID o rinominare record senza prova di proprietà sintetica. |
| Correzione retroattiva orario seduta, sito pubblico branded completo, POS/feed bancario, payment links, OCR e analytics avanzate | Rinviati/esclusi; non sono difetti dell'attuale React MVP. |
| React come unica UI operativa primaria | Gate Owner visuale non superato: `cc_premium_primary=0`; non attivare nel lavoro #157. |

Il confronto con il modello dati esistente precede qualsiasi proposta futura: Patient e Practitioner sono Marley; Item/Item Price/Price List e documenti fiscali sono ERPNext; Branch/centro e membership sono Frappe/CC; note, package ledger, audit e bridge sono DocType CC. Non duplicare Customer, bilanci o snapshot storici. I ruoli nel CSV sono **contratti attesi**, non risultati di test multiruolo per ciascuna riga.

## G. Workflow Codex per interfaccia (ciclo replicabile)

1. Confermare commit/branch/immagine realmente serviti; **NON eseguire test mutativi** su dataset Owner prima di fixture isolata con cleanup verificato. Rispettare #148/DECISION-066 e gate successivi.
2. Leggere tutte le righe collegate alla schermata, inclusi ruoli, casi di errore, obblighi cross-screen e issue preesistenti.
3. Eseguire audit visivo/funzionale e backend, registrare ogni azione e relativi esiti con prove. Separare errore vero, mock, omissione, esclusione approvata e `NOT_TESTED`.
4. Creare/riusare issue correttive **solo per gap confermati**, con criteri di accettazione e dipendenze. Una sola interfaccia ACTIVE; non duplicare una issue già valida. #136/#137/#139/#148/#78 restano riferimenti esistenti, non da riaprire automaticamente.
5. Codex corregge, nella slice selezionata, `DocType/schema (se necessario) + backend/API + React + test`, verificando prima tutte le fonti dati esistenti, i contratti API e gli effetti sulle altre schermate.
6. Test/CI e review → PR piccole → merge approvato → distribuzione DEV solo se autorizzata → prova Owner. Report con SHA, CI/test, risultati e limiti.
7. Aggiornare matrice, issue #156 e issue area. Marcare `DONE` solo dopo criteri completi o defer approvato; **poi** passare alla prossima.

### Login — prime verifiche per #158
- `/premium` senza sessione → redirect login nativo Frappe; autenticazione corretta/errata; errori in italiano; logout; refresh, scadenza sessione, back/forward.
- Sessione server, cookie/CSRF; niente informazioni cliniche o contabili per utenti non autorizzati; accesso API diretto e hash manipolato.
- Routing per Manager, Secretariat, Professional, Finance, Accountant e Guest secondo decisioni/ruoli reali; cambio centro e autorizzazione coerente.
- Desktop/mobile, tastiera/focus, loading, feedback, regressione dalle altre route; screenshot non sensibili.
- Non creare una seconda login page React: verificare l'integrazione con Frappe. Nessun `PASS` senza prova sul candidato identificato.

## H. Regole anti-perdita di contesto

- **Una master:** #156. **Una matrice:** questo file. **Una area ACTIVE:** issue di audit dedicata. **Ogni fix:** issue figlia o issue già esistente + PR collegata.
- Alla fine di ogni sessione Codex aggiorna nel commento della issue attiva: commit/branch, risultato, test, evidenza, blocchi, prossimo passo concreto; il prossimo agente deve poter riprendere senza chat.
- Le PR aperte (compresa #150) non vengono automaticamente fuse per accelerare l'audit. Le decisioni di merge, uso server, cambio schema/policy, dati reali, provider e produzione mantengono i propri gate.
- Questo documento si aggiorna **insieme** alle prove dell'area, non prima di averle ottenute.

