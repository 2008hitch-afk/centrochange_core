# #148 / DECISION-064 — correzione recuperabilità e regressioni

**Stato: BLOCKED_SAFE_ROLLBACK · PR #150 DRAFT · verifica offline.** Questo report integra, senza sostituire, `DECISION-064-EXECUTION-REPORT-2026-10-21.md`. Nessuna operazione runtime sul DEV, restore reale, deploy, merge o cleanup in questo ciclo. I due checkpoint cifrati e le chiavi preesistenti sono preservati, ma restano `FAIL_FULL_SITE_RESTORE` perché non contengono `private/uat`.

## Correzioni effettive

- `infra/premium_single_backup.py` conserva ora i quattro artefatti nativi Frappe **e** `site-tree.tar` dell'intero volume `sites` **e** `site-manifest.json`. Due scansioni dirette del Site originale nel container e due letture tar devono coincidere; ogni differenza interrompe il checkpoint. Il manifest privato resta dentro l'archivio cifrato. L'inventario esterno contiene solo classi, dimensioni e hash dei sei componenti.
- `infra/premium_site_checkpoint.py` valida SHA-256 di ogni file, presenza di file e directory vuote, mode/UID/GID e link. Richiede esplicitamente `apps.json`, `apps.txt`, `common_site_config.json`, `site_config.json` e `private/uat/demo.json`; qualsiasi altro elemento presente nel manifest originale è ugualmente obbligatorio. Rifiuta path assoluti, `..`, duplicati, hardlink, device/special file e symlink non approvati. L'unico link ammesso è `sites/assets` verso il target pinned dell'immagine. La verifica dell'archivio esterno rifiuta il vecchio bundle a quattro componenti. Il comando `verify-encrypted` confronta l'hash del ciphertext, decritta in directory privata temporanea e verifica i sei componenti e il Site. `extract` agisce solo su destinazione isolata vuota; `verify-tree` confronta il ripristinato con l'originale.
- Le regressioni API/UI coprono `cmd` POST esatto senza mass assignment, risultati Patient autorizzati ma vuoti, selettore Agenda univoco e richiesta Payment Entry di 90 giorni. Nessun ruolo o permesso è stato ampliato.

## Inventario completo del Site corrente, sola lettura

Volume `centrochange-dev-sites`, mount `/home/frappe/frappe-bench/sites`, Site `centrochange.local`: **54 elementi sotto la root** (40 file, 13 directory, 1 symlink), **55 incluso la root `sites`**; **1.236.393 byte** di file nel momento dell'inventario. La lista integrale di nomi/dimensioni/hash è stata calcolata nel container senza leggere contenuti nei log; i nomi di allegati e valori privati non vengono riportati qui. Il nuovo checkpoint genera il manifest integrale cifrato al momento del freeze; l'inventario corrente non può certificare un futuro stato immutato.

| Gruppo | Presenza osservata | Trattamento nel restore |
|---|---:|---|
| Configurazione Bench/Site: `apps.json`, `apps.txt`, `common_site_config.json`, `site_config.json` | 4 file | Indispensabili; byte/hash, mode e owner esatti; config e segreti solo nel cifrato |
| `private/uat/demo.json` | 1 file, 3.367 byte | Indispensabile: manifest fixture e credenziali sintetiche; assenza blocca PASS_RESTORE |
| `private/uat/demo.lock` | 1 file vuoto | Stato di lock temporaneo, incluso e verificato; nessuna eliminazione implicita |
| `private/files` | 15 allegati, 16.384 byte | Indispensabili; tutti inclusi nel Site tar e nei tar nativi; confronto SHA |
| `builder_analytics.duckdb` | 1 file, 274.432 byte | Potenziale stato Builder unico; trattato come indispensabile finché ricostruibilità non dimostrata |
| `touched_tables.json` | 1 file, 467 byte | Stato Frappe relativo alle tabelle; trattato come indispensabile |
| `indexes/web_routes` | 3 file, 37.670 byte, incluso `MAIN_WRITELOCK` vuoto | Indice potenzialmente ricostruibile, lock temporaneo; entrambi inclusi e confrontati allo snapshot. Nessuna rigenerazione assunta per PASS |
| `logs` dentro Site | 14 file, 902.487 byte, inclusi zero-byte | Log operativi, non necessari per il rendering ma evidenza unica; inclusi e confrontati prima di avviare restore. Dopo avvio runner possono crescere: confronto post-restore esclude soltanto differenze di log, conservando lo snapshot originale cifrato |
| `public/files`, `private/backups`, `locks`, directory pagine | directory vuote osservate | Incluse con nomi, mode e owner; la loro assenza nel restore fallisce |
| `sites/assets` | 1 symlink assoluto verso `/home/frappe/frappe-bench/assets` | Output build ricostruibile **solo** da immagine pinned; il link esatto e il target immagine sono verificati, altri link rifiutati |

