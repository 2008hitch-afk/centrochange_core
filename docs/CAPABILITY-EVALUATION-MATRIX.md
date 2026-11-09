# Centro Change — Capability Evaluation Matrix

## COLLAUDO CLIENTE 09/11/2026 — A PASS / B NO-GO, ROTTE PUBBLICHE ASSENTI

**Gate A — ACCOUNT PROFESSIONISTA: PASS, 4/4 desktop e mobile sul clone isolato.** Codex ha verificato login/logout reale di **Giulia Moretti, Andrea Ricci, Elena Bianchi e Marco Ferri**, Agenda personale, paziente assegnato, disponibilità, lettura note, report, e blocco degli accessi ai pazienti dei colleghi e al report economico Manager. Credenziali sintetiche generate **solo sul clone**, nessuna alterazione agli account STAGING.

**Gate B — PRENOTAZIONE ONLINE: NO-GO, 0/4 combinazioni.** Sullo STAGING **mancano entrambe le righe `CC Public Booking Route` per `Marco` e `Francesca`**. La pagina Guest renderizza su desktop/mobile e mostra entrambe le modalità; i due servizi `sede` e `online`, gratuiti, 20 minuti, risultano configurati. Nessun test POST di booking è stato eseguito perché sarebbe artificiale inventare le associazioni mancanti. **Non dichiarare pronto per la presentazione al cliente.**

**Decisione organizzativa richiesta all'Owner:** per ciascuna route `Marco` e `Francesca`, identificare **l'esatto Healthcare Practitioner responsabile e abilitato nel centro**. Nel dataset dimostrativo i soli quattro sono Giulia Moretti, Andrea Ricci, Elena Bianchi e Marco Ferri: non compare alcuna `Francesca`; non assumere che Marco Ferri coincida col direttore Marco. Se Francesca è un quinto professionista, il dataset/dichiarazione di 4 account non può essere cambiato senza approvazione esplicita. Se i nomi pubblici sono solo segnaposto, serve decisione esplicita per cambiarli su UI/API e relativi test. **Non creare rotte con ID a caso o associarle per somiglianza del nome.**

**Dopo la decisione:** backup cifrato STAGING; inserire le due rotte con manager autorizzato, puntando soltanto a professionisti esistenti e attivi, centro coerente, senza nuovi pazienti, appuntamenti, invii o modifiche contabili; verificare proiezione `available_slots` per tutte e quattro le combinazioni, e test POST guest E2E solo su clone isolato. Consolidare risultati e screenshot prima di dare GO. Non modificare produzione o fare merge.

**Baseline invariata secondo Codex:** SHA STAGING `6e982a2715dc3aec89b3f7c65e52c3aa995d45a8`; 4 professionisti, 18 Patient, 17 Customer, 35 appuntamenti, 10 ricevute per €392. Nessun dato STAGING modificato. Percorsi screenshot forniti da Codex sono temporanei sul server (`/tmp/cc156-...`), non asset GitHub; conservarli privatamente.

---

## GO/NO-GO CLIENTE — ACCOUNT PROFESSIONISTA POI PRENOTAZIONE ONLINE (09/11/2026)

**Stato: VERIFICHE OPERATIVE DA ESEGUIRE, NON ANCORA APPROVATO PER PRESENTAZIONE.**

L'audit backend generale 47/47 PASS non equivale a login UI né a prenotazione Guest completa. Il dataset ha quattro User Frappe `@presentation.example.invalid`, ma l'autenticazione reale e la navigazione desktop/mobile di ciascuno vanno collaudate. La prenotazione pubblica utilizza due direttori espliciti `Marco` / `Francesca`, due modalità `sede` / `online` e un account di servizio dedicato; non assumere che il caricamento 4/18/17/35 abbia abilitato automaticamente tutte le route.

**Gate A:** lettura account, ruoli, appartenenza e permessi; quattro accessi reali UI su clone con credenziali sintetiche, agenda e soli pazienti propri, note, disponibilità, report, divieti di accesso cross-professionista e dati fiscali; scritture soltanto nel clone.

**Gate B:** route pubbliche/servizi/slot attivi e corretti sullo STAGING in sola lettura; prenotazioni Guest reali soltanto nel clone per tutte le combinazioni modalità × direttore, 20 minuti €0, conferme simulate, replay/idempotenza, conflitti, 0 invii e nessuna seduta successiva generata.

**Gate C (presentazione):** A e B PASS, UI desktop/mobile e testi/indirizzo coerenti, database STAGING invariato, nessun dato personale reale. Se manca la route Francesca o l'account di servizio, riportarlo come **blocco**, senza associare automaticamente professionisti o modificare la produzione.

**Strumenti e istruzioni:** `infra/qa_professional_public_readonly.py` (bench console, sola lettura), `tests/test_presentation_professional_public_readonly.py`, `docs/uat/PROFESSIONAL-AND-ONLINE-BOOKING-GO-NOGO-2026-11-09.md` nella PR #205. Non cambiare la SHA installata `6e982a...` solo per il controllo; usare un file temporaneo. Nessun nuovo seed.

---

## STATO OPERATIVO 09/11/2026 — AUDIT BACKEND CHIUSO, STAGING SHA 6e982a27

**STAGING installato secondo il resoconto operativo Codex:** `6e982a2715dc3aec89b3f7c65e52c3aa995d45a8`; gestionale accessibile su `https://centro-uat.empv.it/premium`. Migrazione Frappe eseguita, backup cifrato verificato con **ripristino su clone isolato**.

**Audit sul database STAGING dopo il rilascio, eseguito da Codex:** **47 PASS / 0 FAIL**, compresi normalizzazione orari, isolamento e permessi, Patient→Customer, Healthcare, ERPNext, fonti economiche, ricevute e report. Numero record **immutato** prima/dopo: 4 professionisti, 18 pazienti, 17 Customer, 35 Patient Appointment, 10 CC Operational Receipt, 35 CC Economic Source Link. Zero Email Queue, log SMS, transazioni fiscali, Sales Invoice, Payment Entry e GL Entry. `mute_emails` ancora attivo; nessun nuovo popolamento.

**Scheduler post-migrazione riferito da Codex:** il solo job nativo Healthcare `patient_appointment.update_appointment_status` è **disattivato**, mentre `centrochange_core.operations.automation.catch_up` è **attivo**. L'`AppointmentMixin.validate` non è stato indebolito. I due PermissionError del job Healthcare dell'8–9/11 sono **storici, precedenti alla correzione**: monitorare eventuali nuove ricorrenze dopo il rilascio.

