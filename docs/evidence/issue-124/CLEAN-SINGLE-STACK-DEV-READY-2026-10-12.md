# Issue #124 — Clean single-stack DEV

**Esito: `CLEAN_SINGLE_STACK_DEV_READY` (2026-10-12, 11:53 UTC).** Ambiente DEV sintetico persistente sul server esistente. PR #125 resta DRAFT; nessun merge, cutover o GOAL-03.

## Gate e cancellazione

L'Owner ha approvato il manifest `docker-delete-gate-2026-10-12.json`, SHA-256 `2a0e1e51c1ccaeff458b174a3d4711640ab741b07cd1baed3f7443ec4d4d4208`; l'autorizzazione è stata registrata sulla issue #124 prima della prima cancellazione. Hash, ID, nomi, attribuzione esclusiva, assenza di condivisione, sorgenti e immagini pinned sono stati ricontrollati senza deriva. Sono state eliminate esclusivamente le 241 vecchie istanze container, 254 volumi demo, 28 reti demo e 36 percorsi privati del manifest. Verifica finale: tutti gli ID e percorsi storici assenti. Preservati 23 volumi esclusi/non attribuiti/buildx, tre checkout sorgente, immagini necessarie, OS/SSH/Nginx e servizi estranei. Il vecchio RC22 è stato spento nel downtime approvato; nessun suo dato demo è stato ripristinato.

## Installazione unica

| Elemento | Stato verificato |
| --- | --- |
| Host/progetto Docker | Un server, progetto `centrochange-dev`, una rete di progetto |
| Bench/Site | Un Bench logico condiviso dai servizi applicativi, una sola directory Site `centrochange.local` |
| Database | Un solo DB applicativo nuovo `_4f614b4543aa5230`; gli altri schemi MariaDB sono di sistema |
| App installate | Frappe 16.50.0, ERPNext 16.50.0, Builder 1.35.1, Healthcare 16.6.1, `centrochange_core` 0.0.1, ciascuna una volta nel Site |
| Servizi | Nove container attivi nello stesso progetto: DB, due Redis, backend, frontend, websocket, due worker, scheduler. Un configurator one-shot concluso (exit 0), stesso progetto |
| Storage | Quattro volumi nuovi dello stesso progetto: Site, DB e due Redis. Nessun volume storico collegato |
| Accesso | Frontend `127.0.0.1:8082`; `GET /login` = 200. Nessuna porta HTTP pubblica |
| Limiti | Limiti memoria per servizio e swap nullo verificati via Docker HostConfig; progetto DEV unico |

Sorgenti upstream pinned: Frappe `f20f92d29706510551b4438cc196b0323a7f1a92`, ERPNext `7474d9e786277383de1242ab882f16856d17a9c9`, Builder `37e958bc4f801d06d0438c21b97b42c45c4eaa51`, Healthcare/Marley `dda107b26e3a0fe1dbd65c7257371235de054a04`. Immagine applicativa verificata `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`, revisione `e2fd728ecf6acdb0e0ab26379820df6905dd5521`, albero applicativo identico alla HEAD PR #112 `6f8a8f5f28ebc39f8e25eecd10086a601fc21419` (che include PR #107). La ricetta versionata `infra/Dockerfile.issue124` ricostruisce gli asset mancanti di login a partire da quell'immagine: immagine runtime finale `sha256:8822eee88b37d1659d94c8eb95c8bc737f75edb605042f96809eda2f9199e1b2`. L'immagine base TARGET locale era `sha256:10e701947cccc377dc1d3c2082a03ef69b81d14da8e08fac75f07e78bcf974ce`. Il Dockerfile generico con ERPNext 16.32.0 non è stato usato.

Configurazione privata: `/home/empv26/.local/state/centrochange-single/runtime.env` (0600), con segreti nuovi fuori Git. La ricetta Compose è `infra/compose.yaml` + `infra/compose.uat.yaml` + `infra/compose.issue124.yaml`; `CC_UAT_IMAGE` nella env privata punta all'ID immutabile sopra. Per ricostruire l'immagine derivata sullo stesso server, la precondizione è l'immagine base C109 verificata; il tag locale `centrochange-single:issue124-base` la identifica. Nessuna patch manuale ai container attivi.

Il Site è stato creato su DB vuoto. Sono stati impostati `cc_synthetic_dev=1` e `cc_uat_demo=1`; `python3 infra/uat_demo.py seed` ha caricato soltanto dati sintetici nuovi con tooling versionato. Validazione `goal02-demo-v1`: sette utenti demo, otto pazienti, due centri, due professionisti, dieci appuntamenti e dati economici/fiscali simulati; hash semantico `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`.

## Collaudo reale

- Riavvio completo dei nove servizi: PASS. `infra/uat_runtime_health.py`: PASS dopo il riavvio (HTTP/asset, WebSocket, due worker, job short/long, scheduler); `infra/uat_demo.py validate`: PASS, hash invariato.
- Chromium Playwright reale, QA temporanea 512 MiB, login Manager e sei sezioni: PASS dopo il riavvio. Tutte mostrano dati; link Agenda cliccato; nessun errore JavaScript o overflow orizzontale. Home, Agenda, Finanza e Report usano Unified Desk; Pazienti e Professionisti sono le viste Healthcare esposte dalla navigazione.
- Permessi server-side: `centrochange_core.security.desk_boundary_acceptance.run` PASS per sette ruoli. Test HTTP diretto `infra/issue124_role_api.py` PASS: Manager 200 su report scoped e fattura nativa; ruolo amministrativo non autorizzato e Guest 403 su entrambi; nessuna mutazione.
- `infra/security_acceptance.py --with-booking --with-operations` non completato sul Site persistente: il proprio fixture tenta di creare una route pubblica già presente nel seed. È collisione del fixture; il controllo diretto dei permessi sopra è PASS. La suite completa richiede fixture isolati/idempotenti prima di essere usata sul Site persistente.

Screenshot reali: [Home](screenshots/issue124-home.png), [Agenda](screenshots/issue124-agenda.png), [Pazienti](screenshots/issue124-pazienti.png), [Professionisti](screenshots/issue124-professionisti.png), [Finanza](screenshots/issue124-finanza.png), [Report](screenshots/issue124-report.png). Nessun dato reale o segreto negli screenshot.

## Accesso Owner

Da una macchina con accesso SSH autorizzato al server:

```sh
ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100
```

Aprire `http://127.0.0.1:8082/login`. Per ricevere le credenziali demo dal canale SSH privato:

```sh
scp empv26@179.198.222.100:/home/empv26/.local/state/centrochange-single/demo-owner.json ./centrochange-demo-owner.json
```

Nel file usare `users.m.name` e `users.m.password` per il ruolo Manager. Il file sul server è 0600; conservarlo localmente in modo privato. L'ambiente DEV è persistente, **senza scadenza automatica**; il tunnel dura finché resta aperta la sessione SSH. Nessuna credenziale è in GitHub.

## Residui e GOAL-02

Difetti UI minori osservati: una voce secondaria Report si comprime a larghezza 1440 px e alcune etichette delle liste native restano in inglese. Non impediscono navigazione o dati. La suite generale di security acceptance va resa compatibile con il seed persistente. Il ripristino integrale da zero senza l'immagine base locale non è stato provato: per la riproducibilità fuori da questo server occorre pubblicare o ricostruire con pin espliciti l'immagine base. Proseguire con gli acceptance criteria funzionali restanti di GOAL-02 e la review Owner; `READY_FOR_OWNER_UAT` non è dichiarato. Nessuna attività GOAL-03 è stata eseguita.
