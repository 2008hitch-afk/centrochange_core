# Technical Decision Log — Centro Change

Questo file registra **decisioni tecniche proposte o confermate** nel repository tecnico. Non sostituisce la validazione cliente dei requisiti funzionali.

## TD-001 — Piattaforma

**Stato:** PROPOSTA / RUNTIME VALIDATION REQUIRED

Centro Change viene costruito su Frappe Framework + ERPNext + Builder/Website + custom app `centrochange_core`.

## TD-002 — Upstream immutabile

**Stato:** PROPOSTA FORTE

Non modificare direttamente Frappe, ERPNext o Builder. Usare meccanismi di estensione supportati.

## TD-003 — Native-first

**Stato:** PROPOSTA FORTE

Ordine di scelta:

1. native;
2. extension;
3. official app;
4. custom `centrochange_core`;
5. external integration.

Criterio: qualità, sicurezza, tempo di sviluppo, manutenibilità/upgrade.

## TD-004 — Runtime locale

**Stato:** RUNTIME VALIDATION REQUIRED

Riutilizzare il workstation Windows/WSL2/Docker già disponibile come host, creando `centrochange-dev` come stack isolato. Riutilizzare pattern/tooling, non stato applicativo di altri progetti.

## TD-005 — Marley Health

**Stato:** OPEN / SPIKE REQUIRED

Prima di definire Patient/Practitioner/Appointment/Availability custom, valutare Marley Health sul runtime.

Esiti ammessi:

- riuso esteso;
- riuso selettivo;
- nessun riuso.

## TD-006 — Professionista

**Stato:** PROPOSTA

`Sales Person` non è identità operativa né security principal. Può essere proiezione economica opzionale.

## TD-007 — Pagamento MVP

**Stato:** PROPOSTA

Pagato Sì/No + metodo informativo non deve generare automaticamente `Payment Entry`. Usare settlement operativo separato, con pathway futuro verso Sales Invoice/Payment Entry.

## TD-008 — Pacchetti

**Stato:** PROPOSTA / SPIKE REQUIRED

Pacchetti custom con ledger append-oriented. Non forzare Product Bundle/Subscription se la semantica non coincide.

## TD-009 — Note

**Stato:** PROPOSTA FORTE / SECURITY CRITICAL

Separare `CC Organizational Note` e `CC Professional Note`, con permessi server-side e test anti-leakage.

## TD-010 — Git/Codex

**Stato:** OPERATIVO

- ChatGPT: architect/reviewer;
- Codex: runtime engineer/implementer;
- GitHub: source of truth tecnico;
- issue → branch → PR → evidence → review → merge.

## TD-011 — CC-CAP-020 Patient History / clinical feed

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **EXTENSION**.

Decisione:

- riutilizzare la Patient History di Marley come base funzionale/UI;
- non usare i due endpoint PMR `get_feed` e `get_feed_for_dt` as-is nel perimetro professionisti assegnati;
- applicare in `centrochange_core` un'estensione supportata tramite override dei metodi whitelisted, con autorizzazione esplicita sul Patient e regression test own/cross-patient;
- non patchare Frappe o Marley core;
- mantenere come fallback un feed custom o l'esclusione della Patient History se l'override non mantiene il contratto/upgrade path richiesto.

Evidenza principale: Spike 02 `S02-PAT-013`–`S02-PAT-021`. I due endpoint PMR hanno FAIL runtime indipendenti sul confine di assegnazione; il guard esplicito sul Patient ha PASS semantico; il runtime Frappe espone `override_whitelisted_methods` come superficie di estensione supportata.

Questa decisione è limitata a **CC-CAP-020**. Non determina da sola l'esito complessivo Marley A/B/C e non approva automaticamente Patient Progress o altre capability Marley.

## TD-012 — CC-CAP-021 Patient Progress / clinical analytics

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **DEFERRED / EXCLUDE FROM CURRENT SURFACE**.

Decisione:

- non esporre né sviluppare la pagina/funzionalità Marley Patient Progress nello scope corrente di Centro Change;
- non correggere ora l'intera superficie analytics Marley solo perché disponibile nell'app;
- mantenere la capability riapribile se emergerà un requisito funzionale reale di andamento clinico, assessment o terapia;
- in caso di riapertura, rivalutare una extension selettiva o analytics custom Centro Change con autorizzazione server-side esplicita;
- nessuna patch a Frappe o Marley core.

