# #139 — secondo gate DEV dopo prova W5 isolata — 14/10/2026

**Stato: `ISOLATED_W5_PASS / SECOND_DEV_INSTALL_OWNER_GATE_REQUIRED`.** La prima installazione DEV resta `ROLLED_BACK`; questo rapporto non la ripete e non dichiara `READY_FOR_OWNER_VISUAL_UAT` sul DEV. PR #140 rimane DRAFT. La decisione successiva dell'Owner deve autorizzare **una nuova, singola installazione**; la precedente autorizzazione è stata consumata.

## Baseline preservata

- Candidato applicativo invariato `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f` (57 file applicativi). Non include #78/#128.
- Preflight read-only dell'executor: `DRY_RUN_PASS`, nove servizi `centrochange-dev`, sei servizi applicativi ancora su `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`, due sedi, fingerprint dati Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3`. Env, Site, schema, permessi, sei hook e CSS #79 sono stati verificati dal gate. Il tag e l'overlay della prima installazione restano inattivi; non sono stati selezionati o ripuliti manualmente.
- Nessun container, Site, database o volume del DEV è stato installato, migrato o riavviato durante questa fase. Il clone `cc139-w5-isolated` è stato rimosso con i suoi volumi; inventario DEV identico prima/dopo.

## Causa e correzione Socket.IO

Nel Frappe/ERPNext pinned 16.50, `realtime/middlewares/authenticate.js` usa `get_url()` per richiamare via HTTP l'Origin della connessione. L'Origin pubblico è `http://centrochange.local:8082`; Docker pubblica quella porta verso il frontend che ascolta **internamente sulla 8080**. La sola risoluzione DNS non crea un listener interno sulla 8082: questo spiega il `TypeError: fetch failed` del primo W5.

`infra/issue139_frontend.conf.template` è la configurazione Nginx originale dell'immagine pinned con un delta circoscritto alla location `/socket.io`: il proxy verifica la coppia Host/Origin pubblico ammessa, quindi invia al worker l'Origin interno `http://centrochange.local:8080` e l'Host del Site. Le sole entrate pubbliche ammesse sono il nome canonico e il tunnel privato `127.0.0.1:8082`. Origin estranei o incrociati ricevono 403; autenticazione e autorizzazione Frappe restano attive. L'executor costruisce l'immagine dal candidato esatto, installa il template in build e ne verifica hash, rendering e risposte prima di W5. Il nuovo tag candidato `centrochange-single:issue139-realtime-v2` è distinto dal tentativo consumato.

Il runner Chromium tratta HTTP 304 come validazione cache soltanto quando la richiesta include `If-None-Match` o `If-Modified-Since`; 304 non condizionale, 404 e MIME errato restano FAIL. Test unitari positivi e negativi PASS.

## Prova sulla topologia isolata

Il clone usa nove servizi, volumi e rete dedicati, Site sintetico ripristinato dal backup nativo verificato, frontend pubblicato su `127.0.0.2:8082 → 8080` e alias interno `centrochange.local`. L'immagine isolata `sha256:6c42f39b75a6d8414637d6a05882ac21f5fe8a7972f271739a9c66407fb4cebd` dichiara sorgente `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`. Nginx `-t` PASS. `bench migrate` PASS; Centro A è stato attivato tramite `set_operational` con un singolo audit nel clone, Centro B è rimasto inattivo. Nessuna di queste scritture ha coinvolto il DEV condiviso.

| Verifica isolata | Risultato |
| --- | --- |
| Realtime: Origin canonico e tunnel | HTTP 200; namespace Manager autenticato |
| Realtime: Guest, Origin estraneo e Origin/Host incongruenti | Guest rifiutato da Frappe; coppie estranee/incongruenti HTTP 403 |
| Chromium, sette ruoli × desktop/mobile | **128/128 visite PASS**, zero mutazioni inattese |
| Native List/Form | **11/11 coppie PASS** su desktop e **11/11 su mobile** |
| Administrator tecnico; Guest API Patient | Desk tecnico PASS; accesso Guest negato |
| Sicurezza con fixture sintetiche | **38/38 controlli PASS**, cleanup PASS |
| Integrità dopo suite e riavvio clone | Fingerprint Owner/Communication/permessi invariati salvo il solo audit Centro A; sei hook una volta; A=1/B=0; realtime ancora PASS |
| Suite offline e dry-run DEV | **51 test Python PASS**, test 304 PASS, `git diff --check` PASS, `DRY_RUN_PASS` |

Screenshot Chromium reali e sanitizzati: [Agenda desktop](screenshots/w5-final-agenda-desktop.png), [Agenda mobile](screenshots/w5-final-agenda-mobile.png), [Fattura paziente desktop](screenshots/w5-final-sales-invoice-form-desktop.png), [Fattura paziente mobile](screenshots/w5-final-sales-invoice-form-mobile.png). Altri report/screenshot e log grezzi restano in `~/.local/state/centrochange-single/issue139-isolated-w5-browser/w5-20261014T185418Z-3263959/` con accesso privato. Il controllo visuale dei campioni non mostra asset rotti o overflow bloccante; l'accettazione estetica resta Owner.

## Procedura pronta per un secondo gate Owner

Il nuovo executor `infra/issue139_install_gate.py`, SHA-256 `f0e55f7dd30212bf976cb1e8a8dc41cc65fea8f6db86d662df70d36802138efd`, conserva checkpoint completo, backup cifrato verificato, preflight ripetuto immediatamente prima del fermo, limiti host, verifica delle sei immagini e dei tre servizi tecnici, migrazione e attivazione auditata A/B, W5, controllo fingerprint e **un solo rollback**. Il vecchio overlay inattivo è ammesso solo se il suo hash è quello documentato; qualsiasi drift blocca. Il gate privato con SHA executor esatto viene creato all'ora UTC effettiva di avvio, con massimo quattro ore operative più un'ora esclusiva di recupero. Nessuna finestra calendario separata è richiesta.

Prima del secondo deploy: verificare che PR #140 sia alla HEAD riportata qui e DRAFT, preflight `--dry-run` PASS, clone rimosso, risorse e dati invariati, immagine candidata nuova non già taggata, backup/rollback recuperabili. **Solo dopo nuova autorizzazione Owner** eseguire una singola installazione; al primo FAIL significativo fare un solo rollback e fermarsi. Dopo l'installazione, ripetere i 128 controlli, 11 List/Form per viewport, 38 controlli sicurezza e le impronte sul DEV reale. Non riutilizzare il gate del primo tentativo.

## Limiti

Il PASS W5 è su clone fedele e isolato: non dimostra ancora il risultato dell'installazione sul DEV condiviso. Le prove browser sono principalmente di navigazione e rendering read-only; i 38 controlli usano fixture sintetiche con cleanup, non costituiscono accettazione visiva Owner né convalida di tutti i workflow finanziari. Nessun merge, produzione, GOAL-03 o modifica a Missione C.
