# AUDIT-05 — Professionisti e accessi

Issue [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171). Baseline `main` `61324c8f462a07aa1b893c69a52e825e4342f9db`. Questo documento è l'oracle del candidato; i risultati Frappe/DEV e la decisione Owner sono registrati nella PR e nella Issue, senza attribuire PASS live ai mock.

I due addendum Owner del 24/10/2026 nella #171 integrano l'oracle dell'**account Professionista**: non basta la directory. Le prove mutative e temporali usano solo il Site/DB isolato `cc171-prof-restore-*`; nessuna di esse si applica al DEV condiviso.

| Requisito | UI Premium | API / dato canonico | Positivo | Negativo / limite | Stato al commit |
|---|---|---|---|---|---|
| CC-CAP-002 e CC-EXT-004: identità, stato, lista, ricerca, scheda | `#Professionisti`, `Professionals` | `profiles.practitioners`, `profiles.practitioner_detail`; Healthcare Practitioner, User, CC Center Membership | Nome/cognome, stato, pagina successiva e dettaglio nel centro operativo | Centro diverso/inattivo, record altrui, 403, lista vuota, ricerca oltre bootstrap e risposta tardiva | Clone API PASS; browser SHA finale/DEV da verificare |
| CC-EXT-009: modifica autorizzata | `#Archivi` → Professionisti, `ScopedArchive` | `profiles.practitioner_save`; first_name/last_name; Version e CC Audit Event | Manager: motivo, nuova versione, persistenza e replay stessa chiave | Segreteria/professionista/Guest, stale, chiave diversa, campo extra, CSRF, IDOR | Clone browser/API PASS; SHA finale/DEV da verificare |
| CC-CAP-005/033/038/039 e CC-EXT-020/026/027 nel perimetro | Menu, URL, scheda, ricerca, Agenda/selettore/Report | DocType permission hooks, membership attiva, Branch operativo, practitioner_for | Professionista proprio; Manager nel centro autorizzato; Segreteria directory limitata | Revoca e centro inattivo negano DocType/query/API; centro B isolato; nessun dato contabile | Clone API PASS; browser SHA finale/DEV da verificare |
| Regressioni mirate CC-CAP-004/007 | Pazienti assegnati, Agenda, Disponibilità | Assegnazioni/Marley esistenti | ID canonici coerenti tra sezioni | Nessun edit esteso o permesso aggiuntivo | Clone backend PASS; browser SHA finale da verificare |

## Oracle account Professionista, addendum Owner #171

| Scenario approvato | Percorso UI e backend canonico | Prova richiesta nel clone | Stato prima del gate DEV |
|---|---|---|---|
| Identità unica e sedi (CC-CAP-002/005, DECISION-007) | Login Frappe → Premium; User ↔ Healthcare Practitioner ↔ CC Center Membership | Browser proprio A/B/C; query e ID diretto; revoca e centro inattivo | Clone API/ruoli PASS sul candidato precedente; SHA finale e DEV da verificare |
| Agenda propria (CC-CAP-005/006) | `#Agenda`; `workspace.agenda`, Patient Appointment | A vede solo sedute assegnate; B/C negati, centro B isolato | Clone browser/API PASS; SHA finale da verificare |
| Chiusura quotidiana pagata/non pagata (CC-CAP-014/022) | Drawer «Chiudi seduta» → `lifecycle.close` → CC Settlement | Due sedute sintetiche concluse, persistenza, metodo, replay, futura/altrui negata | Clone browser/API PASS; SHA finale da verificare |
| Reminder 21:00 e blocco 07:00 (CC-CAP-023/024/027) | `automation.catch_up` → CC Notification → Notification Log proprio; blocco server `require_mutable` | Orologio Europe/Rome controllato, retry/lock, destinatario A non B; Premium «Notifiche» | Backend clone PASS con rollback; UI personale in candidato da verificare |
| Riapertura/correzione limitata (CC-CAP-026, DECISION-059) | `lifecycle.reopen` / `record_settlement`, audit | P negato dopo lock/chiusura; Segreteria autorizzata con motivo; nessuna correzione retroattiva dell'orario | Backend clone PASS con rollback; DEV non mutativo |
| Pazienti e note private (CC-CAP-004/018) | `#Pazienti` → `notes.add_note`; CC Private Note append-only | Crea/rettifica, revoca, Manager/Segreteria/B negati anche via API diretta | Backend clone PASS con rollback; browser finale da verificare |
| Disponibilità self-service (CC-CAP-007, issue #9) | `#Disponibilità` → `availability.set_schedule/create_absence/cancel_absence`; Marley | Orario proprio, assenza/annullo, B negato, stale/overlap e audit | Clone browser/API PASS; SHA finale da verificare |
| Report personali ed export (CC-CAP-028) | `#Report` → `workspace.agenda`, `reporting.summary/export_csv` | Conteggi propri e non altrui; dati economici limitati dal ruolo | Clone browser/API PASS; export diretto finale da verificare |
| Robustezza Premium (CC-EXT-020/026/027) | Hash diretto, desktop/mobile, messaggi italiani, date Roma | Desktop 1440×900, mobile 390×844, refresh, focus/overflow | Offline PASS; clone finale da verificare |

La fixture dell'account crea prenotazioni tramite `booking.book` sul clone e riposiziona **solo i due record test-owned** nel giorno corrente per poter provare la chiusura browser senza cambiare l'orologio del server. I controlli 21:00/07:00 usano `frappe.flags.cc_test_clock` e transazione con rollback, non l'orologio host. Il reminder usa il `Notification Log` nativo, già isolato da Frappe per `for_user`; la UI Professionista lo legge senza una nuova API o permessi. Non è stata autorizzata una nuova consegna esterna/email.

Le catture in `docs/evidence/issue-171/` usano **API sintetiche mock** e dimostrano solo resa desktop/mobile. Il gate DEV richiede CI sullo SHA esatto, revisione indipendente senza Critical/Important, immagine/manifest coerenti, nuovo checkpoint cifrato, restore isolato PASS, test Frappe/MariaDB sul clone, fingerprint e rollback. `cc_premium_primary=1` resta invariato. Nessuna migration, modifica di ruoli/schema o scrittura UAT sul DEV.

## Difetti confermati e correzioni nel candidato

- La ricerca iniziale filtrava solo lo snapshot `bootstrap`: ora interroga la lista Frappe paginata con ricerca server-side, loading, errore, stato e pagina vuota. Le risposte tardive di una pagina precedente non contaminano la ricerca corrente.
- Il permesso diretto del professionista restava valido con membership revocata o centro non operativo: query e controllo record ora richiedono identità attiva e almeno un'appartenenza a sede operativa. Le API scoped richiedono inoltre il centro operativo specifico.
- La scheda e l'Archivio mostravano il nome tecnico di una fixture HTTP, e il selettore Report usava una proiezione diversa: la lettura usa la stessa identità sintetica leggibile, mentre form e API mantengono i valori canonici. L'Archivio non ripete il titolo nel drawer.
- Nessun editor duplicato in `#Professionisti`: la modifica resta in `#Archivi → Professionisti`, con i soli campi già approvati `first_name` e `last_name`.