**Errore residuo distinto:** `ConnectionError` del controllo aggiornamenti Frappe dell'8/11, attribuito da Codex alla risoluzione DNS all'interno della rete Docker; **non equivale a un errore dei flussi Patient/Customer o incassi**. Da investigare operativamente solo se si ripete, senza allentare la sicurezza.

**Evidenza indipendente da GitHub:** sulla SHA installata `6e982a...` `dataset-offline`, `frontend-synthetic`, `presentation-clone` **3/3 PASS**. I conteggi live, l'audit e il ripristino backup provengono invece dal **resoconto dell'operatore server**, non da accesso diretto della chat al DB.

**Vincoli:** PR #205 resta DRAFT, `main` e produzione invariati; non ripetere il seed. Le sezioni storiche qui sotto sono conservate come cronologia, **non descrivono lo stato attuale**.

---

## STORICO — AUDIT 09/11/2026 — INTEGRITÀ DATI OK, JOB GIORNALIERO DA CORREGGERE

**Staging installato (invariato):** `254af1505dc56ae9123ce64469f856cefabf61d4`; 4 professionisti, 18 pazienti, 17 Customer, 35 appuntamenti, 10 ricevute per 392€.

**Auditor Codex (sola lettura):** 43 PASS e 2 FAIL script su 45 check. I due FAIL discendono entrambi dalla formattazione degli orari `9:00` vs `09:00`; la verifica indipendente normalizzata sul DB ha confermato tutti i 35 appuntamenti e i loro stati. I link Patient–Customer, Frappe User/practitioner, Supplier/Cost Center, Economic Source, ricevute e report hanno superato la riconciliazione; nessun dato scritto durante l'audit.

**Problema reale ancora aperto sullo STAGING:** `healthcare...patient_appointment.update_appointment_status` ha fallito l'8 e il 9 novembre con `PermissionError` su `AppointmentMixin.validate`. Il job nativo salva appuntamenti con stati automatici che aggirano il flusso Centro Change, ed è quindi correttamente bloccato. Il job privato Centro Change `operations.automation.catch_up` è già preposto al blocco automatico delle sedute con audit. Un terzo job di verifica aggiornamenti Frappe ha avuto `ConnectionError` di rete indipendente dai record.

**Correzioni proposte sulla PR #205, ancora NON installate:** lo script audit normalizza `HH:MM`; una nuova configurazione `scheduling.native_scheduler.configure` chiamata `after_migrate` (dopo `sync_jobs` Frappe) arresta **solo** il `Scheduled Job Type` nativo in conflitto (`stopped=1`) e verifica attivo il job di `automation.catch_up`. **Nessuna deroga a `AppointmentMixin.validate`**. Nuovi test unitari e verifica su clone. Non eseguire di nuovo il seeder né correggere gli stati sullo STAGING. Per deploy servono CI/clone PASS sulla nuova SHA, backup cifrato, migrazione controllata, query scheduler e nuovo audit 0 FAIL; produzione intatta.

---

## STATO OPERATIVO 07/11/2026 — STAGING POPOLATO (PR #205)

**STAGING attuale:** `https://centro-uat.empv.it/premium`, **SHA installata `254af1505dc56ae9123ce64469f856cefabf61d4`**. Questa è la versione di riferimento per la presentazione; la precedente `51ed781b16550a0fd93aee968f44c3d761534429` è **STORICA/SUPERATA sullo STAGING**, pur essendo stata la prima versione del collegamento fiscale Patient–Customer.

**Conferma caricamento:** Codex ha riferito `plan READY`, `apply PASS`, `inspect PASS` su STAGING, con **4 professionisti e 4 account individuali attivi, 18 pazienti, 17 intestatari fiscali, 35 appuntamenti (10 colloqui gratuiti/25 sedute)**; **10 ricevute operative per 392 €**; nessuna Sales Invoice, Payment Entry, GL, email, SMS o trasmissione fiscale registrata. Il backup cifrato è stato **verificato con ripristino su clone isolato**. Codex ha riferito smoke browser desktop/mobile per agenda, pazienti, intestatari, pagamenti e Report cliente. Questi dati di esecuzione sono un **report dell'operatore**, non una nuova interrogazione diretta del database da GitHub.

**Verifica indipendente GitHub:** CI della SHA installata **3/3 PASS**: `dataset-offline`, `frontend-synthetic`, `presentation-clone`.

