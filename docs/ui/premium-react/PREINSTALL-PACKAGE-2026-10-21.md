# #148 · pacchetto preinstallazione React + API per PR DRAFT #150

**Stato:** `SOURCE_PACKAGE_PASS / OFFLINE_REGRESSION_PASS / IMAGE_NOT_BUILT / FRAPPE_LIVE_NOT_VERIFIED / PARTIAL`. Questa preparazione non è un deploy né `READY_FOR_OWNER_VISUAL_UAT`. DECISION-060/061/062/063 applicabili; il Site unico futuro è `centrochange.local` sullo stack esistente `centrochange-dev`.

## Overlay riproducibile

La base locale letta in sola lettura è `centrochange-single:issue75-form-affordance-r2`, image ID `sha256:6d6f9d2e65d0b16974e6b04aeaaf6d1210f071448ace5276689ebc9652bc2f7b`. La label della revisione app non è presente; il manifest verifica invece gli hash della revisione `e2fd728ecf6acdb0e0ab26379820df6905dd5521` per otto file critici al momento della build. Il Dockerfile usa la stessa base e sovrappone solo:

| Tipo | File installati nell'app Bench esistente |
|---|---|
| DECISION-063 API | `catalog.py`, `scoped_api.py`, `operations/profiles.py`, `finance/payments.py`, `finance/documents.py` |
| React/Frappe | `www/premium.html`, `www/premium.py`, `www/premium-primo-incontro.html`, `www/premium_primo_incontro.py`, `public/premium/*` |
| Verifica | `infra/premium-single-stack-payload.json`, `infra/premium_single_stack_package.py` |

Il manifest contiene SHA-256 per ogni file della sovrapposizione e per `hooks.py`, `security/{audit,guards,lifecycle,permissions}.py`, `scheduling/booking.py`, `finance/guards.py`, `operations/workspace.py` della base. `--source` controlla copie Dockerfile, pin, lockfile, pagina Frappe, bundle Archivi e tutti i 20 endpoint con verbo GET/POST; `--image` controlla hash, import dalla app editable, quattro versioni upstream e hook prima e dopo `bench build`. File, versione o codice base discordante = build interrotta. Il manifest non prova la presenza effettiva del Site/Custom Field o la semantica delle API: servono test Frappe reali.

La build React production usa `ScopedArchive` e metodi di dominio, mentre la preview sintetica Vite usa `MasterArchive`. Il bundle `app.js` e la shell `premium.html` sono verificati staticamente. Non sono aggiunti `hooks.py`, DocType, DocPerm, migrazioni, librerie Python/npm, Site, database, credenziali o servizi permanenti. Item, Patient e Practitioner standalone create restano bloccati; Payment Entry resta read-only nelle nuove API.

## Prove offline di questa HEAD

| Controllo | Esito |
|---|---|
| `python3 infra/premium_single_stack_package.py --source` | PASS |
| `python3 -m unittest discover -s tests -p 'test_premium_single_stack_package.py' -q` | 5 PASS: fonte, hash divergente, pin upstream/backend discordante, payload immagine mancante |
| `python3 -m unittest discover -s tests -p 'test_premium_scoped_api.py' -q` | 11 PASS con Frappe fake, nessuna prova DB reale |
| `npm run typecheck` / `npm run build` | PASS; Vite 8.3.5, bundle production aggiornato |
| `playwright.scoped.config.ts` | 28 PASS desktop/mobile, API intercettate |
| `playwright.config.ts` | 77 PASS + 1 SKIP intenzionale, preview sintetica |

Gli screenshot Playwright precedenti sono sintetici; il test live futuro salva screenshot in `test-results` fuori Git se configurato così dall'operatore. Nessun Docker build, container aggiuntivo, backup/restore o test Frappe reale è stato eseguito in questo ciclo.

## Suite Frappe da eseguire solo dopo gate

`frontend/premium/playwright.live.config.ts` e `tests/live.spec.ts` non intercettano HTTP. Richiedono URL locale `127.0.0.1`, `CC_PREMIUM_LIVE_SYNTHETIC=YES` e file fixture privato fuori Git con sette storageState sintetici, centro A/B, Item esclusivo A, Payment Entry e Sales Invoice sintetici. Coprono 7 identità + Guest, 11 liste, GET server-side, centro A/B, CSRF, campo extra, replay, audit, stampa, errori, read-only Payment Entry, p50/p95 API e screenshot desktop/mobile. Le write usano lo stesso valore `item_name` su Item sintetico e una chiave unica; registrano comunque un evento audit. Nessun dato reale o sessione viene salvato nel repository.

La suite #139 e `infra/integrated_acceptance.py` completano gli scenari operativi/finanziari e le negative security. Prima della UAT tecnica serviranno fixture che coprano 11 dettagli/form, note private, API native dirette, export, concorrenza, report, health/risorse/OOM, e confronto schema/permessi. La prova grafica Owner è separata. Fino a PASS reale: `NOT_VERIFIED` per import nell'immagine, autenticazione/CSRF/ACL sul Site, cgroup, prestazioni e restaurabilità.

## Unico gate Owner residuo

Seguire [SINGLE-STACK-EXECUTION-GATE-2026-10-21.md](SINGLE-STACK-EXECUTION-GATE-2026-10-21.md): ricontrollo fingerprint e override Compose privato, backup cifrato, prova restore isolata e rimossa dopo esito, build candidata con verificatore, sostituzione controllata dei **sei** container applicativi del solo `centrochange-dev`, test reali e rollback ai sei image ID originali se serve. MariaDB, Redis, Site, DB, quattro volumi nominati, rete e porta restano gli stessi. Nessun `migrate`, nuova auth, stack permanente, merge, cutover o produzione. L'Owner deve autorizzare quel piano materiale; le policy ancora chiuse restano raccolte in [SCOPED-API-DECISION-063-REPORT.md](SCOPED-API-DECISION-063-REPORT.md).
