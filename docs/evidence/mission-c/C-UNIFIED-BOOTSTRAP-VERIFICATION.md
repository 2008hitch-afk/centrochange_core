# C-UNIFIED — verifica bootstrap fail-closed

**Mandato:** #109 / piano #110 §§11–12. **Stato della prova inerte:** `CONFIRMED_TRANSITION` **solo per il QA diagnostico**; il gate dei servizi applicativi resta `NOT_VERIFIED`. DIAG-01 #122 rimane `INCONCLUSIVE` e consumata; questa è una nuova attivazione distinta, non un retry implicito.

## Contratto del gate

`infra/c109_cgroup_gate.py` legge il cgroup **del PID host reale** da `/proc/<PID>/cgroup`, pretende lo scope systemd del container Docker esatto, rifiuta PID assente, path ambiguo o diverso, gruppo non popolato, cap RAM `max`/diverso dall'atteso, swap diverso da zero ed eventi OOM. Legge tutta la gerarchia, trattando l'assenza di `memory.max` **soltanto alla radice cgroup v2** come normale. Restituisce inode, timestamp e limiti locali/antenati. Non modifica Docker.

`infra/c109_inert_cap_probe.py` riusa lo script DIAG-01 ma corregge il parser. Avvia **un solo** QA diagnostico nuovo con `PID1 sleep`, rete assente, filesystem read-only, niente mount o workload. Copia byte-identico il watchdog R3 e il monitor eventi protetti, attivi prima dello start. Il polling a 2 ms registra ogni transizione dello scope. Durante i primi **2 secondi**, un `max` può essere soltanto osservato mentre PID1 resta inerte; se persiste oltre il limite, se ricompare dopo un cap valido, o se il watchdog/host segnala un problema, il container è fermato. Nessun processo Frappe, worker o Chromium viene rilasciato da questo script. Un cap numerico finale richiede anche il controllo del PID e degli antenati. Un marker locale single-use impedisce retry nella stessa attivazione. Il container viene fermato e conservato in ogni caso.

**Limite importante:** una prova QA GREEN non abilita automaticamente i servizi Compose C109 esistenti, i cui entrypoint lanciano workload senza un gate equivalente. Serve prima un protocollo versionato e verificato `inert PID1 → cap reale → release` per **ogni** servizio, senza modificare i container RC22 né disattivare il watchdog. Il presente script non è una scorciatoia per avviare la UI.

## Verifiche offline

`python3 infra/test_c109_cgroup_gate.py`: 11/11 PASS su fixture temporanee senza Docker: radice priva di `memory.max`, PID assente, scope errato, `max`, swap nonzero, OOM, gruppo non popolato, antenato mancante, `max→cap` durante sola fase inerte, `max` persistente e regressione del cap. `python3 -m compileall` e `node --check` della Page modificata PASS. La lettura live read-only del parser DIAG-01 corretto su un PID RC22 ha confermato la forma root → system.slice → docker scope; quel container è senza cap e **non** prova l'enforcement del futuro QA.

## Attivazione prevista

Finestra UTC **10 ottobre 2026, 15:20–16:20**; hard stop **16:30**, dieci minuti per arresto/verifiche. Gate prima della prima mutazione: RC22 HTTP200 con nove ID invariati; C109 fermo; nessun altro writer Docker; SHA immagine QA locale previsto; MemAvailable ≥3 GiB, disco libero ≥4 GiB, PSI basso, OOM host stabile; nessun cambiamento a volumi, reti o checkpoint. Un solo QA512 MiB; budget aggregato C109 2,5 GiB invariato. Se i gate non passano, nessun create. La prova conclusiva, se eseguita, è riportata in modo append-only qui sotto.

## Risultato live

La prova unica è partita alle **15:20:11 UTC**, marker single-use scritto prima di Docker create. `Docker StartedAt=15:20:11.316674759`; `HostConfig.Memory=MemorySwap=536870912`. I campioni host dello **stesso scope/inode 223805** sono:

