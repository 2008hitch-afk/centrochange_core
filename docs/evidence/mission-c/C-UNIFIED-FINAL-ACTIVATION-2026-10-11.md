# C109 — attivazione finale singola, 2026-10-11

**Autorizzazione Owner:** issue #109, [registrazione pre-mutazione](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6107091632). **Stato iniziale:** PRECHECK; nessuna mutazione runtime al momento di questo record. PR #112 resta DRAFT e stacked su #107. Il precedente stop R2 resta storico e non viene riutilizzato come attivazione.

## Perimetro e finestra proposta

- Nuovo progetto container: `centrochange-c109-gated-r3`, site sintetico C109 esistente `b99.local`, frontend locale `127.0.0.1:8109`; nessun nome/volume/rete RC22 riutilizzato. I volumi C109 esistenti sono riusati soltanto dopo checkpoint privato verificato.
- Finestra UTC proposta: **08:30–11:30** per mutazioni e test; **11:30–12:00** per arresto, verifiche e recupero. Hard stop assoluto **12:00 UTC**. La prima mutazione richiede verifica live dell'ora; se il tempo residuo non è sufficiente, non iniziare.
- Otto servizi C109 con cap complessivo 2 GiB e swap zero; un QA 512 MiB con swap zero, processo Chromium fresco e sequenziale. Nessun aumento di soglie PSI, MemAvailable, OOM o disco; niente lavoro pesante concorrente.
- Watchdog e monitor eventi protetti devono essere attivi prima del Docker create. Inventario Docker protetto a 64 caratteri validato contro il live inventory; heartbeat verificati. Il primo evento di sicurezza causa stop dei soli container C109-r3 senza retry.

## Preflight letto alle 08:23–08:24 UTC

- Sorgente prodotto `78e293a` pulita prima della preparazione harness; RC22 HTTP200 e nove container running con ID completi; C109 running zero. RAM disponibile ~5,5 GiB, swap zero, disco libero 46.958.678.016 byte, memoria/I/O PSI full avg10 0%, host `oom_kill=7`.
- Docker inventory: 163 ID completi e unici; writer lock disponibile, nessun build/bench/migrate/Chromium attivo. Immagine TARGET pinned base `sha256:342dd48b649aae93fe2e9cc080e44b1ff622b11c900bd084b636af3f2e4624a7` e archivio OCI verificabile, QA pinned `sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3`.
- Il codice harness ora abilita soltanto il progetto `gated-r3` aggiuntivo e include il nuovo asset `cc_desk_fragments.js` nel COPY-only OCI delta. Il precedente progetto R2, immagine, volumi ed evidenze restano conservati.

## Gate da chiudere prima del primo workload

1. Commit e parità della HEAD finale; test statici e manifest OCI COPY-only; pin verificati.
2. Checkpoint privato completo dei cinque volumi C109 spenti, hash e prova di leggibilità; procedura di restore solo C109, non RC22.
3. `docker compose config` del progetto r3, verifica risorse e isolamento; inventario RC22 prima/dopo; snapshot host RAM/PSI/OOM/disco.
4. Monitor eventi protetti full-ID e watchdog con heartbeat, lock writer, budget RAM/swap cgroup prima del rilascio.

**Non dichiarare GREEN finché questi quattro punti non sono verificati.** Tutti i test di prodotto e il confronto C3 restano `NOT TESTED` sulla nuova immagine al momento di questo record.

## Esito append-only dell'unica attivazione

**`MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`.** La HEAD effettiva di preparazione è `d213371cc372272106728e7a920325dab43fa4e3`. Il delta OCI COPY-only da tale HEAD è stato generato e verificato offline: manifest `sha256:b70ee0995bd0d8d8445db1a2167173c57559d3c5ccaf8eed8b02b0e68ce79a16`, 14 file tra cui Page Desk e `cc_desk_fragments.js`. Non è stato importato come immagine Docker e non è stato avviato alcun servizio Frappe C109-r3.

