# C109 DIAG-01 — attivazione unica

- Mandato: issue #122, Owner `OWNER_AUTHORIZED_C109_SINGLE_CGROUP_DIAGNOSTIC_PROBE`.
- Stato finale: **eseguita una volta e arrestata**; marker single-use scritto `2026-10-10 14:30:20.903749 UTC`. Nessuna ripresa UI né secondo tentativo.
- Finestra UTC: **10 ottobre 2026, 14:30–15:15**; hard stop **15:25**. Dopo le 15:15 solo arresto e verifiche; dieci minuti riservati al recupero. La prova inerte dura al massimo pochi secondi dopo lo start.
- Target unico: nuovo container `centrochange-c109-diag01`, immagine QA già presente `sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3`, PID1 `sh -c 'sleep 300'`, nessun mount, rete `none`, filesystem read-only, privilegi ridotti.
- Cap Docker: RAM 536870912 B, RAM+swap 536870912 B; nessun container Frappe, worker applicativo o Chromium avviato. Runtime C109 esistente fermo. Il totale autorizzato 2,5 GiB non viene superato; il singolo diagnostico usa il budget QA512 MiB.
- Watchdog: copia **byte-identica** di `recovery-20261010-r3/safety.py`, più monitor eventi protetti esistente, entrambi attivi e con heartbeat prima dello start. Nessuna modifica a soglie, stop o eccezioni.
- Preflight obbligatorio: RC22 HTTP200/nove container e ID invariati; C109 fermo; Docker writer libero; image SHA corrispondente; MemAvailable ≥3 GiB, disco ≥4 GiB, PSI basso, OOM invariato. Il marker locale `attempted` è scritto **prima** del primo Docker create; vietato un secondo tentativo se esiste.
- Campionamento: polling host del path scope dall'istante precedente a `docker start`; Docker PID/HostConfig, `/proc/PID/cgroup`, `memory.max`, `memory.swap.max`, inode, gerarchia e tempi. Qualsiasi cap `max`/diverso dal configurato su cgroup popolato, swap nonzero, PID/path discordante, alert watchdog, OOM, PSI, riserva disco/memoria o RC22 anomalo → stop del solo diagnostico, nessun retry.
- Chiusura: `docker stop` soltanto del diagnostico se ancora running; mantenerne il container fermo per ispezione, non rimuovere volumi o immagini; monitor finish; confronto RC22 e risorse protette prima/dopo. File raw nel solo stato locale privato; report GitHub sanitizzato.
- Condizione di decisione: una sola prova può risultare inconcludente. Nessuna seconda esecuzione, allentamento guardrail o adozione del fix senza nuovo gate Owner.

La prova ha emesso lo start alle `14:30:21.290580 UTC` ed è stata fermata per `CAP_NOT_ENFORCED_EARLY_SAMPLE`. Il risultato, incluso un difetto del solo harness nella lettura degli antenati, è nel rapporto `C109-CGROUP-DIAG-01-RESULT.md`. La correzione successiva del protocollo DRAFT non è stata eseguita.
