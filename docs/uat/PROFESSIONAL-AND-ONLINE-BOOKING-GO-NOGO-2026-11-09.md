# Centro Change — Verifiche obbligatorie prima della presentazione (09/11/2026)

## Esito operativo 09/11/2026

**A — ACCOUNT PROFESSIONISTA: PASS** (clone isolato; 4/4 sia desktop sia mobile). Giulia Moretti, Andrea Ricci, Elena Bianchi e Marco Ferri: login/logout, Agenda, pazienti assegnati, disponibilità, note e report PASS; letture di pazienti altrui e report economico Manager NEGATE. Credenziali create soltanto nel clone.

**B — PRENOTAZIONE ONLINE: NO-GO**. Le due modalità pubbliche 20 minuti/€0 e la UI desktop/mobile esistono, ma in STAGING **non esiste alcuna `CC Public Booking Route` attiva per Marco o Francesca**, quindi 0/4 combinazioni disponibili. Codex non ha eseguito prenotazioni POST nel clone perché inventare le rotte avrebbe invalidato il test di configurazione effettiva. Nessun record dello STAGING mutato; SHA e conteggi invariati.

**Decisione Owner bloccante:** quale *esatto Healthcare Practitioner* deve ricevere la route `Marco` e quale la route `Francesca`? I quattro account dimostrativi non includono `Francesca`; `Marco Ferri` non è automaticamente il direttore pubblico. Non associare, creare, rinominare né aggiungere un quinto account senza la decisione.

**Prossimo gate:** dopo identificazione e autorizzazione dei due target, Codex configura le due `CC Public Booking Route` sullo STAGING con backup e account manager, senza nuovo seed; poi testa GET slot delle 4 combinazioni e POST guest soltanto su clone isolato con le stesse rotte e regole. Solo dopo 4/4 PASS e senza effetti esterni si può dare GO alla presentazione.

---

**Ordine vincolante:** 1. account professionista; 2. prenotazione online; 3. presentazione cliente.

**STAGING attuale:** https://centro-uat.empv.it/premium, SHA installata 6e982a2715dc3aec89b3f7c65e52c3aa995d45a8, database già popolato (4 professionisti, 18 pazienti, 17 Customer, 35 appuntamenti, 10 ricevute per €392, 35 fonti economiche). Non effettuare nuovo seed, migrazione o cambio SHA solo per test.

## A — Account professionista

**A1, lettura STAGING:** eseguire il file standalone infra/qa_professional_public_readonly.py, copiato dalla PR #205 in /tmp, nel bench console del vero site Frappe. Lo script rifiuta siti diversi dallo STAGING esplicitamente configurato, e scrive solo JSON di controllo in output. Controllare 4 User Frappe distinti, abilitati, System User, ruolo CC Professional senza manager/finance/system manager; collegamento a Healthcare Practitioner attivo, CC Center Membership, Supplier, 18 CC Patient Assignment coerenti; proprio calendario e pazienti visibili, pazienti dei colleghi e Customer fiscali inaccessibili.

**A2, login reale:** la sola esistenza degli account non prova username/password e navigazione. Gli indirizzi dei quattro professionisti sono @presentation.example.invalid, quindi non spedire inviti o reset via email. Se mancano credenziali di prova già autorizzate, usare un clone isolato ripristinato dal backup, creare SOLO nel clone credenziali sintetiche, quindi verificare login/logout, Premium, Agenda, scheda dei soli pazienti assegnati, disponibilità, note, report professionale e diniego degli accessi al collega, per quattro utenti, desktop e mobile. Non creare sessioni o ruotare credenziali nel database STAGING.

**A3, scrittura SOLO clone:** riutilizzare i test reali frontend/premium/tests/professionals.live.spec.ts, compresi chiusura sedute pagata/non pagata, disponibilità, note, notifiche, tentativi cross-center/IDOR e ruoli negati. Richiedere tutti PASS, con screenshot privi di dati reali.

**Gate A:** quattro login autentici e UX/permessi verificati. Se manca anche un account o login, è NO-GO.

## B — Prenotazione online

**B1, sola lettura STAGING:** controllare il percorso guest /primo_incontro, da desktop e mobile, e la disponibilità futura senza effettuare POST. UI: due modalità In sede/Online, due direttori Marco/Francesca. Server: CC Public Booking Route deve avere entrambe le route attive, legate alla sede operativa e a un Healthcare Practitioner attivo; account di servizio cc-public-booking-service@example.invalid abilitato; due Appointment Type distinti su cc_public_first_meeting_types, 20 min, €0, EUR, con Item Price e CC Center Service attivi; orari reali per ciascuno dei direttori. Verificare tutte le 4 combinazioni modalità × direttore. Non indovinare i legami con i quattro professionisti presenti: la ricetta del dataset non garantisce automaticamente l'esistenza delle due route.

**B2, prenotazione effettiva SOLO clone:** per ciascuna modalità e direttore, effettuare un Guest booking con email @example.invalid. Verificare una sola creazione Patient + assignment + Patient Appointment 20min/€0, senza prenotare automaticamente la Seduta €44; comparsa nell'Agenda professionista, conferma simulata non spedita; zero email reali, fatture, Payment Entry, GL, SMS, TS e SdI. Eseguire replay della chiave, collisione slot e rifiuto payload diverso, modalità/route arbitrarie, date passate e oltre 120 giorni, lettura REST Guest negata. Verificare Europe/Rome, responsività e conferma leggibile su desktop e mobile.

**Gate B:** tutte le quattro combinazioni disponibili e correttamente prenotabili su clone, idempotenza/sicurezza PASS. In caso di servizio o direttore mancante, NO-GO. Non creare/rinominare automaticamente professionisti o direttori per aggirare il problema.

## C — Go/No-Go finale per il cliente

Verifica visiva delle due interfacce, testi italiani e privi di etichette tecniche, sede/indirizzo, Agenda e prezzo. Il frontend pubblico contiene un riferimento letterale a Bergamo: confrontarlo con la sede effettiva prima della presentazione. Non utilizzare dati personali reali.

**Rapporto richiesto a Codex:** esito per 4 account, per 4 combinazioni di booking, screenshot desktop/mobile, verifica stato e sessioni autentiche, elenco dei blocker con motivazione, contatori STAGING prima/dopo identici (4/18/17/35/10/35), stessa SHA installata, invii disabilitati, produzione invariata. Eseguire una seconda serie di test di scrittura solo su clone; nessun POST di prenotazione sul database STAGING.

**Nessun claim "pronto per il cliente" prima di entrambi i gate A e B PASS.**

## Esecuzione script lettura

Copiare solo infra/qa_professional_public_readonly.py nella cartella /tmp del contesto bench, senza cambiare checkout Git o eseguire migrazioni. Dal bench console del sito STAGING, eseguire una sola riga Python:

    exec(compile(open('/tmp/cc-professional-public-readonly.py', encoding='utf-8').read(), '/tmp/cc-professional-public-readonly.py', 'exec'), {'__name__': '__main__'})

Lo script NON dimostra il login password né effettua prenotazioni: richiede una seconda fase HTTP/browser sul clone.
