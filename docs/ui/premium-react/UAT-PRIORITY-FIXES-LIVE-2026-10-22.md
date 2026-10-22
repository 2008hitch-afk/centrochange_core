# #148 — correzioni UAT prioritarie, DEV single-stack

**Stato: runtime e QA live PASS; richiesta etichette demo PARTIAL.** PR #150 resta DRAFT. Nessuna accettazione grafica Owner dichiarata.

## Intervento

- Agenda React: settimana lunedì–domenica predefinita, sette colonne uguali e allineate, professionisti nelle righe, appuntamenti nella cella giorno/professionista. Filtri, navigazione, prenotazione e dettaglio restano attivi. Il nome del professionista ora entra nella colonna senza spezzare la parola sul desktop; sul mobile la griglia scorre orizzontalmente nella regione dedicata.
- **Professionisti** segue **Pazienti** nel menu. Elenco ricercabile e scheda usano API e permessi esistenti.
- **Report professionisti** è raggiungibile da Report. Selezione, periodo, conteggi, sedute ed esportazione autorizzata sono attivi; dettagli economici restano circoscritti ai ruoli Finance già autorizzati.
- Alias demo deterministici per gli ID esatti del manifest UAT, distinti per Patient e Customer, propagati a React tramite proiezioni già autorizzate. ID API, relazioni e documenti canonici non sono modificati. Quattro Patient sintetici storici fuori manifest non ricevono alias: non esiste una fonte di ownership esatta approvata per assegnarli senza indovinare. Questo è il solo punto PARTIAL delle quattro richieste.

## Immagine e recovery

- Sorgente prodotto `749eef346e9d259ce59266a5455311b45d498a76`; immagine completa `sha256:54db4262375457bee60f497029f8cf05f38e99bfab6ec9caa6762078a5f74b6f`. Parità source/manifest e parità dell'immagine costruita PASS.
- Checkpoint cifrato nuovo `cc148-checkpoint-413c1tgm`, sei componenti, 55 elementi Site e 40 file. Chiave separata fuori Git, checkpoint precedenti conservati. Restore reale su rete, database, container e volumi temporanei isolati: **PASS_RESTORE**; 929 tabelle, colonne, indici, conteggi e 15 hash critici identici; albero Site 55/55 prima dell'avvio, 41/41 componenti durevoli dopo.
- Solo i sei container applicativi di `centrochange-dev` sono stati ricreati. MariaDB, Redis, volumi DEV, Site, rete e porta `127.0.0.1:8082` invariati. Blocco scritture **3,44 minuti** su massimo 120. Nove servizi attivi, `cc_synthetic_dev=1`, `cc_uat_demo=1`, `cc_premium_primary=0`. Nessuna migrazione, reset, secondo stack permanente o cleanup storico.
- Risorse temporanee del restore rimosse dopo verifica di ID, label, rete e mount. Backup cifrato, chiave e vecchia immagine di rollback conservati.

## Verifiche

- Offline: typecheck e build PASS; 44 test Python PASS; Playwright completo **89 PASS, 1 SKIP** prima della rifinitura CSS. Dopo la rifinitura: due test Agenda desktop/mobile PASS e due test alias desktop/mobile PASS. Lo SKIP resta distinto dai PASS.
- Frappe reale: suite live finale **24/24 PASS**, fixture possedute dai test rimosse (`fixture_teardown=PASS`). Copre sette ruoli più Guest, centri A/B, 11 archivi e schede, Agenda, profili, Report, Finanza, stampa, CSRF, scritture consentite, dinieghi e responsive. `catalog.records` p95: 12 ms desktop, 11 ms mobile su dieci campioni per viewport.
- Dopo i test: schema e 15 hash dei dati clinici/finanziari identici. Crescono solo audit, commenti di teardown, log permessi e preferenze di notifica/sessione Frappe.
- Screenshot **live**: Agenda [desktop](../../evidence/issue-148/uat-live-agenda-desktop.png) / [mobile](../../evidence/issue-148/uat-live-agenda-mobile.png); Professionisti [desktop](../../evidence/issue-148/uat-live-professionisti-desktop.png) / [mobile](../../evidence/issue-148/uat-live-professionisti-mobile.png); Report [desktop](../../evidence/issue-148/uat-live-report-professionisti-desktop.png) / [mobile](../../evidence/issue-148/uat-live-report-professionisti-mobile.png). Screenshot **offline sintetici** con appuntamenti nella griglia: `docs/evidence/issue-148/uat-agenda-week-{desktop,mobile}.png`; alias e ID canonici: `uat-alias-demo-{desktop,mobile}.png`. Gli screenshot live del Report possono mostrare nomi di vecchie fixture sintetiche fuori manifest: non sono dati reali.

## Accesso Owner

La React DEV esistente risponde a `http://127.0.0.1:8082/premium` **sul server**. Da un dispositivo Owner usare il tunnel SSH già autorizzato verso `srv2033673.hstgr.cloud` con inoltro locale `8082:127.0.0.1:8082`, poi aprire lo stesso URL locale ed entrare con la propria utenza UAT Frappe. Nessuna credenziale è nel report. `cc_premium_primary` resta disattivato in attesa dell'accettazione visiva esplicita.
