# Missione C #109 — tentativo singolo con QA browser alleggerito

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. L'Owner ha autorizzato una nuova attivazione distinta dal precedente stop I/O, [registrata sulla issue prima delle mutazioni](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6110568736). Finestra privata 2026-10-11 15:25:11–21:25:11 UTC, con un'ora aggiuntiva solo per arresto/recupero e hard stop automatico 22:25:11 UTC. L'attivazione è terminata alle **15:25:58 UTC** al primo evento di sicurezza. Nessun retry.

## Sorgente e preparazione

- PR prodotto #112 DRAFT, dipendenza #107 DRAFT. Codice applicativo nell'immagine immutabile: `97092a06659b4d3322bf4ce30ff6cbb06f8c28c1`, OCI manifest `sha256:602b7a1930a918dce5b957602e645a34fb4947092b6fbd55fd60e62b5694f1c1`. Nessuna build, migrazione o modifica del prodotto in questo tentativo.
- Harness `eac4187`: progetto dedicato `centrochange-c109-gated-r5` per conservare intatti i container fermati del precedente tentativo; stessi volumi/reti sintetici C109, disgiunti da RC22. Compose statico: otto servizi con cap aggregato 2 GiB, swap zero. QA separato 512 MiB, profilo Chromium temporaneo su tmpfs 64 MiB compreso nel cap, cache disco/media disabilitate, nessun tracing/video, screenshot soltanto su richiesta. Sessione browser fresca per esecuzione; JavaScript, CSS e login reali preservati.
- I 33 campioni del tentativo precedente mostravano il salto dei byte letti dal cgroup QA da 139 KiB a circa 214 MiB durante l'avvio Chromium, con circa 2 MiB scritti. Questo ha motivato la riduzione delle scritture, ma **non** dimostra che Chromium fosse l'unica causa della pressione host. Test statici mirati: 17 PASS, syntax Python/Node e diff check PASS. Browser plugin non disponibile; harness Playwright isolato predisposto, non eseguito.
- Prima del bootstrap: RC22 HTTP 200 e nove ID registrati, nessun workload C109 attivo, porta 8109 libera, risorse Docker disgiunte, immagine esatta disponibile, disco libero 43,48 GiB, MemAvailable 5,46 GiB, PSI memory/io full 0, OOM host 7. Accesso Docker dei tre scope verificato; watchdog, monitor eventi protetti ed expiry attivi prima del rilascio dei workload. Soglia PSI I/O full **1% invariata**.

## Primo evento e arresto

Il progetto r5 ha creato otto container inertemente. Il solo database era stato rilasciato dopo verifica cgroup `memory.max=536870912` e `memory.swap.max=0`. Alle 15:25:58 UTC il watchdog ha rilevato PSI I/O host full avg10 **1,25%** e scritto `IO_PSI`; il launcher ha rilevato lo stesso superamento e fermato solo C109. Nessun servizio applicativo, QA o Chromium era stato rilasciato. Il database C109 aveva letto circa 70 MiB e scritto 28 KiB nel proprio cgroup; PSI I/O full locale 0,36%. Questi dati non consentono di attribuire l'intero picco host al database o all'applicazione.

Tre campioni privati mostrano PSI memoria full massimo 0%, MemAvailable minimo circa 5,29 GiB, OOM host 7→7, nessun alert di evento protetto. Al termine: zero container C109 r5 running, otto container creati conservati, database/volumi/immagini intatti. RC22 HTTP 200 e **stessi nove ID** prima/dopo. Disco libero finale 43,46 GiB. Nessun provider o dato reale.

## Conclusione dei test

| Area | Esito su questa attivazione |
| --- | --- |
| Isolamento statico, cap Compose e guard attivi | PASS |
| Cap reale del database r5 prima del workload | PASS |
| Stop fail-closed a PSI I/O full 1% | PASS |
| QA Chromium alleggerito, JS/CSS/login/navigazione | NOT TESTED — stop prima del QA |
| 24 aree GOAL-02 e sette ruoli + Guest/Administrator | NOT TESTED |
| Sicurezza API/direct/query/export/print e confronto C3 | NOT TESTED |
| Integrità RC22 | PASS |

Il tentativo non fornisce evidenza di difetto applicativo né dimostra la completezza della UI. Il limite osservato è la pressione I/O **host** durante il bootstrap, precedente alla prova del browser alleggerito. L'attivazione r5 è consumata: nessun retry con gli stessi parametri e nessuna dichiarazione `READY_FOR_OWNER_UAT`. I campioni tecnici dettagliati restano in archivio privato fuori Git. Nessun merge, cutover o modifica RC22.
