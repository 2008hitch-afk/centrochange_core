# CENTROCHANGE-MVP-LIVE-FUNCTIONAL-VALIDATION-REPORT

## Aggiornamento finale — 2026-10-19

**Esito dell'unico aggiornamento DEV autorizzato: `ROLLED_BACK` con recupero verificato.** Chromium è stato riparato nell'ambiente QA con sole dipendenze runtime mancanti; l'immagine candidata ha superato 128/128 route read-only, 22/22 verifiche List/Form desktop/mobile, Administrator, asset e Socket.IO. La prima preparazione del flusso finanziario si è fermata prima del test POS per un valore Enum non valido nella fixture nativa `Mode of Payment`. La fixture ha eseguito cleanup PASS; l'executor ha ripristinato il backup verificato e tutti i nove servizi sono tornati alla baseline.

### Chromium

Ambiente QA Ubuntu 26.04, utente `empv26`, Node/Playwright `1.58.2`, Chromium headless shell `1208`. `ldd` dopo l'installazione mirata non mostra librerie mancanti. Nelle stesse variabili (`NODE_PATH`, `LD_LIBRARY_PATH`, `HOME`, `PATH`) e con la stessa regola di risoluzione host dell'executor, Chromium ha aperto `/login` su `centrochange.local:8082` (HTTP 200), ha trovato il form, ha salvato uno screenshot privato e si è chiuso correttamente. APT ha installato soltanto i pacchetti runtime richiesti e tre dipendenze dirette; 0 aggiornati, 0 rimossi. Nessun servizio/container ha richiesto restart.

### Diagnosi del fallimento finanziario

La catena di eccezione sanitizzata del fixture identifica `frappe.exceptions.ValidationError` durante `Mode of Payment.insert()` in `prepare_browser_invoice`. Il candidato impostava `type="Credit Card"`. Il DocType `Mode of Payment` dell'ERPNext `16.50.0` effettivamente installato espone le opzioni `Cash`, `Bank`, `General`, `Phone`; la documentazione ERPNext descrive il campo come categoria del metodo e chiarisce che il conto mappato/il Payment Entry determinano la registrazione contabile. Il metodo si chiama `CC-HTTP-… BROWSER POS`, ma il campo di classificazione deve essere il tipo del conto selezionato (`Bank` o `Cash`). La prova ha fallito prima che la fattura browser fosse creata e prima del POS.

