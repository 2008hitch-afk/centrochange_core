# C109 R12 — blocco statico del preflight prima di Docker

**Esito:** `MISSION-C: PARTIAL`; `C109_OWNER_PREVIEW_AVAILABLE: NO`. La singola attivazione R12 autorizzata **non è stata consumata**: nessuna root privata R12, rete, volume, container, copia o deroga PSI I/O è stata creata/avviata. Il controllo è stato interrotto prima della prima mutazione Docker, secondo il gate fail-closed.

## Identità e baseline read-only

PR #112 DRAFT alla HEAD autorizzata `6dee9463a747709bb8ec3c7c7549ce0d250544cb`, worktree pulito; dipendenza #107 DRAFT `d50299f8d9ad32640259ff1c3a1fded47db5c447`. Immagine locale `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`, label applicativa `e2fd728ecf6acdb0e0ab26379820df6905dd5521`. I 99 test offline precedenti erano PASS, ma il test simulava il guard e non eseguiva il suo script privato reale.

Al 2026-10-11 21:56 UTC: RC22 aveva nove container **in esecuzione** e ping HTTP 200 (circa 20 ms); nessun C109 attivo. MemAvailable circa 5,5 GiB, disco libero circa 43 GiB, swap zero, PSI I/O/memoria full avg10 0%. Le cinque copie R10 etichettate C109 sono presenti e il report di recupero R10 le dichiara verificate. Nessuna scrittura o test funzionale è stata eseguita su RC22.

## Incompatibilità accertata

`infra/c109_r12_preflight.py:83-91` acquisisce e trattiene fino alla conclusione il lock esclusivo `/run/user/1000/centrochange-docker-writer.lock`; all'interno chiama `launch_scopes()`. Per il ruolo `watchdog`, `infra/c109_guard_access.py` avvia un **processo systemd scope distinto** che esegue `app-run/safety.py`. Il `safety.py` privato conservato da R10 acquisisce **lo stesso lock** con `fcntl.flock(LOCK_EX|LOCK_NB)` alla riga 2. Poiché il launcher lo detiene già in un processo distinto, il watchdog fallirebbe prima di produrre heartbeat e il launcher fermerebbe il preflight. Il test integrato simula `launch_scopes()` e non ha attraversato questa acquisizione reale. Non è una prova che Docker o RC22 siano guasti; è un conflitto deterministico tra due componenti della procedura prevista.

È emersa anche una lacuna nello stop del helper di copia: `infra/c109_r12_resources.py` lo etichetta con `com.docker.compose.project=centrochange-c109-gated-r12`, mentre `safety.py:stop()` seleziona soltanto `centrochange.mission=C109`. Il loop sincrono del launcher controlla i guard e rimuove il helper in caso di errore, ma il watchdog indipendente non può arrestarlo direttamente se il launcher rimane bloccato. Gli otto servizi applicativi hanno invece la label missione. Questo va corretto prima di una copia sotto guard, senza allargare il target di stop a RC22.

## Delta minimo da verificare offline

1. Separare in modo versionato il lock del writer del launcher da quello di esclusività del watchdog, preservando un solo writer Docker e la continuità dei quattro guard. Non eliminare nessuno dei due controlli. Il `safety.py` R12 privato deve essere generato/verificato da codice versionato, non patchato nel runtime.
2. Etichettare il helper R12 anche `centrochange.mission=C109` e verificarne esattamente progetto/missione prima del rilascio. Il watchdog potrà così fermare il solo helper C109 in uno stop di sicurezza.
3. Ampliare il test integrato affinché esegua la logica reale di lock/avvio del watchdog privato in processi isolati simulati e verifichi l'arresto mirato del helper. Aggiornare il manifest SHA-256 e la HEAD; i 99 PASS storici non bastano per il nuovo contratto.

**Prossimo gate:** autorizzazione Owner a questa correzione offline mirata, seguita da nuova review/approvazione della HEAD risultante prima di qualunque attivazione. L'approvazione R12 corrente non è stata estesa automaticamente al codice corretto. Nessun merge, cutover o `READY_FOR_OWNER_UAT`.
