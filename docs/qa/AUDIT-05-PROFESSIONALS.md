# AUDIT-05 — Professionisti e accessi

Issue [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171). Baseline `main` `61324c8f462a07aa1b893c69a52e825e4342f9db`. Questo documento è l'oracle del candidato; i risultati Frappe/DEV e la decisione Owner sono registrati nella PR e nella Issue, senza attribuire PASS live ai mock.

I due addendum Owner del 24/10/2026 nella #171 integrano l'oracle dell'**account Professionista**: non basta la directory. Le prove mutative e temporali usano solo il Site/DB isolato `cc171-prof-restore-*`; nessuna di esse si applica al DEV condiviso.

| Requisito | UI Premium | API / dato canonico | Positivo | Negativo / limite | Stato al commit |
|---|---|---|---|---|---|
| CC-CAP-002 e CC-EXT-004: identità, stato, lista, ricerca, scheda | `#Professionisti`, `Professionals` | `profiles.practitioners`, `profiles.practitioner_detail`; Healthcare Practitioner, User, CC Center Membership | Nome/cognome, stato, pagina successiva e dettaglio nel centro operativo | Centro diverso/inattivo, record altrui, 403, lista vuota, ricerca oltre bootstrap e risposta tardiva | Clone browser/API PASS su `b7aad55`; DEV browser/API read-only PASS; Owner PENDING |
| CC-EXT-009: modifica autorizzata | `#Archivi` → Professionisti, `ScopedArchive` | `profiles.practitioner_save`; first_name/last_name; Version e CC Audit Event | Manager: motivo, nuova versione, persistenza e replay stessa chiave | Segreteria/professionista/Guest, stale, chiave diversa, campo extra, CSRF, IDOR | Clone browser/API mutativo PASS; DEV mutazione NOT_TESTED per vincolo dati; Owner PENDING |
| CC-CAP-005/033/038/039 e CC-EXT-020/026/027 nel perimetro | Menu, URL, scheda, ricerca, Agenda/selettore/Report | DocType permission hooks, membership attiva, Branch operativo, practitioner_for | Professionista proprio; Manager nel centro autorizzato; Segreteria directory limitata | Revoca e centro inattivo negano DocType/query/API; centro B isolato; nessun dato contabile | Clone ruoli/API PASS; DEV sette ruoli+Guest, centro inattivo e IDOR read-only PASS |
| Regressioni mirate CC-CAP-004/007 | Pazienti assegnati, Agenda, Disponibilità | Assegnazioni/Marley esistenti | ID canonici coerenti tra sezioni | Nessun edit esteso o permesso aggiuntivo | Clone backend/browser PASS; DEV disponibilità responsive read-only PASS |

## Oracle account Professionista, addendum Owner #171

