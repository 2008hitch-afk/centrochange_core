# #148 — copertura UI React sintetica, PR #150

Stato: **UI di sviluppo**, fixture sintetiche. La vista `Archivi` è abilitata solo con `import.meta.env.DEV && VITE_CC_SYNTHETIC_UI=1`. La build per Frappe non espone i suoi editor finché API di dominio e ruoli non sono approvati. Ogni conferma modifica esclusivamente lo stato React della pagina: niente POST, `/api/resource`, database, localStorage o scrittura Frappe. Il messaggio in UI lo dice prima del form e dopo la conferma. Le altre funzioni operative/finanziarie React usano gli endpoint Frappe già presenti; Playwright li intercetta con fixture di prova. Un PASS sintetico non prova i permessi del server.

## 11 liste e 11 schede/form dell'UAT #136

Ogni riga ha elenco, ricerca, scheda, nuovo/modifica di prova, campi obbligatori, conferma, successo/errore, stato vuoto e screenshot lista+form a 1440×900 e 390×844. Il test parametrico `archivio …` esegue il flusso su entrambe le viewport e asserisce **zero POST**. Gli ID `*-DEMO-*`, importi e nominativi sono inventati e non provengono dal Site.

| Superficie UAT | Area React | Azione UI sintetica | Backend canonico / contratto futuro | Ruolo UI in preview | Prova |
|---|---|---|---|---|---|
| Sales Invoice | Archivi → Fatture pazienti; Finanza reale separata | lista/scheda/form di prova | ERPNext Sales Invoice; `finance.receivables.*` per flussi approvati | Manager/finance writer | `archivio Fatture pazienti` |
| Purchase Invoice | Archivi → Fatture professionisti; Finanza separata | lista/scheda/form di prova | ERPNext Purchase Invoice; `finance.incoming.*` | Manager/finance writer | `archivio Fatture professionisti` |
| Payment Entry | Archivi → Pagamenti | lista/scheda/form di prova | ERPNext Payment Entry; `finance.payments.list/position` proposta | Manager/finance writer | `archivio Pagamenti` |
| Bank Transaction | Archivi → Movimenti bancari; Finanza separata | lista/scheda/form di prova | ERPNext Bank Transaction; `finance.banking.*` per flussi approvati | Manager/finance writer | `archivio Movimenti bancari` |
| Patient | Archivi → Pazienti; percorso Pazienti separato | lista/scheda/form di prova | Marley Patient; `patient_profile_save` proposta | Manager/finance writer in preview; matrice reale da approvare | `archivio Pazienti` |
| Healthcare Practitioner | Archivi → Professionisti | lista/scheda/form di prova | Marley Healthcare Practitioner; `practitioner_profile_save` proposta | Manager/finance writer in preview; matrice reale da approvare | `archivio Professionisti` |
| Item | Archivi → Articoli | lista/scheda/form di prova | ERPNext Item; `service_upsert`/catalogo proposta | Manager/finance writer | `archivio Articoli` |
| Item Price | Archivi → Tariffe | lista/scheda/form di prova | ERPNext Item Price; `price_set` proposta | Manager/finance writer | `archivio Tariffe` |
| Appointment Type | Archivi → Tipi seduta | lista/scheda/form di prova | Marley Appointment Type; `service_upsert` proposta | Manager/finance writer | `archivio Tipi seduta` |
| CC Center Service | Archivi → Servizi del centro | lista/scheda/form di prova | centrochange_core CC Center Service; `service_upsert` proposta | Manager/finance writer | `archivio Servizi del centro` |
| CC Package Template | Archivi → Modelli pacchetto | lista/scheda/form di prova | centrochange_core CC Package Template; `package_template_upsert` proposta | Manager/finance writer | `archivio Modelli pacchetto` |

**Ruoli:** la shell offre `Archivi` in preview solo a `CC Manager` o a una sessione con `finance.reporting.bootstrap.can_write`; senza facoltà, anche `#Archivi` ricade su Agenda. Il test negativo è `archivio nascosto a ruolo senza facoltà amministrativa`. È una protezione della preview, non una decisione sui ruoli finali e non sostituisce 401/403 server. Permessi live per 7 ruoli+Guest, membership A/B, note private, URL Desk e export: **NOT_VERIFIED**.

**API:** la proposta tecnica, whitelist campi, CSRF, idempotenza, scope centro, conflitti e test negativi è in `SCOPED-MASTER-API-PROPOSAL.md`. Nessun endpoint proposto è stato aggiunto. I form di prova esercitano interazione/validazione UX, non replicano tutte le regole cliniche, fiscali o contabili del backend pinned. La scelta dei campi e dei ruoli resta Owner/backend gate.

## Altre aree principali

`premium.spec.ts` esercita Agenda/prenotazioni, pazienti/storico/note/pacchetti/assegnazioni, catalogo servizi consultivo, disponibilità, report, Finanza (fatture, pagamenti, banca, XML, compensi, report), accessi, notifiche (loading, errore, riprova e vuoto), audit e primo incontro pubblico con fixture API sintetiche. Gli screenshot `docs/evidence/issue-148/area-*-{desktop,mobile}.png` e `archive-*-{desktop,mobile}.png` / `archive-form-*-{desktop,mobile}.png` documentano la build di sviluppo; `first-meeting-*.png` era già presente. Gli screenshot sono prove di rendering, non di autorizzazione server. Browser plugin non disponibile nella sessione; eseguito Playwright Chromium locale.

## Evidenza e limiti

- Eseguire `npm run typecheck`, `npm run build`, `npm run test:e2e` da `frontend/premium`; Playwright avvia solo Vite su `127.0.0.1:5182` con `VITE_CC_SYNTHETIC_UI=1`.
- La prova di una modifica sintetica include zero POST; gli endpoint già approvati sono testati separatamente per payload/CSRF con mock API.
- Screenshot ispezionati: Archivi/Tariffe desktop+mobile, Professionisti mobile, Finanza desktop; difetti corretti: input ricerca troncato, ambiguità selettore nomi, doppio bootstrap centro, date archivio uniformate a `GG/MM/AAAA`, focus ciclico nei dialoghi. Valutazione grafica Owner: **NOT_VERIFIED**.
- Le viste dell'archivio non sono ancora integrate al Site e non condividono lo stato con le proiezioni finanziarie reali. Stampa documenti, Payment Entry reale, editor master reali, test live multi ruolo, budget p95 e sicurezza server: **NOT_VERIFIED**.
