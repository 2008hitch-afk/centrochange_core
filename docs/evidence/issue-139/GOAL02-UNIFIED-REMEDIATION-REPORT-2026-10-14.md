# GOAL-02 / #139 — unified remediation report — 14/10/2026

**Esito finale dopo due installazioni autorizzate distinte: `ROLLED_BACK` / `PARTIAL`.** Il primo tentativo si è fermato su Socket.IO; il secondo ha superato i controlli browser ma si è fermato prima della suite sicurezza per un errore nell'invocazione del runner. Entrambi hanno eseguito **un solo rollback verificato**. Il DEV serve ancora la baseline precedente. `READY_FOR_OWNER_VISUAL_UAT` **non** è raggiunto; nessun Owner PASS, merge, produzione o GOAL-03.

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

## Seconda installazione distinta — esito effettivo

L'Owner ha autorizzato direttamente una seconda installazione del commit PR #140 `02d04207415c804bb7f1e9a48ce187b9252b2e73`, candidato applicativo immutato `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`, executor SHA-256 `f0e55f7dd30212bf976cb1e8a8dc41cc65fea8f6db86d662df70d36802138efd`. Il preflight read-only iniziale e il controllo Git erano PASS. Il gate privato 0600 è stato creato all'ora effettiva `2026-10-14 21:41:28 UTC`, scadenza operativa `2026-10-15 01:41:28 UTC`, recupero `02:41:28 UTC`; l'avvio è stato registrato nella issue #139 prima della prima mutazione.

L'executor ha creato checkpoint e backup cifrato verificato, costruito `sha256:0b50ab087069abbcd2ff8a2390f78b47dd2465178cf96a1a29e938006fe0196b`, installato i sei servizi applicativi, migrato il Site, attivato Centro A con audit tecnico e lasciato Centro B inattivo. I tre servizi tecnici sono rimasti sulle immagini precedenti. Prima del FAIL sono passati: sei immagini servite, sei hook e permessi, **11 asset diretti** con hash corretto, **69 mapping manifest**, proxy realtime con Origin canonico/tunnel HTTP 200 e Origin incongruenti/estranei HTTP 403, autenticazione Administrator, **128/128 visite route×ruolo×viewport** senza FAIL, e **22/22 coppie Lista/Scheda native** (11 desktop + 11 mobile). Le screenshot e i report sono Chromium live sul DEV candidato, non prove HTTP-only. La suite W5 read-only non ha generato mutazioni inattese.

**FAIL preciso:** `infra/issue139_install_gate.py` ha invocato `infra/issue137_safe_security_run.py` tramite `sys.executable` senza `-I`. Il runner stesso richiede `sys.flags.isolated == 1`, quindi è uscito immediatamente con `Requires sudo python3 -I on the authorized host`. **Nessuno dei 38 controlli sicurezza live è partito**; il loro PASS precedente appartiene soltanto al clone isolato. L'executor ha interpretato correttamente il FAIL come significativo e ha eseguito l'unico rollback; report privato `issue139-install-runs/20261014T214144Z-3392744/report.json`: `status=ROLLED_BACK`, `rollback_failure=null`. Non esiste un terzo tentativo automatico.

Verifica indipendente post rollback: nove servizi attivi; sei immagini applicative tornate a `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`; `DRY_RUN_PASS` con fingerprint Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3`, schema, configurazione, permessi, sei hook, CSS #79 e due sedi nella baseline originaria. Il Site DEV non mantiene la migrazione né l'attivazione Centro A del candidato.

### Correzione preparata dopo il rollback, senza deploy

Il runner ora riceve `-I` sia nel processo figlio avviato dall'executor sia nella chiamata interna alla suite. Un test unitario verifica entrambi i passaggi. **52 test Python offline PASS**, dipendenze SHA pin coerenti, `git diff --check` e preflight read-only PASS. Una verifica non mutativa con fingerprint volutamente errato è arrivata al controllo dati e ha risposto `BLOCKED: current synthetic fingerprint differs from this run checkpoint`: conferma che il runner supera il controllo `-I` senza creare fixture. Il nuovo executor ha SHA-256 `fe4b8d1b2e68bec138d54e29e217eebfc9cdd9392be6ef61f1bb0b019015ee9e`; appartiene soltanto alla PR DRAFT, **non è installato né autorizza un nuovo tentativo**.

### Checklist Owner #136 — stato dimostrabile

| Area | Sul candidato prima del rollback | DEV attuale / limite |
| --- | --- | --- |
| Undici liste e undici schede native | PASS renderer/asset/geometria desktop e mobile, screenshot live | Baseline precedente ripristinata; accettazione visiva Owner ancora aperta |
| Login/Agenda e navigazione dei sette ruoli | 128/128 visite Chromium PASS, nessun errore JS/asset/realtime nella suite | Fluidità percepita e ogni transizione richiedono giudizio Owner |
| Centro A/B | A attivato con audit; B inattivo durante il candidato | Transizione annullata dal rollback; enforcement live con 38 test non completato |
| Selettori e #79 | Route Agenda senza regressioni automatiche | Interazioni complete e giudizio UX Owner non rieseguiti in questo tentativo |
| Italiano, date e orari | Campioni di Agenda/Finanza in italiano e date europee nelle screenshot | Copertura globale di ogni errore, stampa e picker non dimostrata |
| Storico sedute, revisioni note, azioni sensibili | Rendering delle route PASS | Scenari A1–A5 di #136 non collaudati operativamente in questo tentativo |
| Finanza, Banca, SdI/TS simulati, Report | Route dei ruoli autorizzati PASS e schermate leggibili | Operazioni contabili e chiarezza finale richiedono collaudo Owner; nessun invio reale |
| Sicurezza/API/cross-center | 38/38 PASS solo nel clone isolato | **BLOCKED live** dal runner; non attribuire PASS al DEV candidato |
| Integrità dati | Fingerprint invariati dopo rollback | PASS sul DEV ripristinato |

Screenshot **live del secondo tentativo**, con soli dati demo: [Agenda desktop](screenshots/w5-live-attempt-agenda-desktop.png), [Agenda mobile](screenshots/w5-live-attempt-agenda-mobile.png), [Fattura paziente desktop](screenshots/w5-live-attempt-sales-invoice-form-desktop.png), [Fattura paziente mobile](screenshots/w5-live-attempt-sales-invoice-form-mobile.png). Il campione Agenda desktop mostra ancora «Inizio» e «Agenda» contemporaneamente evidenziati; alcuni identificativi sintetici restano molto prominenti. Questi sono rilievi UX, non un PASS visivo Owner. Evidenze raw private: `~/.local/state/centrochange-single/browser-evidence/issue139-20261014T214144Z-3392744/`.

**Accesso Owner attuale:** tunnel privato `ssh -L 8082:127.0.0.1:8082 empv26@srv2033673`, quindi `http://127.0.0.1:8082`; usare le credenziali demo già custodite nel canale sicuro. Il link serve **la baseline ripristinata**, non il candidato #139. Una review finale del candidato non può essere dichiarata pronta in questo stato.

**Prossimo gate:** valutazione Owner del risultato `ROLLED_BACK` e, soltanto se desiderato, autorizzazione distinta per un eventuale terzo tentativo con il nuovo executor pin e suite live completa. Nessun retry in questo mandato. La [panoramica GOAL-03](GOAL03-READONLY-PREREQUISITES-2026-10-14.md) è documentale; GOAL-03 non è stato avviato.