Evidenza principale: Spike 02 / testlab `S02-PAT-015`, `S02-PROG-001`–`S02-PROG-006`.

Nel runtime osservato, i sei percorsi Patient Progress effettivamente eseguibili testati con fixture non vuote non rispettano il confine A/B quando il caller passa esplicitamente Patient B, mentre `get_therapy_sessions_distribution_data` fallisce per incompatibilità con il controllo Frappe v16 sui campi SELECT. Il JS Marley corrente inoltre mantiene il grafico di distribuzione nascosto/commentato come broken.

Conseguenza: la capability non è eliminata definitivamente; viene esclusa dalla superficie corrente per ridurre rischio di sicurezza, superficie custom e tempo di sviluppo finché non esiste un requisito che ne giustifichi la riapertura.

Questa decisione è limitata a **CC-CAP-021** e non determina da sola l'esito complessivo Marley A/B/C.

## TD-013 — CC-CAP-004 Assegnazione paziente-professionista

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **EXTENSION**.

Decisione:

- usare il motore permessi Frappe come base, con `Custom DocPerm` restrittivo sul `Patient` per il ruolo professionista e `DocShare` per concedere l'accesso al singolo Patient assegnato;
- non usare la sola `User Permission: Patient` come modello completo di assegnazione, perché il caso zero-assignment non mantiene il deny-by-default nel runtime testato;
- gestire in `centrochange_core` le operazioni di assegnazione, revoca e riassegnazione come estensione server-side controllata;
- per la riassegnazione usare il pattern atomico `remove-old -> add-new -> commit`, supportato dalle evidenze single-session e cross-session dello Spike 02;
- mantenere espliciti guard Patient negli endpoint custom/third-party che usano `frappe.get_all`, `frappe.db.get_all`, query raw o SQL, perché tali primitive non applicano il normale boundary documentale;
- non patchare Frappe o Marley core;
- mantenere aperta come policy separata la scelta su print/email del Patient assegnato, perché il DocShare read di Frappe abilita anche tali superfici nel runtime osservato.

Evidenza principale: Spike 02 `S02-PAT-001`–`S02-PAT-012` più testlab `CAP004-SURFACE-001` e `CAP004-SURFACES-002`.

Nel runtime osservato, `Custom DocPerm + DocShare` ha rispettato il confine A/B su list, `frappe.client.get_list`, `frappe.client.get`, reportview e ha negato Data Export senza relativo diritto. Revoca e riassegnazione hanno mostrato comportamento coerente con deny-before-grant e con il confine di commit. Il probe ha inoltre confermato che `get_all` vede entrambi i Patient e va quindi trattato come primitiva interna/privilegiata che richiede un guard esplicito quando esposta tramite endpoint.

Questa decisione è limitata a **CC-CAP-004**. Non decide automaticamente `CC-CAP-033` Permission model generale né sostituisce i test specifici delle altre capability sensibili.

## TD-014 — CC-CAP-005 Segregazione appuntamenti per professionista

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **EXTENSION**.

Decisione:

- riutilizzare Marley `Patient Appointment` e la normale propagazione Frappe basata su `User Permission: Healthcare Practitioner` come base della segregazione appuntamenti;
- mantenere i normali path permission-aware Frappe per list, direct access, client API, reportview, export e calendar, che nel runtime testato hanno rispettato il confine A/B;
- non usare come trusted authorization boundary i mutatori whitelisted Marley che scrivono direttamente sul database senza controllo documentale esplicito;
- proteggere in `centrochange_core` i mutatori Marley non permission-aware con un guard server-side esplicito sul `Patient Appointment` prima della mutazione; `update_status` è il bypass runtime già provato e deve essere coperto da regression test own/cross-appointment;
- trattare `frappe.get_all`, `frappe.db.get_all`, raw query e SQL come primitive interne che richiedono guard espliciti quando esposte tramite endpoint custom/third-party;
- non patchare Frappe o Marley core.

Evidenza principale: Spike 02 `S02-PERM-003`–`S02-PERM-005`, testlab `CAP005-SURFACE-001` e `CAP005-BOUNDARY-003`.

