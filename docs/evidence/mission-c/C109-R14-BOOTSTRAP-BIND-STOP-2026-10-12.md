# C109 R14 — avvio fermato dal bind del gate PID1

**Esito:** `MISSION-C: PARTIAL/BLOCKED`; `OWNER_PREVIEW_AVAILABLE: NO`; `READY_FOR_OWNER_UAT: NO`. La singola attivazione R14 è conclusa, senza retry.

## Autorizzazione e finestra

L'Owner ha autorizzato in chat una nuova singola R14 e la deroga temporanea al solo stop PSI I/O host. La [finestra](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6119596108) è stata registrata prima della prima mutazione: 2026-10-12 07:18–13:18 UTC per esecuzione/collaudo, fino alle 14:18 UTC solo per arresto/recupero. Harness `e905d2f04c1846777921a302ea5941daa9634d89`, applicazione `e2fd728ecf6acdb0e0ab26379820df6905dd5521`, immagine invariata `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. PR #112 resta DRAFT.

## Esecuzione osservata

- Quattro guard, rinnovo Docker, lock writer, monitor RC22 e watchdog erano attivi. Le cinque copie isolate R14 da sorgenti sintetiche R10 read-only hanno superato il confronto dei digest. Il progetto isolato aveva otto servizi, 2 GiB complessivi, QA previsto 512 MiB, swap zero e porta privata `127.0.0.1:8114`.
- `c-fit-db` è stato creato con cap 512 MiB/swap zero e rilasciato dal gate host alle 07:21:10 UTC. Dopo 90 secondi non era healthy. Healthcheck: `Can't connect to local server through socket '/run/mysqld/mysqld.sock' (2)`. Il launcher ha registrato `service health timeout: c-fit-db`, ha fermato il solo container R14 e scritto `monitor-finish` alle 07:22:51 UTC. Nessun altro servizio applicativo né QA/browser è stato avviato.
- Diagnosi deterministica: Compose aveva montato `/cc-bootstrap` dal percorso `/home/empv26/.local/state/centrochange-c109-final-r14-20261011/gates/c-fit-db`, mentre il launcher scriveva `release` in `/tmp/centrochange-c109-final-r14-20261012/gates/c-fit-db`. La normalizzazione del Compose conferma il percorso errato. Il container è rimasto nel PID1 inattivo, senza avviare MariaDB; il file `release` esiste solo nel percorso del launcher. La preparazione privata aveva sostituito `r12` con `r14` prima della sostituzione della directory sorgente, perciò il bind non è stato aggiornato. Non è una prova di corruzione DB.
- Nessun `safety-stop.json` né alert RC22/eventi protetti. PSI memoria full massimo 0,18%, PSI I/O full massimo 5,05% **misurato sotto la deroga R14**, MemAvailable minimo circa 5,15 GiB; nessun nuovo OOM. Dopo lo stop: nessun container C109 running, nove ID RC22 invariati e ping HTTP 200. Volumi, reti, container fermati e log R14 sono conservati; nessun volume storico cancellato.

## Correzione offline

Il preflight versionato ora confronta i bind normalizzati `/cc-bootstrap` e `/opt/cc-bootstrap.sh` con le directory e lo script effettivi **prima** dei guard e li ricontrolla prima del gate applicativo. Sul Compose R14 conservato il controllo produce `R14 bootstrap bind differs from release path: c-fit-db`. Il nuovo caso negativo e i test mirati R14 passano **41/41**, con `compileall` e `git diff --check` PASS. Questa correzione non riavvia R14 e non rende disponibile la UI.

## Decisione successiva

Per raggiungere l'anteprima serve una **nuova autorizzazione Owner** per una distinta singola attivazione, con nuovo progetto/finestra e una nuova decisione esplicita sulla deroga PSI I/O; quella R14 è conclusa. Il percorso di preparazione deve produrre bind verificati prima di creare risorse. Non sono stati eseguiti merge, cutover, interventi RC22, dati reali o traffico provider reale. Le sei sezioni e le 24 aree restano `NOT TESTED` in R14; non esiste URL Owner live.
