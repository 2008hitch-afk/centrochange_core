# GOAL-02 / #139 — unified remediation report — 14/10/2026

**Esito effettivo: `ROLLED_BACK` / `PARTIAL`.** L'unica installazione DEV autorizzata è stata eseguita, il primo sweep W5 ha fallito e l'executor ha eseguito **un solo rollback verificato**. `READY_FOR_OWNER_VISUAL_UAT` **non** è raggiunto; nessun Owner PASS, merge, produzione o GOAL-03.

## Versioni, gate e rehearsal

- PR #140 DRAFT, candidato applicativo immutato `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`, executor SHA-256 `e44be980328860fdaf250032e54219f3c6c0dba1380a7c34a9c67d27ba4b5970`.
- Guard isolata `infra/issue139_restore_guard.py`: trace fail-closed di 24 comandi del vero `restore_backup()`, comprese destinazioni `container:path`; tre test positivi/negativi PASS. Clone Docker su rete interna senza porte pubbliche: restore executor PASS per DB, file pubblici/privati, configurazione, schema, ruoli, permessi, sei hook, HTTP 200 e riavvio. Risorse temporanee rimosse. 50 test Python offline e preflight DEV PASS prima dell'installazione.
- Gate privato creato all'avvio effettivo `2026-10-14 18:12:14 UTC` con scadenza operativa `22:12:14 UTC` e recupero `23:12:14 UTC`, modalità 0600, candidato e SHA pinati. Nessun orario fittizio.
- Baseline DEV: nove servizi `centrochange-dev`, un Site, Frappe/ERPNext 16.50.0; sei servizi applicativi `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`. Fingerprint Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3`, Communication `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`.

## Unica installazione e test live

L'executor ha creato checkpoint e tag rollback, costruito l'immagine candidata `sha256:0a2d520cba930e8930470a74457cbf928b452038707560c814ab26d4cdf4abdd` dai 57 file applicativi del commit pinato, fermato i servizi applicativi, verificato backup nativo cifrato di DB/file/config e migrato il Site. Ha verificato A/B inattive dopo la migrazione, attivato **Centro A** tramite `set_operational` con audit e lasciato **Centro B inattivo** prima della riapertura. Alias DNS frontend `centrochange.local` applicato. Sono passati controllo delle sei immagini, servizi tecnici invariati, sorgenti/hook/permessi/dati e probe asset: **11 file pubblici serviti con SHA corretto, manifest di 69 mapping coerente**.

**W5 si è fermato al primo sweep Chromium reale `m/1440`: 23/23 route FAIL per `REALTIME_ERROR`** (`Error connecting to socket.io: Unauthorized: TypeError: fetch failed`). Nessuna richiesta mutativa inattesa, nessun errore API aggregato. Tre route hanno anche risposte asset 304 senza MIME classificate dal runner come `ASSET_HTTP_OR_MIME_ERROR`; sono una distinta anomalia di classificazione/cache da riesaminare, non prova di CSS mancanti. La suite si è arrestata correttamente: **gli altri sei ruoli, mobile, 11 liste/schede native e 38 controlli di sicurezza non sono stati eseguiti**. Nessun PASS W5 dedotto da prove offline o HTTP 200.

### Diagnosi mirata realtime

Nel Frappe pinned, `realtime/middlewares/authenticate.js` esegue una `fetch(get_url(socket, path))`; `realtime/utils.js` costruisce l'URL dall'header `Origin` senza cambiare porta fuori da developer mode. Il browser usa `http://centrochange.local:8082`, mentre Compose pubblica **host 8082 → frontend container 8080**. L'alias introdotto rende risolvibile `centrochange.local` nel network Docker, ma non crea un listener sulla porta interna 8082: la fetch dal websocket continua a fallire. Questa è la spiegazione supportata da codice e topologia; una correzione richiede un delta di rete/proxy o configurazione progettato e provato separatamente, non un secondo tentativo automatico. Non è stata ridotta la sicurezza Socket.IO.

## Rollback e stato DEV dopo il tentativo

Alla prima failure W5, l'executor ha fermato il candidato, ripristinato DB, file e config dal backup cifrato con il percorso `restore_backup()` provato nel clone, rimesso in servizio la baseline e terminato **`ROLLED_BACK`, `rollback_failure: null`**. Una verifica indipendente successiva ha confermato:

- Nove servizi attivi; sei immagini applicative di nuovo `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`; DB e Redis immutati.
- Env privato SHA-256 `589a74a2020c583e4e6def59a343ec49fe78264704e56107bb28c6c7aa8dec0b`, senza overlay candidato nel `COMPOSE_FILE`.
- Fingerprint Owner e Communication identici alla baseline; schema `a6e45ecfb3ac9bf08f5d51d1123cb928de828580df2bf7b21e3fe3c865c89375`, Site config `6db58e4d24377f9ebf2aa0c35c0e22633c1e44aa262521250ae72cc4c76f1eb2`, permessi `97af394ec1d9b4fe18b551282c2ecec40b5b70558e0d4968dfadf341ec66b52c` identici; sei hook presenti.
- `Branch.cc_operational` assente come prima della migrazione; due Branch demo preservati. Directory backup del Site vuota. PSI memoria full 0, disco libero circa 53 GiB.

Il file privato `compose.issue139_candidate.yaml` e il tag immagine candidato restano come artefatti **non selezionati**; il file overlay non compare nel `COMPOSE_FILE`. La loro presenza fa fallire un nuovo preflight, prevenendo retry impliciti. Non sono stati rimossi o riutilizzati in questo turno.

## Decisione successiva

La PR #140 resta DRAFT e il DEV serve ancora la baseline precedente. Per un nuovo intervento serve prima correggere e verificare il percorso di autenticazione realtime con la porta interna corretta, distinguere le risposte asset 304 dai veri errori e preparare **una nuova attivazione singola autorizzata** con checkpoint pulito. W5 completo, integrità e review visiva Owner restano aperti. Il tentativo presente non viene ritentato.

Evidenze raw, screenshot e backup cifrati restano privati sotto `~/.local/state/centrochange-single/issue139-install-runs/20261014T181223Z-3192594/` e `~/.local/state/centrochange-single/browser-evidence/issue139-20261014T181223Z-3192594/`; nessun secret o dump è in Git.
