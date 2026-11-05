# C109 — diagnosi read-only `CAP_NOT_ENFORCED`

**Issue:** #120. **Assessment:** `ROOT_CAUSE: INSUFFICIENT_EVIDENCE`.
**Perimetro:** rapporto diagnostico; nessuna esecuzione C109, modifica Docker, retry, cleanup o modifica al watchdog. Missione C #109 resta `BLOCKED`, `READY_FOR_OWNER_UAT: NO`.

## Fatti verificati

| Evento | Docker configurato | Sequenza osservata | Lettura watchdog | Esito |
| --- | --- | --- | --- | --- |
| R3, QA seriale | `HostConfig.Memory=536870912`, `MemorySwap=536870912` (512 MiB, swap disabilitato) | Docker `StartedAt=2026-10-10 12:34:59.192519 UTC`; campione `12:34:59.271417 UTC`, **78,9 ms dopo** | cgroup `populated 1`, `memory.max=max`, `memory.current=1282048` B, eventi OOM 0 | `CAP_NOT_ENFORCED`, stop; `OOMKilled=false` |
| R4, worker queue-long | `HostConfig.Memory=402653184`, `MemorySwap=402653184` (384 MiB, swap disabilitato) | Docker `StartedAt=2026-10-10 13:05:44.952599 UTC`; campione `13:05:45.091083 UTC`, **138,5 ms dopo** | cgroup `populated 1`, `memory.max=max`, `memory.current=2785280` B, eventi OOM 0 | `CAP_NOT_ENFORCED`, stop prima di creare QA; `OOMKilled=false` |

Le due letture sono nel *primo* campione dopo l'avvio dei rispettivi container. In R3 i campioni precedenti di QA e worker mostravano cap numerici corretti (rispettivamente 79 e 259 campioni); nei campioni immediatamente precedenti il nuovo QA non esisteva. In R4 i campioni immediatamente precedenti non contenevano il worker fermo. Non esiste quindi un campione successivo che dimostri se il limite del medesimo container si sarebbe stabilizzato. R3/R4 non hanno prodotto nuovi OOM host (`oom_kill 7→7`) né pressione memoria pericolosa. Gli **OOM reali** del browser QA nelle R1/R2, inclusa `OOMKilled=true` in R2, sono un difetto distinto e non vanno riclassificati come falsi allarmi.

Il codice esatto di `recovery-20261010-r3/safety.py`, riusato identico in R4, costruisce il percorso host `/sys/fs/cgroup/system.slice/docker-<container-id>.scope`; legge `cgroup.events`, `memory.max`, `memory.swap.max`, usage ed eventi; se `memory.max=max`, controlla `docker inspect .State.Running` e ignora soltanto il teardown di un container già uscito. Con `running=true`, oppure `memory.swap.max!=0`, emette immediatamente `CAP_NOT_ENFORCED` e ferma i container C109. Il campione non registra PID del processo, `/proc/<PID>/cgroup`, inode del cgroup, gerarchia degli antenati o valore swap nel record di probe. Il watchdog fa quindi una lettura reale del file host previsto, ma non prova che esso fosse il cgroup effettivo del PID nel momento critico.

Sul server attuale Docker usa driver cgroup `systemd` e cgroup v2. Il percorso derivato dall'ID coincide con `/proc/<PID>/cgroup` di un container RC22 vivo; il suo cgroup risulta `populated 1`. RC22 non ha un limite di memoria configurato, quindi il suo `memory.max=max` è atteso e non convalida i limiti dei container C109 storici. I loro PID storici non sono più disponibili; non sono stati conservati snapshot contemporanei di `/proc/<PID>/cgroup` o dei cap degli antenati. La namespace cgroup privata dichiarata da Docker riguarda la vista interna del container; il watchdog legge i file host. Il path host hardcoded è coerente con la convenzione Docker/systemd corrente, ma non è stato dimostrato per quei due PID al momento dell'incidente.

