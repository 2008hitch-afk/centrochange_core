# Centro Change — flussi per ruolo (audit UX, 19/10/2026)

Baseline: single-stack DEV, immagine `sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834`. Questa è analisi; nessun flusso è stato modificato. **Agenda invariata e fuori dagli interventi UX per decisione Owner 20/10/2026**, compreso il ruolo Professionista. I percorsi indicano attività approvate, non nuove autorizzazioni.

| Ruolo | Compito principale | Ingresso e dati necessari | Azione / esito comprensibile | Evidenza e limite UX |
|---|---|---|---|---|
| Direzione | Coordinare attività e consultare indicatori | Agenda, pazienti, professionisti, finanza e report autorizzati | Individuare seduta/documento, agire secondo stato, tornare al contesto | Sweep live: 23 rotte desktop e mobile; la fattura apre correttamente ma mescola riepilogo e campi ERPNext tecnici. |
| Segreteria | Prenotazioni, ricerca, notifiche e funzioni amministrative autorizzate | Agenda e informazioni pertinenti | Flussi attuali approvati | Sweep live: 14 rotte mobile. L'Agenda non è nel piano di modifica. |
| Professionista A/B | Vedere sedute assegnate e compilare esito/note consentiti | Agenda e dati già autorizzati | Flussi attuali approvati | Sweep live: 4 rotte. Nessun cambiamento a griglia, filtri, navigazione o azioni Agenda. Il Report professionisti della Direzione è altra funzione. |
| Professionista C | Consultare le funzioni già autorizzate | Stato attuale delle assegnazioni | Flussi attuali approvati | Sweep live: 4 rotte; nessuna proposta di modifica dell'Agenda. |
| Finance | Documenti, pagamenti, banca e simulazioni fiscali | Soggetto, importo, stato, residuo, documento collegato | Azione consentita per stato; conferma e saldo leggibili | Sweep live: 10 rotte desktop. Servono descrizioni operative per documento e stati, senza cambiare menu né contabilità. |
| Commercialista | Consultare documenti e report in sola lettura | Documento, periodo, importi, stato e audit | Consultazione/export autorizzato, nessun comando mutativo | Sweep live: 5 rotte desktop. La distinzione tra riepilogo e dettagli contabili deve restare chiara. |
| Administrator tecnico | Amministrare Frappe/ERPNext | Desk e strumenti tecnici | Funzioni native complete | Fuori dalla superficie cliente; non applicare semplificazioni che nascondano strumenti tecnici. |

## Percorsi di compilazione da validare con persone

1. **Anagrafica Paziente:** l'operatore identifica la persona da nome e stato, trova campi obbligatori, contatti e dati fiscali pertinenti, salva e verifica la persistenza. Le informazioni cliniche seguono i permessi esistenti.
2. **Anagrafica Professionista:** Direzione trova nome, stato, collegamento utente/struttura e campi richiesti; salva e verifica la persistenza senza confondere questa pagina con il Report professionisti.
3. **Fattura paziente:** il ruolo autorizzato distingue soggetto, stato, importo, residuo e azioni consentite; Finance e Commercialista mantengono dettagli contabili e cronologia.
4. **Altre native:** test di campo, validazione, salvataggio e accessi diretti prima di nascondere o ridurre elementi. Nessun PASS d'usabilità deriva dalla sola apertura.

Evidenze live: probe read-only e screenshot sintetici del 19/10/2026 in `screenshots/`. Le suite #137/#139 dimostrano routing/rendering, non che un operatore completi il compito senza guida. Nessun percorso proposto modifica l'Agenda.
