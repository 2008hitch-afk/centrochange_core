# #148 — proposte API per editor ordinari mancanti

**PROPOSTA, nessun endpoint implementato o autorizzato.** DECISION-062 richiede catalogo, tariffe, anagrafiche e pagamenti ordinari in React. Le API correnti espongono snapshot di servizi/practitioner/pazienti e workflow finanza, ma non una scrittura di dominio per questi master. Non usare `/api/resource`, `frappe.client.insert/set_value` o permessi elevati nel browser come scorciatoia. Il backend resta la fonte autorevole.

## Confini di dominio

| Compito React | Autorità canonica | Contratto proposto (POST, sessione + CSRF) | Gate |
|---|---|---|---|
| Catalogo servizi del centro | CC Center Service, Marley Appointment Type, ERPNext Item | `centrochange_core.catalog.service_upsert(center, appointment_type, item, label, duration, enabled, expected_version, reason, request_key)`; risposta solo proiezione autorizzata | Nuova write API + eventuali permessi master |
| Tariffa | ERPNext Item Price e snapshot booking | `centrochange_core.catalog.price_set(center, item, currency, price_list, valid_from, rate, expected_version, reason, request_key)`; mai riscrivere prezzi di appuntamenti già prenotati | Nuova write API e policy di listino/valuta |
| Modello pacchetto | CC Package Template e child rows centri/servizi | `centrochange_core.catalog.package_template_upsert(...)` con unità, eleggibilità, stato, versione, motivo, idempotenza; preservare pacchetti emessi | Nuova write API/business rule da approvare |
| Anagrafica paziente | Marley Patient, Customer solo tramite link fiscalmente governato | `centrochange_core.operations.patient_profile_save(patient, center, allowed_fields, expected_version, reason, request_key)`; creare profilo e cambiare legame Customer in operazioni **distinte** e autorizzate | Dati personali, mascheramento, permessi, deduplica, link fiscale |
| Anagrafica professionista | Marley Healthcare Practitioner + CC Center Membership/assignment | `centrochange_core.operations.practitioner_profile_save(practitioner, center, allowed_fields, expected_version, reason, request_key)`; stato/membership continuano nel servizio `security.lifecycle.*` esistente | Nuova write API e separazione ruoli |
| Payment Entry consultazione | ERPNext Payment Entry attraverso transazioni finance esistenti | `centrochange_core.finance.payments.position(center, name)` e `list(center, start, end, cursor)` read-only, con link alle fatture e saldo canonico; nuovi POST solo se flusso ordinario non coperto dagli attuali `finance.receivables`, `incoming`, `banking` | Nuove read projection; POST eventuale dopo gap live |

I nomi/argomenti sono una **bozza di contratto**, non codice disponibile. Prima dell'implementazione occorre confrontare campi realmente supportati nel pin Frappe 16.50/ERPNext 16.50/Healthcare 16.6.1 e nelle DocType `centrochange_core` effettive. Le scelte `label`, prezzo/listino, unità e link Customer possono avere implicazioni contabili e di sicurezza: **NOT_VERIFIED** finché business owner e backend review le approvano. Nessun generic CRUD write è già stato aggiunto alla PR.

## Permessi e minacce da chiudere nel gate API

- **Scope server-side:** `require_center(center)` e permesso DocType nativo, verifica di CC Center Membership attiva; per Patient, contesto assegnazione/practitioner e protezione delle note private. Mai fidarsi di `center`/ID/ruolo presentati da React. `CC Manager` potrebbe amministrare il catalogo; Finance potrebbe gestire Item Price solo se Owner conferma il perimetro. Secretariat/Professional devono poter consultare solo i dati loro assegnati. Matrice esatta per tutte le 7 identità UAT + Guest: **NOT_VERIFIED**, da fissare prima del codice.
- **Mass assignment / IDOR:** whitelist esplicita di campi; vietare in ogni payload ruoli, user permissions, `docstatus`, GL Entry, stato contabile, Customer arbitrario, note cliniche/private e metadati di audit. Rileggere record/centro dal DB sotto lock; rifiutare UUID o link di altro centro anche se l'utente vede la UI.
- **Concorrenza e retry:** `expected_version`/`modified` e `request_key` server-side; rifiutare versioni obsolete, replay diversi con stessa chiave, duplicati di tariffa e intervalli ambigui. Audit con actor, centro, motivo, before/after sanitizzati. Una tariffa nuova non muta snapshot di sedute passate.
- **Validazioni native:** usare le API documentate `Document.insert/save/submit` e validazioni ERPNext/Marley pinned; niente SQL diretto, patch core, eccezioni per Administrator o `ignore_permissions` fuori da un servizio con controllo equivalente e testato. Policy fiscale multi valuta, prezzo zero, durata e disponibilità devono essere esplicitate prima della write API.
- **CSRF e metodo:** solo POST autenticato, session cookie same-origin, token, rate limit per operazioni master; `GET` bounded, filtrato server-side, senza PII eccedente. Guest e ruolo non autorizzato = 401/403; nessuna distinzione informativa su record cross-center.

## Test negativi obbligatori prima di attivare editor

Per ogni endpoint: Guest, ruolo senza facoltà, membership revocata, centro B da utente A, Patient/Practitioner di altro contesto, link a Item/Customer fuori scope, payload con campi vietati, prezzo negativo/valuta non ammessa, duplicato periodo/listino, `expected_version` stantia, retry con stessa chiave e payload differente, POST senza CSRF, accesso diretto `/api/method`, export/list/get nativi e assenza di write dopo rifiuto. Provare con database e ruoli **sintetici** sul pin effettivo, confrontando audit/DB/permessi prima e dopo. Poi Playwright desktop/mobile e 11 liste + 11 form del perimetro UAT.

**Decisione separata richiesta prima del codice API:** approvare campi/ruoli/business rules e i sei contratti oppure restringere esplicitamente il MVP. Fino a quel gate, i master editor React restano `UI_MISSING`; non classificare il frontend completo né `READY_FOR_OWNER_VISUAL_UAT`.
