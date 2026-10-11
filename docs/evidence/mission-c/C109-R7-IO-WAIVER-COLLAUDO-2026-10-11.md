# Missione C #109 — r7, deroga I/O controllata e collaudo parziale

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. Una sola attivazione r7, autorizzata dall'Owner e [registrata prima di Docker create](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6111696011). Finestra 2026-10-11 17:26:53–23:26:53 UTC, con recupero fino a 00:26:53 UTC. Il laboratorio è stato fermato anticipatamente alle 17:48 UTC in modalità fail-closed durante l'aggiornamento mirato del frontend; nessun retry.

## Protezioni e identità

- Progetto esclusivo `centrochange-c109-gated-r7`, otto servizi, 2 GiB RAM aggregati e swap zero; QA separato limitato a 512 MiB. Immagine applicativa iniziale `sha256:602b7a1930a918dce5b957602e645a34fb4947092b6fbd55fd60e62b5694f1c1`, codice prodotto `97092a06659b4d3322bf4ce30ff6cbb06f8c28c1`. Nessuna build completa, nuova base, migrazione o modifica RC22.
- La deroga r7 ha rimosso i soli cap artificiali 4/2 MiB/s e lo stop automatico **sul solo PSI I/O**. Il watchdog ha continuato a campionare PSI I/O; memoria, OOM, swap, cgroup, riserva disco, eventi protetti ed expiry sono rimasti attivi. Il monitor RC22 indipendente ha verificato ogni due secondi i nove ID esatti, ping e pagina web; soglie 1 s per tre campioni o 3 s immediati. Test offline positivi/negativi e selettore Docker esatto verificati prima dell'avvio; il percorso di stop poteva fermare solo r7.
- Bootstrap 8/8 servizi PASS, ciascuno rilasciato dopo verifica HostConfig e cgroup memoria/swap; QA inert 512 MiB/swap zero PASS. C109 HTTP 200. 252 campioni watchdog: PSI I/O full massimo **2,57%** (registrato, deroga autorizzata), PSI memoria full massimo 0%, MemAvailable minimo **4,39 GiB**, OOM host **7→7**. 604 campioni RC22: HTTP sempre 200, latenza massima 0,527 s, zero alert. RC22 ha mantenuto gli stessi nove ID e HTTP 200 al controllo finale.

## Prove sulla build iniziale effettivamente rilasciata

