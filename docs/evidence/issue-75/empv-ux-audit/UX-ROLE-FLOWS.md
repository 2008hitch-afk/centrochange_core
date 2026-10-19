# Centro Change — flussi per ruolo (audit UX, 19/10/2026)

Baseline: single-stack DEV, immagine `sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834`. Questa è analisi; nessun flusso è stato modificato. I percorsi indicano attività approvate, non nuove autorizzazioni.

| Ruolo | Compito principale | Ingresso e dati necessari | Azione / esito comprensibile | Evidenza e limite UX |
|---|---|---|---|---|
| Direzione | Coordinare attività e consultare indicatori | Agenda, pazienti, professionisti, finanza e report autorizzati | Individuare seduta/documento, agire secondo stato, tornare al contesto | Sweep live: 23 rotte desktop e mobile; la fattura apre correttamente ma mescola riepilogo e campi ERPNext tecnici. |
| Segreteria | Prenotazioni, ricerca, notifiche e funzioni amministrative autorizzate | Agenda, paziente, disponibilità, stato della seduta | Prenotare/gestire solo le azioni autorizzate, conferma esplicita | Sweep live: 14 rotte mobile. Verificare con compito assistito la comprensione delle azioni di cancellazione. |
| Professionista A/B | Vedere sedute assegnate, aprirle, compilare esito/note consentiti | Oggi/prossima seduta, paziente assegnato, stato, campi esito obbligatori | Apri seduta → compila → salva → conferma e lista aggiornata | Sweep live: 4 rotte; l'Agenda apre su griglia settimanale anche se vuota nella settimana corrente. «+ Prenota» è visibile per A/B: verificare significato e permesso prima di rimuoverlo; non aggiungere capacità di prenotazione. Il Report professionisti della Direzione è altra funzione. |
| Professionista C | Capire che non ci sono assegnazioni | Stato vuoto e istruzione pertinente | Nessuna azione non autorizzata | Live: «Nessun professionista assegnato in questo centro», ma il primo piano rimane la griglia. |
| Finance | Documenti, pagamenti, banca e simulazioni fiscali | Soggetto, importo, stato, residuo, documento collegato | Azione consentita per stato; conferma e saldo leggibili | Sweep live: 10 rotte desktop. Servono descrizioni operative per documento e stati, senza cambiare menu né contabilità. |
| Commercialista | Consultare documenti e report in sola lettura | Documento, periodo, importi, stato e audit | Consultazione/export autorizzato, nessun comando mutativo | Sweep live: 5 rotte desktop. La distinzione tra riepilogo e dettagli contabili deve restare chiara. |
| Administrator tecnico | Amministrare Frappe/ERPNext | Desk e strumenti tecnici | Funzioni native complete | Fuori dalla superficie cliente; non applicare semplificazioni che nascondano strumenti tecnici. |

## Percorso Professionista da validare con persone

1. L'accesso deve mostrare le attività assegnate di oggi o il prossimo appuntamento, con uno stato vuoto utile se non ve ne sono.
2. Da una seduta, il professionista deve distinguere orario, paziente autorizzato, stato e azione possibile. Nessuna modifica di prenotazione o pagamento va introdotta tramite il prototipo.
3. L'esito deve distinguere campi obbligatori, note riservate e dati consultabili; salvataggio, errore e conferma devono nominare la seduta interessata senza diffondere contenuti clinici.
4. La lista deve riflettere lo stato dopo salvataggio. Questo percorso richiede prova funzionale su fixture isolata prima di qualsiasi PASS di usabilità.

Evidenze live: `issue75-empv-ux-audit/probe.json` e screenshot privati del 19/10/2026; prove grafiche sintetiche riportate in `screenshots/`. Le suite #137/#139 dimostrano routing/rendering, non che un operatore completi il compito senza guida.
