# GOAL-02 #139 — W0 baseline e W1 diagnosi asset (14/10/2026)

**Stato: PARTIAL.** La causa del difetto P0 è provata; il DEV non è stato modificato. W1 non è PASS finché non si esegue il gate Owner e il retest visivo live. #23 risulta CLOSED su GitHub, mentre il manifest cliente mantiene GOAL-02 `AUTHORIZED_ACTIVE`: nessuno dei due stati è stato modificato.

## Baseline osservata, sola lettura

- Branch sorgente della nuova linea: PR #138 DRAFT `cc2b12a2aa84494d654b67287a62252868b4bca1`, discendente dalla PR #133 DRAFT `2272fa9d5f757987f88c45b1b2843afb92cac093`. Nuovo branch `issue-139/unified-remediation`; PR #128/#78 non incorporata.
- `centrochange-dev`: nove container in esecuzione (sei applicativi, DB, due Redis), un Site `centrochange.local`; immagine applicativa `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`, sorgente applicativa `83f8f4f97b74e25e73710b6fc3667be0ae473fce`. Frappe/ERPNext 16.50.0, Healthcare 16.6.1, Builder 1.35.1.
- I sei hook di guardia/lingua sono presenti una volta e nell'ordine atteso. Impronta degli 11 DocType Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3`; `Communication` `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`, uguali al report #137. RAM disponibile 4,9 GiB, disco libero 53 GiB, PSI memoria full 0,00% (avg10), I/O full 0,06% (avg10). Nessuna suite mutativa o build eseguita.

## Causa dimostrata del P0

I file `assets.json` nei container backend e frontend mappano `desk.bundle.css`, `erpnext.bundle.css`, `report.bundle.css` su `P52FIUJ5`, `SX3UNIE7`, `H6YVEPG5`; tutti e tre i file esistono e sono serviti con HTTP 200 `text/css`. La cache Redis **bench-shared** `assets_json`, letta attraverso Frappe 16.50 `get_assets_json()`, contiene ancora `7IQ4MBII`, `2XFOQZJL`, `UX3MMGCD`. Il renderer Jinja `bundled_asset()` usa quella cache e genera gli URL vecchi; Nginx risponde 404 perché i file vecchi non esistono. La PR #133 ha cambiato i sei container applicativi preservando Redis, senza invalidare questa chiave al cambio immagine. Questo spiega perché hard refresh del browser non risolve.

Il confronto completo di `assets.json` più `assets-rtl.json` mostra **69 mapping**, tutti con file fisici presenti; **24 mapping CSS** (12 normali e 12 RTL) differiscono dalla cache. Il gate richiede esattamente queste 24 differenze note prima della mutazione e zero differenze dopo.

Fonti: [documentazione ufficiale Frappe Asset Bundling](https://docs.frappe.io/framework-git/client-side/asset-bundling) (hash, `assets.json`, `bundled_asset`), [Bench overview](https://docs.frappe.io/framework-git/administration/bench-overview) (cache site-specific). Verifica sul sorgente Frappe 16.50 installato: `frappe/utils/__init__.py:get_assets_json`, `frappe/utils/jinja_globals.py:bundled_asset`, `frappe/cache_manager.py:bench_cache_keys`, `frappe/utils/redis_wrapper.py:ClientCache.delete_value`. Il problema è la cache condivisa obsoleta, non CSS mancante nell'immagine né un solo problema browser.

## Correzione preparata e gate

`infra/issue139_asset_cache_gate.py` verifica immagine e inventario, Site, sei hook, fingerprint Owner/Communication, manifest e HTTP degli asset. Senza flag è read-only e segnala `STALE` con exit 2. Con `--invalidate` elimina **solo** la chiave Redis bench-shared `assets_json` usando l'API Frappe pinned, quindi verifica manifest/cache e impronte dati. Non cambia DB, immagini, container, Compose, file o permessi. I cinque test offline verificano no-mutation di default, invalidazione esplicita, idempotenza del gate e FAIL se il nuovo mapping non coincide. Il check read-only contro il DEV restituisce `STALE` atteso.

**Autorizzazione Owner DEV distinta richiesta prima di `--invalidate`.** Dopo l'eventuale autorizzazione: un'unica esecuzione, confronto delle 11 liste e 11 schede native con Chromium desktop/mobile, CSS status/content-type e icon sizing; stop a nuovi errori. La correzione deve poi entrare nella procedura versionata di cambio immagine affinché il problema non ricompaia al deploy del candidato finale. L'errore socket.io resta da diagnosticare separatamente, senza cambiare autenticazione.

### Errore realtime separato

Il sorgente Frappe 16.50 `realtime/middlewares/authenticate.js` chiama `fetch(get_url(socket, ...))`; `get_url` usa l'header `Origin`. Nginx invia `Origin: http://centrochange.local` per preservare il controllo hostname, mentre il container websocket non risolve `centrochange.local` nella rete Docker (risolve `frontend` e `backend`). Questo spiega il `TypeError: fetch failed` prima dell'autenticazione. La configurazione versionata `infra/compose.issue139_realtime.yaml` aggiunge **solo** l'alias di rete `centrochange.local` al frontend esistente; una simulazione `docker compose config` dimostra che nessun altro servizio o campo cambia. Nessuna applicazione dell'override, ricreazione o test live autorizzato: il risultato realtime è ancora **NOT_TESTED**. Non si disabilita il confronto Origin/Host.

## Fasi successive

- W2: l'attuale `Branch` non espone uno stato operativo Centro Change; i `require_center`/`require_finance` controllano appartenenza, non inattività. Inventariare le chiamate server e i selettori prima di introdurre uno stato versionato; nessuna modifica ai dati Centro B eseguita.
- W3/W4: non si valuta né ritocca la resa visiva sopra le 22 native rotte. Si riusano i test #137 e i difetti #136 dopo il retest del renderer.
- W5: 128 visite comparabili, 11 liste/Form, sette ruoli, Guest e fixture di sicurezza soltanto con ownership/cleanup verificato; report finale e Owner visual UAT separata.
