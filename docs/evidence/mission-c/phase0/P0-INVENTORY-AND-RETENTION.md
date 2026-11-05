# Fase 0 — inventario e retention del server (sola lettura)

**Esito dell'inventario: PASS con limiti espliciti; nessuna eliminazione autorizzata o eseguita.** Mandato: issue #117 e piano Missione C #110 §10. Rilevazione live del 10 ottobre 2026, su un clone documentale isolato da `main` `2fab181cd61cfc69e341d9fa1849038c6646e87e`. Il checkout operativo non è stato cambiato. La matrice nominativa completa è `P0-RESOURCE-INVENTORY.csv` (525 righe: 251 container, 202 volumi, 21 immagini locali, 23 reti, 23 directory, tre archivi e due siti). Le dimensioni dell'archivio sono **già comprese** nelle rispettive directory. ID Docker completi e configurazioni con environment restano in archivio privato fuori Git; il CSV contiene solo nomi e ID abbreviati dei container, immagini, riferimenti e misure non sensibili.

## Stato live e consumo effettivo

| Misura | Osservato | Interpretazione |
|---|---:|---|
| Disco root | 102.915.489.792 B totali; 36.836.163.584 B disponibili | 65% occupato; inode liberi 10.859.929 |
| Host RAM | 8.321.208.320 B totali; 5.825.536.000 B `MemAvailable`; swap 0 | La RAM disponibile include cache recuperabile; non sommare alla dimensione disco Docker |
| Container | 251 totali, **9 running**, 242 stopped | I 9 running sono tutti `centrochange-dev` RC22 |
| RC22 | ping HTTP 200 sulla porta 8082 | Site `centrochange.local`, immagine pinned `sha256:4ce7cbb0bcfb…`; dati owner-modified da preservare |
| C109 | 8 container Compose fermi, nessun QA R4 creato | Site sintetico `b99.local`, immagine finale `sha256:6855661acef0…`, cinque volumi e due reti dedicate da conservare |
| Immagini | 21 ID locali, Docker 27,01 GB complessivi | Molti layer condivisi; Docker segnala solo 1,816 MB reclaimable in questo stato |
| Volumi | 202, Docker 17,5 GB complessivi | 188 ancora referenziati anche da container **fermi**; il riepilogo reclaimable è solo 1,994 MB prima di staccarli |
| Layer scrivibili container | Docker 1,447 GB; 1,323 GB dei container fermi | Questi byte sono distinti dai layer immagine condivisi |
| Build cache Docker dichiarata | 0 B | Due **volumi** BuildKit storici occupano separatamente circa 12,399 GB, non compaiono come Build Cache reclaimable |
| RAM dei 9 container live | cgroup `memory.current` 1.179.856.896 B; working-set stimato `current - inactive_file` 984.641.536 B | I container fermi occupano **0 RAM operativa**; i valori per container sono nel CSV |
| PSI | memoria some/full 0,00%; I/O some/full 0,00% al campione | Nessuna prova di pressione host sostenuta in questo snapshot |

`docker ps -a`, `docker compose ls -a`, `docker inspect --size`, `docker image/volume/network inspect`, `docker system df -v`, `docker stats --no-stream`, cgroup v2, `free`, `df` e `du` sono stati usati in sola lettura. `docker compose ls` mostra `centrochange-dev` 9 running + 1 stopped; B99 R1–R5 e C109 sono spenti. Non sono emersi container Docker running di altri progetti. Le risorse built-in `bridge`, `host`, `none` sono OUT_OF_SCOPE.

| Gruppo da label/ownership | Running / stopped | Layer scrivibili | Volumi referenziati e dimensione lorda* | Retention |
|---|---:|---:|---:|---|
| `centrochange-dev` RC22 | 9 / 1 | 186,4 MB | 11; ~400,9 MB | `KEEP_CRITICAL` |
| `centrochange-c109` | 0 / 114, inclusi 103 QA browser | 78,0 MB | 19; ~933,8 MB | 8 Compose e cinque volumi dedicati `KEEP_TEMPORARY`; QA effimeri candidati |
| B99 R2/R3/rehearsal e helper | 0 / 75 più 1 builder senza label | ~761 MB più helper | 66+ volumi; comprende cache BuildKit | Dati/site `HOLD`; cache candidate |
| B99 R4 | 0 / 25 | ~276,5 MB | 27 volumi | `HOLD` |
| B99 R5 | 0 / 27 | ~145 MB | 34 volumi | `HOLD` per upgrade/rollback storico |