- Browser reale, un Chromium alla volta: dashboard dei sette ruoli sintetici `m/s/f/t/a/b/c`, quattro ingressi custom (Agenda, Finanza, Report professionisti, Report pazienti), dieci List native e Agenda settimanale per `m/s/a/b/c). JS page errors **0** nei percorsi eseguiti. Su Centro A, 28/09–04/10, Segreteria 9 sedute, Alfa 8, Beta 1, professionista senza assegnazioni 0; A∩B vuoto e A/B sottoinsiemi delle nove sedute di Segreteria. Header sette giorni, dettaglio Seduta/Storico/Note e apertura del dialog Prenota verificati. La suite browser non ha eseguito submit/sposta/cancella; i corrispondenti servizi sono coperti dalla suite backend.
- `centrochange_core.operations.integration_acceptance.run`: **189 controlli PASS**, rollback della fixture. HTTP security core adattata esclusivamente al site C109: **17 PASS**, cleanup PASS. `security.desk_boundary_acceptance.run`: sette ruoli cliente privi di grant tecnici e Administrator separato, PASS. Native finance adapter: **11 PASS**. Finance/receivables/banking/incoming/professional/reporting/SdI simulato/TS simulato: rispettivamente **24/17/16/12/18/21/6/8 controlli PASS**, con cleanup PASS; nessun provider reale. La security suite completa con prenotazione pubblica non era riutilizzabile senza toccare la route sintetica `Marco` già presente: la variante core ha escluso quel ramo, e il primo tentativo di fixture è stato respinto per duplicato prima del collaudo.
- Dopo `bench --site b99.local clear-cache` sul solo C109, il runtime ha incluso l'hook `app_include_js` già versionato e la barra Centro Change è comparsa sulle List native. Prima del refresh degli hook, il browser era arrivato correttamente a `/desk/healthcare/patient`, mentre il vecchio harness attendeva solo `/app`; il timeout iniziale era del test, non della List.

## Difetto UI e aggiornamento interrotto

La [screenshot reale della build iniziale](r7/agenda-before-fix-synthetic.png) mostra l'Agenda compressa a destra: il menu client era un figlio diretto del `body` flex di Frappe v16 e occupava circa 655 px; la Page misurava 551 px. Una [prova DOM transitoria, **non** un PASS della build](r7/agenda-dom-probe-synthetic.png) ha spostato il menu dentro `.main-section`: Page 1206 px e calendario leggibile. Il fix prodotto è versionato nel commit `713d517`; test offline dei sette profili PASS.

Per verificare il fix sull'immagine effettiva, è stato confezionato e validato un delta OCI della revisione `09dab7ac6fc6bc0e9b0bdc806c91dac4c88d0060`, manifest `sha256:f91c10a997fe594e5fabe21e4b6173582cbdaec73a202ca51ac847f6b20f2e1d`. L'aggiornamento controllato del solo frontend ha creato il nuovo container **inerte**, ma il gate cgroup ha ricevuto `docker ps -aq` in formato ID abbreviato e ha rifiutato `read_snapshot` prima del rilascio. L'harness ha fermato r7 come previsto. La nuova immagine **non è stata collaudata nel browser**. Il difetto del gate è corretto offline con `--no-trunc` e test di ID abbreviato/vuoto/multiplo; non è stato usato per ritentare r7. Il container nuovo, immagini, volumi ed evidenze restano conservati e fermati.

Anche prima di questo aggiornamento, le List native mostravano label e chrome upstream (per esempio `Patient`, `Healthcare`, `Magazzino` e campi tecnici), quindi la conformità richiesta per l'esperienza cliente non era dimostrata. La barra Centro Change aggiunta dagli hook non risolve da sola tale requisito.

## Matrice GOAL-02 su r7

`PARTIAL` significa servizio o schermata provati solo in parte; nessuna riga è promossa a PASS per la UI finale.

| # | Area | Esito | Evidenza o limite |
| --- | --- | --- | --- |
| 1 | Agenda | PARTIAL | Browser 7 giorni/A-B-C PASS; geometria della build iniziale FAIL |
| 2 | Prenota/sposta/cancella | PARTIAL | Servizi nella suite 189; dialog Prenota aperto, submit browser non eseguito |
| 3 | Seduta/storico/note | PARTIAL | Tre tab browser e guard backend; azioni browser non complete |
| 4 | Pazienti | PARTIAL | List Manager e direct/API scoped; chrome/label upstream |
| 5 | Professionisti | PARTIAL | List Manager e report, isolamento A/B/C; shell nativa da rifinire |
| 6 | Disponibilità | PARTIAL | Backend integrato; editor browser non esercitato |
| 7 | Catalogo/prezzi/pacchetti | PARTIAL | Cinque List native aperte; editing browser non esercitato |
| 8 | Contabilità/registri | PARTIAL | Finance 24 e List contabili; UI end-to-end incompleta |
| 9 | Fatture | PARTIAL | Finance/receivables e List Sales Invoice; print browser non eseguito |
| 10 | Incassi/pagamenti | PARTIAL | Finance/native adapter e List Payment Entry |
| 11 | Banca/riconciliazione | PARTIAL | Banking 16 e Bank Transaction List |
| 12 | Report Centro/Professionisti/Pazienti | PARTIAL | Reporting 21 e due ingressi browser; drill-down browser non completo |
| 13 | Report ERPNext generici | NOT TESTED | Direct/export sui report generici non dimostrati |
| 14 | SdI simulato | PARTIAL | Suite 6 PASS, nessun traffico reale; pagina browser non completa |
| 15 | TS simulato | PARTIAL | Suite 8 PASS, nessun traffico reale; pagina browser non completa |
| 16 | Audit | PARTIAL | List Manager e negative Finance; export/print non completi |
| 17 | Accessi/centri | PARTIAL | Security 17 e boundary tecnico; workflow UI non completo |
| 18 | Compensi | PARTIAL | Professional 18; pagina browser non completa |
| 19 | Notifiche/job | NOT TESTED | Nessuna prova browser/worker specifica r7 |
| 20 | Login/logout | PARTIAL | Login sette ruoli; logout/Guest browser non esercitati |
| 21 | Primo incontro pubblico | NOT TESTED | Fixture route esistente preservata; Guest flow non esercitato |
| 22 | Stampa/export | PARTIAL | Security negative API; output positivi non esercitati |
| 23 | Validazione DEV | NOT TESTED | Superficie tecnica esclusa dal collaudo cliente r7 |
| 24 | Identità e confronto C3 | FAIL | Geometria iniziale, chrome upstream; nessun confronto funzionale RC22 completato |

## Stato finale e gate

Zero container r7 running; database/volumi e immagini preservati. Nessun alert RC22, OOM o evento protetto; 44 GiB disco disponibile e circa 5,4 GiB MemAvailable al termine. La deroga era confinata ai processi privati r7 ora terminati: configurazioni globali, RC22 e profilo storico con stop PSI I/O all'1% invariati. Nessun merge/cutover/produzione.

La singola attivazione Owner è consumata. Per provare il fix `713d517` serve una **nuova autorizzazione operativa** per un laboratorio isolato con il gate ID completo già corretto, immagine frontend verificata e medesimo monitor RC22. Restano poi il completamento visivo delle List/Form native, Guest/logout, drill-down browser, API/export/print per tutti i ruoli e confronto C3. Nessun PASS storico sostituisce la prova sulla build finale.
