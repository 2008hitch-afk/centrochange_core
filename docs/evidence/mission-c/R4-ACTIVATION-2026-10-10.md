# Missione C #109 — attivazione R4

- Autorità: https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6097734350 e PR #110 §9.
- Stato iniziale: `ACTIVE`; R3 resta `BLOCKED` per `CAP_NOT_ENFORCED`, senza reinterpretare gli esiti precedenti.
- Inizio UTC: 2026-10-10T13:05:12.792879+00:00. Fine validazione prevista: 2026-10-10T18:05:12.792879+00:00. Hard stop: 2026-10-10T19:05:12.792879+00:00; margine di recupero 60 minuti.
- Prodotto: PR #112 commit `d9c09e1d44795b068b4869c013263531dc53a936`; immagine `sha256:6855661acef0f98978cc969e3f12e418b68ff2744d5b47f625bc8afde5acdbae`. Nessuna nuova build prevista.
- Isolamento: solo progetto `centrochange-c109`, site sintetico `b99.local`, porta `127.0.0.1:8109`. UAT RC22 su 8082 esclusa.
- Limiti: runtime 2 GiB, QA 512 MiB, aggregato 2,5 GiB. Un solo QA preavviato; verifica HostConfig, `memory.max` e `memory.swap.max` prima di Chromium. Un processo Chromium fresco per caso, in serie.
- Watchdog R3 invariato: OOM, PSI, MemAvailable, disco ≥4 GiB, RC22 e container protetti. Qualsiasi stop → arresto dei soli container C109, nessun retry R4.
- Preflight: 137/137 container protetti invariati rispetto al checkpoint R3 per ID, immagine, stato, avvio, restart, mount e reti; RC22 HTTP ping 200; C109 fermo. Disco libero circa 34,3 GiB, MemAvailable circa 5,4 GiB, swap zero, PSI memoria/I/O basso, host OOM count 7.

Questo record è precedente alle mutazioni R4. Risultati, stop e limiti saranno documentati separatamente e non sostituiranno la cronologia R1–R3.