Alle **08:30 UTC** i gate iniziali erano GREEN: RC22 HTTP200/nove ID completi, C109 running zero, monitor eventi e watchdog attivi, inventario di 163 ID Docker completi/correnti, PSI full memoria/I/O sotto 1%, `oom_kill=7`, disco libero 46,96 GB. Il Compose statico del nuovo progetto dichiarava otto servizi, cap complessivo 2 GiB, swap zero, porta `127.0.0.1:8109` e soltanto cinque volumi/due reti C109, con intersezione zero con i volumi RC22. L'helper di checkpoint è stato avviato inerte con cap HostConfig 256 MiB; host PID e cgroup effettivo mostravano `memory.max=268435456`, `memory.swap.max=0`, inode stabile prima del comando tar. L'immagine helper Redis è stata risolta al digest pinned già noto; Docker ha comunque effettuato un pull del tag locale, senza cambiare RC22. Si è attesa la discesa di PSI I/O full a 0,09% prima della copia.

Durante il **primo e unico** comando di copia dei volumi, l'orchestratore monitorato ha letto host PSI I/O `full avg10=2,13%` alle **08:30:50 UTC** (soglia conservativa invariata 1%) e ha arrestato il solo helper C109-r3. Alle 08:30:55 il campione era 1,16%. Nessun retry: il marker `monitor-finish` ha chiuso l'attivazione; zero container C109-r3 rimasti e i precedenti trenta container C109 sono conservati. L'archivio privato di circa 61 MB è **PARZIALE/NON VALIDO**, non è un checkpoint né una base di rollback. Il site, DB e volumi C109 non sono stati modificati dal comando, che li montava read-only. Non sono stati eseguiti `docker load`, bootstrap, migrazione, browser o test delle 24 aree sulla nuova HEAD.

Nel monitor: 57 campioni, memoria PSI full massima **0%**, `oom_kill 7→7`, MemAvailable minima **5.781.987.328 byte**, consumo C109 massimo **267.501.568 byte**, disco minimo libero **46.895.906.816 byte**. Nessun alert del monitor eventi protetti. Dopo lo stop, RC22 risponde ancora HTTP200 con i nove ID iniziali; i container C109-r3 running sono zero, i volumi e le immagini precedenti restano presenti. I log tecnici e l'archivio parziale restano privati in `/home/empv26/.local/state/centrochange-c109-final-20261011/`, non in Git.

### Matrice finale delle 24 aree sulla candidata `d213371`

La matrice architetturale statica resta `C1-NATIVE-FIRST-REALIGNMENT-REVIEW.md`; **nessuna delle 24 aree è PASS runtime sulla candidata finale**, perché il gate è scattato prima del checkpoint. Aree 1–12, 14–20 e 22: `NOT TESTED` su questa HEAD. Aree 13 e 24: `OWNER DECISION/EXCLUSION` secondo la matrice C1, non trasformate in PASS. Aree 21 e 23: `PUBLIC/DEV SEPARATE`, non sottoposte a collaudo Desk. Sono `NOT TESTED` anche i sette ruoli più Guest, API/direct/query/export/print, desktop/mobile, C3 versus RC22, login e asset. I PASS precedenti appartengono a immagini storiche diverse e non vengono trasferiti alla candidata.

### Unica proposta correttiva prima di un'altra autorizzazione

Preparare **offline** un checkpoint per volume, strettamente seriale, con limite I/O applicato al **cgroup dell'helper sul device reale** (`io.max`/opzioni Docker equivalenti) e verificato prima della lettura, più pausa di stabilizzazione tra i volumi. Conservare identici il gate PSI I/O all'1%, watchdog, cap RAM/swap e stop immediato. Questo affronta il picco osservato durante la copia senza allentare protezioni né attribuire il precedente stop R2 a una causa non provata. Va prima dimostrato che il throttling sia effettivo e che archivio/restore siano verificabili. **Serve una nuova decisione Owner per qualunque ulteriore attivazione**; l'autorizzazione singola corrente è consumata. Nessun link Owner UAT può essere fornito per la candidata.
