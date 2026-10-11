# Missione C #109 — accesso Docker dei guard C109

**Esito: `DOCKER_GUARD_ACCESS_READY` per il preflight e launcher offline.** Nessuna nuova attivazione C109, immagine importata, container creato o workload rilasciato. La demo Owner resta indisponibile fino a distinta autorizzazione.

## Causa verificata

Il socket Docker è `/var/run/docker.sock`, `root:docker`, modalità `0660`; il contesto CLI effettivo è `default` su `unix:///var/run/docker.sock`. La shell operativa appartiene al gruppo primario `docker` (GID 986), mentre il gestore `systemd --user` già avviato ha gruppo primario dell'utente (GID 1000) e non include GID 986 nei gruppi supplementari. Le precedenti unità transitorie `.service` ereditavano quindi credenziali prive di accesso al socket. Il journal mostrava `permission denied` per entrambi i monitor prima del primo `docker load`/`docker create`; l'evento fail-closed resta registrato in `C109-VISUAL-DEMO-STOP-2026-10-11.md`.

Una prova read-only in `.service` ha fallito esplicitamente `Docker socket unavailable to effective groups`. Tre prove read-only in `.scope`, lanciate dalla shell già autorizzata, hanno raggiunto Docker: `docker version`, `docker ps`, e — per il monitor eventi — una sottoscrizione `docker events` rimasta connessa fino al timeout locale. Due prove in scope con script inerti temporanei hanno inoltre eseguito il percorso reale `serve` di *events* e *watchdog*, creando i rispettivi marker di accesso dopo il controllo Docker. Nessun gruppo, permesso socket, daemon o contesto Docker globale è stato modificato.

## Correzione versionata

- `infra/c109_guard_access.py` lancia i guard esclusivamente in scope systemd utente ereditati dal chiamante Docker-autorizzato. Il preflight verifica nei medesimi scope utente, gruppo/socket, `DOCKER_HOST`, `DOCKER_CONTEXT`, endpoint, API e stream eventi. Il processo di ciascun guard verifica nuovamente l'accesso **nel proprio scope**, registra PID e start time, poi esegue lo script storico senza modificarlo.
- `infra/c109_gated_start.py` richiede i tre marker di processi vivi e la prova recente **prima** del marker `app-attempted` e della prima mutazione Docker; il guard continuo rifiuta processi terminati o PID riutilizzati. I heartbeat, PSI, OOM, RAM, disco, RC22 e limiti cgroup preesistenti restano attivi.
- `infra/c109_demo_expiry.py` può attendere la scadenza dentro uno scope con accesso Docker verificato; il watchdog indipendente mantiene anch'esso il controllo `HARD_DEADLINE`. Un fallimento durante l'avvio degli scope arresta soltanto gli scope avviati e non avvia C109.

Nella futura finestra **separatamente autorizzata**, il percorso è `python3 infra/c109_guard_access.py preflight`, quindi `python3 infra/c109_guard_access.py launch PRIVATE_ROOT`, verifica dei tre processi/heartbeat/alert, e soltanto allora il bootstrap già protetto. Non riutilizzare la precedente attivazione consumata. Non usare le unità `.service` del vecchio tentativo per i guard Docker.

## Verifica e limiti

- Test offline C109: **44/44 PASS**, inclusi override di `DOCKER_HOST`/contesto non consentiti, stream eventi non disponibile, ruolo sconosciuto, marker stantio/PID riutilizzato e rifiuto di una attivazione già consumata. Sintassi Python e `git diff --check`: PASS.
- Prove read-only effettive: `.service` DENIED, `.scope` Docker API/event stream ALLOWED, due `serve` inerti ALLOWED. Il launcher completo con i guard storici, il timer a scadenza e la demo non sono stati avviati: rimangono da verificare nella prossima singola attivazione autorizzata, senza chiamarli PASS ora.
- Stato finale read-only: progetto C109 R4 **0** container attivi; RC22 **9/9** container e HTTP **200**. Nessuna modifica a RC22, UAT o ai dati.