Nel runtime osservato, A vede solo Appointment A e B solo Appointment B su `frappe.get_list`, `frappe.client.get_list`, accesso diretto, reportview, export e `patient_appointment.get_events`; `make_encounter` ha negato una sorgente cross-practitioner grazie al controllo permission-aware di `get_mapped_doc`. Al contrario, `patient_appointment.update_status` ha consentito ad A di cambiare lo stato di Appointment B da `Scheduled` a `Confirmed` nonostante il normale `write` fosse negato. Il test ha eseguito rollback immediato e cleanup verificato.

Questa decisione è limitata a **CC-CAP-005**. Non decide automaticamente lifecycle/seduta (`CC-CAP-006`), availability (`CC-CAP-007`), no-double-booking (`CC-CAP-008`) o prenotazione pubblica/backend-only (`CC-CAP-009`/`010`).

## TD-015 — CC-CAP-006 Appuntamento/seduta

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **CONFIGURATION**.

Decisione:

- usare Marley `Patient Appointment` come record base dell'appuntamento/seduta di Centro Change;
- riusare il lifecycle nativo osservato per creazione, data/ora, durata iniziale, stati, calendario/Event, spostamento, cancellazione e storico Version;
- non introdurre nello scope corrente un `CC Appointment/Session` custom, perché l'evidenza runtime non mostra un beneficio sufficiente a giustificare duplicazione di modello e manutenzione;
- trattare separatamente la sicurezza dei mutatori Marley non permission-aware secondo `CC-CAP-005` / TD-014;
- lasciare a capability separate availability (`CC-CAP-007`), concurrency/double booking (`CC-CAP-008`), booking pubblico/backend-only (`CC-CAP-009`/`010`) e snapshot storico servizio/durata/prezzo (`CC-CAP-013`);
- non patchare Frappe o Marley core.

Evidenza principale: Spike 02 `S02-SCHED-001`, `S02-SCHED-002`; testlab `CAP006-INVENTORY-001` e `CAP006-LIFECYCLE-003`.

Nel runtime osservato, il reschedule ha aggiornato coerentemente `appointment_date`, `appointment_time`, `appointment_datetime`, `appointment_end_datetime` e l'Event associato e ha prodotto una nuova `Version`. La cancellazione funzionale ha portato Appointment ed Event a `Cancelled`. `duration` è `set_only_once`: un tentativo programmatico 60 -> 45 può ritornare da `save()` senza eccezione ma lo stato persistito resta 60, l'Event resta coerente e non compare una Version spuriosa; il comportamento è quindi un caveat API/UX da non interpretare come mutazione riuscita. Rollback e cleanup hanno ripristinato Appointment A/B ed Event A/B alla baseline.

Questa decisione è limitata a **CC-CAP-006** e non modifica né sostituisce le decisioni sulle capability collegate sopra indicate.

## TD-016 — CC-CAP-007 Disponibilita professionista

**Stato:** CONFERMATA DALL'OWNER — 2026-09-06

Classificazione capability: **EXTENSION**.

Decisione:

- usare Marley `Practitioner Schedule` come baseline ricorrente settimanale, con uno schedule dedicato per ciascun professionista;
- usare Marley `Practitioner Availability` di tipo `Unavailable` per ferie, assenze ed eccezioni;
- consentire sia la gestione centrale sia il self-service del singolo professionista;
- instradare il self-service attraverso una piccola estensione server-side in `centrochange_core` che risolve il mapping `User -> Healthcare Practitioner` e consente la mutazione solo quando il Practitioner target coincide con quello dell'utente;
- negare prima della scrittura ogni tentativo del professionista di modificare lo schedule o creare un'assenza per un Practitioner diverso dal proprio;
- consentire alla gestione centrale autorizzata di usare lo stesso servizio con scope più ampio; il ruolo finale segreteria/admin resta da definire separatamente;
- mantenere `Practitioner Schedule` dedicato uno-per-professionista per evitare che una modifica self-service ad uno schedule condiviso alteri la baseline altrui;
- preservare lo storico `Version` sulle modifiche agli schedule ricorrenti;
- non patchare Frappe o Marley core.

Evidenza principale: testlab `CAP007-INVENTORY-001`, `CAP007-AVAILABILITY-002`, `CAP007-SCHEDULE-004`, `CAP007-OWNER-005`, `CAP007-GUARD-006`.