La fixture temporanea è stata recuperata con `cleanup: PASS`. La correzione locale non installata, commit `0b03f1f85267cf707316c82ffa7300a2e3bd135e`, aggiunge `_mode_of_payment_type_for_account()`, ricava il tipo dal conto reale sintetico e rifiuta conti non Bank/Cash; entrambi i punti di creazione del metodo POS ora lo usano. La regressione offline impedisce di reintrodurre `Credit Card` come Enum e verifica che entrambi i fixture ricavino il valore dal conto. Fonti: [documentazione ufficiale ERPNext Mode of Payment](https://docs.frappe.io/erpnext/mode-of-payment); schema runtime pinned letto dal container Frappe/ERPNext 16.50.0.

### Installazione, prove e recupero

- Branch locale `audit/mvp-functional-completion`; PR #141/#140 restano DRAFT e non sono state aggiornate su GitHub.
- HEAD dell'executor al momento dell'unico aggiornamento: `09e1cad00320bd1456d204a98b56e1680d9dc0e2`; SHA-256 executor `933ab9698e02d529a544667dbfdbc2a958e02a22100540cd3f4dccc39a496e06`.
- Candidato installato per la prova: `d41ac305c6c5f86c37fd0b64e4e588255c467478`; immagine costruita `sha256:3fdc9a94d985fb9971dfc4c45d18dacc7be63db3da56de207bd3fd0f4465996a` (non attiva dopo il rollback).
- Run privato `20261019T082643Z-2882304`. Gate privato: 08:25:40–12:25:40 UTC operativa, recupero fino alle 13:25:40 UTC.
- Preflight attuale `DRY_RUN_PASS`: 9 servizi, un Site, Centro A attivo, Centro B inattivo, sei hook/guard, CSS #79 e cache asset corretti; schema, permessi e configurazione coerenti.
- Backup privato cifrato verificato di database, file pubblici, file privati e `site_config.json`; SHA-256 e decifratura/formato verificati dall'executor. Rollback `rollback_failure: null`.
- Postcheck: 9/9 servizi running sulla baseline `centrochange-single:issue139-realtime-v2`; DB e Redis healthy; `/api/method/ping` HTTP 200; fingerprint Owner `caba48b14430cd975213fde6273aada780aecd6e6604ad4fbb5ccda8bfc4eae0`, Communication `a13e25cf97b4bfa76856038614ec3e99380c086fc83c322db0958490ff19ac81`, schema e permessi invariati. Centro A/B restano rispettivamente operativo/inattivo.
- L'immagine residua dell'esecuzione precedente, inattiva e senza container dipendenti (`sha256:737d351e…`), è stata conservata con un tag d'archivio; nessun layer è stato cancellato. La nuova immagine candidata di questo tentativo resta non attiva.

### Risultati effettivi delle capability

| Gruppo | Esito effettivo |
|---|---|
| 40 capability precedentemente PASS | PASS storico conservato dall'audit; non dichiarato come nuovo PASS live in questo aggiornamento |
| POS / CC-CAP-042 | PARTIAL — preparazione fattura fallita per Enum fixture non valido; cleanup e rollback PASS; nessun test POS o saldo eseguito |
| Libro giornale / Bilancio di verifica — CC-CAP-047 | PARTIAL/BLOCKED — test nativo non avviato dopo il fallimento precedente |
| Allegati amministrativi — SCOPE-DOC | PARTIAL/BLOCKED — upload/download/permessi non avviati |
| Localizzazione ed export — CC-CAP-029 | PARTIAL/BLOCKED — export non avviato; le route della webapp sono state renderizzate |
| Fixture e suite aggiornate — CC-CAP-050 | PARTIAL — 79 test offline PASS dopo la correzione locale; preparazione live fallita ma cleanup esatto PASS; suite backend di sicurezza 38 controlli non avviata |
| Ruoli/browser/mobile — UAT-GLOBAL | PARTIAL — W5 read-only 128/128 e List/Form 22/22 PASS su candidato; operazioni browser con salvataggi non eseguite |

Il fix POS è **solo nel worktree locale** dopo il rollback, non installato. Sono stati rieseguiti `python3 -I -m unittest discover -s infra/tests -p 'test_*.py'` (79/79 PASS), `compileall`, `node --check infra/browser/finance.cjs` e `git diff --check` (PASS). Non è stata eseguita una seconda installazione. Pertanto nessuna delle sei voci PARTIAL diventa PASS funzionale in questo risultato: il conteggio resta 40/46 PASS con sei non verificate/completate; i 38 test sicurezza live, POS, GL/TB, allegati ed export non sono stati raggiunti.

**Prossimo gate minimo:** una nuova autorizzazione Owner per un singolo aggiornamento del candidato corretto, necessaria perché l'unico aggiornamento autorizzato è stato consumato e ripristinato. Nessun merge, produzione o GOAL-03.

## Esito del tentativo precedente (08:05 UTC)

**Esito del precedente singolo aggiornamento autorizzato: `ROLLED_BACK`.** Il candidato è stato costruito, avviato e ha superato i controlli asset e Socket.IO. La suite browser W5 non è partita: Chromium non caricava otto librerie di sistema mancanti nella directory QA temporanea. L'executor ha eseguito il rollback previsto e verificato. Nessun fixture funzionale è stato creato nel tentativo precedente.

## Risultato

- **DEV aggiornato:** NO; baseline precedente ripristinata e accessibile.
- **MVP dimostrato:** 40/46 PASS storici; 6/46 PARTIAL. Le sei correzioni restano non verificate funzionalmente live.
- **Sei lacune risolte e verificate:** 0/6 in questo tentativo.
- **Regressioni del candidato:** BLOCKED dalla dipendenza Chromium assente; nessuna regressione prodotto osservata nei controlli precedenti alla suite.
- **Secondo aggiornamento:** non eseguito.

## Baseline e candidate

- Branch: `audit/mvp-functional-completion`.
- Candidate applicativo immutato: `d41ac305c6c5f86c37fd0b64e4e588255c467478` (20 file applicativi); nessun delta #78/#128.
- Immagine DEV di baseline prima e dopo: `sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc`, sorgente `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`.
- Immagine candidata costruita: `sha256:737d351ef46890aa2a884f08fa9ed2701e47fb63742602414a72e95e28013a5c`; non è rimasta in esecuzione.
- Executor usato per il singolo tentativo: SHA-256 `da6f1adf2b63399e82d872261277d430f7e6f60bb7ef5fc4c7a093492d5752fc`.
- Run privato: `20261019T080512Z-2857766`; autorizzazione e gate privati registrati prima dell'arresto applicativo.
- Finestra registrata: 08:05:06–12:05:06 UTC operativa, fino alle 13:05:06 UTC per recupero.

## Causa del blocco e correzione preventiva

L'errore Chromium acquisito è `Target page, context or browser has been closed`; il messaggio sottostante mostra che il processo headless non poteva caricare `libnspr4.so`. La verifica `ldd` eseguita con lo stesso utente e lo stesso `LD_LIBRARY_PATH` del runner ha identificato otto librerie mancanti: `libnspr4.so`, `libnss3.so`, `libnssutil3.so`, `libatk-1.0.so.0`, `libatk-bridge-2.0.so.0`, `libatspi.so.0`, `libXdamage.so.1`, `libasound.so.2`. Il requisito del vecchio preflight controllava soltanto l'esistenza del pacchetto Playwright e dell'eseguibile Chromium, perciò il difetto infrastrutturale del runner è emerso dopo lo switch.

L'executor aggiornato ora controlla versione Playwright e dipendenze condivise Chromium con `ldd` prima di fermare qualunque servizio. I test provano il fallimento chiuso se una libreria manca. Il preflight attuale termina con `BLOCKED` e l'elenco delle librerie, senza toccare il runtime. Non sono state installate librerie di sistema.

Il precedente problema GPG dell'utility `infra/dev_backup.py` era distinto: la home GPG annidata nel percorso di stato privato produceva un socket `S.gpg-agent` oltre il limite Unix. Il helper crea ora una home temporanea breve `/tmp/ccg-*`, considera non-zero un vero errore GPG, redige i percorsi privati e verifica output cifrato e decifrato byte per byte. Due test GPG sintetici passano.

## Aggiornamento, backup e rollback

Il backup nativo del run comprende database, file pubblici, file privati e configurazione. Tutti e quattro gli artefatti cifrati sono stati decifrati in memoria dopo il run e hanno superato SHA-256 e controllo formato (`gzip`, `tar.gz`, JSON). Nessuna password o chiave è inclusa in questo report. Non è stato necessario ripristinare il database durante il rollback: la suite non ha raggiunto la fase mutativa dei fixture e il fingerprint era invariato. La procedura completa di restore dell'executor era già stata provata nella rehearsal isolata precedente; questo run non costituisce una nuova prova di restore DB.

Esito rollback: `ROLLED_BACK`, `rollback_failure: null`. I nove servizi sono nuovamente attivi; i sei servizi applicativi puntano alla baseline attesa, DB/Redis sono `healthy`, gli hook restano sei, il Site rimane unico e `/api/method/ping` risponde `200`. Fingerprint dati prima/dopo: `caba48b14430cd975213fde6273aada780aecd6e6604ad4fbb5ccda8bfc4eae0`; Communication: `a13e25cf97b4bfa76856038614ec3e99380c086fc83c322db0958490ff19ac81`; 137 eventi audit. Il controllo read-only successivo al rollback ha confermato gli stessi valori.

Il Compose source temporaneo mancante è stato ricostruito esclusivamente da tre file versionati con hash già pinati dall'executor. Playwright 1.58.2 è stato ripristinato nell'area QA temporanea da `package-lock.json`, senza modificare l'app DEV. I servizi e il database non sono stati modificati da queste operazioni.

## Controlli live raggiunti

| Controllo | Esito |
|---|---|
| Preflight iniziale baseline, nove servizi, Site/dati, sei hook, Centro A attivo e Centro B inattivo | PASS |
| Backup cifrato dei quattro componenti, digest e decifratura | PASS |
| Immagine candidata: sorgente, layer e hash dei 20 file applicativi | PASS |
| Asset manifest e asset diretti | PASS — 69 mapping, 3 file diretti |
| Socket.IO | PASS — porte pubblica/interna 8082/8080; Origin ammessi 200, mismatch/estranei 403 |
| Browser route sweep 128 | BLOCKED prima della prima route; Chromium non carica librerie |
| 22 test native List/Form | BLOCKED — runner browser non disponibile |
| POS, report GL/TB, allegati, export/localizzazione, suite fixture/sicurezza | BLOCKED — non avviati; nessun fixture creato |
| Integrità dati e rollback | PASS — fingerprint, configurazione, schema, permessi, hook e immagini ripristinati |

Le 128 route e le 22 coppie List/Form già passate sul candidato nell'esecuzione precedente restano evidenza storica; non sono state ripetute qui. Il fallimento odierno è nell'avvio del browser, prima delle asserzioni applicative.

## Stato delle sei capability

| Capability | Stato | Evidenza di questo tentativo |
|---|---|---|
| CC-CAP-029 — export e localizzazione | PARTIAL | download/valori live non raggiunti |
| CC-CAP-042 — pagamento carta/POS e saldo | PARTIAL | fixture fattura e azione POS non avviate; cleanup POS esiste nel candidate, non eseguito live |
| CC-CAP-047 — Libro giornale e Bilancio di verifica | PARTIAL | report non avviati |
| CC-CAP-050 — fixture/test obsoleti | PARTIAL | 78 test offline passano; suite Frappe live non avviata |
| SCOPE-DOC — allegati amministrativi privati | PARTIAL | upload/download e permessi non avviati |
| UAT-GLOBAL — localizzazione/mobile | PARTIAL | precedenti route/List/Form conservati; browser corrente bloccato prima del rendering |

## Modifiche e verifiche versionate

- `dcd1c31869019b44cedc7e1306a55b3d2ee6a4b7` — fix GPG, test crittografici sintetici e fixture Compose del test resa deterministica.
- `8017389de6ab342b0c5b50173296e5b03ab7410c` — executor pinna anche `infra/fixture_command.py`.
- `07a3c35a2ac2869ffb18bdf9d3963297553de468` — preflight Chromium `ldd` fail-closed e test positivi/negativi.
- SHA-256 executor aggiornato: `933ab9698e02d529a544667dbfdbc2a958e02a22100540cd3f4dccc39a496e06`.
- `python3 -I -m unittest discover -s infra/tests -p 'test_*.py'`: 78/78 PASS.
- `compileall` e `git diff --check`: PASS.
- Il dry-run iniziale prima dello switch era PASS. Dopo il fix preflight, il dry-run è intenzionalmente `BLOCKED` per le otto librerie assenti; non è stato eseguito un secondo install.

## Conclusione

Il candidate applicativo contiene le sei implementazioni previste, ma questo unico aggiornamento è stato ripristinato prima dei test funzionali. Stato operativo finale: **baseline accessibile; 40/46 PASS storici e sei PARTIAL; nessun PASS funzionale aggiunto**. Non è dimostrato un difetto applicativo POS o di altra capability. Il solo impedimento concreto è il runtime Chromium QA privo delle librerie elencate. Nessuna nuova installazione è stata avviata.
