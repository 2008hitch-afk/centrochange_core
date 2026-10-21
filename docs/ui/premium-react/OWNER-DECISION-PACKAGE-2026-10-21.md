# #148 — unico pacchetto Owner residuo

**Aggiornamento DECISION-063:** il gate per implementare API delimitate in codice isolato è stato APPROVATO. La richiesta API qui sotto è storica; per i soli contratti rimasti senza policy e per l'unico gate DEV usare [SCOPED-API-DECISION-063-REPORT.md](SCOPED-API-DECISION-063-REPORT.md). Il piano runtime resta non autorizzato e non eseguito. La PR #150 resta DRAFT / PARTIAL.

**Proposta, non autorizzazione.** La PR #150 rimane DRAFT e il DEV `centrochange-dev` non è stato modificato. DECISION-060/061/062 approvano direzione e lavoro isolato; la mutazione dell'unico stack e le nuove API di scrittura richiedono il gate materiale. Il risultato di questa PR è una UI React di sviluppo con fixture sintetiche; 77 test Playwright PASS, 1 skip desktop intenzionale. Nessun test live Frappe/multiruolo o collaudo grafico Owner è stato svolto.

## Decisione richiesta, in una sola revisione

1. **Contratti API e ruoli:** approvare, emendare o negare i contratti puntuali in [SCOPED-MASTER-API-PROPOSAL.md](SCOPED-MASTER-API-PROPOSAL.md) per Item, Appointment Type, CC Center Service, Item Price, CC Package Template, Patient, Healthcare Practitioner, lettura Payment Entry, eventuale allocazione diretta e stampa. Definire campo per campo, ruoli 7+Guest, centri, privacy, contabilità, snapshot e idempotenza prima di qualunque implementazione POST. Una approvazione runtime non concede implicitamente questa approvazione API.
2. **Sequenza single-stack:** approvare o negare la sequenza indivisibile in [SINGLE-STACK-EXECUTION-GATE-2026-10-21.md](SINGLE-STACK-EXECUTION-GATE-2026-10-21.md): fingerprint, backup cifrato dell'unico Site, restore rehearsal isolata temporanea, build immagine derivata offline, sostituzione dei soli sei container applicativi `centrochange-dev`, test reali, rollback verificato se necessario. Una approvazione API non concede implicitamente il cambio DEV.

## Risorse esatte del gate runtime

- **Mantenere:** un Bench logico, Site `centrochange.local`, database `_4f614b4543aa5230`, container MariaDB e due Redis, `configurator` spento, rete `centrochange-dev-net`, quattro volumi nominati `centrochange-dev-{sites,db-data,redis-cache-data,redis-queue-data}`, porta host `127.0.0.1:8082`, image ID attuale `sha256:6d6f9d2e65d0b16974e6b04aeaaf6d1210f071448ace5276689ebc9652bc2f7b` disponibile per rollback.
- **Sostituire solo dopo gate:** `centrochange-dev-{backend,frontend,websocket,queue-short,queue-long,scheduler}-1`, con gli ID completi registrati nel piano e da rifissare immediatamente prima dell'intervento. La nuova immagine deriva da quella pinned 16.50 attuale e aggiunge solo `www/premium*` e `public/premium/*`; non eseguire migrate.
- **Temporanee per prova restore, poi rimuovere per ID verificato:** container `cc148-restore-db` e `cc148-restore-runner`, volumi `cc148-restore-db-data` e `cc148-restore-sites`, rete interna `cc148-restore-net`; nessuna porta host o Site/DB DEV condiviso. Backup cifrato con chiave separata fuori Git, accessi 0600/0700; conservarlo fino a recovery test concluso.
- **Non toccare:** altri progetti, produzione, vecchie immagini/volumi anonimi, laboratori storici, dati reali, provider reali, permessi, route native e pagina iniziale, merge o cutover. Non nasce un secondo ambiente permanente.

## Condizioni prima/dopo

Prima: ricontrollare `git`/asset hash, image/container/site/DB/Compose effettivi, file override privato con identità già autorizzata senza cambiare permessi, solo dati sintetici, `docker stats`, PSI, RAM/disco e `memory.max/events`; abort se mismatch o cap OOM non dimostrati. Eseguire il backup nativo `bench --site centrochange.local backup --with-files --compress --ignore-backup-conf` con wrapper revisionato; testare decrittazione e restore in risorse temporanee prima dello switch. La configurazione Compose privata e il comportamento restore non interattivo sono ancora **NOT_VERIFIED**.

Dopo: un solo Site/DB/Bench, schema e app pinned invariati, `/premium` e `/premium-primo-incontro` same-origin, login/CSRF, 7 ruoli+Guest con centro A/B, note private, 11 liste/form, URL dirette, export, negative matrix 38, p50/p95 e OOM, nessun provider. Registrare prove tecniche e screenshot; Owner visual UAT separato. Se fallisce, rimettere l'image ID precedente ai sei container con lo stesso Compose e verificare health/schema/permessi; usare il backup solo con procedura di restore autorizzata in caso di mutazione dati imprevista. Nessuna pulizia storica automatica.

**Stato:** `PARTIAL / RUNTIME_GATE_BLOCKED`; `SYNTHETIC_UI_QA_PASS`; frontend operativo reale e `READY_FOR_OWNER_VISUAL_UAT` **NOT_VERIFIED**. L'Owner può decidere i due ambiti insieme in questa revisione, indicando l'esito di ciascuno. Fino ad allora nessuna operazione sul DEV e nessuna nuova API sensibile.