Nel runtime osservato, `Practitioner Schedule` ha supportato orari distinti per giorno e `Practitioner Availability` `Unavailable` ha bloccato server-side gli appuntamenti nelle eccezioni. La configurazione permission basata solo su `if_owner` non è sufficiente: A ha potuto creare un record di disponibilità con scope sul Practitioner B. Nel probe finale guarded, A ha invece potuto modificare il proprio schedule e creare la propria assenza, mentre i corrispondenti tentativi su B sono stati negati prima di qualsiasi write; Administrator ha gestito correttamente entrambi come identità di controllo per la gestione centrale. Le modifiche agli schedule hanno prodotto `Version` history e rollback/cleanup hanno rimosso tutte le fixture sintetiche preservando le User Permission Practitioner persistenti.

Questa decisione è limitata a **CC-CAP-007**. Non definisce il nome/ruolo definitivo della gestione centrale e non chiude `CC-CAP-008` concurrency/double-booking né le capability di booking pubblico/backend-only.

## TD-017 — CC-CAP-008 No double booking / slot concurrency

**Stato:** CONFERMATA DALL'OWNER — 2026-09-06

Classificazione capability: **EXTENSION**.

Decisione:

- mantenere Marley `Patient Appointment` e la sua validazione overlap come base funzionale per i controlli sequenziali;
- non considerare la sola `validate_overlaps()` un boundary atomico di concorrenza, perché il runtime ha dimostrato che due reschedule concorrenti possono completare entrambi il controllo nativo e poi committare sullo stesso Practitioner/timeslot;
- serializzare in `centrochange_core` i path sensibili di creazione/spostamento appuntamento tramite lock transazionale su una riga stabile `Healthcare Practitioner` prima della re-validazione e della write;
- mantenere il lock fino al commit/rollback della mutazione, così la richiesta concorrente successiva rilegge lo stato aggiornato e viene respinta dal normale `OverlapError` Marley se lo slot è ormai occupato;
- non patchare Frappe o Marley core;
- trattare la vera idempotenza request-id/replay come responsabilità separata: il runtime nativo evita il duplicato su retry sequenziale già committato ma non fornisce una chiave di idempotenza o un contratto di replay del risultato originale;
- mantenere booking pubblico (`CC-CAP-009`) e relative protezioni anti-abuso/idempotenza come capability separate.

Evidenza principale: testlab `CAP008-INVENTORY-001`, `CAP008-CONCURRENCY-003`, `CAP008-RESCHEDULE-004`.

Nel runtime osservato, Marley ha respinto correttamente overlap e move collision nei path sequenziali e un retry dopo commit non ha creato un secondo appuntamento. L'inventario ha però rilevato assenza di `FOR UPDATE`, named lock, vincolo univoco sullo slot o campo idempotency dedicato. Il primo test di race su nuove create è stato correttamente classificato `NON_PROBATIVE` a causa di lock contention precedente al barrier. Il follow-up su due Appointment già committati è stato invece probativo: entrambi i worker hanno completato il controllo overlap nativo e sono riusciti a committare sul medesimo Practitioner/timeslot. Nello stesso probe, il candidato lock `Healthcare Practitioner ... FOR UPDATE` ha serializzato i due reschedule: una sola richiesta ha committato e la seconda è stata respinta con `OverlapError`. Rollback e cleanup hanno rimosso tutte le fixture sintetiche e preservato Appointment/Event A/B.

Questa decisione è limitata a **CC-CAP-008**. Non decide automaticamente booking pubblico/backend-only (`009`/`010`) né la strategia generale di idempotenza per integrazioni future.

## TD-018 — CC-CAP-001 Runtime foundation e isolamento DEV

**Stato:** CONFERMATA DALL'OWNER — 2026-09-06 (standing technical authorization)

Classificazione capability: **CONFIGURATION**.

Decisione:

