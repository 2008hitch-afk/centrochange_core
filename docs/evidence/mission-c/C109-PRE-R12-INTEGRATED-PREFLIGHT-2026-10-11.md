# C109 #109 — preflight integrato offline pre-R12

**Esito:** `C109_PRE_R12_INTEGRATED_PREFLIGHT_READY` per il solo codice e la simulazione offline. **R12 non è autorizzata né attivata.** Le 24 aree GOAL-02 e i ruoli restano da collaudare sul runtime; `MISSION-C: READY_FOR_OWNER_UAT` non è dichiarato.

## Origine e identità preservata

PR prodotto #112 DRAFT, base PR #107 DRAFT; partenza PR #112 `84b983dee54c35a403498abe1359aae2c8d262c5`. I report R10, pre-R11 e R11 restano invariati. R11 si è fermata prima di creare risorse perché un wrapper manuale ha passato nove ID Docker RC22 da 64 caratteri a `guard()`, mentre il guard interrogava `docker ps -q` e confrontava ID da 12 caratteri. La verifica indipendente a 64 caratteri aveva confermato che RC22 non era cambiato. Non era stata dimostrata una perdita di accesso Docker.

La candidata applicativa resta `e2fd728ecf6acdb0e0ab26379820df6905dd5521`, immagine OCI `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. **Questa immagine non è stata avviata o ricostruita in questa attività.** Nessun file prodotto, schema o dato è stato modificato.

## Correzione e contratto condiviso

- `infra/c109_rc22_identity.py` definisce una sola identità canonica: esattamente nove ID completi, distinti, esadecimali e lunghi 64 caratteri. Legge `rc22-before.json` e interroga sempre `docker ps -q --no-trunc`. ID brevi, duplicati, mancanti, aggiunti o malformati sono rifiutati prima del confronto. Il guard rilegge la baseline privata a ogni verifica; nessun wrapper può sostituire il valore atteso passandolo come argomento.
- `c109_gated_start.guard()`, il monitor RC22, il launcher checkpoint, il wrapper dei passi Docker, il frontend update e il launcher QA usano lo stesso contratto. La verifica indipendente dei nove ID completi nel monitor RC22 rimane presente. Non sono state ridotte le verifiche HTTP, heartbeat, eventi protetti, OOM, RAM, disco, PSI o cgroup.
- `c109_gated_start.precreate_gate()` è la funzione di gate effettivamente chiamata dal launcher applicativo immediatamente prima di `docker compose up --no-start`. Verifica attivazione/finestra, identità RC22, inventario Docker protetto, guard vivi, assenza di workload C109, otto servizi, limite aggregato 2 GiB, swap zero, entrypoint inerte, cinque volumi/due reti isolate, esistenza effettiva delle risorse, parità `docker compose config` e assenza di limiti I/O artificiali sul progetto R12.
- `infra/c109_r12_preflight.py` è l'unico ingresso R12 predisposto. Rifiuta pin immagine/revisione errati, HEAD non autorizzata o worktree sporco, finestra non valida e mancanza del lock Docker writer. Verifica RC22 e inventario prima di avviare i quattro scope, poi osserva per oltre 30 secondi i loro rinnovi effettivi, riesegue il medesimo `precreate_gate()`, emette un'attestazione privata e chiama il launcher applicativo, che esegue **ancora** lo stesso gate. L'attestazione scade dopo 30 secondi ed è legata a baseline RC22, attivazione e digest dei file verificati.
- `infra/c109_r12_verified.json` contiene gli SHA-256 dei moduli del percorso e del test integrato. Un cambio di codice non verificato blocca l'ingresso R12. Il digest aggregato dell'insieme viene verificato dal launcher, senza soglie maggiorate o marker fittizi.

## Simulazione integrata e controlli offline

Comando: `PYTHONPATH=infra python3 -m unittest discover -s infra -p 'test_c109_*.py' -q` — **88/88 PASS**. `python3 -m compileall -q infra/c109_*.py infra/test_c109_r12_preflight.py` e `git diff --check` — PASS. Nessun Docker reale, browser, RC22 o database usato dai test: host e API Docker sono simulati. Digest del contratto verificato: `af262aa86b2a1643c4d33d6cfd827dfd23558661423f7e0ceefe4b536459211f`.

`test_c109_r12_preflight.py` attraversa l'effettivo percorso `preflight → precreate_gate → attestazione → precreate_gate`, fino al punto immediatamente precedente alla creazione dei container. Il caso GREEN simula 34 secondi e rinnovi multipli dei quattro marker; nessun `docker create`/`compose up` viene chiamato. Casi STOP: sostituzione/assenza/aggiunta/duplicazione/abbreviazione di ID RC22, baseline divergente, API Docker indisponibile durante rinnovo, prova scaduta, processo sostituito, heartbeat assente, alert watchdog, inventario protetto divergente, immagine o SHA harness errati, Compose/file mancanti, limiti RAM/swap incoerenti, risorsa non isolata o mancante e finestra scaduta. Il test del launcher conferma lo stop mirato R12 su un fallimento del preflight prima del workload. I test preesistenti coprono inoltre la mancata pubblicazione di marker su perdita accesso, l'immutabilità dell'identità del processo e l'accesso reale al socket/API nel processo di guardia, sempre tramite mock offline.

## Procedura predisposta per una futura attivazione distinta

1. Richiedere e registrare **nuova** autorizzazione Owner R12, inclusa eventuale deroga I/O temporanea; questo mandato non la concede. Conservare R10/R11 e preparare in modo controllato risorse sintetiche R12 esclusive, configurazione privata, baseline RC22 a 64 caratteri e inventario protetto. Non riusare volumi conservati come destinazione mutativa.
2. Pin l'HEAD esatta del branch PR #112, confermare worktree pulito, candidata OCI e configurazione Compose; verificare recupero, RC22 e capacità di risorse. La procedura versionata blocca l'avvio se file o risorse differiscono.
3. Dopo l'autorizzazione e dentro la finestra, usare **soltanto** `python3 infra/c109_r12_preflight.py PRIVATE_ACTIVATION_ROOT`. Il comando detiene il lock writer, avvia i quattro guard, dimostra rinnovi >30 secondi, esegue i gate e soltanto dopo arriva al launcher degli otto container. Non usare wrapper Python ad hoc né chiamare `c109_gated_start.py` direttamente.
4. In caso di qualunque stop, terminare solo R12; non ritentare la stessa attivazione. Verificare RC22, conservare marker/log sanitizzati e riferire il gate preciso. La finestra deve includere un'ora riservata a stop/recupero e arresto automatico.

## Limiti della prova

I test offline non provano l'effettiva disponibilità futura di socket Docker, immagine, volumi, reti, tempo, memoria e RC22, né il caricamento della UI o le 24 aree. La creazione e il collaudo runtime R12 richiedono una nuova decisione Owner. Il percorso di clonazione dei volumi resta preparazione controllata separata: il launcher ne verifica identità e isolamento, ma non li crea implicitamente. Nessun merge, cutover, nuovo container, volume, rete, test attivo su RC22 o deroga è stato effettuato in questa attività.