**Vincoli:** la [PR #205](https://github.com/2008hitch-afk/centrochange_core/pull/205) resta **DRAFT**, nessun merge su `main` e nessun rilascio in produzione. `cc_presentation_seed` è stato disattivato dopo l'importazione, secondo il resoconto dell'operatore. Il limite del **9/11/2026** riguarda soltanto l'avvio di un nuovo import del dataset originario: **i dati caricati persistono oltre tale data**. Nessun nuovo seed/reimportazione senza nuova approvazione. Per procedura e riconciliazione storica vedere [runbook dataset](uat/CLIENT-PRESENTATION-DATASET-2026-11-07.md).

---

## DECISIONE OWNER 06/11/2026 — ATTIVAZIONE COMPLETA DEL NUOVO ACCOUNT

Prevale sulle precedenti formulazioni: dalla sola pagina **Professionisti**, l'account **Amministratore/Manager Full Permission** crea e attiva in un passaggio nuovo `User` Frappe personale (`enabled=1`, `CC Professional`), centro e membership attivi, Healthcare Practitioner attivo/collegato, ACL coerenti e onboarding credenziali sicuro. Lo stesso Manager può disattivare/riattivare successivamente, senza autorizzazione Owner per ciascun inserimento dopo la consegna. **NON CONFORME** il flusso finale `new → Disabled`; [requisito PR #203](https://github.com/2008hitch-afk/centrochange_core/pull/203#issuecomment-6671993943). Test solo sintetici finché non vengono forniti i dati reali; decisione funzionale non equivale a implementazione, merge o deploy.

---


## DECISIONE OWNER VIGENTE 05/11/2026 — RUOLI E INTERFACCE
<!-- OWNER_CURRENT_2026_11_05 -->

Per CC-CAP-002/003/033/038/049: **Amministratore/Manager Full Permission (anche segreteria)**, **Professionista con account personale**, **Commercialista con accesso finanziario limitato**. La UI Professionisti consente al Full Permission di creare e gestire sia professionista sia utente Frappe individuale (ruolo, centro, stato). La UI Pazienti gestisce anagrafica e preferenza opposizione TS tracciata. Archivi non duplica questi percorsi. Modello professionista operativo senza account: **revocato**. Questa decisione non significa che codice, CI, UAT e produzione siano già allineati. Le classificazioni tecniche sottostanti restano valide solo nel loro perimetro storico; vedere [indice operativo](qa/ACTIVE-GOAL-ROUTER.md).

---


**Stato:** CANONICAL PLAN / RUNTIME VALIDATION COMPLETE — 40/40 TECHNICALLY DETERMINED  
**Issue:** #5  
**Test execution repository:** `2008hitch-afk/centrochange-testlab`

## 1. Scopo

Questo documento e il piano canonico per evitare che una funzione di Centro Change venga implementata senza aver prima valutato le alternative disponibili.

Per ogni capability l'ordine di valutazione e:

1. **native Frappe/ERPNext**;
2. **estensione supportata del nativo**;
3. **app ufficiale/pertinente**;
4. **custom pulito in `centrochange_core`**;
5. **integrazione esterna**, solo se necessaria.

La regola e **native-first, non native-at-all-costs**. Il nativo non deve essere preferito quando introduce semantica errata, rischio di sicurezza, UX significativamente peggiore, forte upgrade risk o complessita sproporzionata.

Criteri trasversali:

- fit funzionale e semantico;
- qualita/UX operativa;
- sicurezza e permission server-side;
- velocita di sviluppo;
- manutenibilita;
- upgrade risk;
- concorrenza e idempotenza quando pertinenti;
- auditabilita;
- report/export/API/direct-access consistency;
- ripetibilita del test e del deployment.

## 2. Regole di stato

Stati tecnici ammessi:

- `PROVEN NATIVE`
- `CONFIGURATION`
- `EXTENSION`
- `CUSTOM`
- `DEFERRED / EXCLUDE FROM CURRENT SURFACE`
- `RUNTIME VALIDATION REQUIRED`

Esiti dei singoli test:

- `PASS`
- `PARTIAL`
- `FAIL`
- `NON_PROBATIVE`

Un test `PASS` valida soltanto gli acceptance criteria dichiarati. Non equivale a una decisione architetturale finale.

## 3. Execution model

Ogni capability con runtime validation viene collegata a uno o piu task in `centrochange-testlab` tramite il proprio `CC-CAP-NNN`.

Dopo il bootstrap del bridge locale:

```text
ChatGPT prepara task
-> testlab runner esegue sul DEV locale
-> result/evidence tornano in GitHub
-> ChatGPT revisiona
-> viene proposta una classificazione o una decisione
-> l'utente resta l'autorita finale
```

I test vengono eseguiti **una capability alla volta**. L'utente puo mantenere come unico intervento un gate `OK` prima di iniziare la capability successiva; non deve eseguire manualmente i singoli comandi di test.

## 4. Matrice canonica

Questa versione include tutte le capability esplicitamente presenti nelle fonti tecniche correnti. Nuovi requisiti scoperti successivamente devono ricevere un nuovo ID senza rinumerare quelli esistenti.

| ID | Capability | Candidati native / extension / app | Custom candidate/fallback | Test obbligatori principali | Stato corrente |
|---|---|---|---|---|---|
| CC-CAP-001 | Runtime foundation e isolamento DEV | Frappe/ERPNext container pattern; Docker Compose | infra Centro Change dedicata | versioni, rebuild, restart, network/volume isolation, no cross-project impact | **CONFIGURATION — OWNER CONFIRMED 2026-09-06** |
| CC-CAP-002 | Identita professionista | User, Employee; Marley `Healthcare Practitioner`; eventuale Sales Person solo proiezione | `CC Professional` se il fit nativo/app e insufficiente | identity mapping, permission scope, disable/reassignment, list/direct/API | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-003 | Anagrafica paziente | Contact/Customer dove semanticamente corretti; Marley `Patient` | `CC Patient` o extension fields se necessario | identity semantics, codice fiscale/UID, CRUD, privacy, direct/API/report/export | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-004 | Assegnazione paziente-professionista | Frappe User Permission / DocShare / supported permission hooks; Marley relations se pertinenti | assignment model + permission hooks in `centrochange_core` | own/cross patient, reassignment, revoke, list/direct/API/report/export/query | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-005 | Segregazione appuntamenti per professionista | Frappe permissions/User Permission; Marley `Patient Appointment` | custom permission layer o custom appointment | list own/cross, direct read/write, API, report/export, reassignment | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-006 | Appuntamento/seduta | ERPNext/Frappe scheduling primitives; Marley `Patient Appointment` | `CC Appointment/Session` se semantica insufficiente | create/update/move/cancel, lifecycle, history, required fields, extension fit | **CONFIGURATION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-007 | Disponibilita professionista | Marley `Practitioner Availability` / schedules | custom availability model | recurring availability, exception/absence, timezone, access scope, edit history | **EXTENSION — OWNER CONFIRMED 2026-09-06** |
| CC-CAP-008 | No double booking / slot concurrency | native appointment validation where available | transactional lock/constraint in `centrochange_core` | concurrent booking, retry, stale slot, move collision, idempotence | **EXTENSION — OWNER CONFIRMED 2026-09-06** |
| CC-CAP-009 | Primo incontro pubblico solo Marco/Francesca | Website/Builder + native scheduling filters; Marley portal if fit | custom booking endpoint/rule | public eligibility, allowed practitioners, race condition, abuse/input validation | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-010 | Sedute successive solo backend | Desk/role permissions / workflow | custom server-side transition/rule | public route denial, backend allow, API bypass attempts | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-011 | Prestazioni / catalogo servizi | Item, Item Group | custom service metadata only if needed | semantics, active/inactive, duration linkage, reporting compatibility | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-012 | Prezzi | Item Price / Price List | custom pricing rule only where native fit fails | effective price, historical changes, role access, future accounting compatibility | **CONFIGURATION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-013 | Snapshot storico servizio/durata/prezzo sulla seduta | supported custom fields / snapshot on native appointment | fields/doctype in `centrochange_core` | price/duration changes after booking, historical immutability, audit | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-014 | Pagato Si/No + metodo informativo MVP | Mode of Payment as reference; ERP accounting evaluated but not auto-triggered | `CC Settlement` | payment flag semantics, correction/audit, permissions, no unintended Payment Entry | **EXTENSION — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-015 | Future invoice/payment/accounting pathway | Sales Invoice, Payment Entry, Payment Ledger | adapter from `CC Settlement` | mapping, idempotent posting, reversal, migration path, accounting integrity | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-016 | Pacchetti | Product Bundle / Subscription evaluated for semantic fit | `CC Package Template`, `CC Patient Package`, `CC Package Ledger` | reserve/release/consume/adjust, concurrency, idempotence, correction/audit | **CUSTOM — OWNER CONFIRMED 2026-09-08** |
| CC-CAP-017 | Note organizzative | native Communication/comment mechanisms evaluated | `CC Organizational Note` | secretary access, professional access, API/report/export/direct, audit | **CONFIGURATION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-018 | Note professionali riservate | native/private record mechanisms; Marley clinical records evaluated | `CC Professional Note` | secretary denial, assigned professional scope, API/report/export/direct/query leak tests | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-019 | Scheda paziente unificata | Desk/Form/dashboard composition; Marley patient views | custom workspace/page if needed | data aggregation, permission inheritance, performance, leakage between sections | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-020 | Patient history / clinical feed | Marley patient history endpoints | guarded extension or custom feed | assigned/cross patient, endpoint arguments, list/direct/API, non-empty fixtures, permission bypass | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-021 | Patient progress / clinical analytics | Marley patient progress methods | guarded extension/custom analytics | cross-patient reads, SQL/get_all paths, empty/non-empty fixtures, report/export consistency | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-022 | Chiusura giornaliera sedute | Frappe scheduler/queue/workflow primitives | `CC Session Closure` | Pending/Closed/Auto Locked/Reopened, retries, idempotence, permissions, audit | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-023 | Reminder 21:00 | Notification/email + scheduler | scheduled job in `centrochange_core` | only pending sessions, duplicate prevention, retry, timezone, delivery failure | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-024 | Auto-lock 07:00 giorno successivo | scheduler/workflow extension | custom scheduled rule | boundary time, retries, idempotence, lock enforcement server-side | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-025 | Regola 48h | workflow/permission extension if fit | centralized business rule | exact boundary, timezone, override roles, API bypass, audit | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-026 | Sblocco/correzione chiusure | Role Permission / Workflow | custom correction action | authorized roles only, immutable audit, repeated corrections, direct/API | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-027 | Email / Communication / Notification | Frappe Email Account, Communication, Notification | custom templates/jobs only if required | permissions, retry, duplicate prevention, failure visibility, no secret leakage | **EXTENSION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-028 | Reporting operativo | native Report infrastructure | custom Script/Query Report | correctness, role filtering, assigned-patient isolation, performance | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-029 | Export/print/email document surfaces | Frappe print/export/email infrastructure | explicit server-side guards/extensions | same permission boundary as UI/direct access; hidden-field/data leakage | **CONFIGURATION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-030 | Dashboard direzionale | native dashboard/report/chart | custom dashboard | aggregate correctness, role scope, privacy, performance | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-031 | Sito pubblico branded | Frappe Website / Builder | custom blocks/pages | reproducible build, Git versionability, responsive UX, no admin leakage | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-032 | Builder/Git reproducibility | Builder supported workflow and pinned source | custom build/deploy automation | rebuild from clean state, asset parity, version pinning, upgrade path | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-033 | Permission model generale | Frappe Role Permission, User Permission, DocShare, supported hooks | centralized `centrochange_core` permission logic | list/direct/API/report/export/query, reassignment, cache, strict user permissions | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-034 | Audit business | Version/audit facilities where sufficient | custom immutable audit events | actor/time/before-after, protected access, correction trail, export restrictions | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-035 | Backup | bench/native DB+files backup primitives | orchestration/runbook only | DB + public/private files + config, encryption/location policy, failure handling | **CONFIGURATION — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-036 | Restore / disaster recovery | bench restore primitives | automated isolated restore procedure | clean-environment restore, version compatibility, integrity checks, measured RTO evidence | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-037 | Upgrade/migration safety | pinned upstream versions + Frappe migrations | migration code in `centrochange_core` | clean upgrade rehearsal, schema migration, regression suite, rollback strategy | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-038 | API/web endpoint authorization | Frappe whitelisted/REST permission mechanisms; app endpoints | wrappers/guards in `centrochange_core` | caller-controlled IDs, cross-user reads/writes, get_all/sql bypass, error behavior | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-039 | Direct/query/report leakage regression suite | native permission-aware APIs where applicable | test/guard layer | REST, URL direct, List, Report, export, custom query, app endpoints | **CUSTOM — OWNER CONFIRMED 2026-09-09** |
| CC-CAP-040 | Operational deploy reproducibility | Compose + pinned images/apps | deploy scripts/runbook | fresh build/start, migrate, health checks, rollback, no manual container patching | **CUSTOM — OWNER CONFIRMED 2026-09-09** |

## 5. Known evidence already available

### CC-CAP-001

Decisione owner del **2026-09-06** sotto standing technical authorization: **CONFIGURATION**.

Evidenza versionata in `docs/spikes/SPIKE-01-REUSE-ISOLATION.md` e `docs/RUNTIME-BASELINE.md`:

- host Windows/WSL2/Docker e versioni live sono stati censiti;
- `centrochange-dev` usa Compose project, DB, Redis, sites volume, network, naming e porta localhost dedicati;
- Frappe/ERPNext/Builder e `centrochange_core` sono pinati e installati senza patch upstream;
- secret/config locali restano fuori Git; nel repository rimangono solo template placeholder;
- install, migrate, asset build, backend/frontend/websocket, worker, scheduler, Desk, website, health check e restart sono stati validati;
- il bootstrap e documentato come procedura ripetibile;
- durante start/stop/rebuild e test Centro Change, gli altri stack locali osservati sono rimasti `Up` senza restart o comandi rivolti a loro;
- i dati usati sono sintetici.

Classificazione confermata: riusare il runtime upstream tramite configurazione infrastrutturale Centro Change dedicata e pinata. Backup/restore (`CC-CAP-035`/`036`), upgrade/migration safety (`037`) e operational deploy reproducibility (`040`) restano capability separate.

### CC-CAP-002

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP002-IDENTITY-001`, `CAP002-LIFECYCLE-002`:

- Marley/Frappe fornisce un mapping nativo utile `User -> Healthcare Practitioner` e le User Permission Practitioner isolano correttamente A/B nei normali path list/direct;
- `Healthcare Practitioner.status=Disabled` non revoca da solo la visibilita permission-aware osservata;
- disabilitare `User.enabled` lascia persistente la User Permission Practitioner, quindi lo stato applicativo non coincide automaticamente con revoca del security principal;
- il reassignment documentale `Practitioner.user_id A -> C` non ha dimostrato un lifecycle nativo completo e sicuro;
- rollback e cleanup sono verificati.

Classificazione confermata: mantenere Marley `Healthcare Practitioner` e Frappe `User`/User Permission come baseline, aggiungendo in `centrochange_core` un servizio server-side di offboarding/reassignment che riconcilia status, User state e User Permission con revoca/grant deterministici e regression test list/direct/API.

### CC-CAP-003

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP003-PATIENT-IDENTITY-001`, `CAP003-PATIENT-MASTER-002` e boundary riusato `CAP004-SURFACES-002`:

- Marley `Patient` e una baseline master utilizzabile e il campo `uid` e univoco;
- l'unicita di `uid` non equivale a validazione formale del codice fiscale italiano e il campo osservato resta mutabile;
- create/read/update, Active/Disabled, Customer/Contact coupling e Version history sono riusabili;
- `frappe.client.get` rispetta il boundary A/B, mentre Marley `get_patient_detail` restituisce Patient B nel contesto professionista A, confermando leakage cross-assignment su un endpoint non permission-aware;
- l'hard delete non puo essere assunto come semplice cascade per i link Contact/Customer;
- rollback e cleanup sono verificati.

Classificazione confermata: mantenere Marley `Patient`, proteggendo o escludendo in `centrochange_core` gli endpoint Patient non permission-aware e definendo una policy esplicita di retention/disable/delete-unlink. Una eventuale validazione codice fiscale va introdotta solo come requisito dedicato.

### CC-CAP-004

Decisione owner del **2026-09-05**: **EXTENSION**.

Evidenza Spike 02 `S02-PAT-001`–`S02-PAT-012` e testlab `CAP004-SURFACE-001`, `CAP004-SURFACES-002`:

- il default Marley `Physician` sul `Patient` e troppo ampio e non soddisfa l'isolamento assegnato/non assegnato;
- la sola `User Permission: Patient` non e sufficiente come modello completo, perche il caso zero-assignment riapre la visibilita globale nel runtime testato;
- un `Custom DocPerm` restrittivo sul Patient, combinato con `DocShare` read/write sul singolo Patient assegnato, ha mantenuto A e B isolati nei normali path list/direct;
- revoca e riassegnazione hanno mostrato comportamento coerente con il pattern atomico `remove-old -> add-new -> commit`, incluso il confine cross-session osservato;
- nel probe `CAP004-SURFACES-002`, `frappe.get_list`, `frappe.client.get_list`, `frappe.client.get` e reportview hanno rispettato il boundary A/B; Data Export e stato negato senza diritto export;
- `frappe.get_all` ha invece mostrato entrambi i Patient, confermando che custom/third-party endpoint basati su `get_all`/raw query/SQL richiedono un guard Patient esplicito;
- rollback e cleanup hanno ripristinato `Custom DocPerm=0`, `DocShare=0` e preservato le due User Permission sintetiche persistenti.

Classificazione confermata: usare il motore Frappe come base e implementare in `centrochange_core` una piccola estensione server-side per assegnazione, revoca, riassegnazione atomica e guard espliciti sugli endpoint non permission-aware. La policy print/email sul Patient assegnato resta un punto separato da definire. Questa decisione non chiude automaticamente `CC-CAP-033`.

### CC-CAP-005

Decisione owner del **2026-09-05**: **EXTENSION**.

Evidenza Spike 02 `S02-PERM-003`–`S02-PERM-005` e testlab `CAP005-SURFACE-001`, `CAP005-BOUNDARY-003`:

- le User Permission native sul `Healthcare Practitioner` hanno mantenuto A e B separati nei normali path `Patient Appointment` list/direct;
- `frappe.get_list`, `frappe.client.get_list`, accesso diretto, reportview, Data Export e `patient_appointment.get_events` hanno restituito solo l'appuntamento del professionista corrente nel runtime testato;
- `patient_appointment.make_encounter` ha negato una sorgente cross-practitioner grazie al controllo read permission eseguito da `get_mapped_doc`;
- `frappe.get_all` ha mostrato entrambi gli Appointment, confermando che raw/get_all/SQL non sono un authorization boundary;
- il normale write permission di A su Appointment B era negato e un `check_permission("write")` esplicito ha correttamente bloccato l'accesso;
- Marley `patient_appointment.update_status`, invece, ha modificato Appointment B da `Scheduled` a `Confirmed` quando chiamato come A, perche usa `frappe.db.set_value` senza un controllo documentale esplicito;
- il probe ha eseguito rollback immediato e il cleanup finale ha verificato entrambi gli Appointment nuovamente `Scheduled`, con identita A/B e User Permission Practitioner preservate.

Classificazione confermata: riusare `Patient Appointment` Marley e i normali meccanismi Frappe permission-aware, aggiungendo in `centrochange_core` guard server-side sui mutatori Marley non permission-aware. `update_status` e il bypass runtime gia provato e deve essere coperto da regression test. Questa decisione non chiude automaticamente `CC-CAP-006`, `007`, `008`, `009` o `010`.

### CC-CAP-006

Decisione owner del **2026-09-05**: **CONFIGURATION**.

Evidenza Spike 02 `S02-SCHED-001`, `S02-SCHED-002` e testlab `CAP006-INVENTORY-001`, `CAP006-LIFECYCLE-003`:

- Marley `Patient Appointment` espone i campi core richiesti, gli stati `Scheduled/Open/Confirmed/Checked In/Checked Out/Closed/Cancelled/No Show`, `track_changes=1` e relazione con `Event`;
- un normale reschedule ha aggiornato data/ora, `appointment_datetime`, `appointment_end_datetime` e l'Event associato in modo coerente;
- il reschedule ha prodotto una nuova `Version` con le modifiche osservate;
- la cancellazione funzionale ha portato sia `Patient Appointment` sia `Event` a `Cancelled`;
- `duration` e `set_only_once`: nel runtime testato un tentativo programmatico di cambiare 60 -> 45 puo ritornare da `save()` senza eccezione ma lo stato persistito resta correttamente a 60 minuti, l'Event resta coerente e non viene generata una Version spuriosa; questo e un caveat API/UX, non una perdita di integrita nel caso osservato;
- rollback e cleanup hanno ripristinato esattamente Appointment A/B ed Event A/B alla baseline persistente.

Classificazione confermata: usare Marley `Patient Appointment` come record base dell'appuntamento/seduta e configurarne il lifecycle, senza introdurre oggi un `CC Appointment/Session` custom. Restano separate la protezione dei mutatori non permission-aware (`CC-CAP-005`), availability (`007`), concorrenza/double booking (`008`), booking pubblico/backend-only (`009`/`010`) e snapshot storico servizio/durata/prezzo (`013`).

### CC-CAP-007

Decisione owner del **2026-09-06**: **EXTENSION**.

Evidenza testlab `CAP007-INVENTORY-001`, `CAP007-AVAILABILITY-002`, `CAP007-SCHEDULE-004`, `CAP007-OWNER-005`, `CAP007-GUARD-006`:

- Marley `Practitioner Schedule` e adatto come baseline ricorrente settimanale e supporta orari diversi per giorno, mentre modellare la baseline con record ricorrenti `Practitioner Availability` ha mostrato conflitti di overlap non desiderati;
- Marley `Practitioner Availability` di tipo `Unavailable` funziona come overlay per ferie, assenze ed eccezioni e blocca server-side gli appuntamenti nel periodo indisponibile;
- il runtime usa `Europe/Rome` e il modello ibrido ha mantenuto il comportamento atteso nel fuso configurato;
- la sola configurazione permission `if_owner` non lega in sicurezza il Dynamic Link `scope` al professionista corrente: nel probe `CAP007-OWNER-005`, A ha potuto creare un record riferito a Practitioner B;
- nel probe finale `CAP007-GUARD-006`, un guard server-side esplicito `User -> Healthcare Practitioner` ha consentito ad A di modificare il proprio schedule e creare una propria assenza, negando entrambe le operazioni quando il target era Practitioner B;
- lo stesso servizio guarded ha consentito alla gestione centrale di operare su entrambi i professionisti;
- gli schedule ricorrenti sono dedicati uno-per-professionista per evitare che una modifica self-service possa alterare la baseline di un altro professionista;
- le modifiche a `Practitioner Schedule` hanno prodotto `Version` history;
- rollback e cleanup finali hanno rimosso schedule, child rows, availability e Version sintetiche e hanno preservato le User Permission Practitioner persistenti.

Classificazione confermata: riusare Marley per il modello dati e la logica di disponibilita, aggiungendo in `centrochange_core` una piccola estensione server-side per autorizzare il self-service solo sul Practitioner associato all'utente e consentire alla gestione centrale uno scope piu ampio. Nessuna patch a Frappe o Marley core. Il nome/ruolo definitivo di segreteria/admin resta separato.

### CC-CAP-008

Decisione owner del **2026-09-06**: **EXTENSION**.

Evidenza testlab `CAP008-INVENTORY-001`, `CAP008-CONCURRENCY-003`, `CAP008-RESCHEDULE-004`:

- i normali overlap e move collision sequenziali Marley sono stati respinti correttamente;
- l'inventario runtime non ha rilevato `FOR UPDATE`, named lock, vincolo univoco composito sullo slot o campo idempotency dedicato nel boundary nativo osservato;
- il race su nuove create e stato classificato `NON_PROBATIVE` per lock contention precedente al barrier e non e stato usato come prova di sicurezza;
- il follow-up probativo su due Appointment gia committati ha mostrato che entrambi i worker possono completare `validate_overlaps()` e poi committare sullo stesso Practitioner/timeslot, producendo un double booking concorrente;
- nello stesso scenario, un lock transazionale sulla riga stabile `Healthcare Practitioner` prima di save/revalidation ha serializzato i due worker: uno ha committato, il secondo ha rieseguito il controllo sullo stato aggiornato ed e stato respinto con `OverlapError`;
- rollback e cleanup hanno rimosso tutte le fixture Appointment/Event di test e preservato la baseline A/B.

Classificazione confermata: mantenere Marley `Patient Appointment` e la validazione overlap come base, aggiungendo in `centrochange_core` un boundary transazionale di serializzazione sui path create/reschedule sensibili. La vera idempotenza request-id/replay resta separata e va affrontata dove necessaria, in particolare nel booking pubblico `CC-CAP-009`. Nessuna patch a Frappe o Marley core.

### CC-CAP-009

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP009-BASELINE-002`, `CAP009-PUBLIC-BOUNDARY-003`:

- il baseline ha confermato Practitioner A/B non esposti nel portal (`show_in_portal=0`), schedule link vuoti e default appointment type non configurato;
- con fixture positiva completa, un Website User non correlato ha potuto creare booking scegliendo caller-controlled Patient e Practitioner;
- il path ha consentito booking verso Practitioner nascosto, off-schedule e in data passata;
- il retry non offre un contratto idempotente di replay: il secondo tentativo e stato respinto da overlap, non riconciliato con il risultato originario;
- cleanup e stato verificato.

Classificazione confermata: riusare schedule/availability di `CC-CAP-007` e serializzazione di `CC-CAP-008`, ma esporre il booking pubblico solo tramite un ingress server-side Centro Change che valida identita Patient, practitioner ammessi, appointment type, slot/date e idempotency; non usare `patient_portal.make_appointment` as-is come boundary di autorizzazione.

### CC-CAP-010

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP010-BACKEND-ONLY-001`:

- il controllo backend permission-aware ha consentito la creazione autorizzata di una seduta successiva;
- REST/client/direct create e REST update ordinari hanno rispettato i permessi e negato il Website User;
- il Website User ha tuttavia potuto creare appuntamenti successivi e cross-patient attraverso il portal Marley;
- un mutatore generico `set_request_status` ha consentito una mutazione di stato non coerente con il boundary backend-only; `update_status` resta inoltre il regression sentinel gia provato da CC-CAP-005;
- cleanup e stato verificato.

Classificazione confermata: mantenere `Patient Appointment` e i normali path backend permission-aware, aggiungendo un authorization service server-side che decide se un create/mutation path e ammesso dopo il primo incontro e protegge/override/esclude tutti gli endpoint Marley non permission-aware. Il boundary deve restare server-side, non UI-only.

### CC-CAP-011

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP011-CATALOG-PRICE-SNAPSHOT-INVENTORY-001` e runtime Wave 2:

- ERPNext `Item` / `Item Group` forniscono un master catalogo e tassonomia riusabili;
- il collegamento tra servizio economico e scheduling Marley non e nativamente un'unica fonte autorevole;
- `Item.disabled` non deve essere assunto come guard automatico sufficiente per impedire booking del relativo servizio.

Classificazione confermata: usare `Item` come master servizio/economico e `Item Group` per tassonomia/reporting, aggiungendo una sottile estensione Centro Change che collega il servizio al profilo scheduling e applica eligibility/disabled guard server-side. Evitare due master indipendenti per la stessa prestazione.

### CC-CAP-012

Decisione owner del **2026-09-08** sotto standing technical authorization: **CONFIGURATION**.

Evidenza testlab `CAP012-EFFECTIVE-PRICE-002`:

- Price List + `Item Price` effective-dated hanno fornito la semantica di prezzo richiesta nel runtime testato;
- il modello puo essere riusato come fonte autorevole del prezzo corrente senza introdurre un motore prezzi custom;
- la data esatta di cattura del prezzo nello snapshot appuntamento resta policy di prodotto separata.

Classificazione confermata: configurare Price List + effective-dated Item Price come sistema prezzi. Le esigenze di storico sulla singola seduta sono risolte da `CC-CAP-013`, non duplicando la tariffa in un secondo master.

### CC-CAP-013

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP013-CATALOG-PRICE-SNAPSHOT-001`:

- `Patient Appointment.duration` si comporta come snapshot stabile della durata iniziale;
- Marley non conserva sulla seduta uno snapshot completo e autorevole di service identity/label, prezzo, valuta e Price List provenance;
- il billing Marley osservato ri-risolve la tariffa corrente dall'Appointment Type, quindi una variazione successiva puo influenzare una seduta storica se non viene introdotto uno snapshot esplicito;
- cleanup e stato verificato.

Classificazione confermata: riusare la durata nativa e aggiungere campi snapshot supportati su `Patient Appointment` per servizio, label, prezzo, valuta e provenienza tariffaria. Futuro settlement/accounting deve leggere questi snapshot invece di ri-risolvere il prezzo corrente.

### CC-CAP-014

Decisione owner del **2026-09-08** sotto standing technical authorization: **EXTENSION**.

Evidenza testlab `CAP014-SETTLEMENT-002`:

- `Mode of Payment` e riusabile come tassonomia/riferimento informativo;
- la mutation sintetica ha dimostrato che un Mode of Payment informativo non mappato puo essere creato/modificato/disabilitato senza generare `Sales Invoice`, `Payment Entry`, `GL Entry` o `Payment Ledger Entry`;
- cleanup e stato verificato.

Classificazione confermata: introdurre in Centro Change uno stato settlement operativo minimo (pagato si/no, metodo informativo, attore/data/correzione e audit) referenziando `Mode of Payment`, senza attivare automaticamente accounting ERPNext.

### CC-CAP-015

Decisione owner del **2026-09-08** sotto standing technical authorization: **DEFERRED / EXCLUDE FROM CURRENT SURFACE**.

Evidenza testlab `CAP015-PATHWAY-001` (`PARTIAL`) e source inventory Wave 3:

- i boundary di posting ERPNext (`Sales Invoice`, `Payment Entry`, Payment Ledger/GL) sono stati identificati;
- `Payment Entry.reference_no` non fornisce da solo una chiave di idempotenza applicativa sufficiente;
- nessuna mutation contabile e stata eseguita e il pathway non e richiesto per l'MVP informativo;
- una assertion sorgente del probe ha sovrastimato un segnale `creates_sales_invoice`, ma il risultato non cambia la scelta di non attivare accounting ora.

Classificazione confermata: mantenere il pathway futuro documentato ma escluso dalla superficie corrente. Prima dell'attivazione servono mapping `CC Settlement -> Sales Invoice -> Payment Entry`, idempotency key deterministica, reversal/correction, snapshot provenance, rehearsal di migrazione e integrita contabile.

### CC-CAP-016

Decisione owner del **2026-09-08** sotto standing technical authorization: **CUSTOM**.

Evidenza testlab `CAP016-PACKAGE-002` e inventory Wave 3:

- `Product Bundle` rappresenta composizione statica di articoli e non un saldo consumabile per paziente;
- `Subscription` e orientata a billing ricorrente e puo generare/submittare invoice, semantica non adatta al package ledger operativo corrente;
- il transaction surrogate del probe ha validato grant/reserve/release/consume/adjust, serializzazione `FOR UPDATE` contro overspend e idempotenza tramite event key deterministica;
- il surrogate ToDo e solo strumento di test, non schema prodotto;
- cleanup e stato verificato.

Classificazione confermata: implementare un modello Centro Change dedicato, append-oriented, con `CC Package Template`, `CC Patient Package` e `CC Package Ledger`, includendo reserve/release/consume/adjust, concurrency, idempotenza e correction audit. Non forzare Product Bundle/Subscription come modello di saldo paziente.

### CC-CAP-020

Decisione owner del **2026-09-05**: **EXTENSION**.

Evidenza Spike 02 `S02-PAT-013`–`S02-PAT-021`:

- `patient_history.get_feed` e `get_feed_for_dt` hanno entrambi evidenza runtime non-vuota di FAIL sul confine di assegnazione Patient;
- sostituire semplicemente `frappe.db.get_all` con `frappe.get_list` non applica automaticamente il confine, anche perche `Patient Medical Record.patient` usa `ignore_user_permissions=1` nel runtime osservato;
- un guard esplicito basato sul permesso di lettura del Patient preserva il risultato autorizzato e nega il cross-patient nel probe;
- Frappe espone `override_whitelisted_methods` come superficie supportata per intercettare i due metodi senza patchare Marley core.

Classificazione confermata: riusare la Patient History Marley dietro una piccola estensione in `centrochange_core`, con override protetti e regression test. Questa decisione resta limitata a CC-CAP-020 e non decide il riuso Marley complessivo A/B/C.

### CC-CAP-021

Decisione owner del **2026-09-05**: **DEFERRED / EXCLUDE FROM CURRENT SURFACE**.

Evidenza testlab `S02-PAT-015`, `S02-PROG-001`–`S02-PROG-006`:

- il modulo Marley Patient Progress installato espone sette metodi whitelisted con parametro `patient`; l'inventario sorgente ha rilevato accesso dati diretto e nessun guard Patient esplicito;
- `get_patient_heatmap_data` ha evidenza runtime non-vuota di FAIL sul confine A/B;
- `get_patient_assessment_data`, `get_therapy_assessment_correlation_data` e `get_assessment_parameter_data` hanno tutti riflesso marker sintetici di Patient B nel contesto professionista A, con normale Patient-B read negato;
- `get_therapy_sessions_count` e `get_therapy_progress_data` hanno entrambi riflesso una Therapy Session sintetica di Patient B nel contesto A;
- `get_therapy_sessions_distribution_data` non e eseguibile nel runtime Frappe 16.31 osservato per il formato `count(*)` rifiutato dal query layer; il JS Marley corrente mantiene inoltre il relativo grafico nascosto/commentato come broken;
- tutti i test mutanti pertinenti hanno verificato rollback/cleanup e preservazione delle User Permission sintetiche persistenti.

Classificazione confermata: non esporre ne sviluppare Patient Progress nello scope corrente. La capability resta riapribile se emerge un requisito funzionale reale; in quel caso rivalutare extension selettiva o analytics custom con autorizzazione server-side esplicita. Questa decisione non determina il riuso Marley complessivo A/B/C.

### CC-CAP-017..040 — final technical dispositions

Decisione owner del **2026-09-09** sotto standing technical authorization; `CC-CAP-037` confermata esplicitamente: **40/40 technical dispositions**.

Evidenza autorevole: `centrochange-testlab` coordinator #56, issue/probe capability-specific e `centrochange_core` #18. Sintesi:

- `CC-CAP-017/018/019`: note organizzative `CONFIGURATION`, note professionali riservate `CUSTOM`, scheda paziente unificata `EXTENSION`, sulla base della recovery Wave 4 con cleanup verificato.
- `CC-CAP-022..026`: `EXTENSION` per lifecycle giornaliero/reminder/auto-lock/cancellation-policy/correction; il ciclo temporale ha verificato timezone, scheduler, idempotenza e server-side enforcement. Per `CC-CAP-025`, il probe cancellation-specific ha provato `<48h => LATE CANCELLATION / DUE` e waiver backoffice auditata; l'esatta uguaglianza a `48:00:00` resta una policy business non definita.
- `CC-CAP-027..030`: `EXTENSION`, `CUSTOM`, `CONFIGURATION`, `CUSTOM` rispettivamente per Communication/Notification, reporting operativo, export/print/email e dashboard, secondo i boundary security/ops provati.
- `CC-CAP-031/032/036`: `DEFERRED / EXCLUDE FROM CURRENT SURFACE` finché sito Builder, clean rebuild e restore/DR non sono riproducibili dal deploy path versionato completo.
- `CC-CAP-033/034`: `CUSTOM` per permission model generale e audit business; i primitivi Frappe restano riusabili ma non sufficienti come contratto complessivo.
- `CC-CAP-035`: `CONFIGURATION`; le primitive `bench backup --with-files` coprono DB/public/private/config tramite runbook, mantenendo raw artifacts fuori Git.
- `CC-CAP-037`: `DEFERRED / EXCLUDE FROM CURRENT SURFACE`, con **TEST OUTCOME: PARTIAL** sul run isolato `centrochange-cap037-20260909r2`. Provati CURRENT → checkpoint completo hashato → TARGET migrate exit `0` → target health/hooks/services → restore CURRENT con successo nel log e pin/health ripristinati → `cleanup.verified=true`; nessun manual SQL/source/upstream patch e nessun contatto con `centrochange-dev`. Residui: inventari normalizzati pre/post di schema, Custom Field e Custom DocPerm non catturati e restore exit code non preservato indipendentemente. Questi gap impediscono la promozione a `CONFIGURATION` senza un nuovo ciclo discriminante completo.
- `CC-CAP-038/039`: `CUSTOM` per endpoint authorization e leakage regression suite sui caller-controlled IDs e sui path REST/direct/list/report/export/query/app endpoint.
- `CC-CAP-040`: `CUSTOM`; il clean-deploy FAIL e discriminante perché la recipe prodotto versionata non dichiara completamente il bootstrap Healthcare/Marley. Il provisioner testlab CAP037 non costituisce prova di deploy riproducibile del prodotto.

La technical classification non equivale a product implementation: le estensioni/custom/deferred indicate restano lavoro downstream separato.

## 6. Security surface minima per capability sensibili

Quando una capability tocca dati o autorizzazioni, i test devono considerare, se applicabili:

- Desk/UI;
- List View;
- direct document access;
- REST/API;
- whitelisted/app endpoints;
- Report;
- export;
- print/email;
- custom query/query builder;
- raw/get_all/SQL paths usati da app;
- permission state dopo reassignment/revocation;
- cache/session effects.

La UI nascosta non e un controllo di sicurezza.

## 7. Completeness gate

Una capability non puo essere proposta come `PROVEN NATIVE`, `CONFIGURATION`, `EXTENSION` o `CUSTOM` finche non sono compilati, ove pertinenti:

```text
[ ] requisito/semantica chiariti
[ ] candidati native identificati
[ ] extension supportate identificate
[ ] app pertinente valutata
[ ] custom fallback definito
[ ] criteri qualita/UX valutati
[ ] security surfaces valutate
[ ] runtime evidence presente
[ ] concurrency/idempotence testata se pertinente
[ ] reporting/export/API testati se pertinenti
[ ] upgrade/maintenance risk valutato
[ ] cleanup/rollback verificato per test mutanti
[ ] unknown residui dichiarati
[ ] raccomandazione separata dalla decisione finale
```

Se una voce non e applicabile deve essere marcata `N/A` con motivazione, non semplicemente omessa.

## 8. Regola di copertura

Il testlab deve poter produrre, per ogni `CC-CAP-NNN`, un indice di task/result/evidence. Una review periodica deve segnalare:

- capability senza test ma con runtime validation richiesta;
- capability con test `NON_PROBATIVE` non sostituiti da evidenza utile;
- capability con `FAIL/PARTIAL` senza decisione o mitigazione proposta;
- decisioni senza evidence reference;
- test mutanti senza cleanup verificato;
- nuove funzioni introdotte nel prodotto senza capability ID associato.

## 9. Fonti correnti

Questa matrice e stata ricostruita dalle fonti tecniche versionate correnti:

- `README.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `docs/DECISIONS.md`
- `docs/RUNTIME-BASELINE.md`
- Spike 01 e Spike 02 / relative issue runtime
- `2008hitch-afk/centrochange-testlab` issue #56 e issue/probe capability-specific
- `centrochange_core` issue #18

Non sostituisce i requisiti funzionali del cliente e non inventa decisioni non ancora approvate.