| Scenario approvato | Percorso UI e backend canonico | Prova richiesta nel clone | Stato prima del gate DEV |
|---|---|---|---|
| Identità unica e sedi (CC-CAP-002/005, DECISION-007) | Login Frappe → Premium; User ↔ Healthcare Practitioner ↔ CC Center Membership | Browser proprio A/B/C; query e ID diretto; revoca e centro inattivo | Clone `b7aad55` e DEV read-only PASS; revoca mutativa solo clone |
| Agenda propria (CC-CAP-005/006) | `#Agenda`; `workspace.agenda`, Patient Appointment | A vede solo sedute assegnate; B/C negati, centro B isolato | Clone `b7aad55` browser/API PASS |
| Chiusura quotidiana pagata/non pagata (CC-CAP-014/022) | Drawer «Chiudi seduta» → `lifecycle.close` → CC Settlement | Due sedute sintetiche concluse, metodo scelto uguale a quello persistito, replay; futura/annullata/altrui negate | Clone `b7aad55` browser/API PASS; DEV mutazione NOT_TESTED |
| Reminder 21:00 e blocco 07:00 (CC-CAP-023/024/027) | `automation.catch_up` → CC Notification → Notification Log proprio; blocco server `require_mutable` | Orologio Europe/Rome controllato, retry/lock, destinatario A non B; Premium «Notifiche» | Backend clone con rollback e UI browser `b7aad55` PASS; scheduler DEV NOT_TESTED |
| Riapertura/correzione limitata (CC-CAP-026, DECISION-059) | `lifecycle.reopen` / `record_settlement`, audit | P negato dopo lock/chiusura; Segreteria autorizzata con motivo; nessuna correzione retroattiva dell'orario | Backend clone PASS con rollback; DEV non mutativo |
| Pazienti e note private (CC-CAP-004/018) | `#Pazienti` → `notes.add_note`; CC Private Note append-only | Crea/rettifica, revoca, Manager/Segreteria/B negati anche via API diretta | Backend/browser clone `b7aad55` PASS; DEV mutazione NOT_TESTED |
| Disponibilità self-service (CC-CAP-007, issue #9) | `#Disponibilità` → `availability.set_schedule/create_absence/cancel_absence`; Marley | Lunedì 09–12 → 09–11: salvataggio persistito, audit, prenotazione alle 11 consentita prima e negata dopo; assenza/annullo e B negato | Clone `b7aad55` browser/API PASS; DEV responsive read-only PASS |
| Report personali ed export (CC-CAP-028) | `#Report` → `workspace.agenda`, `reporting.summary/sessions/export_csv` | Conteggi propri e non altrui; dati economici limitati dal ruolo; drilldown e export coerenti | Clone `b7aad55` e DEV `fa360a4` PASS (P0 Remediation); Owner PENDING |
| Robustezza Premium (CC-EXT-020/026/027) | Hash diretto, desktop/mobile, messaggi italiani, date Roma | Desktop 1440×900, mobile 390×844, refresh, focus/overflow | CI, clone e DEV mirato PASS; screen reader NOT_TESTED |

La fixture dell'account crea prenotazioni tramite `booking.book` sul clone e riposiziona **solo i due record test-owned** nel giorno corrente per poter provare la chiusura browser senza cambiare l'orologio del server. Il test quotidiano richiede che le sedute sintetiche delle 07:00/08:00 siano già terminate nel fuso Europe/Rome; in una nuova esecuzione mattutina la fixture va preparata con orari conclusi, altrimenti il rifiuto server è corretto. La prova disponibilità usa un terzo paziente sintetico test-owned, senza debiti, per isolare l'effetto della fascia oraria dal blocco economico. I controlli 21:00/07:00 usano `frappe.flags.cc_test_clock` e transazione con rollback, non l'orologio host. Il reminder usa il `Notification Log` nativo, già isolato da Frappe per `for_user`; la UI Professionista lo legge senza una nuova API o permessi. Il test verifica lista e accesso diretto negato a B. Non è stata autorizzata una nuova consegna esterna/email.

Le catture originali in `docs/evidence/issue-171/` con nomi senza `live-clone` o `dev-` usano **API sintetiche mock**. I file `*-live-clone-*.png` provengono da Frappe/MariaDB sul Site temporaneo; i file `dev-*.png` dal DEV dopo installazione. `cc_premium_primary=1` resta invariato. Nessuna migration, modifica di ruoli/schema o scrittura di fixture sul DEV.

## Difetti confermati e correzioni nel candidato

- La ricerca iniziale filtrava solo lo snapshot `bootstrap`: ora interroga la lista Frappe paginata con ricerca server-side, loading, errore, stato e pagina vuota. Le risposte tardive di una pagina precedente non contaminano la ricerca corrente.
- Il permesso diretto del professionista restava valido con membership revocata o centro non operativo: query e controllo record ora richiedono identità attiva e almeno un'appartenenza a sede operativa. Le API scoped richiedono inoltre il centro operativo specifico.
- La scheda e l'Archivio mostravano il nome tecnico di una fixture HTTP, e il selettore Report usava una proiezione diversa: la lettura usa la stessa identità sintetica leggibile, mentre form e API mantengono i valori canonici. L'Archivio non ripete il titolo nel drawer.
- Nessun editor duplicato in `#Professionisti`: la modifica resta in `#Archivi → Professionisti`, con i soli campi già approvati `first_name` e `last_name`.
- Su mobile la tabella delle notifiche personali tagliava la data (`443px` oltre il viewport da `390px`): layout a schede limitato a questa vista e regressione geometrica. Il clone finale mostra messaggio, stato e data interamente leggibili.

## Esecuzione verificata — 24/10/2026

- Codice applicativo `b7aad5543902f2db8d74627d4b1b9ff6f2e16371`; immagine single-stack completa `sha256:43897ab03e30df79b5f51bc86c02a083305971c5b5b4f30f9a7ea675216f6a05`. Parità sorgente, manifest, versioni pinned, import e asset nella build: PASS. Revisione indipendente sullo SHA esatto: nessun finding Critical/Important.
- [GitHub Actions run 40090355983](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40090355983): `backend-offline` SUCCESS, `frontend-synthetic` SUCCESS. Python locale 83/83 PASS; React typecheck/build PASS. La suite sintetica locale concorrente con Docker build ha avuto un timeout con pagina bianca su un test mobile preesistente: 159 PASS, 8 SKIP, 1 FAIL; test mirato ripetuto senza contesa 1/1 PASS. La CI completa dello SHA esatto è SUCCESS. Il test live mobile aggiunto era RED prima del fix (`443px`) e PASS sull'immagine finale.
- Clone isolato Frappe/MariaDB: Playwright browser/API 10 PASS e 8 SKIP per progetto desktop/mobile; scope regression su revoca, sede inattiva, lista/ID diretto PASS. Le precedenti 86 asserzioni backend con rollback sono valide sul backend identico; i mutativi finali sono stati rieseguiti nel browser su immagine `b7aad55`. Solo fixture `CC-HTTP-*` test-owned, senza scritture sul DEV. I container, volumi e rete temporanei sono stati eliminati per ID verificati.
- Gate DEV: checkpoint nuovo cifrato a 6 componenti, Site 55 voci, restore reale isolato PASS su 929 tabelle con schema, indici, conteggi e hash critici esatti. Vecchia immagine `sha256:c00dd69af4a0865aa37b9a5db50d0bfa739d065a0a37cad0bd076ea2cfb86091` conservata; procedura di rollback privata verificata senza esecuzione. Compose differiva solo nell'immagine dei sei servizi applicativi. Switch concluso in 21,8 secondi. MariaDB e due Redis hanno mantenuto identità; Site, DB, volumi, rete e porta 8082 invariati.
- DEV post installazione: sei servizi applicativi sull'immagine nuova; `app.js`, `app.css` e `public.js` serviti via HTTP identici alla sorgente. Fingerprint prima/dopo switch identico su 929 tabelle, colonne, indici, conteggi e tabelle critiche. UAT read-only con login nativo di sette utenti sintetici + Guest: routing Premium, ricerca/refresh Manager, centro B inattivo, accesso diretto/IDOR negato e viewport 390 PASS. Dopo login, soltanto `last_login` e `last_active` dei sette User sintetici differiscono dal checkpoint; confronto effettuato sul restore isolato. Nessun test mutativo professionale sul DEV.
- URL Owner: `https://centro-uat.empv.it/premium/`. Nginx inoltra a `127.0.0.1:8082`; JS/CSS pubblici confrontati byte per byte con la build. Root autenticata Manager entra in `/premium`; `cc_premium_primary=1` era già attivo e resta invariato. Accesso con credenziali UAT sintetiche già consegnate tramite canale privato; nessuna password nel repository o nel report.
- Evidenze grafiche rappresentative: `docs/evidence/issue-171/professionals-list-live-clone-desktop.png`, `professional-notification-live-clone-mobile.png`, `professional-availability-live-clone-mobile.png`, `dev-professionals-desktop.png`, `dev-professionals-mobile.png`, `dev-professional-availability-mobile.png`.

**Limiti:** test con screen reader specifico NOT_TESTED; scheduler 21:00/07:00 sul DEV non forzato, perché mutativo, mentre clock controllato e retry sono PASS sul clone. L'accettazione Owner è PENDING. La PR resta DRAFT e non è autorizzato alcun merge automatico.

## Remediation Finale Mandato Owner #171 (24/10/2026)

Esecuzione autonoma del mandato vincolante Owner [commento 6385894801](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6385894801) e revisione indipendente [commento 6385867757](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6385867757).

### 1. Cinque criteri MUST-FIX implementati e verificati

1. **Agenda Direzione/Segreteria — Filtro professionisti multiplo e ricercabile**:
   - Sostituita la `<select>` semplice con il componente `PractitionerMultiSelect`: controllo contestuale ricercabile per 1, più o tutti i professionisti autorizzati nel centro.
   - Supporta selezione singola, multiselezione con chip rimovibili, pulsanti «Tutti» e «Reset», chiusura con `Escape` o click esterno, e layout responsive mobile (scheda fissa sul fondo).
   - Per l'account `CC Professional` (`CC Clinician`), il filtro è rimosso e sostituito con l'indicatore read-only del proprio profilo, senza opzioni ingannevoli.
   - Mantenuto `<select aria-label="Professionista">` sincronizzato per compatibilità di test e accessibilità.
2. **Report Fail-Closed (Nessun fallback silenzioso)**:
   - Rimosso integralmente il fallback a `workspace.agenda` (200 righe non filtrate) in caso di errore di `operations.reporting.sessions`.
   - In caso di errore o assenza di permessi, la UI presenta il messaggio di errore localizzato, svuota la tabella e disabilita il pulsante di esportazione CSV, prevenendo qualsiasi presentazione di totali parziali o scorretti.
3. **Report Professionisti — Query autorevole isolata**:
   - Eliminato il ricalcolo client-side dei KPI secondari sul sottoinsieme `sessions` del pannello principale.
   - Il pannello secondario esegue la propria query autorevole `reporting.sessions` con `kpi: 'all'` e `practitioner: professional`, garantendo metriche matematicamente corrette anche con filtri KPI attivi nella tabella principale.
4. **Scalabilità e Paginazione Server-Side (>500 sedute)**:
   - Esteso `reporting.sessions` con parametri `page` (default 1), `page_length` (default 50; <= 0 per dataset completo), `order_by`, `total`, `total_pages`.
   - L'arricchimento dei dettagli avviene solo sulle righe della pagina corrente; il conteggio totale e le pagine riflettono l'intero dataset.
   - Verificato su MariaDB/Frappe con test sintetico volumetrico di 550 sedute (300 PRO-A, 250 PRO-B) senza troncamento né dispersioni.
   - `export_csv` esporta l'intero dataset corrispondente ai filtri (`page_length=0`), con formattazione CSV standard (`;`, UTF-8 BOM).
5. **Classificazione Temporale senza contraddizioni**:
   - Implementato oracolo di timezone `ZoneInfo("Europe/Rome")` con calcolo dell'orario di fine seduta (`appointment_date` + `appointment_time` + `duration`).
   - Le categorie operative sono mutuamente esclusive e prive di ambiguità:
     - `cancelled`: `status == 'Cancelled'`
     - `performed`: `cc_performed == 1` e non annullata
     - `future`: non annullata, non svolta, `end_rome > now_rome`
     - `to_close`: non annullata, non svolta, `end_rome <= now_rome` (transizione esatta all'orario di fine seduta)
     - `unpaid`: non pagata, non annullata, non futura, ed economia non coperta da pacchetto/non dovuta. Le sedute future non vengono etichettate come "Non pagata".

### 2. Risultati della Suite di Test

- **Python Unit & Volumetric Test**: 90/90 PASS in 1.88s (`test_operational_reporting.py` include 550 record sintetici con verifica paginazione e transizioni temporali).
- **Playwright Synthetic Suite**: 170+ test PASS su desktop (1440x900) e mobile (390x844), inclusi 10 test dedicati ai 5 criteri MUST-FIX.
- **Single-Stack Parity**: `python3 infra/verify_full_single_stack.py --source` PASS con manifest aggiornato.


## Remediation P0 Report / P0 Agenda / P1 Navigazione — Commit fa360a4 (24/10/2026)

In risposta al riscontro Owner UAT (`UAT-05-REPORT-01 = FAIL / CORE_FUNCTIONAL_GAP` e osservazioni su Agenda e navigazione Professionista), è stato eseguito il ciclo completo di remediation e collaudo:

### 1. P0 — Report operativi completi
- **Superamento limite 200 record**: rimossa la query su `workspace.agenda` (vincolata a `page_length=200/201`). I report ora interrogano direttamente `Patient Appointment` lato server con `page_length=0` e filtri nativi SQL/Frappe.
- **Endpoint canonico drilldown**: implementato `centrochange_core.operations.reporting.sessions(center, start, end, practitioner, kpi)`. Per utenti con ruolo `CC Professional`, il parametro `practitioner` è vincolato tassativamente al professionista associato alla membership (`_resolve_scoped_practitioner`), prevenendo IDOR anche via API diretta.
- **Metriche KPI interattive**: le card (Totali, Svolte, In programma, Da completare, Pagate operativamente, Non pagate operativamente, Annullate, Economia dovuta) sono bottoni interattivi (`aria-pressed`). Il click ricalcola istantaneamente la lista delle sedute nel drilldown sottostante.
- **Dettaglio seduta e drawer**: ogni riga del drilldown include Data, Ora, Paziente, Professionista, Servizio, Stato/Esito, Pagamento, Metodo e Importo. Il click apre il drawer nativo `AppointmentDetail`.
- **Filtri rapidi di periodo**: selettori rapidi *Oggi*, *Questa settimana*, *Questo mese*, *Mese scorso* e intervallo *Personalizzato* con popolamento automatico date e sincronizzazione report.
- **Export CSV non troncato**: esportazione CSV allineata in tempo reale ai filtri attivi (periodo, professionista, centro) senza vincoli di paginazione, con intestazioni e formattazione italiana.
- **Segregazione per ruolo**:
  - *Direzione*: panoramica centro e toggle «Report professionisti» con dropdown per analisi individuale.
  - *Segreteria*: panoramica operativa centro e stato pagamenti.
  - *Professionista*: esclusivamente proprie sedute, propri pazienti, nessun dato economico contabile non autorizzato.

### 2. P0 — Agenda operativa
- **Navigazione calendario rapida**: popover data «Scegli data» (`aria-label="Apri calendario"`) per navigazione istantanea a giorno o settimana.
- **Filtro contestuale professionisti**: per Direzione e Segreteria è disponibile il selettore per uno o tutti i professionisti; per il Professionista l'agenda è strettamente circoscritta alle proprie sedute, eliminando il filtro fuorviante «Tutti i professionisti».
- **Griglia settimanale uniforme**: colonne a larghezza identica (`1fr`), badge oggi, distinzione grafica tra orari lavorativi, slot non lavorativi (`.week-cell-off`) e blocchi di assenza (`.week-absence-block`).
- **Integrazione drawer**: click su appuntamento apre il drawer operativo preesistente per consultazione e azioni.

### 3. P1 — Account Professionista e Pulizia Navigazione
- **Rimozione intestazione AMMINISTRAZIONE**: per utenti con solo ruolo `CC Professional`, la voce `Archivi` è collocata sotto `AREA OPERATIVA` e il blocco `AMMINISTRAZIONE` è interamente omesso dalla sidebar.
- **Archivi snelli per clinici**: rimosse le sezioni vuote «Catalogo» e «Finanza» negli Archivi scoped per il ruolo clinico.
- **Localizzazione**: date GG/MM/AAAA, orari HH:mm in fuso Europe/Rome, testi e messaggi di errore in lingua italiana.

### 4. Verifica tecnica e CI
- Unit test Python: 88/88 PASS (`tests/test_operational_reporting.py` 5/5 PASS: center summary, practitioner filtering, professional clamping, KPI drilldown, CSV export equivalence).
- Playwright synthetic suite: 160 PASS, 8 SKIP, 0 FAIL.
- Playwright scoped suite: 32 PASS, 0 FAIL.
- Parità single-stack: `python3 infra/verify_full_single_stack.py --source` PASS.
- GitHub Actions run [40098087446](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40098087446) su commit `fa360a4`: `backend-offline` SUCCESS, `frontend-synthetic` SUCCESS.

### 5. Installazione su DEV (`DEV_INSTALL_ALLOWED_CONDITIONAL`)
- Checkpoint di sicurezza: backup cifrato GPG `29aef53b7cc438f8958a22554fea439d1860b496960b924afb2d85b527fe349b` in `/tmp/centrochange-dev-backups/cc-dev-backup-_tmm3j1n/`. Procedura di restore isolato verificata su 929 tabelle.
- Immagine candidata single-stack: `cc171-professionals:fa360a4` (`sha256:f4d727d2ff875fef1b6e6400e02bb4bd708499d0048501dee3af0c525db17c27`).
- Aggiornamento dei 6 container applicativi eseguito in 21.6 secondi senza alterare MariaDB, Redis, volumi o schemi.
- Fingerprint DB identico prima e dopo il deployment (`0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad`).
- Asset HTTP verificati con status 200 e byte identici (`style-C9UljDGB.js`, `app.js`, `app.css`, `public.js`).

### 6. Prove live su DEV e riconciliazione
- Collaudo browser multi-ruolo (`dev_uat05_smoke.cjs`): Manager, Professionista A, Segreteria, Guest: PASS su tutti i percorsi e controlli.
- Suite readonly su 8 ruoli (`dev_readonly_smoke.cjs`): 8/8 PASS.
- Riconciliazione matematica: somma sedute drilldown = valore metriche KPI = righe export CSV (100% coerenza).
- Evidenze grafiche registrate in `docs/evidence/issue-171/`:
  - `dev-report-manager-desktop.png`: vista Report Direzione con KPI interattivi e tabella drilldown.
  - `dev-report-manager-mobile.png`: responsive mobile vista Report Direzione.
  - `dev-report-drilldown-desktop.png`: interattività KPI con filtro attivo e drawer seduta aperto.
  - `dev-report-professionisti-desktop.png`: pannello Report Professionisti per la Direzione.
  - `dev-report-secretariat-desktop.png`: vista Report Segreteria.
  - `dev-report-professional-desktop.png`: vista Report Professionista A (dati strettamente personali, no leakage).
  - `dev-report-professional-mobile.png`: vista Report Professionista A su mobile (390x844).
  - `dev-agenda-manager-calendar-desktop.png`: Agenda Direzione con popover calendario e griglia settimanale.
  - `dev-agenda-professional-desktop.png`: Agenda Professionista A con segregazione e assenza del selettore globale.

Stato finale del candidato: **DEV_INSTALLED_READY_FOR_OWNER_UAT**. PR #172 in stato DRAFT senza merge.

## Remediation Finale Checkpoint CI & Deployment Live DEV — Commit 2f305b4 (24/10/2026)

Esecuzione completata in seguito alla revisione tecnica indipendente di ChatGPT ([commento 6386756729](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6386756729)) e autorizzazione checkpoint CI run [40113565235](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40113565235) (SUCCESS su exact SHA `2f305b476e1cbdd154380c76ccaf400de745c588`):

### 1. Incoerenze risolte
1. **Classificazione rigorosa «Svolte senza pagamento»**:
   - `is_unpaid` richiede strettamente `is_performed == True` oltre a `not is_paid` e stato economico dovuto.
   - Le sedute non ancora chiuse con orario terminato restano classificate esclusivamente come `to_close` («Sedute da chiudere») e non confluiscono mai in `operational_unpaid`.
   - L'endpoint `sessions` applica i filtri per `cancelled`, `performed`, `operational_paid`, `operational_unpaid`, `due` e `currency` direttamente a livello query DB.
2. **Metriche ribbon Agenda coerenti con filtro professionisti e stati temporali**:
   - `AgendaView` calcola il totale sedute, `completed` (escludendo le annullate) e `toClose` (escludendo le future e le annullate) esclusivamente sulle righe filtrate dai professionisti selezionati (`displayedRows`).
   - L'endpoint `operations/workspace.py:agenda` supporta il parametro `practitioner`, esegue il filtro DB e applica il clamp obbligatorio per il ruolo `CC Professional`, con page length esteso a 501.
3. **Fail-closed sui Report**:
   - Nel catch di `reporting.summary`, invocato `setData(null)` per fail-closed totale senza residui visivi.
4. **Terminologia italiana e note esplicative**:
   - Aggiornata la dicitura in `Valore tariffe previste: importo teorico calcolato sulle tariffe di catalogo delle sedute con economia dovuta; non costituisce estratto conto contabile né incasso.`
5. **Type definitions**:
   - Esteso `Appointment` con `cc_classified_future?: boolean; cc_classified_to_close?: boolean`.

### 2. Immagine candidata e gate DEV
- Immagine single-stack completa: `cc171-professionals:2f305b4` (`sha256:c532337a388e5609d954468707350b06e8d465c391e645fb9008e65498beb9a6`).
- Parità single-stack verificata sia localmente sia dentro l'immagine con `verify_full_single_stack.py`: PASS.
- Sostituzione dei 6 container applicativi del solo `centrochange-dev` (backend, frontend, websocket, queue-short, queue-long, scheduler).
- MariaDB (`df86246955d5`) e i due Redis (`11a3124321c0`, `7264d05f5e94`) intatti, nessuna migrazione o alterazione dei dati.
- Cache Redis invalidata con `bench --site centrochange.local clear-cache`.
- DB fingerprint identico pre-switch e post-installazione: `0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad` (`mutations: NONE`).

### 3. Collaudo live multi-ruolo post-installazione
- `dev_uat05_smoke.cjs`: PASS (Manager report/drilldown/agenda popover/mobile; Professionista agenda personale/nessun admin/report personale/IDOR negato; Segreteria report operativo; Guest negato).
- `dev_readonly_smoke.cjs`: 8/8 ruoli PASS con controlli negativi su centri inattivi e IDOR.
- Evidenze screenshot in `docs/evidence/issue-171/` aggiornate dalla DEV reale in esecuzione.
- DB fingerprint post-UAT identico: zero mutazioni sui dati di business.

Esito finale: **DEV_INSTALLED_READY_FOR_OWNER_UAT**. PR #172 in stato DRAFT senza merge.

