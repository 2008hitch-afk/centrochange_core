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
