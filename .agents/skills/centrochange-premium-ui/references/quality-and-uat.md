# Quality gates — Centro Change Premium Frontend

## Ogni route è PASS solo se

1. Browser reale renderizza correttamente CSS/JS/font/icon e dati autorizzati: niente layout rotto, svg giganti, toolbar incoerente, spinner infiniti o error overlay.
2. Flusso realmente funzionante verificato in test controllato, non solo HTTP200 o screenshot statico.
3. Loading/empty/error/validation/conferma/modale e focus/tab/keyboard/ESC accessibili.
4. Desktop almeno `1440x900` e mobile `390x844`, no clipping e horizontal overflow.
5. Ogni ruolo ha test positivi e negativi per UI/API, URL diretta, query/list/export/print, pazienti e note riservate; Guest bounded.
6. Errori e testi in italiano, date `GG/MM/AAAA`, ore `HH:mm`, `Europe/Rome` inclusi DST e mezzanotte; semantica timestamp originale conservata.
7. Confronto screenshot e interazioni con reference visiva approvata, senza riprodurre pixel o copyright Fresha.
8. Performance su stesso hardware/rete/fixture, baseline e soglie fissate in W0; misurare p50/p95 nav e Agenda. Niente numeri inventati.
9. Dipendenze pinned/licenze/NOTICE, nessun CDN obbligatorio o font proprietario.
10. No regressioni sui workflow GOAL-02 e su permessi/audit. SdI/TS solo simulated.

## Matrice

`ROUTE | RUOLO | EXPECTED | ACTION | API/DATA | DISPLAY | DESKTOP/MOBILE | ERROR | SECURITY | RESULT | EVIDENCE`.

Usare `PASS/FAIL/BLOCKED/NOT_TESTED`; non convertire retroattivamente PASS di build precedenti o di un browser che vede soltanto HTTP 200. Baseline #137/#139 (128 route×ruolo×device e 38 sicurezza) va rieseguita sul candidato React con metodi equivalenti o migliorati.

## Evidenza finale

- Report `PREMIUM-FRONTEND-GOAL-COMPLETION-REPORT.md` con build SHA, matrice delle route/ruoli/API/test, screenshot sintetici, log sanitizzati, performance prima/dopo, sicurezza e limiti.
- Distinzione `TECHNICAL PASS` / `READY_FOR_OWNER_VISUAL_UAT` / `OWNER ACCEPTED` / `RELEASED`.
- Goal Learning Extraction secondo policy HITCH: solo generalized learning `CANDIDATE` sanitizzati, mai APPROVATO automaticamente.

## Gate stop

Fix ordinari autonomi; stop per rischi dati/sicurezza, nuove licenze/acquisti, cambio architettura/scope, clone server, DEV condiviso, merge, cutover, GOAL-03, produzione, credenziali/provider reali.