Il volume separato dei log di Bench, montato su `/home/frappe/frappe-bench/logs`, non fa parte del Site volume: è preservato nel DEV e non rimosso. Non è stata dimostrata una recovery completa dell'intero host; questo piano copre Site applicativo e database. I permessi originali sono preservati; nessun `chmod` sul DEV è stato eseguito. La directory temporanea dei segreti di checkpoint usa `0700`, i file chiave/inventario `0600`.

## Verifiche offline

| Prova | Esito |
|---|---|
| Test Python di recovery e API scoped, incluso errore storico quattro componenti, file UAT mancante, qualsiasi file inventariato mancante, hash alterato, traversal del Site/tar nativo/bundle esterno, link/hardlink, cifratura e `cmd` | **24 PASS** |
| Playwright sintetico regressione Agenda e intervallo Payment Entry, 1440×900 e 390×844 | **2 PASS** |
| Typecheck React | **PASS** |
| Manifest sorgente completo contro codice app/React pinned | **PASS** |
| Immagine `sha256:a7921c5143e5294fa4a6849455a51b67eb4b3a41331832000254db252d409fa2` in container effimero isolato, app/API/versioni/asset | **PASS** |
| Nuovo checkpoint reale cifrato e restore isolato con `private/uat` | **NOT_VERIFIED**; richiede nuovo gate Owner |
| Quattro regressioni su Frappe live corretto, ruoli/centri, UAT completa e prestazioni | **NOT_VERIFIED** |

La HEAD corrente non modifica file `app/centrochange_core`, sorgenti React, lockfile, Dockerfile full o manifest rispetto al commit immagine `eec7efd1237489ee1aa72fe1c50fe32f49b3e80f`: modifiche solo a tooling recovery, test e documentazione. Perciò **nessun rebuild** dell'immagine app è necessario in questo ciclo. Un controllo read-only finale conferma il DEV sull'immagine precedente `sha256:6d6f9d2e65d0b16974e6b04aeaaf6d1210f071448ace5276689ebc9652bc2f7b`, con nove servizi, zero container restore attivi e `cc_premium_primary=0`; nessun nuovo test live è stato eseguito.

## Secondo tentativo e gate Owner unico

La procedura completa è nella sezione «Recovery completa» di `SINGLE-STACK-COMPLETE-REBUILD-EXECUTION-PLAN.md`. Il nuovo gate deve nominare **solo**: project `centrochange-dev`, Site `centrochange.local`, DB `_4f614b4543aa5230`, sei processi app da ricreare condizionatamente, quattro volumi DEV da preservare, immagine candidata ID completo sopra e precedente ID completo, due checkpoint/chiavi da preservare, nuovi checkpoint/chiave privati, quattro container restore `cc148-restore-{db,runner,redis-cache,redis-queue}`, due volumi `cc148-restore-{db-data,sites}` e rete interna `cc148-restore-net`. Nessun secondo stack permanente, no migrate, no reset, no attivazione UI primaria.

**Autorizzazione richiesta all'Owner:** un nuovo tentativo condizionato con preflight, freeze ≤120 minuti, nuovo backup completo cifrato, decrittazione/verifica, restore reale isolato e confronto Site+DB, poi soltanto se `PASS_RESTORE` e gli altri gate sono PASS ricreazione dei sei container app nell'unico DEV e collaudo live integrale. Su qualsiasi discrepanza di file, schema, sicurezza, segreti, OOM/PSI, configurazione o finestra: STOP e rollback soltanto se dimostrato sicuro. Le risorse restore temporanee vanno rimosse per ID dopo evidenza; backup/chiavi/immagine precedente restano. L'approvazione DECISION-064 del primo ciclo non autorizza automaticamente questo secondo tentativo.

`PASS_RESTORE` reale, `FRAPPE_LIVE_QA_PASS` e `READY_FOR_OWNER_VISUAL_UAT` **non sono dichiarati**. L'URL privato Owner e l'attivazione `cc_premium_primary=1` restano sospesi fino alle prove e alla distinta accettazione grafica.
