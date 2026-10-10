# C109 DIAG-01 — risultato della prova unica

**Issue #122 / PR draft #123.** `RESULT_GATE: INCONCLUSIVE`. La prova ha verificato un `memory.max=max` su uno scope Docker popolato, ma non l'origine né la durata della condizione. Non vi è stata una seconda prova. Missione C #109 resta `BLOCKED / READY_FOR_OWNER_UAT: NO`.

## Sequenza osservata (UTC, 10 ottobre 2026)

| Istante | Evidenza |
| --- | --- |
| 14:30:20.903749 | Marker locale single-use scritto **prima** del Docker create. |
| 14:30:21.290580 | Richiesto `docker start` dell'unico QA diagnostico, PID1 inerte `sh -c 'sleep 300'`. Watchdog R3 e monitor eventi protetti erano già attivi con heartbeat. |
| 14:30:21.318398 | `Docker StartedAt`. `HostConfig.Memory=536870912` e `MemorySwap=536870912`; immagine QA locale SHA-256 `f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3`. Nessuna rete, mount o workload applicativo. |
| 14:30:21.341221 | Scope host `/sys/fs/cgroup/system.slice/docker-<ID>.scope`, inode **223283**: `cgroup.events populated 0`, `memory.max=max`, `memory.swap.max=max`; **22,8 ms dopo** `StartedAt`. |
| 14:30:21.347840 | Stesso scope e inode: `populated 1`, `memory.max=max`, `memory.swap.max=max`; **29,4 ms dopo** `StartedAt`. Il sampler emette immediatamente `CAP_NOT_ENFORCED_EARLY_SAMPLE`. |
| 14:30:24.486100 | Container diagnostico fermato, exit 137 da stop controllato, `OOMKilled=false`. Nessun processo Frappe, worker applicativo o Chromium rilasciato. |

Il codice del watchdog storico è stato copiato byte-identico, SHA-256 `bd01b44e0a706146c1fc1cdc7f64da18a377a0676eea6e7c78577109aeb8da24`. È rimasto attivo, senza cambiare regole o soglie. Il sampler più rapido ha incontrato il primo cap non valido prima del prossimo campione del watchdog (intervallo di 5 secondi) e ha richiesto l'arresto; il watchdog non ha emesso un proprio `safety-stop.json`. Il monitor eventi protetti non ha emesso alert. Il container diagnostico fermo è stato conservato per ispezione, senza delete.

## Difetto del protocollo e limite della diagnosi

Subito dopo lo start, la lettura della gerarchia dal PID ha generato `FileNotFoundError` su `/sys/fs/cgroup/memory.max`: la radice cgroup v2 di questo host non espone quel file. Il blocco `finally` ha comunque fermato il diagnostico e registrato `result.json`. Per questa esecuzione **non esiste** uno snapshot completo `/proc/<PID>/cgroup`/gerarchia; il PID storico non è più disponibile dopo lo stop. La PR corregge ora il parser degli antenati facendo risultare `null` i file assenti alla radice. Il parser corretto ha superato AST e una lettura **read-only** della gerarchia di un container RC22 vivo; **non** è stato rieseguito sul QA diagnostico. È un difetto dell'harness diagnostico, non una causa accertata del comportamento Docker R3/R4.

Il campionamento dimostra che lo scope Docker con ID e inode coerenti era illimitato localmente anche con `populated 1`. Non prova che lo scope fosse il cgroup effettivo del PID, né se il limite sarebbe comparso dopo pochi millisecondi. Pertanto:

- `CONFIRMED_TRANSITION`: **NO** — manca un successivo cap numerico dello stesso scope/inode; lo stop al primo evento lo impedisce deliberatamente.
- `CONFIRMED_PATH_BUG`: **NO** — il path è coerente con lo scope Docker, ma il confronto contemporaneo con `/proc/<PID>/cgroup` non è stato completato.
- `CONFIRMED_CAP_NOT_APPLIED`: **NO come causa persistente** — `max` è confermato nel campione popolato, non per la successiva vita potenziale del container né per l'intera gerarchia del PID.
- `INCONCLUSIVE`: **SÌ** per la root cause. La prova conferma il trigger che impone lo stop fail-closed e riproduce il fenomeno con un processo inerte.

## Sicurezza e invarianti

Preflight: RC22 HTTP 200, nove container attivi, C109 fermo, MemAvailable **5,89 GB**, disco libero **46,69 GB**, swap zero, PSI memoria/I/O sotto soglia, `oom_kill=7`. Post: RC22 HTTP 200 con i medesimi nove ID; C109 running **0**; `oom_kill=7`; OOM del diagnostico **false**; MemAvailable **5,87 GB** e disco libero **46,69 GB**. Il numero container è 144→145 per il solo diagnostico ora spento; volumi **201→201**, reti **23→23**, immagini **21→21**. L'ultimo volume cache Fase 0 è presente. Nessun servizio RC22, database, volume, immagine, codice prodotto, configurazione condivisa o watchdog è stato modificato. Nessun cleanup, retry, browser test o merge.

## Passo minimo successivo

La modifica DRAFT del parser degli antenati va verificata prima di qualunque nuova mutazione. Per distinguere le cause serve un **nuovo gate Owner** per un'altra prova singola con PID e cgroup reale acquisiti prima dell'arresto. Il protocollo dovrebbe anche registrare in modo atomico il PID appena Docker lo rende disponibile, confrontarlo con lo scope e continuare a fermare il container al primo cap non valido. Nessun periodo di tolleranza con workload attivo, aumento dei limiti o disattivazione del watchdog è proposto.

Evidenza privata: `~/.local/state/centrochange-c109-diag01-20261010/` (attivazione, campioni timestamped, snapshot pre/post, hash sorgenti e log monitor). I log grezzi non sono nella PR.
