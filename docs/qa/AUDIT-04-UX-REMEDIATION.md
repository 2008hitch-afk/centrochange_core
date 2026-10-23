# AUDIT-04 #167 — Prosecuzione UX-04, PR DRAFT #168

**Stato del candidato:** `PENDING_CI` sullo SHA finale, dopo PASS tecnico locale e Frappe isolato; sviluppo in branch `issue-167/patients-audit`, DEV **non modificato**. La decisione `SINGLE_CLIENT_UI_PREMIUM_ONLY` è già attiva sul DEV tramite PR #169 e rimane vincolante. Questa PR non incorpora ancora #169: prima di un futuro gate DEV occorre costruire un candidato che contenga entrambi gli alberi e verificare routing, manifest e SHA risultanti.

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
- Frappe/MariaDB reale: immagine applicativa `sha256:4ba222ea03c37c5c12d4f4512bbabfcd92194ee9df9d2a91ea113818752d84ce`, sorgente `d70a43bcaf9251f72cae353e595f1a280f972d37`, manifest/asset PASS. Clone temporaneo con Site, DB e rete separati: restore cifrato di 6 componenti, 55 entry Site e 929 tabelle, confronto schema/conteggi/hash critici PASS. Suite browser/API su clone fresco: **21 PASS, 17 SKIP** per casi desktop-only; Sette ruoli più Guest e centri A/B inclusi; `CC-HTTP-*` e `CC-MVP-POS-*` reali in fixture esclusivamente sintetiche.
- Reviewer indipendente: la prima review ha trovato nome incompleto ambiguo, Agenda oltre 500 e test live dipendente dallo stato. La seconda review del diff ha verificato il ramo `get_all` ristretto agli appuntamenti già autorizzati per Segreteria/Professionista e non ha trovato blocker statici. La prova HTTP Agenda su Manager, Segreteria e Professionista è PASS nel clone; un test Python impedisce la regressione `get_list` Patient senza DocPerm.
- DEV condiviso: `NOT_TESTED` per questa PR; nessun deploy o cambiamento di dati, schema, ruoli o permessi autorizzato in questa fase. L'immagine backend DEV è rimasta `sha256:540f8f87c2802cd35fa85ecdbe48f38037a5611fb3e3f4d0fdae5b861fde267c`. Le dieci risorse Docker del clone finale sono state rimosse per ID verificato; backup cifrato e prove private restano fuori Git.

**Gate DEV residuo:** autorizzazione specifica #167 dopo riconciliazione PR #169, CI su SHA finale, nuovo checkpoint cifrato completo, restore isolato PASS e rollback indipendente. Solo allora eventuale installazione dei sei servizi applicativi previsti; nessun merge automatico.

## Screenshot rappresentativi

- [Scheda reale desktop](../evidence/audit-04-patients/ux-live-patient-desktop.png) · [mobile](../evidence/audit-04-patients/ux-live-patient-mobile.png): «Chiara Bellini», un solo titolo e campi Marley coerenti.
- [Anagrafica incompleta CC-MVP-POS](../evidence/audit-04-patients/ux-live-mvp-fallback-desktop.png) e [fallback mobile](../evidence/audit-04-patients/ux-live-fallback-mobile.png): riferimento opaco e stabile. Le stringhe tecniche nel campo di ricerca sono query digitate dal test; i motivi di audit della fixture riflettono input sintetico e non sono trasformati in dati inventati.
- [Ricerca contestuale aperta desktop](../evidence/audit-04-patients/ux-search-open-desktop.png) · [mobile](../evidence/audit-04-patients/ux-search-open-mobile.png): focus e risultati senza overflow.

## Esito e decisione DEV

`READY_FOR_DEV_GATE`, subordinato ai check GitHub sullo SHA pubblicato, significa che il codice di presentazione e le API scoped sono pronti alla **richiesta del gate di installazione**, non che il DEV sia già aggiornato o che l'Owner abbia accettato Pazienti. La PR #168 resta DRAFT. Il gate deve: (1) riconciliare PR #169, ancora DRAFT, così che l'immagine target includa il routing Premium primario; (2) eseguire CI sull'ultimo SHA e verificare manifest/image/source parity; (3) checkpoint cifrato nuovo, restore reale isolato e rollback indipendente; (4) sostituire soltanto i sei servizi applicativi se tutti i controlli sono PASS; (5) verificare `/premium/#Pazienti`, accessi diretti, ruoli, centri e `cc_premium_primary=1` senza toccare schema, dati storici o produzione. La nuova autorizzazione `DEV_INSTALL_ALLOWED` della Issue #167 è obbligatoria.

La suite GitHub Actions non usa DEV, segreti o dati reali. Il suo esito va letto dai checks della PR sulla HEAD pubblicata; i test locali non sono CI GitHub.
