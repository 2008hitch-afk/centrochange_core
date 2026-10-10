# Fase 0 — attivazione controllata del bundle approvato

- Autorità Owner: https://github.com/2008hitch-afk/centrochange_core/issues/117#issuecomment-6098062980. Branch operativo distinto dalla PR draft #118; la PR e il CSV autorizzati restano invariati.
- PR HEAD autorizzato: `f7069bd3350b6d64e2255b3fe7350ad9bf3b4e22`; blob CSV: `7dfe4db830399d5d5bfd0b0989defadc0fceeab3`. Preflight read-only `PASS` su 109/109 ID, stato, labels, mount, riferimenti e container non candidati.
- Avvio UTC: 2026-10-10T13:40:08.294944+00:00; fine prevista eliminazioni/verifica: 2026-10-10T15:10:08.294944+00:00; hard stop: 2026-10-10T15:40:08.294944+00:00; margine 30 minuti.
- Baseline: 251 container (9 accesi RC22, 242 spenti), 202 volumi, 21 immagini, 23 reti; RC22 ping HTTP 200; C109 fermo. Disco libero 36,800,425,984 B; MemAvailable 5,707,177,984 B; host `oom_kill` 7; PSI memoria/I/O basso al campione.
- Lotti autorizzati: 103 QA stopped, quattro builder/helper stopped, due cache BuildKit nominate nel CSV. Nessuna rimozione di image, DB/site, backup, archivio, codice o C109 Compose.
- Stop immediato su difformità ID/mount/reference, RC22 o altra risorsa protetta alterata, OOM/pressione anomala, esaurimento margine o errore di rimozione. Nessun force/prune, nessun recupero distruttivo improvvisato.

Questo record precede la prima cancellazione. Il ledger finale sarà append-only.
