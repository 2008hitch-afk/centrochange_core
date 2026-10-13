# #79 — executor Owner a comando unico

**Stato della preparazione:** script e ricetta versionati sulla PR #129 DRAFT. **Nessun deploy eseguito da Codex.** Il CSS autorizzato rimane il commit `1b2486d00754ba68fa4ee3c57a39060dc8cc781c`; #78/#128 e il checkout `/tmp/centrochange-issue124` restano esclusi.

## Perché basta la Page CSS

Nel [codice Frappe 16.50.0 della Page](https://github.com/frappe/frappe/blob/v16.50.0/frappe/core/doctype/page/page.py), `load_assets()` legge il file `.css` della Page e lo mette in `style`. [Il caricatore Desk](https://github.com/frappe/frappe/blob/v16.50.0/frappe/desk/desk_page.py) chiama `load_assets()` in `getpage`. Sul DEV è stata osservata la risposta `frappe.desk.desk_page.getpage` con il campo `docs[0].style` e le regole `.cc-client` della Page. **Questa ricetta non esegue `bench build`, migrate o clear-cache:** ricrea il solo backend, che rilegge la Page CSS dall'immagine nuova. Il test `live` verifica il risultato realmente servito.

## Contenuto e comportamento

- Executor: `infra/issue79_one_command.py`; Dockerfile: `infra/Dockerfile.issue79`; inventario read-only: `infra/browser/issue79_inventory.cjs`; regressione reale: `infra/browser/issue79_unified_autocomplete.cjs`.
- Il comando Owner avvia un solo `sudo` interattivo. Lo script verifica il proprio SHA-256, l'immagine base e rollback `f3821526…`, CSS precedente `d3b04182…`, CSS candidato `f3ab9d5d…`, commit e due righe esatte, recipe/harness, 9 container, health, Compose/env/checkpoint, spazio, browser, fixture privata e dataset sintetico. Acquisisce lock e ricontrolla il drift prima dello switch.
- Il contesto di build contiene soltanto Dockerfile versionato e CSS estratto con `git show` dal commit CSS fissato; la nuova immagine ha il medesimo prefisso di layer più un solo layer `COPY`. Il tag candidate è `centrochange-single:issue79-css-f3ab9d5ddf9f`.
- L'env privata cambia **solo** `CC_UAT_IMAGE`, con backup 0600 e sostituzione atomica. Compose ricrea **solo** `backend`, `--no-deps --no-build`. DB, Redis, frontend, websocket, queue e scheduler non vengono ricreati; il volume Site resta montato identico.
- Chromium gira come `empv26`, non come root, e usa `CC_ISSUE79_ASSET_MODE=live` sulla route `/app/cc-unified-desk?cc_view=agenda`. Il test non inietta CSS e non invia POST booking. L'inventario read-only di m/s/a/b/c produce hash dei record visibili prima/dopo.
- Se un check fallisce prima dello switch, esce `BLOCKED` senza cambiare il runtime. Se fallisce dopo lo switch, ripristina byte per byte l'env, ricrea il solo backend con l'immagine precedente e riverifica health, CSS, volumi e inventario. Ritorna `ROLLED_BACK` solo dopo ripristino verificato; altrimenti `BLOCKED` con motivo di rollback da esaminare. Non fa retry.
- Report e backup locale sotto `/home/empv26/.local/state/centrochange-single/issue79-runs/<timestamp>-<pid>/` (0700, root); screenshot sintetici sotto `browser-evidence/<timestamp>-<pid>/`. Nessun secret o backup va in Git.

## Preparazione e limiti

Check statici **PASS**: Python AST, Node `--check`, `git diff --check`; 2 test offline PASS (sostituzione/ripristino env e checkpoint). Dry-run senza sudo **PASS**: `STATIC_DRY_RUN_PASS`, con SHA Compose/env/commit CSS attesi e zero mutazioni runtime. Un hash script errato è stato rifiutato con `BLOCKED`. La prova Docker completa avverrà **solo** quando l'Owner lancerà il comando autorizzato. Il dry-run non dichiara immagine nuova né PASS live.

Lo script versionato è `/tmp/centrochange-issue79/infra/issue79_one_command.py`, SHA-256 `cf0baed590d7675264fae2ff445d266c8272a248c70dde8f926d5a0fdce92473`. L'Owner lo esegue nella propria sessione SSH sul server `srv2033673` con **un solo comando**:

```sh
sudo /usr/bin/python3 -I /tmp/centrochange-issue79/infra/issue79_one_command.py --script-sha256 cf0baed590d7675264fae2ff445d266c8272a248c70dde8f926d5a0fdce92473 --apply
```

`sudo` chiede la normale password locale dell'Owner. `-I` isola gli import Python; l'esecutor confronta il proprio hash prima di ogni operazione. Nessuna esecuzione remota pipe-to-shell o modifica ai privilegi. PR #129 resta DRAFT; nessun Owner PASS.
