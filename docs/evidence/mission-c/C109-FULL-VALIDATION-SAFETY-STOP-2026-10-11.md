# Missione C #109 — collaudo anticipato, stop al primo guard I/O

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. L'Owner ha sostituito la data d'avvio del 12 ottobre e autorizzato una sola attivazione immediata, [registrata prima delle mutazioni](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6108151255). Finestra privata 2026-10-11 10:37:46–16:37:46 UTC, con hard stop 17:37:46 UTC. L'attivazione si è conclusa anticipatamente al primo evento di sicurezza, alle **10:42:40 UTC**. Nessun retry.

## Build, isolamento e sicurezza

- PR draft #112, codice prodotto effettivamente caricato dal commit `97092a06659b4d3322bf4ce30ff6cbb06f8c28c1`; OCI manifest `sha256:602b7a1930a918dce5b957602e645a34fb4947092b6fbd55fd60e62b5694f1c1`. Quattro file app cambiati rispetto alla demo precedente hanno superato confronto byte-per-byte sia nel layer sia nel container. Hook/asset Desk HTTP 200; `/api/method/ping` C109 HTTP 200.
- Otto servizi nel solo progetto `centrochange-c109-gated-r4`, volumi e reti C109 esclusivi, cap aggregato **2 GiB**, swap zero. Nuovi scope indipendenti watchdog/eventi/expiry attivati con C109 fermo, prima di rilasciare uno a uno i workload; verifica HostConfig, PID e cgroup `memory.max`/`memory.swap.max` per tutti gli otto PASS, OOM locale zero. QA inerte avviato separatamente con cap **512 MiB** e cgroup verificato prima di Chromium. Nessuna build o migrazione; DB e cinque volumi C109 conservati.
- `security.desk_boundary_acceptance.run` read-only sulla nuova immagine: **PASS per m/s/f/t/a/b/c**. Nessun `System Manager` o `Website Manager`; `Builder Page` non leggibile/scrivibile/creabile, configurazioni tecniche non mutabili; Administrator tecnico separato. Questo non sostituisce ancora test HTTP/direct/API/export/print.
- Al primo Chromium (Segreteria, route `/app/cc-unified-desk`) PSI I/O host **full avg10 1,26%**, oltre soglia invariata **1%**. Il watchdog ha scritto `IO_PSI`, arrestato soltanto C109 e concluso l'attivazione; anche il wrapper del test ha rilevato `host PSI full`. Nessun risultato browser o screenshot è stato prodotto. Il picco appartiene all'host: la quota causale del browser rispetto ad altri I/O non è dimostrata.
- 33 campioni privati: PSI memoria full massimo **0,00%**, MemAvailable minimo **5.132.976.128 byte**, OOM host **7→7**, alert eventi protetti assente. Il codice di uscita 137 di alcuni container deriva dallo stop controllato entro timeout e non è evidenza di OOM. RC22 prima/dopo: stessi **9/9 ID** e ping HTTP **200**. C109 finale: **0 container running**; vecchia e nuova immagine, container fermati, database e volumi conservati. Nessun dato reale o traffico provider.

## Matrice finale sulla nuova immagine

`NOT_TESTED` indica che il guard è intervenuto prima dello scenario browser/funzionale. I PASS storici R2/R3 e la demo visuale non sono trasferiti alla nuova immagine.

| # | Area | Esito su `97092a0` | Evidenza/gap |
| --- | --- | --- | --- |
| 1 | Agenda | NOT_TESTED | asset caricato, griglia e azioni non eseguite |
| 2 | Prenota/sposta/cancella | NOT_TESTED | nessuna mutazione funzionale |
| 3 | Seduta/storico/note | NOT_TESTED | nessun dettaglio aperto |
| 4 | Pazienti | NOT_TESTED | List/Form e ricerca non eseguite |
| 5 | Professionisti | NOT_TESTED | List/Form e self-view non eseguite |
| 6 | Disponibilità | NOT_TESTED | editor e native read non eseguiti |
| 7 | Catalogo/prezzi/pacchetti | NOT_TESTED | List/Form e snapshot non eseguiti |
| 8 | Contabilità/registri | NOT_TESTED | native read, query ed export non eseguiti |
| 9 | Fatture paziente/fornitore | NOT_TESTED | workflow contabili non eseguiti |
| 10 | Incassi/pagamenti | NOT_TESTED | Payment Entry non eseguiti |
| 11 | Banca/riconciliazione | NOT_TESTED | reconcile/undo non eseguiti |
| 12 | Report Centro/Professionisti/Pazienti | NOT_TESTED | KPI e drill-down non eseguiti |
| 13 | Report ERPNext generici | NOT_TESTED | 403 diretti da verificare |
| 14 | SdI simulato | NOT_TESTED | nessun provider utilizzato |
| 15 | TS simulato | NOT_TESTED | nessun provider utilizzato |
| 16 | Audit | NOT_TESTED | List/Form, append-only/export non eseguiti |
| 17 | Accessi e centri | PARTIAL | technical-role/Builder DocPerm PASS; lifecycle, direct API e revoca non eseguiti |
| 18 | Compensi/coda amministrativa | NOT_TESTED | soglia/override non eseguiti |
| 19 | Notifiche/job | NOT_TESTED | retry/idempotenza non eseguiti |
| 20 | Login/logout | NOT_TESTED | browser interrotto prima del risultato |
| 21 | Primo incontro pubblico | NOT_TESTED | superficie separata, non toccata |
| 22 | Stampa/export | NOT_TESTED | nessuna prova positiva o negativa |
| 23 | Validazione DEV | NOT_TESTED | esclusa dalla UI cliente; non provata qui |
| 24 | Identità/cutover/C3 | NOT_TESTED | solo salute RC22 verificata; nessun confronto funzionale né cutover |

**Per ruolo:** m/s/f/t/a/b/c hanno solo il controllo server-side tecnico read-only PASS. Guest e Administrator non hanno un browser test completo; per Administrator è stata verificata soltanto la separazione tecnica nel test server-side. Desktop, mobile, italiano, ricerca, keyboard/focus, List/Form e confronto C3: **NOT TESTED** sulla nuova immagine.

## Recupero e limite residuo

Il codice sorgente, l'OCI nuova e l'immagine precedente restano disponibili; nessuna migrazione schema è stata eseguita. Il dataset è sintetico. Il precedente checkpoint integrale C109 interrotto rimane **invalido** e non viene indicato come restore verificato. La prova server-side non ha modificato i dati; il browser è stato interrotto prima di completare scenari mutativi. I log e i campioni grezzi rimangono nell'archivio privato della singola attivazione, fuori Git.

La sola evidenza materiale nuova è il superamento della soglia I/O durante l'avvio del browser; non vi è prova di difetto prodotto. Prima di una nuova attivazione serve una decisione Owner sul percorso di collaudo con sufficiente capacità I/O **mantenendo la soglia e il fail-closed**, e una nuova autorizzazione singola. Non usare un retry nella stessa attivazione. Nessun merge, cutover o modifica a RC22.