- riusare il runtime Frappe/ERPNext/Builder ufficiale tramite un Compose project Centro Change dedicato e pin espliciti delle versioni/image;
- mantenere `centrochange-dev` isolato dagli altri stack locali con DB, Redis, sites volume, network e naming dedicati;
- mantenere secret/config runtime fuori da Git e usare nel repository solo template con placeholder;
- conservare bootstrap, migrate, asset build, worker/scheduler, restart e health check come procedura ripetibile e versionata;
- non dipendere da image, mount, dati, app o secret di altri progetti locali;
- non patchare Frappe/ERPNext/Builder core;
- classificare la capability come `CONFIGURATION`, non `PROVEN NATIVE`, perché l'isolamento e il pinning richiedono una configurazione infrastrutturale dedicata; non `CUSTOM`, perché non richiede un runtime framework proprietario né codice prodotto per il foundation layer.

Evidenza principale: `docs/spikes/SPIKE-01-REUSE-ISOLATION.md` e `docs/RUNTIME-BASELINE.md`.

Lo Spike 01 ha censito host/WSL/Docker e versioni, creato `centrochange-dev` con DB/Redis/sites/network dedicati, installato Frappe/ERPNext/Builder/`centrochange_core`, verificato migrate/assets/backend/frontend/websocket/worker/scheduler/Desk/website, eseguito restart con ping positivo, documentato bootstrap ripetibile e osservato che gli altri stack locali sono rimasti `Up` senza restart o comandi rivolti a loro. Le credenziali sono rimaste fuori Git e i dati di test sono sintetici.

Questa decisione è limitata a **CC-CAP-001**. Backup/restore (`035`/`036`), upgrade/migration safety (`037`) e operational deploy reproducibility (`040`) restano capability separate con validation dedicata.

## TD-019 — CC-CAP-002 Identita professionista

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: mantenere `User + Healthcare Practitioner + User Permission` come baseline nativa/app, ma implementare in `centrochange_core` un lifecycle service di offboarding/reassignment che riconcilia atomicamente status, User state e User Permission, revocando il vecchio principal e concedendo il nuovo in modo deterministico. Il flag `Healthcare Practitioner.status` non e un authorization boundary sufficiente.

Evidenza principale: testlab `CAP002-IDENTITY-001`, `CAP002-LIFECYCLE-002`. Mapping e isolamento A/B sono riusabili; disable e reassignment mostrano gap di lifecycle/security; cleanup verificato.

## TD-020 — CC-CAP-003 Anagrafica paziente

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: mantenere Marley `Patient` come master, aggiungendo guard/override/esclusione per gli endpoint non permission-aware, a partire da `get_patient_detail`, e una policy esplicita di retention/disable/delete-unlink. `uid unique` e riusabile ma non costituisce validazione del codice fiscale italiano.

Evidenza principale: `CAP003-PATIENT-IDENTITY-001`, `CAP003-PATIENT-MASTER-002`, con boundary standard riusato da `CAP004-SURFACES-002`. Confermato cross-assignment leakage via `get_patient_detail`; cleanup verificato.

## TD-021 — CC-CAP-009 Primo incontro pubblico

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: non usare Marley `patient_portal.make_appointment` as-is come authorization boundary. Riutilizzare disponibilita/schedule di CC-CAP-007 e serializzazione di CC-CAP-008 dietro un ingress server-side Centro Change che valida Patient identity, practitioner ammessi, appointment type, slot/data e idempotency.

Evidenza principale: `CAP009-BASELINE-002`, `CAP009-PUBLIC-BOUNDARY-003`. Un Website User non correlato ha creato booking caller-controlled, anche su practitioner nascosto, off-schedule e nel passato; cleanup verificato.

## TD-022 — CC-CAP-010 Sedute successive solo backend

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: mantenere `Patient Appointment` e i normali path backend permission-aware, ma centralizzare in `centrochange_core` il guard server-side post-first e proteggere/override/escludere i mutatori Marley non permission-aware. La sola rimozione della UI pubblica non e sufficiente.

Evidenza principale: `CAP010-BACKEND-ONLY-001`. Backend control positivo; REST/direct ordinari negano; portal e generic mutator hanno mostrato bypass; cleanup verificato.

## TD-023 — CC-CAP-011 Catalogo servizi

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: usare ERPNext `Item` come master servizio/economico e `Item Group` come tassonomia, con una sottile estensione Centro Change che collega il servizio al profilo scheduling e applica eligibility/disabled guard server-side. Evitare due master autorevoli indipendenti.

Evidenza principale: `CAP011-CATALOG-PRICE-SNAPSHOT-INVENTORY-001` e Wave 2 runtime evidence.

