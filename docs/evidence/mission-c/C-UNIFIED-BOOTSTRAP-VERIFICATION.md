# C-UNIFIED — verifica bootstrap fail-closed

**Mandato:** #109 / piano #110 §§11–12. **Stato prima della nuova attivazione:** `STATIC_PASS / RUNTIME_PENDING`. DIAG-01 #122 rimane `INCONCLUSIVE` e consumata; questa è una nuova attivazione distinta, non un retry implicito.

## Contratto del gate

`infra/c109_cgroup_gate.py` legge il cgroup **del PID host reale** da `/proc/<PID>/cgroup`, pretende lo scope systemd del container Docker esatto, rifiuta PID assente, path ambiguo o diverso, gruppo non popolato, cap RAM `max`/diverso dall'atteso, swap diverso da zero ed eventi OOM. Legge tutta la gerarchia, trattando l'assenza di `memory.max` **soltanto alla radice cgroup v2** come normale. Restituisce inode, timestamp e limiti locali/antenati. Non modifica Docker.

`infra/c109_inert_cap_probe.py` riusa lo script DIAG-01 ma corregge il parser. Avvia **un solo** QA diagnostico nuovo con `PID1 sleep`, rete assente, filesystem read-only, niente mount o workload. Copia byte-identico il watchdog R3 e il monitor eventi protetti, attivi prima dello start. Il polling a 2 ms registra ogni transizione dello scope. Durante i primi **2 secondi**, un `max` può essere soltanto osservato mentre PID1 resta inerte; se persiste oltre il limite, se ricompare dopo un cap valido, o se il watchdog/host segnala un problema, il container è fermato. Nessun processo Frappe, worker o Chromium viene rilasciato da questo script. Un cap numerico finale richiede anche il controllo del PID e degli antenati. Un marker locale single-use impedisce retry nella stessa attivazione. Il container viene fermato e conservato in ogni caso.

**Limite importante:** una prova QA GREEN non abilita automaticamente i servizi Compose C109 esistenti, i cui entrypoint lanciano workload senza un gate equivalente. Serve prima un protocollo versionato e verificato `inert PID1 → cap reale → release` per **ogni** servizio, senza modificare i container RC22 né disattivare il watchdog. Il presente script non è una scorciatoia per avviare la UI.

## Verifiche offline

`python3 infra/test_c109_cgroup_gate.py`: 11/11 PASS su fixture temporanee senza Docker: radice priva di `memory.max`, PID assente, scope errato, `max`, swap nonzero, OOM, gruppo non popolato, antenato mancante, `max→cap` durante sola fase inerte, `max` persistente e regressione del cap. `python3 -m compileall` e `node --check` della Page modificata PASS. La lettura live read-only del parser DIAG-01 corretto su un PID RC22 ha confermato la forma root → system.slice → docker scope; quel container è senza cap e **non** prova l'enforcement del futuro QA.

## Attivazione prevista

Finestra UTC **10 ottobre 2026, 15:20–16:20**; hard stop **16:30**, dieci minuti per arresto/verifiche. Gate prima della prima mutazione: RC22 HTTP200 con nove ID invariati; C109 fermo; nessun altro writer Docker; SHA immagine QA locale previsto; MemAvailable ≥3 GiB, disco libero ≥4 GiB, PSI basso, OOM host stabile; nessun cambiamento a volumi, reti o checkpoint. Un solo QA512 MiB; budget aggregato C109 2,5 GiB invariato. Se i gate non passano, nessun create. La prova conclusiva, se eseguita, è riportata in modo append-only qui sotto.

## Risultato live

`PENDING`: nessuna attribuzione di PASS runtime finché non viene eseguita e verificata l'unica prova.