| UTC | Dopo StartedAt | `populated` | `memory.max` | `memory.swap.max` |
| --- | ---: | ---: | ---: | ---: |
| 15:20:11.338253 | 21,6 ms | 0 | `max` | `max` |
| 15:20:11.345234 | 28,6 ms | 1 | `max` | `max` |
| 15:20:11.357443 | 40,8 ms | 1 | `536870912` | `0` |

Il cap è quindi diventato numerico **12,2 ms** dopo il campione popolato/illimitato, senza cambiare inode. Il PID host verificato **2472685** puntava esattamente a `/system.slice/docker-<ID>.scope`; gerarchia root senza file limite, `system.slice` con `max`, scope effettivo con 512 MiB/swap zero. Nuova verifica alle **15:20:13.439177**: cap 512 MiB, swap 0, `oom=0`, `oom_kill=0`. Non è stata rilasciata alcuna applicazione; il solo `sleep` inerte è stato fermato e conservato (exit 137 da stop, `OOMKilled=false`). Watchdog R3/monitor eventi protetti erano attivi, nessun safety stop né alert.

RC22 HTTP200 con gli stessi nove ID; C109 runtime running0; host `oom_kill 7→7`; MemAvailable **5.851.430.912→5.857.726.464 byte**; disco libero ~46,68 GB; volumi/reti/immagini invariati. La transizione è **confermata su questo QA**, non automaticamente su worker, DB o browser futuri. I servizi C109 esistenti hanno entrypoint applicativi immediati e rimangono spenti. La fase successiva richiede gate PID1 inerte per ogni servizio e nuova verifica del cap **prima** del rilascio, sotto la stessa finestra e gli stessi guardrail; nessuna Full UI suite è stata eseguita in questo sottopasso.

## Gate Compose per servizi C109 — preparazione offline

`infra/c109_bootstrap_entrypoint.sh` conserva PID1 in un loop inerte finché il **solo host** scrive il file di rilascio della singola service. Solo allora controlla anche la vista RAM/swap interna ed esegue l'entrypoint originale, con il comando originale. `infra/c109_compose_gate.py` genera un override per **tutte e otto** le service, con gate per servizio e script bind read-only; nessun volume/database/permesso nuovo. Il progetto gated ha nome distinto `centrochange-c109-gated`, ma fa riferimento esclusivamente alle cinque risorse volume e alle due reti **sintetiche C109 esistenti**, marcate external; i container originali restano spenti e conservati. Non vi è alcun riferimento a volumi/reti RC22.

`docker compose config` con il file env privato già esistente ha confermato staticamente 8/8 entrypoint gate, cap RAM=RAM+swap per ogni servizio, due bind read-only a servizio, cinque volumi e due reti C109 external, progetto distinto. Output completo privato fuori Git; nessun valore env pubblicato. `python3 infra/test_c109_compose_gate.py`: 4/4 PASS (inventario, cap/swap, resource prefix e gate mounts); `sh -n` PASS. Questo **non** verifica ancora il comportamento runtime dei processi.

`infra/c109_gated_start.py` rende verificabile un solo tentativo applicativo: marker scritto prima di Docker create, inventario e cap HostConfig per ciascun servizio, avvio inizialmente inerte, verifica host PID/scope/antenati/RAM/swap stabile prima di ogni release, controlli RC22/watchdog/PSI/OOM/disco fra i passi e arresto dei soli container del progetto gated in caso di errore. Il file di attivazione privato deve abilitare espressamente `workload_release_allowed=true`; il test QA precedente lo lasciava a `false`. Anche questo script rimane **non eseguito** fino alla nuova verifica immediata dei gate. La versione candidata dell'immagine applicativa è stata prodotta dal commit `12a19f5` riusando l'OCI base TARGET già verificato, senza nuova compilazione integrale; il digest locale è `sha256:2a5a97ab6b2328bf81ddd544c40c1bb178dffcd86fcc9cc4a596ebd65a3feabd`. La configurazione Compose finale, conservata privatamente fuori Git, referenzia quel digest per le cinque service applicative e mantiene gli altri pin originali.

