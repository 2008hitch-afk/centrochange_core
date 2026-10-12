# C109 R12 — correzione offline dei guard di sicurezza

**Esito:** `C109_R12_SECURITY_FIX_OFFLINE_READY`. Si tratta esclusivamente di verifica offline: R12 non è stato avviato, la UI non è stata collaudata in questa revisione e nessuna nuova autorizzazione runtime è implicita.

## Baseline e cause

La correzione parte dalla PR #112 DRAFT, HEAD `aca949a116e8a4bd093ded09599b6b7efacd093e`, dipendente dalla PR #107 DRAFT. Restano invariati il codice applicativo `e2fd728ecf6acdb0e0ab26379820df6905dd5521` e l'immagine OCI dichiarata `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`; l'immagine non è stata rieseguita. I precedenti 99 test offline non esercitavano il lock del watchdog in un processo distinto.

Il launcher R12 deteneva il lock Docker per tutta la procedura e poi avviava il watchdog in uno scope separato. Il watchdog tentava di acquisire lo stesso lock esclusivo: contesa deterministica prima del suo heartbeat. Inoltre il helper di copia aveva soltanto la label di progetto; lo stop indipendente del watchdog cercava la label di missione e non poteva includerlo.

## Correzione versionata

- `infra/c109_r12_writer.py`: il launcher verifica la disponibilità del lock e lo rilascia **prima** di avviare i guard. Il watchdog indipendente lo acquisisce e lo mantiene per l'attivazione. Il launcher richiede prima di ogni fase mutativa una lease con PID/start ticks del watchdog vivo, file di lock invariato e lock realmente detenuto. La contesa o la perdita della lease blocca il rilascio del workload.
- `infra/c109_r12_safety.py` e `infra/c109_r12_safety_prepare.py`: lo script privato `app-run/safety.py` viene installato atomicamente da sorgente versionato, con directory privata, file `0600` e verifica byte per byte. Non si applicano patch manuali al runtime. Restano presenti heartbeat, prova Docker rinnovata nel processo di guardia, monitor RC22, memoria, OOM, disco, scadenza e stop fail-closed.
- `infra/c109_r12_resources.py`: il helper ha sia `com.docker.compose.project=centrochange-c109-gated-r12` sia `centrochange.mission=C109`; identità, mount e cap sono ricontrollati prima della copia. Gli otto servizi applicativi devono avere la stessa label di missione nel precreate gate.
- Lo stop indipendente interroga entrambe le label, richiede ID Docker completi e un secondo controllo delle label su ogni ID prima di agire. RC22 e gli altri laboratori non soddisfano entrambi i vincoli; ID ambigui o inventario incoerente causano errore, senza stop di risorse estranee.
- `infra/c109_r12_contract.py` e `infra/c109_r12_verified.json` includono i nuovi moduli e test nel manifest SHA-256 verificato dal launcher. Restano invariati i cap 2 GiB runtime e 512 MiB QA, swap zero e tutti gli altri guardrail.

## Verifiche offline

`PYTHONPATH=infra python3 -m unittest discover -s infra -p 'test_c109_*.py' -q`: **113/113 PASS**. Comprende processi distinti e vera contesa `flock`, esecuzione dello script privato in sottoprocesso con host/Docker simulati, lease valida e alterata, contesa con altro writer, directory/file non privati, helper e servizi con doppia label, esclusione RC22/altre missioni, errore Docker e fallimento dello stop. Il test integrato attraversa la preparazione lunga e il gate immediatamente precedente al workload; i casi negativi fermano il flusso.

`python3 -m compileall -q infra/c109_r12_*.py infra/c109_gated_start.py infra/test_c109_r12_*.py`: **PASS**. `git diff --check`: **PASS**. Manifest SHA-256 aggiornato e verificato dai test. Le 113 verifiche comprendono i 99 test preesistenti e i nuovi test pertinenti; non costituiscono una prova sul server reale.

## Limiti e prossimo gate

Resta da verificare in un'eventuale **nuova attivazione Owner** che gli scope systemd reali acquisiscano e rinnovino la prova Docker, che il watchdog mantenga la lease durante copie seriali superiori a 30 secondi, che il helper sia arrestabile anche con launcher bloccato e che RC22 resti invariato. La candidata OCI e i cinque volumi sintetici conservati non sono stati modificati né riverificati in runtime da questo mandato.

La futura attivazione deve partire da questa HEAD esatta con worktree pulito e manifest integro, eseguire i preflight reali e fermarsi al primo evento di sicurezza. Non riutilizzare automaticamente l'autorizzazione precedente. PR #112 resta DRAFT; nessun merge, cutover o dichiarazione di Owner UAT.
