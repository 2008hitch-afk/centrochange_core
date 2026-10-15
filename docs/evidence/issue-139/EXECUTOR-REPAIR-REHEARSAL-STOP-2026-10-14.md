# #139 — executor repair / rehearsal stop — 14/10/2026

**Esito: PARTIAL / rehearsal stop.** Nessun deploy, migrazione o riavvio del DEV. Il candidato applicativo resta `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`; la PR #140 resta DRAFT. Non richiedere ancora la finestra d'installazione.

## Correzione preparata

L'immagine pinned `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af` risolve `frappe` in UID 1000, GID 0 (`root`); il gruppo nominale `frappe` non esiste. `restore_backup()` usa ora `frappe:root` nei due comandi `chown` e si arresta prima di copiare file se l'identità Unix diverge. Due test nuovi coprono entrambi i percorsi di ownership e il blocco fail-closed. La modifica non tocca il sorgente applicativo.

Verifiche: 47 test Python offline PASS; sintassi e `git diff --check` PASS; `sudo -n python3 -I infra/issue139_install_gate.py --dry-run` PASS con nove servizi, sei hook, CSS #79 e fingerprint Owner/Communication invariati. SHA-256 dell'executor corretto in questa revisione: `e44be980328860fdaf250032e54219f3c6c0dba1380a7c34a9c67d27ba4b5970`.

## Rehearsal reale e arresto

La prova precedente del 14/10 aveva già dimostrato il restore nativo in clone isolato, con dati, schema, permessi, file, hook, HTTP e riavvio coerenti. Questa nuova prova doveva invocare **direttamente** `restore_backup()` dell'executor corretto. Backup completo e cifratura sono passati; il clone isolato è stato avviato. Il helper di rehearsal ha sostituito il nome del container nei comandi `docker exec`, ma non nella destinazione composta `container:path` di `docker cp`. L'executor ha quindi copiato un singolo file di backup sintetico nella directory privata di backup del DEV e il successivo `chown` sul clone ha fallito per file assente. Il restore dell'executor **non è stato completato** e non viene dichiarato PASS.

Il file inatteso era `restore-db.sql.gz`, SHA-256 `8e4f89faae768cf3967db4b0fb38fbca36563b637fca05f58306cf45f8ef431a`, 1.488.989 byte. Prima della rimozione è stata verificata la coincidenza esatta con il file prodotto dalla rehearsal e che fosse l'unico file nella directory di backup del DEV. È stato eliminato **solo** quel percorso. Il successivo preflight read-only è PASS: nove servizi invariati, Site e schema, sei hook, CSS #79 e fingerprint Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3` invariati. Nessun container, volume o network temporaneo della rehearsal resta attivo; la directory di backup DEV è di nuovo vuota.

I report raw e i backup sintetici della rehearsal sono privati sotto `~/.local/state/centrochange-single/issue139-restore-rehearsal/`, fuori Git. Nessuna credenziale o dump è pubblicata.

## Condizione successiva

Correggere il helper di clone affinché riscriva e verifichi **tutte** le forme di riferimento al container (`container` e `container:path`), con prova che nessun comando di restore possa indirizzare `centrochange-dev-*`. Solo dopo un nuovo gate operativo per la rehearsal ripetere il test end-to-end del vero `restore_backup()`. La finestra Owner di 4h+1h per l'installazione DEV resta non definita e non va richiesta prima di `EXECUTOR_REPAIR_PASS`.