Alle **15:28 UTC**, prima dell'unico tentativo applicativo, il preflight statico mostra RC22 HTTP200/nove container, C109 running0, immagine candidata disponibile, disco libero 46,67 GB, PSI memoria full 0,00%, PSI I/O full 0,00%, nessun alert o safety stop. I due monitor privati sono stati riavviati come processi autonomi perché il primo lancio era terminato con la sessione shell; dopo il riavvio entrambi gli heartbeat sono stati verificati attivi e continui. Questo non consuma un tentativo Docker applicativo. Il perimetro resta 15:20–16:20 UTC, hard stop 16:30, otto servizi/gate e 2 GiB complessivi senza QA concorrente. Solo dopo la presente registrazione versionata è consentito cambiare la **sola** flag privata di rilascio a `true` e consumare il marker single-use. Qualunque guardrail fa arrestare il tentativo senza retry.

## Primo bootstrap applicativo — STOP di harness

Alle **15:28:46 UTC** il marker single-use è stato consumato. Il DB e Redis cache hanno raggiunto cap host corretti e stabili prima del rilascio: rispettivamente 512 MiB e 64 MiB, swap zero. MariaDB era healthy; Redis cache è uscito con codice **0** immediatamente dopo il rilascio. L'orchestratore ha fermato il solo progetto `centrochange-c109-gated` alle **15:28:53 UTC**. Le altre sei service non sono state rilasciate. RC22 era ancora HTTP200 con nove container, nessun safety stop o protected alert, OOM host **7→7**; nel monitor memoria full massimo 0,00%, I/O full massimo 0,73%, MemAvailable minimo 5.737.873.408 byte.

**Causa verificata:** sostituendo `ENTRYPOINT` nell'override Compose si perde il `CMD` predefinito dell'immagine quando la service non lo specifica. `c-fit-redis-cache` risultava `Cmd=null`; l'entrypoint Redis era eseguito senza `redis-server` e terminava correttamente con codice 0. Anche il backend avrebbe perso il `start.sh` predefinito. Si tratta di un errore del protocollo di bootstrap, non di una regressione funzionale del prodotto né di una violazione dei cap. Il primo marker/attivazione e i relativi container restano intatti; non si ritenta in quell'attivazione.

**Correzione minima offline:** il generatore ripristina esplicitamente `redis-server` per le due service Redis e `start.sh` per il backend, coerentemente con i `Config.Cmd` delle immagini pinned ispezionate. Il test del generatore discrimina ora entrambi i comandi. La verifica runtime, se ancora sicura, richiede una **nuova attivazione distinta**, un progetto Docker distinto e nuovo marker single-use, senza cancellare il primo esito. Nessuna modifica a RC22, ai cap o alle soglie.

## Attivazione applicativa distinta dopo il difetto di harness

Il secondo record privato usa il progetto **`centrochange-c109-gated-r2`** e marker separato; il primo record resta append-only. La finestra operativa è **15:34–16:20 UTC**, hard stop **16:30 UTC**. Il rollback consiste nello stop dei soli container gated-r2 e nella conservazione di volumi, immagini e metadati; non è previsto un cleanup. La nuova esecuzione è subordinata a: Docker writer unico, immagine candidata identica, otto gate e comandi originali verificati in `docker compose config`, RC22 HTTP200/nove ID stabili, C109 running0, nessun allarme, MemAvailable ≥3 GiB, PSI sotto soglia, OOM invariato, disco ≥4 GiB e watchdog/monitor eventi attivi prima di Docker create. Ogni service parte con PID1 inerte e viene rilasciata solo dopo verifica host cgroup stabile. **Una sola esecuzione in questa nuova attivazione**, senza retry in caso di guardrail o ulteriore uscita inattesa. Il prodotto rimane la stessa immagine candidata `12a19f5`; non si rifà il build.
