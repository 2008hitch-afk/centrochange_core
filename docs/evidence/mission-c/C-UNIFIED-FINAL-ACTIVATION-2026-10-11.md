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
