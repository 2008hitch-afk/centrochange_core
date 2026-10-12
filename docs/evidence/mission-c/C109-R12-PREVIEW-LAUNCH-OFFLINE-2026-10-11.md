# C109 R12 — preparazione offline del launcher per l'anteprima

**Esito:** `C109_R12_PREVIEW_LAUNCH_READY` limitatamente al percorso offline. Nessun avvio C109, container, volume, rete, copia o restore è stato eseguito in questa attività. Le 24 aree e la visualizzazione Owner restano **non verificate**. La precedente autorizzazione R12 non viene riutilizzata automaticamente dopo questo cambio di codice.

## Fonte e identità

Issue #109; PR prodotto #112 DRAFT stacked sulla #107 DRAFT. Il rapporto `C109-R12-RESOURCE-PREFLIGHT-BLOCK-2026-10-11.md` prova che R12 si fermò prima dell'attivazione: `precreate_gate()` richiedeva cinque volumi e due reti R12 già presenti, mentre l'unico launcher verificato non li creava. Non era corretto preparare i volumi fuori dai quattro guard. I volumi originali e le copie R10 restano conservati.

Candidata applicativa invariata: `e2fd728ecf6acdb0e0ab26379820df6905dd5521`; immagine OCI locale `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. Commit della correzione harness `b4b62bc`; digest del contratto offline `9207dc1a841667ec2f4f39fb4d227997844c6676f4d58dd4ba0963f5c327ed74`. L'ispezione read-only dell'immagine ha confermato utente `frappe` e due `VOLUME` dichiarati (`sites`, `logs`), che il helper di copia sostituisce con tmpfs limitati per non creare volumi anonimi. Le cinque fonti sintetiche R10 hanno nomi esatti `centrochange-c109-r10-c-fit-*`; la verifica runtime della loro provenienza e inattività è obbligatoria nel launcher.

## Correzione versionata

`infra/c109_r12_preflight.py` ora chiama `c109_r12_resources.prepare()` **dopo** l'avvio e la prova di rinnovo dei quattro guard, **prima** dell'attestazione e del gate di creazione applicativo. L'ingresso runtime resta unico: `python3 infra/c109_r12_preflight.py PRIVATE_ACTIVATION_ROOT`. Non è stato introdotto un wrapper operativo separato.

`infra/c109_r12_resources.py` rifiuta risorse R12 già presenti, fonti mancanti, fonti non riconosciute come C109 o montate da un container attivo e inventari Compose divergenti. Marca il tentativo come singolo prima della prima mutazione. Crea solo le due reti con nomi R12 autorizzati e ne verifica driver, carattere interno, label e assenza di container. Crea e copia **uno alla volta** i cinque volumi R12. Il helper usa l'immagine OCI pinned, `--network none`, sorgente read-only, destinazione distinta, RAM 256 MiB, swap zero e due tmpfs da 1 MiB al posto dei volumi impliciti dell'immagine. Parte inerte; PID, ID completo, mount, HostConfig, cgroup e cap sono verificati due volte prima della prima lettura. Durante ogni hash e copia vengono ricontrollati guard, RC22, RAM/OOM/disco, finestra e cgroup. La pressione PSI I/O continua a essere misurata dalla sorveglianza; l'eventuale deroga richiede autorizzazione temporanea separata.

La verifica di integrità confronta un SHA-256 canonico di nomi, tipi, modi, contenuto e target dei symlink tra fonte e destinazione, poi ricalcola la fonte per rilevare derive durante la copia. Il helper viene arrestato e rimosso in modo mirato; destinazioni e prove sono conservate in caso di errore, senza retry automatico. Alla fine il gate esistente controlla ancora l'inventario protetto, la configurazione Compose e le risorse isolate. `infra/c109_r12_verified.json` include anche il nuovo modulo nel contratto SHA-256 dell'harness.

## Verifica offline

`PYTHONPATH=infra python3 -m unittest discover -s infra -p 'test_c109_*.py' -q`: **99/99 PASS**. La simulazione attraversa la logica effettiva del launcher, il clone stateful simulato, il gate e l'attestazione; il caso GREEN esegue una preparazione superiore a 30 secondi con rinnovi dei quattro guard, cinque copie seriali e nessun container applicativo prima del gate. Casi STOP: fonte assente/attiva, destinazione preesistente, rete non isolata, copia incompleta, hash discordante, cap helper errato, perdita Docker, cambio RC22, alert di sicurezza, prova scaduta, limiti Compose errati e pin/manifests non validi. `compileall` e `git diff --check`: PASS. Docker e RC22 sono stati consultati soltanto in sola lettura per identità di immagine e nomenclatura R10; nessuna prova offline è attribuita al runtime.

## Unica procedura per la prossima autorizzazione

1. L'Owner autorizza esplicitamente la **nuova HEAD di PR #112**, una sola attivazione R12, la finestra massima di sei ore più un'ora esclusiva di arresto/recupero e l'eventuale deroga temporanea al solo stop PSI I/O già descritta in #109. Nessuna deroga nasce da questo rapporto.
2. Fuori da Git, predisporre la root privata R12 con attivazione approvata, Compose pinned e normalizzata, gate directory, baseline dei nove ID completi RC22, inventario protetto e recupero verificato. I file privati non contengono dati cliente reali; non preparare manualmente reti o volumi. Confermare HEAD pulita e hash del manifest, immagine OCI, spazio/RAM, writer Docker esclusivo, R10 fermo e RC22 HTTP 200.
3. Nella finestra autorizzata eseguire **solo** `python3 infra/c109_r12_preflight.py PRIVATE_ACTIVATION_ROOT`. Il launcher avvia i quattro guard, dimostra rinnovo Docker, prepara reti/volumi sotto sorveglianza, verifica l'integrità, riesegue i gate e soltanto allora rilascia gli otto servizi. Qualunque safety stop consuma il tentativo: fermare solo R12, conservare prove e verificare RC22, senza retry.
4. Prima anteprima: verificare HTTP, login e asset sulla porta privata configurata; pubblicare all'Owner un tunnel SSH sull'accesso già autorizzato e un URL locale verificato, senza credenziali in GitHub. Controllare Home, Agenda, Pazienti, Professionisti, Finanza e Report, desktop/mobile. Questa anteprima è distinta dal successivo collaudo completo della matrice GOAL-02; nessuna delle 24 aree diventa PASS per la sola navigazione.

## Limiti residui

Solo il prossimo runtime può dimostrare che i quattro guard, Docker, tmpfs dell'immagine pinned, copia reale, integrità dei volumi, asset UI e accesso Owner operano insieme sul server. Le risorse R12 assenti restano intenzionalmente assenti fino alla nuova autorizzazione. L'assenza di un budget disco o recupero live adeguato fermerà l'attivazione. RC22 resta l'interfaccia primaria; nessun merge, cutover o `READY_FOR_OWNER_UAT` è dichiarato.
