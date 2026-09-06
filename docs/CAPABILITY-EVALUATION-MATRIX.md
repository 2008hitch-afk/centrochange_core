# Centro Change — Capability Evaluation Matrix

**Stato:** CANONICAL PLAN / RUNTIME VALIDATION IN PROGRESS  
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

## 4. Matrice canonica iniziale

Questa versione include tutte le capability esplicitamente presenti nelle fonti tecniche correnti. Nuovi requisiti scoperti successivamente devono ricevere un nuovo ID senza rinumerare quelli esistenti.

| ID | Capability | Candidati native / extension / app | Custom candidate/fallback | Test obbligatori principali | Stato corrente |
|---|---|---|---|---|---|
| CC-CAP-001 | Runtime foundation e isolamento DEV | Frappe/ERPNext container pattern; Docker Compose | infra Centro Change dedicata | versioni, rebuild, restart, network/volume isolation, no cross-project impact | EVIDENCE AVAILABLE / REVIEW REQUIRED |
| CC-CAP-002 | Identita professionista | User, Employee; Marley `Healthcare Practitioner`; eventuale Sales Person solo proiezione | `CC Professional` se il fit nativo/app e insufficiente | identity mapping, permission scope, disable/reassignment, list/direct/API | RUNTIME VALIDATION REQUIRED |
| CC-CAP-003 | Anagrafica paziente | Contact/Customer dove semanticamente corretti; Marley `Patient` | `CC Patient` o extension fields se necessario | identity semantics, codice fiscale/UID, CRUD, privacy, direct/API/report/export | RUNTIME VALIDATION REQUIRED |
| CC-CAP-004 | Assegnazione paziente-professionista | Frappe User Permission / DocShare / supported permission hooks; Marley relations se pertinenti | assignment model + permission hooks in `centrochange_core` | own/cross patient, reassignment, revoke, list/direct/API/report/export/query | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-005 | Segregazione appuntamenti per professionista | Frappe permissions/User Permission; Marley `Patient Appointment` | custom permission layer o custom appointment | list own/cross, direct read/write, API, report/export, reassignment | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-006 | Appuntamento/seduta | ERPNext/Frappe scheduling primitives; Marley `Patient Appointment` | `CC Appointment/Session` se semantica insufficiente | create/update/move/cancel, lifecycle, history, required fields, extension fit | **CONFIGURATION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-007 | Disponibilita professionista | Marley `Practitioner Availability` / schedules | custom availability model | recurring availability, exception/absence, timezone, access scope, edit history | **EXTENSION — OWNER CONFIRMED 2026-09-06** |
| CC-CAP-008 | No double booking / slot concurrency | native appointment validation where available | transactional lock/constraint in `centrochange_core` | concurrent booking, retry, stale slot, move collision, idempotence | **EXTENSION — OWNER CONFIRMED 2026-09-06** |
| CC-CAP-009 | Primo incontro pubblico solo Marco/Francesca | Website/Builder + native scheduling filters; Marley portal if fit | custom booking endpoint/rule | public eligibility, allowed practitioners, race condition, abuse/input validation | RUNTIME VALIDATION REQUIRED |
| CC-CAP-010 | Sedute successive solo backend | Desk/role permissions / workflow | custom server-side transition/rule | public route denial, backend allow, API bypass attempts | RUNTIME VALIDATION REQUIRED |
| CC-CAP-011 | Prestazioni / catalogo servizi | Item, Item Group | custom service metadata only if needed | semantics, active/inactive, duration linkage, reporting compatibility | RUNTIME VALIDATION REQUIRED |
| CC-CAP-012 | Prezzi | Item Price / Price List | custom pricing rule only where native fit fails | effective price, historical changes, role access, future accounting compatibility | RUNTIME VALIDATION REQUIRED |
| CC-CAP-013 | Snapshot storico servizio/durata/prezzo sulla seduta | supported custom fields / snapshot on native appointment | fields/doctype in `centrochange_core` | price/duration changes after booking, historical immutability, audit | RUNTIME VALIDATION REQUIRED |
| CC-CAP-014 | Pagato Si/No + metodo informativo MVP | Mode of Payment as reference; ERP accounting evaluated but not auto-triggered | `CC Settlement` | payment flag semantics, correction/audit, permissions, no unintended Payment Entry | RUNTIME VALIDATION REQUIRED |
| CC-CAP-015 | Future invoice/payment/accounting pathway | Sales Invoice, Payment Entry, Payment Ledger | adapter from `CC Settlement` | mapping, idempotent posting, reversal, migration path, accounting integrity | DEFERRED / RUNTIME VALIDATION REQUIRED BEFORE ACTIVATION |
| CC-CAP-016 | Pacchetti | Product Bundle / Subscription evaluated for semantic fit | `CC Package Template`, `CC Patient Package`, `CC Package Ledger` | reserve/release/consume/adjust, concurrency, idempotence, correction/audit | RUNTIME VALIDATION REQUIRED |
| CC-CAP-017 | Note organizzative | native Communication/comment mechanisms evaluated | `CC Organizational Note` | secretary access, professional access, API/report/export/direct, audit | RUNTIME VALIDATION REQUIRED |
| CC-CAP-018 | Note professionali riservate | native/private record mechanisms; Marley clinical records evaluated | `CC Professional Note` | secretary denial, assigned professional scope, API/report/export/direct/query leak tests | RUNTIME VALIDATION REQUIRED |
| CC-CAP-019 | Scheda paziente unificata | Desk/Form/dashboard composition; Marley patient views | custom workspace/page if needed | data aggregation, permission inheritance, performance, leakage between sections | RUNTIME VALIDATION REQUIRED |
| CC-CAP-020 | Patient history / clinical feed | Marley patient history endpoints | guarded extension or custom feed | assigned/cross patient, endpoint arguments, list/direct/API, non-empty fixtures, permission bypass | **EXTENSION — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-021 | Patient progress / clinical analytics | Marley patient progress methods | guarded extension/custom analytics | cross-patient reads, SQL/get_all paths, empty/non-empty fixtures, report/export consistency | **DEFERRED / EXCLUDE FROM CURRENT SURFACE — OWNER CONFIRMED 2026-09-05** |
| CC-CAP-022 | Chiusura giornaliera sedute | Frappe scheduler/queue/workflow primitives | `CC Session Closure` | Pending/Closed/Auto Locked/Reopened, retries, idempotence, permissions, audit | RUNTIME VALIDATION REQUIRED |
| CC-CAP-023 | Reminder 21:00 | Notification/email + scheduler | scheduled job in `centrochange_core` | only pending sessions, duplicate prevention, retry, timezone, delivery failure | RUNTIME VALIDATION REQUIRED |
| CC-CAP-024 | Auto-lock 07:00 giorno successivo | scheduler/workflow extension | custom scheduled rule | boundary time, retries, idempotence, lock enforcement server-side | RUNTIME VALIDATION REQUIRED |
| CC-CAP-025 | Regola 48h | workflow/permission extension if fit | centralized business rule | exact boundary, timezone, override roles, API bypass, audit | RUNTIME VALIDATION REQUIRED |
| CC-CAP-026 | Sblocco/correzione chiusure | Role Permission / Workflow | custom correction action | authorized roles only, immutable audit, repeated corrections, direct/API | RUNTIME VALIDATION REQUIRED |
| CC-CAP-027 | Email / Communication / Notification | Frappe Email Account, Communication, Notification | custom templates/jobs only if required | permissions, retry, duplicate prevention, failure visibility, no secret leakage | RUNTIME VALIDATION REQUIRED |
| CC-CAP-028 | Reporting operativo | native Report infrastructure | custom Script/Query Report | correctness, role filtering, assigned-patient isolation, performance | RUNTIME VALIDATION REQUIRED |
| CC-CAP-029 | Export/print/email document surfaces | Frappe print/export/email infrastructure | explicit server-side guards/extensions | same permission boundary as UI/direct access; hidden-field/data leakage | RUNTIME VALIDATION REQUIRED |
| CC-CAP-030 | Dashboard direzionale | native dashboard/report/chart | custom dashboard | aggregate correctness, role scope, privacy, performance | RUNTIME VALIDATION REQUIRED |
| CC-CAP-031 | Sito pubblico branded | Frappe Website / Builder | custom blocks/pages | reproducible build, Git versionability, responsive UX, no admin leakage | RUNTIME VALIDATION REQUIRED |
| CC-CAP-032 | Builder/Git reproducibility | Builder supported workflow and pinned source | custom build/deploy automation | rebuild from clean state, asset parity, version pinning, upgrade path | RUNTIME VALIDATION REQUIRED |
| CC-CAP-033 | Permission model generale | Frappe Role Permission, User Permission, DocShare, supported hooks | centralized `centrochange_core` permission logic | list/direct/API/report/export/query, reassignment, cache, strict user permissions | RUNTIME VALIDATION REQUIRED |
| CC-CAP-034 | Audit business | Version/audit facilities where sufficient | custom immutable audit events | actor/time/before-after, protected access, correction trail, export restrictions | RUNTIME VALIDATION REQUIRED |
| CC-CAP-035 | Backup | bench/native DB+files backup primitives | orchestration/runbook only | DB + public/private files + config, encryption/location policy, failure handling | RUNTIME VALIDATION REQUIRED |
| CC-CAP-036 | Restore / disaster recovery | bench restore primitives | automated isolated restore procedure | clean-environment restore, version compatibility, integrity checks, measured RTO evidence | RUNTIME VALIDATION REQUIRED |
| CC-CAP-037 | Upgrade/migration safety | pinned upstream versions + Frappe migrations | migration code in `centrochange_core` | clean upgrade rehearsal, schema migration, regression suite, rollback strategy | RUNTIME VALIDATION REQUIRED |
| CC-CAP-038 | API/web endpoint authorization | Frappe whitelisted/REST permission mechanisms; app endpoints | wrappers/guards in `centrochange_core` | caller-controlled IDs, cross-user reads/writes, get_all/sql bypass, error behavior | RUNTIME VALIDATION REQUIRED |
| CC-CAP-039 | Direct/query/report leakage regression suite | native permission-aware APIs where applicable | test/guard layer | REST, URL direct, List, Report, export, custom query, app endpoints | RUNTIME VALIDATION REQUIRED |
| CC-CAP-040 | Operational deploy reproducibility | Compose + pinned images/apps | deploy scripts/runbook | fresh build/start, migrate, health checks, rollback, no manual container patching | RUNTIME VALIDATION REQUIRED |

## 5. Known evidence already available

### CC-CAP-001

Spike 01 ha prodotto evidenze runtime locali su stack pinato, network/volume dedicati, restart, worker/scheduler e assenza di interferenza osservata con gli altri stack. La promozione architetturale resta separata dalla sola evidenza runtime.

### CC-CAP-002 / 004 / 005

Lo Spike 02 ha gia osservato il legame nativo `User -> Healthcare Practitioner` e sta valutando User Permission/DocShare e propagazione verso Patient/Patient Appointment. Nessuna decisione finale di riuso Marley e ancora autorizzata.

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

Non sostituisce i requisiti funzionali del cliente e non inventa decisioni non ancora approvate.