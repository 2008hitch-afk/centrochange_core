# Missione C #109 — R4 safety stop prima della QA

**Esito: `MISSION-C: BLOCKED`; `READY_FOR_OWNER_UAT: NO`.** R4 non ha eseguito Chromium, nuovi test browser, test funzionali o correzioni prodotto. Gli esiti R3 restano quelli del report R3, con le aree PARTIAL e BLOCKED lì indicate. Non vengono promossi a PASS.

## Attivazione e discriminante

L'attivazione R4 è registrata separatamente in `R4-ACTIVATION-2026-10-10.md` sul presente branch stacked sulla PR draft #115. Prodotto PR draft #112 al commit `d9c09e1d44795b068b4869c013263531dc53a936`, immagine `sha256:6855661acef0f98978cc969e3f12e418b68ff2744d5b47f625bc8afde5acdbae`. Il watchdog R3 è stato riutilizzato senza eccezioni o soglie modificate. Il monitor eventi protetti e il watchdog erano attivi prima del riavvio del solo Compose C109.

Al riavvio dei container esistenti C109, il watchdog ha campionato il worker `c-fit-queue-long-1` come `running` con `memory.max=max` e `memory.current=2,785,280` byte e ha registrato **`CAP_NOT_ENFORCED`**. `HostConfig.Memory` e `MemorySwap` erano entrambi `402,653,184` byte. Gli eventi cgroup OOM e OOM kill erano zero; Docker `OOMKilled=false`. La causa precisa della discrepanza transitoria fra configurazione Docker e cgroup effettivo **non è verificata**. L'evento è analogo al limite non applicato campionato nel QA R3, ma questa volta è avvenuto **prima della creazione del QA**, sul worker durante il restart del runtime. Non viene introdotta alcuna finestra di tolleranza post hoc.

Il watchdog ha avviato lo stop C109. Dopo la sua uscita un backend risultava ancora in esecuzione; è stato fermato esplicitamente con `docker stop` mirato al solo container con label C109. La R4 è stata quindi interrotta, **senza retry** e senza lanciare Chromium. Il container QA R4 non è mai stato creato; pertanto la verifica del suo cgroup resta `NON VERIFICATA`.

## Sicurezza finale

| Controllo | Osservato |
|---|---|
| C109 attivi | 0; gli otto container Compose sono conservati e fermi |
| QA R4 | 0 creati; nessun Chromium R4 |
| Container protetti | 137/137 identici al checkpoint R3 per ID, immagine, stato, avvio, restart, mount e reti |
| RC22 | `/api/method/ping` HTTP 200 prima e dopo; nessuna modifica |
| Host `oom_kill` | 7 → 7; nessun nuovo OOM |
| PSI massimo campionato | memoria full 0,00%; I/O full 0,36% |
| MemAvailable minimo | 5.611.360.256 byte |
| Disco libero minimo | 36.819.083.264 byte; riserva 4 GiB rispettata |
| Risorse C109 | cinque volumi, due reti e immagine prodotto conservati; nessun cleanup |
| PR | #112 prodotto invariata; questa PR solo evidenza, draft; nessun merge |

La diagnosi suggerisce una race nella visibilità/applicazione del limite cgroup in fase di start, **ipotesi da verificare**. La prossima decisione deve definire un protocollo di bootstrap che permetta di verificare l'effettivo cap prima dell'esecuzione dei processi applicativi, mantenendo stop immediato per ogni limite non applicato, senza aumentare i 2,5 GiB aggregati o attenuare i guardrail. Fino a tale decisione e a una nuova attivazione distinta, la UI completa e i test ancora PARTIAL non sono attestabili.

Evidenza privata non versionata: `recovery-20261010-r4/activation.json`, `memory-samples.jsonl`, `final-summary.json` e checkpoint dei container protetti sotto `/home/empv26/.local/state/centrochange-c109/`. Nessun secret, fixture o log grezzo è incluso nella PR.