La configurazione Docker dimostra l'**intenzione** di applicare i cap, non che il kernel li avesse già applicati all'istante dei campioni. In cgroup v2 `max` significa assenza di cap *locale*; un antenato può comunque limitarne l'uso. Anche questo non è stato misurato all'incidente. L'ordine dimostrato è `Docker StartedAt → 79/139 ms → lettura watchdog → stop`. L'istante della scrittura del limite da parte di Docker/systemd e quello dell'eventuale avvio del workload applicativo non sono registrati. I journal Docker/containerd e gli eventi storici disponibili non aggiungono una prova di tale ordine.

## Ipotesi e alternative

**Ipotesi principale, non dimostrata:** il watchdog intercetta una transizione iniziale del cgroup prima che il limite venga reso effettivo. La distanza di 79/139 ms e i precedenti campioni capped la rendono plausibile, ma nessun campione successivo del medesimo PID la conferma. È altrettanto possibile che il limite non fosse realmente applicato per l'intera vita del container, oppure che il path hardcoded non corrispondesse al cgroup del workload in quel momento. Non attribuiamo un bug specifico a Docker o systemd senza tale prova. L'arresto fail-closed del watchdog era corretto rispetto al valore che ha osservato.

## Correzione minima proposta, **non implementata**

Una futura prova controllata deve prima registrare l'ID e il PID Docker, derivare il cgroup effettivo da `/proc/<PID>/cgroup` sul **host**, confrontarlo con il path monitorato e leggere `memory.max`, `memory.swap.max` e gli antenati. Un protocollo versionato `limit verified before workload` deve impedire l'avvio di Chromium o del worker applicativo finché cap RAM e swap non risultano effettivi sul cgroup del loro PID. Il solo `docker create` non prova che il cap sia già applicato. Se il path è errato, correggere la risoluzione del path; se si dimostra una transizione, introdurre soltanto una fase bootstrap inerte e **limitata nel tempo**, con stop fail-closed se il cap non si stabilizza. Nessuna finestra di tolleranza mentre il workload è attivo; nessun aumento dei 2 GiB runtime + 512 MiB QA, né modifica a soglie PSI/OOM/disco.

La prova discriminante successiva, se autorizzata, è **un solo** avvio isolato e seriale: watchdog e monitor RC22 attivi prima dello start; acquisizione temporizzata PID/cgroup/configurazione Docker/cap locale e antenati; verifica del cap prima di rilasciare un workload; stop immediato per path discordante, cap `max`, swap inatteso, OOM, PSI o anomalia RC22. Verificare poi che la procedura resti valida su container QA nuovi e worker riavviati, e che i test negativi mantengano lo stop quando il cap è davvero assente. Nessun test di questo tipo è stato eseguito nella diagnosi.

**Unico gate Owner:** autorizzare separatamente un branch di correzione del protocollo watchdog/bootstrap e una prova C109 isolata e limitata, con i guardrail invariati. Questa PR diagnostica non attiva tale prova né riavvia la Missione C.

## Fonti e limiti dell'evidenza

- Rapporti versionati: `R3-FULL-UI-STOP-REPORT.md` (PR draft #115) e `R4-SAFETY-STOP-REPORT-2026-10-10.md` (PR draft #116); report Fase 0 (PR draft #119).
- Fonte locale privata letta in sola lettura: codice `safety.py`, campioni JSONL R3/R4, snapshot Docker inspect della Fase 0. Non sono stati copiati log grezzi, env o credenziali nel repository.
- Fonti ufficiali: [Docker runtime metrics](https://docs.docker.com/engine/containers/runmetrics/) per il path systemd; [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/) per RAM/swap; [Linux cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html) per `memory.max` e limiti gerarchici; [runc systemd cgroup](https://github.com/opencontainers/runc/blob/main/docs/systemd.md) per il meccanismo generale. Le fonti descrivono il comportamento atteso, non provano il timing dei due incidenti.
- Verifica finale read-only: nove container RC22 attivi; `http://127.0.0.1:8082/centrochange` HTTP 200 seguendo il redirect; nessun container C109 avviato; ultimo volume cache Fase 0 presente. Nessun comando Docker mutativo, restart, test browser, retry, modifica a RC22/C109 o cleanup in questa diagnosi.