## TD-024 — CC-CAP-012 Prezzi

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **CONFIGURATION**.

Decisione: usare Price List + `Item Price` effective-dated come fonte autorevole del prezzo corrente. Non introdurre un pricing engine custom nello scope corrente. La data di cattura nello snapshot appuntamento e policy separata gestita insieme a CC-CAP-013.

Evidenza principale: `CAP012-EFFECTIVE-PRICE-002` PASS con cleanup verificato.

## TD-025 — CC-CAP-013 Snapshot storico servizio/durata/prezzo

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: riusare `Patient Appointment.duration` come durata snapshot e aggiungere campi supportati per service identity/label, prezzo, valuta e Price List provenance. Settlement/accounting futuro deve consumare lo snapshot e non ri-risolvere la tariffa corrente.

Evidenza principale: `CAP013-CATALOG-PRICE-SNAPSHOT-001`. Marley ri-risolve il rate corrente e non conserva lo snapshot economico completo; cleanup verificato.

## TD-026 — CC-CAP-014 Pagato Si/No + metodo informativo MVP

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **EXTENSION**.

Decisione: usare `Mode of Payment` soltanto come tassonomia/riferimento e introdurre in Centro Change il settlement operativo minimo (paid flag, metodo, attore/data/correzione/audit), senza generare automaticamente Sales Invoice, Payment Entry, GL Entry o Payment Ledger Entry.

Evidenza principale: `CAP014-SETTLEMENT-002` PASS; zero side effect contabili e cleanup verificato.

## TD-027 — CC-CAP-015 Future accounting pathway

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **DEFERRED / EXCLUDE FROM CURRENT SURFACE**.

Decisione: non attivare accounting nello scope corrente. Conservare il pathway futuro `CC Settlement -> Sales Invoice -> Payment Entry` come design da riaprire con idempotency key deterministica, reversal/correction, snapshot provenance, migrazione e rehearsal di integrita contabile.

Evidenza principale: `CAP015-PATHWAY-001` PARTIAL e inventory Wave 3. Nessuna mutation contabile eseguita; il risultato partial della source assertion non modifica la decisione di deferire.

## TD-028 — CC-CAP-016 Pacchetti

**Stato:** CONFERMATA DALL'OWNER — 2026-09-08 (standing technical authorization)

Classificazione capability: **CUSTOM**.

Decisione: implementare un modello append-oriented dedicato `CC Package Template`, `CC Patient Package`, `CC Package Ledger`, con grant/reserve/release/consume/adjust, concurrency, idempotenza e correction audit. Non forzare Product Bundle o Subscription come saldo consumabile per paziente.

Evidenza principale: `CAP016-PACKAGE-002` PASS. Il surrogate ToDo ha validato il pattern transazionale/`FOR UPDATE`/event-key ma non rappresenta lo schema prodotto; cleanup verificato.

## TD-029 — CC-CAP-017..040 final technical dispositions

**Stato:** CONFERMATA DALL'OWNER — 2026-09-09 (standing technical authorization; CC-CAP-037 explicitly confirmed)

Il programma di capability evaluation ha raggiunto **40/40 technical dispositions**. Le classificazioni canoniche per l'ultima ondata sono:

| Capability | Classificazione |
|---|---|
| CC-CAP-017 | CONFIGURATION |
| CC-CAP-018 | CUSTOM |
| CC-CAP-019 | EXTENSION |
| CC-CAP-022 | EXTENSION |
| CC-CAP-023 | EXTENSION |
| CC-CAP-024 | EXTENSION |
| CC-CAP-025 | EXTENSION |
| CC-CAP-026 | EXTENSION |
| CC-CAP-027 | EXTENSION |
| CC-CAP-028 | CUSTOM |
| CC-CAP-029 | CONFIGURATION |
| CC-CAP-030 | CUSTOM |
| CC-CAP-031 | DEFERRED / EXCLUDE FROM CURRENT SURFACE |
| CC-CAP-032 | DEFERRED / EXCLUDE FROM CURRENT SURFACE |
| CC-CAP-033 | CUSTOM |
| CC-CAP-034 | CUSTOM |
| CC-CAP-035 | CONFIGURATION |
| CC-CAP-036 | DEFERRED / EXCLUDE FROM CURRENT SURFACE |
| CC-CAP-037 | DEFERRED / EXCLUDE FROM CURRENT SURFACE |
| CC-CAP-038 | CUSTOM |
| CC-CAP-039 | CUSTOM |
| CC-CAP-040 | CUSTOM |