\* Le somme per progetto **non sono additive**: un volume può essere montato da container etichettati con progetti differenti, e Docker misura i volumi in forma arrotondata. Il CSV registra per ogni volume i container che lo referenziano.

## Frappe, site, bench, immagini e archivi

- RC22 è il **solo runtime Frappe acceso**: site `centrochange.local`, image GOAL-02 RC22, DB/site/Redis/asset e configurazione privata da conservare. Il suo backup/restore non è stato riprovato in P0: **NON VERIFICATO in questa fase**, quindi nessuna sua risorsa è candidata.
- C109 è lo stack Frappe/ERPNext TARGET per Unified Desk; site sintetico `b99.local` e cinque volumi dedicati sono fermi ma necessari per riprendere #109 senza rifare i test. PR prodotto #112 e immagine finale sono presenti; nessuna risorsa applicativa C109 è proposta per delete.
- B99 R1–R5 sono laboratori sintetici spenti. Le verifiche upgrade/rollback sono storiche; P0 **non** ha provato backup e restore di ogni singolo DB/site/volume, quindi container applicativi, siti e volumi storici restano `HOLD`. Non si è dedotta eliminabilità dai soli nomi o dallo stato `exited`.
- Nessun bench Frappe host standalone è stato trovato sotto `/home/empv26/src` o `/home/empv26/.local/state` fino a profondità sei; le installazioni Frappe qui censite sono negli strati immagine Docker e i site nei volumi. L'accesso diretto al contenuto dei volumi sotto `/var/lib/docker/volumes` non era disponibile senza sudo interattivo; nessun contenuto DB o secret è stato letto. Per i laboratori spenti la lista interna dei site diversi da quelli documentati resta `NON VERIFICATA`.
- L'archivio privato CURRENT/QA `lab-decommission-20261009/current-qa-complete.tar.gz` (~3,01 GB) ha verifica documentata PASS del gzip, hash dei layer e caricamento reale; conserva le immagini `sha256:f8fe936c0b25…` e `sha256:f970b8eb4b0b…`. Restano da conservare anche l'archivio TARGET R5 (~1,65 GB), il checkpoint CURRENT, le PR di evidenza e gli script privati C109. Non si propone di cancellare archivi, checkpoint, codice o immagini.
- La directory `lab-decommission-20261009` (~3,01 GB), quella B99 iniziale (~2,99 GB) e gli archivi TARGET (~1,65 GB ciascuno in directory distinte) sono grandi, ma necessari o non dimostrati ridondanti: `KEEP/HOLD`. Non si sommano al gain Docker proposto.
- Nessuna cache Docker BuildKit è attiva nel riepilogo Engine; `docker buildx ls` mostra **default** running, i builder storici R2/R3 stopped/inactive. Due volumi nominati conservano 8,794 GB e 3,605 GB di cache. Non contengono il DB/site RC22 o C109 secondo mount/ownership Docker; non sono stati ispezionati internamente.

## Limiti e separazione dei problemi

La matrice riporta `BACKUP_VERIFIED` e `RESTORE_VERIFIED` per risorsa: `not verified per-volume/container` è intenzionale, non equivale a NO e non autorizza delete. Per le cache la rigenerazione funzionale è possibile da source/pin/immagini conservate, ma un **ripristino byte-identico della cache non è dimostrato**; la proposta Owner evidenzia questa perdita. Per i QA container gli script/risultati sono bind mount esterni, ma il loro writable layer effimero non è stato archiviato. Il rilievo non certifica l'assenza di automatismi esterni o di altri writer futuri: il preflight andrà ripetuto prima di ogni delete.

Eliminare container fermi o cache recupera disco, **non RAM già occupata**. R3/R4 `CAP_NOT_ENFORCED` ha mostrato un limite cgroup non applicato/visibile al campione con host MemAvailable oltre 5 GB e nessun nuovo OOM; questa Fase 0 non lo risolve. Dopo un eventuale cleanup serviranno diagnosi mirata del bootstrap cgroup e nuova autorizzazione R5, senza abbassare il watchdog.
