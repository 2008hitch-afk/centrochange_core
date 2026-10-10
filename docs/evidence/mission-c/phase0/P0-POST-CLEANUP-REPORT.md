# Fase 0 — report esecuzione cleanup approvato

**`FASE-0-CLEANUP: PARTIAL` — 108/109 oggetti autorizzati eliminati, stop sul guard I/O.** Nessun retry, force, prune, merge, restart di C109 o modifica a RC22. Il singolo oggetto ancora presente è il volume `buildx_buildkit_centrochange-b99-r2-builder0_state`. Il [manifest d'azione nominativo](P0-ACTION-LEDGER.csv) registra ogni ID, il risultato e gli orari disponibili. Questa esecuzione non autorizza a completare il volume residuo in una nuova prova senza riesame Owner.

## Autorità e preflight

- Autorità: issue #117, commento Owner `6098062980`; PR draft #118 invariata a `f7069bd3350b6d64e2255b3fe7350ad9bf3b4e22`; blob del CSV approvato `7dfe4db830399d5d5bfd0b0989defadc0fceeab3` e del piano `2544890fe2ee3fc52f648cf6f01b1172d7f901f1`. La nuova PR di esecuzione è stacked; non altera la PR approvata.
- Preflight read-only PASS: 109 ID, stati spenti, labels, mount, riferimenti, immagini, container non candidati, volumi e reti invariati rispetto all'inventario autorizzato; nessun build/migrate attivo rilevato; RC22 HTTP 200; C109 fermo. Un primo lancio dello **script locale** di preflight si era interrotto perché confrontava l'HEAD del branch di esecuzione con l'HEAD della PR #118; corretto il controllo di ancestry senza toccare Docker, il preflight ha dato PASS prima della prima delete. Non era una difformità dell'inventario.
- Attivazione versionata separata: 10 ottobre 2026, 13:40:08 UTC; stop validazione alle 15:10:08 e hard stop alle 15:40:08, con 30 minuti di margine. Un solo writer Docker tramite lock locale. Baseline: 251 container (9 running), 202 volumi, 21 immagini, 23 reti; disco libero 36.800.425.984 B; MemAvailable 5.707.177.984 B; host `oom_kill=7`; swap 0.

## Azioni ed evento di arresto

1. **Lotto 1 PASS:** rimossi, per ID esatto e senza `-v`, i 103 container QA spenti del manifest. Checkpoint immediato PASS: 148 container, 9 running RC22, tutti i 202 volumi/21 immagini/23 reti presenti, RC22 HTTP 200, risorse non candidate invarianti.
2. **Lotto 2 helper PASS:** rimossi i quattro container builder/helper spenti del manifest, sempre per ID esatto e senza `-v`. Checkpoint PASS: 144 container, 9 running, 202 volumi, 21 immagini e 23 reti; RC22 HTTP 200. Le due cache avevano zero riferimenti dopo la rimozione degli helper.
3. **Lotto 2 cache INTERROTTO:** richiesto `docker volume rm` soltanto per `centrochange-b99-r3-buildkit-state`. Durante l'operazione il guard locale ha rilevato **PSI I/O full ≥10%** e ha terminato il client Docker, interrompendo le operazioni successive. Il daemon Docker ha però completato la rimozione di questo primo volume: assenza verificata con `docker volume inspect`, volume count 201 e aumento misurato dello spazio libero. Il ledger registra `REMOVED_DURING_IO_PSI_STOP` per evitare di rappresentarlo erroneamente come preservato. Il secondo volume `buildx_buildkit_centrochange-b99-r2-builder0_state` **non è stato richiesto né rimosso**. Nessun altro volume è stato eliminato.

La pressione I/O full campionata subito dopo lo stop era ~42%; memoria PSI full 0, host `oom_kill` è rimasto 7. Non si è assunto che terminare il client annulli una delete già consegnata al daemon: l'inventario finale verifica lo stato **effettivo** degli oggetti. Nessun tentativo è stato ripetuto dopo il guard.

| Misura | Prima | Dopo verificato | Delta |
|---|---:|---:|---:|
| Container totali / running | 251 / 9 | 144 / 9 | −107 container spenti |
| Volumi | 202 | 201 | −1 cache; seconda cache conservata |
| Immagini / reti | 21 / 23 | 21 / 23 | 0 |
| Disco libero | 36.800.425.984 B | 46.684.299.264 B | **+9.883.873.280 B (~9,88 GB decimali)** |
| MemAvailable | 5.707.177.984 B | 5.692.080.128 B | −15.097.856 B al campione; nessun guadagno RAM atteso |
| Host `oom_kill` | 7 | 7 | 0 |
| RC22 ping | 200 | 200 | invariato |
| C109 attivi | 0 | 0 | invariato |

## Invarianti e risorse trattenute

Il controllo finale ha confrontato **tutti i container rimasti** con la baseline per ID, nome, immagine, stato, avvio, restart, mount e reti. Tutti i volumi diversi dall'unico cache eliminato mantengono nome, driver, mountpoint, labels e options; i 23 network e le 21 immagini sono presenti. I nove container running sono ancora esclusivamente di `centrochange-dev`. RC22 sulla porta 8082 è HTTP 200. I container Compose C109 sono fermi e invariati. Database/site/volumi RC22 e C109, immagini CURRENT/QA/TARGET/C109, archivi, checkpoint, evidenze, codici PR e configurazioni sono rimasti intatti. Gli eventuali volumi anonimi dei vecchi helper non sono stati toccati.

Il volume residuo (~3,605 GB secondo `docker system df -v` preflight) rimane sotto il gate Owner dopo lo stop PSI. Nessuna prova del contenuto byte-identico della cache rimossa era disponibile; questo rischio era esplicitamente accettato nell'autorizzazione. Il recupero funzionale BuildKit dipende da pin/source/immagini conservati, non da un ripristino della cache stessa. La pulizia non dimostra né risolve `CAP_NOT_ENFORCED` della Missione C.

Evidenze raw e snapshot Docker/PSI sono conservati privatamente fuori Git sotto `/home/empv26/.local/state/centrochange-p0-20261010/cleanup-execution-20261010/`; il CSV pubblicato è sanitizzato. **Prossimo passo:** revisione Owner di questo `PARTIAL` e decisione separata sull'eventuale volume residuo, dopo analisi della pressione I/O; nessuna Missione C R5 è stata riavviata.