Decisione e conseguenze principali:

- `CC-CAP-017`: usare le primitive Communication/comment compatibili con la nota organizzativa tramite configurazione; la nota professionale riservata resta separata.
- `CC-CAP-018`: usare un record Centro Change dedicato per la nota professionale riservata, con boundary server-side e anti-leakage.
- `CC-CAP-019`: comporre la scheda paziente unificata come estensione dei record/view esistenti, preservando i permission boundary delle sezioni.
- `CC-CAP-022`–`026`: implementare lifecycle giornaliero, reminder, auto-lock, regola di cancellazione tardiva e correzioni come estensioni server-side/scheduler idempotenti e auditabili. Per `CC-CAP-025`, il comportamento `<48h` e la waiver autorizzata sono determinati; l'esatta uguaglianza a `48:00:00` resta una policy business esplicitamente non inventata.
- `CC-CAP-027`: riusare Communication/Notification/Email Queue con estensioni per retry, deduplica, failure semantics e boundary di accesso.
- `CC-CAP-028`: reporting operativo custom dove servono aggregazioni e isolamento assegnato non garantiti dal solo report nativo.
- `CC-CAP-029`: riusare e configurare le superfici native export/print/email quando mantengono lo stesso boundary permission-aware.
- `CC-CAP-030`: dashboard direzionale custom per controllare aggregazioni, privacy e bypass via heatmap/raw/query.
- `CC-CAP-031`, `032`: escludere dalla superficie corrente finché sito Builder e asset non sono riproducibili da una clean deploy recipe versionata.
- `CC-CAP-033`: permission model generale custom/centralizzato in `centrochange_core`, mantenendo i primitivi Frappe come base ma proteggendo endpoint/get_all/raw SQL e mutatori non permission-aware.
- `CC-CAP-034`: audit business custom/immutabile per actor/time/before-after/correction trail dove `Version` da sola non soddisfa il contratto.
- `CC-CAP-035`: usare le primitive supportate `bench backup --with-files` tramite configurazione/runbook; backup raw resta fuori Git.
- `CC-CAP-036`: mantenere deferred finché un restore/DR completo e misurato è riproducibile dal deploy path versionato corrente.
- `CC-CAP-037`: **TEST OUTCOME PARTIAL** sul rehearsal isolato `centrochange-cap037-20260909r2`. Sono provati CURRENT → checkpoint DB/public/private/site-config hashato → TARGET migrate con exit `0` → target health/hooks/services → restore CURRENT con successo nel log e pin/health ripristinati → `cleanup.verified=true`, senza manual SQL/source/upstream patch e senza toccare `centrochange-dev`. Restano mancanti gli inventari normalizzati pre/post di schema, Custom Field e Custom DocPerm e un exit code restore indipendentemente preservato. Questi gap impediscono di promuovere la capability a `CONFIGURATION`; la capability viene quindi esclusa dalla superficie operativa di upgrade corrente e può essere riaperta con un nuovo ciclo discriminante completo.
- `CC-CAP-038`, `039`: endpoint authorization e leakage regression richiedono guard/test layer custom sui caller-controlled IDs e sui path REST/direct/list/report/export/query/app endpoint.
- `CC-CAP-040`: `CUSTOM`; il FAIL di clean deploy è discriminante perché la recipe prodotto versionata non dichiara completamente il bootstrap Healthcare/Marley. Il testlab provisioner CAP037 non va reinterpretato come prova di deploy riproducibile del prodotto.

Evidenza autorevole: `centrochange-testlab` coordinator #56 e issue/probe capability-specific; per `CC-CAP-037`, issue #65 e run finale `centrochange-cap037-20260909r2`. Product implementation resta separata da queste classificazioni.

## Regola di aggiornamento

Quando uno spike produce evidenza sufficiente:

1. riportare evidenza nella issue/PR;
2. aggiornare la decisione da `RUNTIME VALIDATION REQUIRED` a stato confermato o sostituito;
3. documentare conseguenze e migrazioni;
4. non usare la parola `APPROVATO` come sostituto della decisione dell'utente/owner.