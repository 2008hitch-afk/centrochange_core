# C109 R13 — safety stop durante la prima lettura del clone

**Esito:** `MISSION-C: PARTIAL/BLOCKED`; `OWNER_PREVIEW_AVAILABLE: NO`; `READY_FOR_OWNER_UAT: NO`. L'unica attivazione R13 autorizzata è consumata. Nessun retry.

## Autorizzazione e identità

L'Owner ha autorizzato R13 in chat il 2026-10-12. La [finestra è stata registrata sulla issue #109](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6119394904) prima della prima mutazione: 07:03–13:03 UTC per esecuzione/collaudo, 13:03–14:03 UTC solo per arresto/recupero, con hard stop automatico. PR #112 resta DRAFT. Harness R13 `8972be41b3e5bb6a31ed269de87f448fb0f6cb21`; applicazione `e2fd728ecf6acdb0e0ab26379820df6905dd5521`; immagine invariata `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. Nessuna build dell'applicazione.

Il progetto nuovo era `centrochange-c109-gated-r13`, con porta frontend privata `127.0.0.1:8113`, cap applicazione 2 GiB, QA 512 MiB e swap zero. Il percorso versionato mantiene i quattro guard, il lock writer, il monitor RC22, lo stop per OOM/memoria/disco/PSI memoria e il **limite PSI I/O ordinario**. Nessuna deroga R12 è stata riutilizzata. Sorgenti previste: cinque copie sintetiche R10 montate read-only; R12 è rimasto spento e preservato.

## Diagnosi mirata R12

Negli ultimi tre campioni R12 il PSI memoria host full era 1,44%, 5,12%, 2,81%, mentre il PSI memoria locale di ciascun cgroup R12 e QA era 0. L'uso aggregato R12+QA scendeva da circa 802 a 702 MiB e MemAvailable restava circa 4,84 GiB. La pressione campionata era esterna ai cgroup R12/QA; la telemetria non identifica il processo host esatto. Prima di R13: PSI memoria host 0, MemAvailable circa 5,4 GiB, solo i nove container RC22 running. Nessun laboratorio demo C109 superfluo attivo da arrestare.

## Esecuzione R13

- Preflight privato: HEAD pulita, manifest dei file R13 valido, immagine/label pinned, RC22 nove ID completi e HTTP 200, nessun workload C109 running, sorgente R10 con label C109. Quattro guard reali e lock writer avviati; rinnovo Docker osservato. Compose privata normalizzata: otto servizi e 2 GiB aggregati.
- Sono state create solo le due reti R13 e il primo volume destinazione `centrochange-c109-r13-c-fit-db-data`. Il helper di sola copia aveva cap 256 MiB/swap zero, cgroup verificato e sorgente R10 read-only.
- Durante il digest della **prima sorgente**, prima di `cp`, il helper ha letto circa 448.299.008 byte. Il PSI I/O host full ha raggiunto 1,92% contro il limite ordinario dell'1%; il watchdog ha scritto `safety-stop.json = ["IO_PSI"]`. Il gate sincrono ha rifiutato il proseguimento con `RuntimeError: host PSI full`.
- Stop mirato e `monitor-finish` alle 07:05:08 UTC. Nessun servizio applicativo R13, QA o browser è stato avviato. Nessun volume R13 è stato completato. Il volume parziale, le due reti e i log privati sono conservati; nessun volume storico è stato cancellato.
- Nove ID RC22 invariati; `/api/method/ping` HTTP 200 dopo lo stop. Nessun alert RC22 o evento protetto. OOM host invariato a 7, PSI memoria full massimo 0, MemAvailable minimo circa 5,28 GiB, uso helper massimo circa 250 MiB. Nessun container C109 running.

Test offline del delta: 80/80 test R12/R13 PASS; `compileall` e `git diff --check` PASS. Il codice R13 e la telemetria privata sono evidenza dello stop, non di una UI avviata. Le sei sezioni e le 24 aree restano `NOT TESTED` in R13. Lo screenshot Home R12 resta evidenza storica limitata e non rappresenta un'anteprima live.

## Decisione minima necessaria

Per una **nuova** attivazione occorre una decisione Owner specifica su una deroga temporanea al solo stop host **PSI I/O** durante clone e preview, con finestra e progetto nuovi, monitor RC22 indipendente e tutti gli altri guard invariati. La deroga R12 è scaduta e non viene rinnovata implicitamente. La soglia PSI memoria resta attiva; la decisione I/O non garantisce che una nuova preview raggiunga la Home. Nessun merge, cutover, intervento RC22, dato reale o accesso Owner è stato effettuato.
