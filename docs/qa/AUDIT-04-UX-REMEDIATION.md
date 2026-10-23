# AUDIT-04 #167 — Prosecuzione UX-04, PR DRAFT #168

**Stato del candidato:** sviluppo in branch `issue-167/patients-audit`, DEV **non modificato**. La decisione `SINGLE_CLIENT_UI_PREMIUM_ONLY` è già attiva sul DEV tramite PR #169 e rimane vincolante. Questa PR non incorpora ancora #169: prima di un futuro gate DEV occorre costruire un candidato che contenga entrambi gli alberi e verificare routing, manifest e SHA risultanti.

## Correzioni

| Difetto | Causa verificata | Correzione |
|---|---|---|
| UX-04-01 | Titolo Patient ripetuto e chip generico nella scheda | Un solo titolo con identità derivata dai campi Marley esistenti; rimossi duplicati di presentazione |
| UX-04-02 | Ricerca globale sempre visibile nella topbar | Pulsante discreto che apre campo e risultati contestuali, con focus/Escape; ricerca locale Pazienti e API scoped intatte |
| UX-04-03 | `patient_name` e fixture tecnici apparivano come nomi o alias fiscali; Agenda dipendeva dal bootstrap limitato a 500 | `first_name`/`last_name` proiettati nelle API già autorizzate di lista, ricerca e Agenda. Nome completo reale prioritario; in mancanza, riferimento opaco stabile e dicitura «Anagrafica da completare». Nessun ID o dato fiscale modificato |

Il clone isolato del primo candidato ha mostrato che otto Patient posseduti dal manifest UAT avevano `name`, `patient_name` e `first_name` tecnici, con `last_name` vuoto. Non è possibile ricostruire un nome reale da questi dati; la UI lo segnala apertamente. Una fixture nuova posseduta dal test ha consentito di verificare un nome completo reale. L'ID resta nelle chiamate API; Customer e documenti fiscali non vengono rinominati.

## Prove e confini

- Python offline: proiezione scoped dei nomi e caso appuntamento fuori bootstrap; nessun nuovo DocType/DocPerm.
- React typecheck/build, manifest sorgente e Playwright mock desktop/mobile: regressioni UX, search aperta/chiusa, due nomi incompleti distinguibili, Agenda fuori bootstrap, lista/drawer e sicurezza di navigazione.
- Frappe/MariaDB reale: clone temporaneo con Site, DB e rete separati; browser e API per sette ruoli più Guest, centri A/B, screenshot. **L'esito definitivo e il digest immagine devono essere riportati dopo la prova del candidato finale**, non dedotti dal precedente clone.
- Reviewer indipendente: la prima review ha trovato nome incompleto ambiguo, Agenda oltre 500 e test live dipendente dallo stato; le tre correzioni sono nel candidato e richiedono verifica sul diff finale.
- DEV condiviso: `NOT_TESTED` per questa PR; nessun deploy o cambiamento di dati, schema, ruoli o permessi autorizzato in questa fase.

**Gate DEV residuo:** autorizzazione specifica #167 dopo riconciliazione PR #169, CI su SHA finale, nuovo checkpoint cifrato completo, restore isolato PASS e rollback indipendente. Solo allora eventuale installazione dei sei servizi applicativi previsti; nessun merge automatico.
