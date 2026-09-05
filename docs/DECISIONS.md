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

## Regola di aggiornamento

Quando uno spike produce evidenza sufficiente:

1. riportare evidenza nella issue/PR;
2. aggiornare la decisione da `RUNTIME VALIDATION REQUIRED` a stato confermato o sostituito;
3. documentare conseguenze e migrazioni;
4. non usare la parola `APPROVATO` come sostituto della decisione dell'utente/owner.