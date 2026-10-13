# #79 — executor Owner a comando unico

**Stato della preparazione:** script e ricetta versionati sulla PR #129 DRAFT. **Nessun deploy eseguito da Codex.** Il CSS autorizzato rimane il commit `1b2486d00754ba68fa4ee3c57a39060dc8cc781c`; #78/#128 e il checkout `/tmp/centrochange-issue124` restano esclusi.

## Perché basta la Page CSS

Nel [codice Frappe 16.50.0 della Page](https://github.com/frappe/frappe/blob/v16.50.0/frappe/core/doctype/page/page.py), `load_assets()` legge il file `.css` della Page e lo mette in `style`. [Il caricatore Desk](https://github.com/frappe/frappe/blob/v16.50.0/frappe/desk/desk_page.py) chiama `load_assets()` in `getpage`. Sul DEV è stata osservata la risposta `frappe.desk.desk_page.getpage` con il campo `docs[0].style` e le regole `.cc-client` della Page. **Questa ricetta non esegue `bench build`, migrate o clear-cache:** ricrea il solo backend, che rilegge la Page CSS dall'immagine nuova. Il test `live` verifica il risultato realmente servito.

## Contenuto e comportamento

- Executor: `infra/issue79_one_command.py`; override persistente versionato: `infra/compose.issue79.yaml`; Dockerfile: `infra/Dockerfile.issue79`; inventario read-only: `infra/browser/issue79_inventory.cjs`; regressione reale: `infra/browser/issue79_unified_autocomplete.cjs`.
- Il comando Owner avvia un solo `sudo` interattivo. Lo script verifica il proprio SHA-256, l'immagine base e rollback `f3821526…`, CSS precedente `d3b04182…`, CSS candidato `f3ab9d5d…`, commit e due righe esatte, recipe/harness, 9 container, health, Compose/env/checkpoint, spazio, browser, fixture privata e dataset sintetico. Acquisisce lock e ricontrolla il drift prima dello switch.
- Il contesto di build contiene soltanto Dockerfile versionato e CSS estratto con `git show` dal commit CSS fissato; la nuova immagine ha il medesimo prefisso di layer più un solo layer `COPY`. Il tag candidate è `centrochange-single:issue79-css-f3ab9d5ddf9f`.
- `CC_UAT_IMAGE` rimane invariata. L'override contiene **solo** `services.backend.image` e `pull_policy: never`; viene copiato, con SHA verificato, in `/home/empv26/.local/state/centrochange-single/compose.issue79.yaml`. L'env privata riceve soltanto `COMPOSE_FILE` con i tre file originali e questo override persistente, con backup 0600 e sostituzione atomica. Il normale `docker compose --env-file ... -p centrochange-dev up` usa così la stessa configurazione anche in futuro. Compose ricrea **solo** `backend`, `--no-deps --no-build`; gli altri cinque servizi applicativi, DB e Redis mantengono immagine, configurazione e container precedenti. Il volume Site resta montato identico.
- Prima dello switch lo script confronta il `docker compose config` risolto di tutti i servizi: l'unica differenza ammessa è l'immagine backend. Dopo la scrittura verifica anche che il normale Compose senza `-f` carichi esattamente i quattro file persistenti. L'uso manuale dei soli tre `-f` originali non rappresenta la configurazione attiva: riporterebbe il backend alla vecchia immagine; non cambierebbe gli altri servizi.
- Chromium gira come `empv26`, non come root, e usa `CC_ISSUE79_ASSET_MODE=live` sulla route `/app/cc-unified-desk?cc_view=agenda`. Il test non inietta CSS e non invia POST booking. L'inventario read-only di m/s/a/b/c produce hash dei record visibili prima/dopo.
- Prima dello switch crea e verifica la scrivibilità della directory screenshot come utente `empv26`, per evitare rollback dovuti a permessi delle evidenze. Se un check fallisce prima dello switch, esce `BLOCKED` senza ricreare servizi. Se fallisce dopo lo switch, ripristina byte per byte l'env, rimuove soltanto l'override con hash esatto, riverifica la configurazione Compose originaria, ricrea il solo backend con l'immagine precedente e riverifica health, CSS, volumi e inventario. Ritorna `ROLLED_BACK` solo dopo ripristino verificato; altrimenti `BLOCKED` con motivo di rollback da esaminare. Non fa retry.
- Report e backup locale sotto `/home/empv26/.local/state/centrochange-single/issue79-runs/<timestamp>-<pid>/` (0700, root); screenshot sintetici sotto `browser-evidence/<timestamp>-<pid>/`. Nessun secret o backup va in Git.

## Preparazione e limiti

Check statici della revisione **PASS**: Python AST, `git diff --check`; 3 test offline PASS, inclusa simulazione reale `docker compose config` della configurazione persistente, del successivo avvio ordinario e del rollback per tutti i servizi. Inoltre la configurazione Compose reale corrente e l'override versionato sono stati confrontati in sola lettura: soltanto `backend.image` cambia. Dry-run isolato `STATIC_DRY_RUN_PASS` sulla HEAD finale, con env originale verificata e zero mutazioni runtime. La prova Docker/runtime completa avverrà **solo** quando l'Owner lancerà il comando autorizzato. Il dry-run non dichiara immagine nuova né PASS live.

Lo script versionato è `/tmp/centrochange-issue79/infra/issue79_one_command.py`, SHA-256 `4294053e6694cbdfa4706ddf0dc411d8bf9e43190eb1c6bbf4ffa3b8a410d574`. L'Owner lo esegue nella propria sessione SSH sul server `srv2033673` con **un solo comando**:

```sh
sudo /usr/bin/python3 -I /tmp/centrochange-issue79/infra/issue79_one_command.py --script-sha256 4294053e6694cbdfa4706ddf0dc411d8bf9e43190eb1c6bbf4ffa3b8a410d574 --apply
```

`sudo` chiede la normale password locale dell'Owner. `-I` isola gli import Python; l'esecutor confronta il proprio hash prima di ogni operazione. Nessuna esecuzione remota pipe-to-shell o modifica ai privilegi. PR #129 resta DRAFT; nessun Owner PASS.
