# Fase 0 — unica proposta Owner per pulizia mirata

**Stato: `PROPOSTA / NO DELETE AUTHORIZED`.** Questa proposta accompagna l'inventario completo e il manifest nominativo `P0-PROPOSED-DELETE-MANIFEST.csv` (109 oggetti con ID Docker completi, stato, prerequisiti e ripristino). Nessun comando di rimozione è stato eseguito. L'approvazione richiesta è **una sola per il bundle esatto**, non una serie di micropassaggi.

## Bundle proposto

| Batch | Oggetti esatti nel manifest | Gain stimato | RAM liberata | Ragione e impatto |
|---|---:|---:|---:|---|
| 1 — QA effimeri | 103 container browser spenti che usano l'immagine pinned `sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3` | 32.751.616 B di writable layer | **0** | Non montano volumi; tre bind mount esterni (fixture, script e risultati). Si perde il writable layer del processo QA. Gli script privati, gli screenshot/risultati esterni, l'immagine e le evidenze versionate rimangono. |
| 2 — builder storici | quattro container stopped: `centrochange-b99-r3-builder` (`59158b02b976`), `centrochange-b99-r3-cache-finish` (`5b8175553672`), `centrochange-b99-r3-cache-copy` (`824a31991a4c`), `buildx_buildkit_centrochange-b99-r2-builder0` (`38ac9ce3aedf`) | 262.144 B di writable layer | **0** | Solo questi quattro referenziano le due cache. Altri loro volumi anonimi rimangono, non inclusi nel bundle. |
| 2 — cache BuildKit | `centrochange-b99-r3-buildkit-state` e `buildx_buildkit_centrochange-b99-r2-builder0_state` | **~12.399.000.000 B**, misura Docker arrotondata | **0** | Sono cache di build precedenti, non DB/site di RC22 o C109. Si perde la cache byte-identica: futuri rebuild possono essere più lenti e consumare I/O. I builder storico R2/R3 diventano da ricreare; il builder `default` rimane attivo. |

**Totale teorico:** ~12.432.013.760 B (~12,43 GB decimali); disco libero da 36,84 GB a circa 49,27 GB se tutte le stime fossero recuperabili. Valore **non garantito**: Docker arrotonda le dimensioni dei volumi, mantiene metadati e layer condivisi. Nessuna immagine, directory, rete, site, database o volume diverso dai due cache volumi entra nel bundle. I 21 ID immagine e la cache BuildKit Engine dichiarata a 0 B sono esclusi: sommare le dimensioni di immagini da 8–9 GB duplicati sovrastimerebbe fortemente il gain.

## Retention, backup e recovery

**Da conservare integralmente:** RC22 `centrochange-dev` (tutti i servizi, database, site, volumi, image, config privata e porta 8082); gli otto container Compose C109, cinque volumi e due reti, immagine `sha256:6855661acef0…`, fixture/scripts/resultati privati e PR #112; immagini CURRENT/QA/TARGET e archivio CURRENT/QA verificato, checkpoint CURRENT, archivi TARGET e prove B99 R5; tutte le PR e le evidenze; ogni B99 DB/site/asset volume; i container applicativi storici non classificati come QA/builders; ogni risorsa esterna o built-in.

- L'archivio CURRENT/QA ha hash dei layer, integrità gzip e load reale già verificati nel precedente `LAB-DECOMMISSION: PASS`; l'immagine QA è presente con ID pinned. L'immagine C109 finale e il codice PR #112 sono presenti. Non viene affermato un nuovo test di restore in P0.
- Le due cache **non hanno un backup byte-identico** né un restore di cache già provato. Il loro recupero è **funzionale**, da sorgente/pin/immagini mantenuti, con costo di build. Questo è il rischio residuo principale che l'Owner deve accettare se approva il batch 2. Non eliminare il bundle qualora venga richiesto un ripristino esatto delle cache senza predisporlo prima.
- I 103 QA non montano volumi Docker e sono tutti exited; non è necessario preservare un database interno. Il loro writable layer non ha un backup per-container, ma i tre bind mount e l'immagine rimangono. Gli script QA privati non sono tutti versionati: **non cancellare** `centrochange-c109/recovery-*`.
- Il rollback di una `docker rm`/`docker volume rm` non è un undo byte-identico. Per i QA si ricrea un nuovo container da script e immagine; per BuildKit si ricrea il builder/cache da pin. Se una verifica preventiva trova stato unico non riproducibile, abortire prima della prima rimozione.

## Procedura proposta **solo dopo approvazione esplicita**

1. Fissare finestra, writer Docker unico e checkpoint preflight: esportare manifest locale degli ID/label/mount/references attuali; verificare corrispondenza **esatta** al CSV, tutti 109 candidati ancora spenti, nessun build/test/migrate attivo, buildx default funzionante, archivi e immagini retained accessibili, RC22 HTTP 200 e dati/config invariati. Revalidare spazio, RAM, PSI/OOM. Se una risorsa è cambiata, **non applicare parzialmente un elenco obsoleto**: stop e nuovo report.
2. Batch 1: rimuovere solo i 103 container con gli **ID esatti** del CSV usando `docker container rm` **senza `-v`**. Dopo il lotto, verificare RC22 ping/servizi/immagine/volumi, e misurare `df` e `docker system df`. Se la differenza non è spiegata o RC22 varia, stop.
3. Batch 2: rimuovere i quattro container builder/helper con ID esatti, ancora senza `-v`. Verificare che le due cache abbiano **zero** riferimenti; rimuovere **solo** i due nomi di volume del CSV con `docker volume rm`. Non rimuovere i volumi anonimi montati dai helper, né builder default, image, rete o altri volumi. Verificare RC22 dopo ogni sottopasso. Qualsiasi failure interrompe il lotto; nessuna force/delete di volume occupato.
4. Registrare postflight: differenza in byte `df`, Docker image/container/volume counts e `system df`, MemAvailable e working set, PSI/OOM, 137 risorse storicamente protette per le categorie che devono restare, RC22 HTTP e configurazione, C109 fermo ma ricostruibile. Conservare rapporto `P0-POST-CLEANUP-REPORT.md`; **nessun** restart di C109 o R5 in questo gate.

Non usare `prune`, `compose down`, wildcard, force remove, delete di immagini o file host. Il preflight garantisce che la rimozione abbia target esatti; il monitoraggio protegge RC22. Un peggioramento di RC22 o un riferimento imprevisto comporta arresto immediato e diagnosi, non tentativi di forza. La riduzione disco **non** risolve di per sé il `CAP_NOT_ENFORCED` di R3/R4: sarà una diagnosi separata dopo P0 e richiederà nuova attivazione runtime.

## Decisione unica richiesta

L'Owner può approvare **il bundle dei 109 ID/nomi contenuti nel manifest, con il rischio esplicito di non poter ripristinare byte-identicamente la cache BuildKit**, subordinato ai preflight e agli stop sopra; oppure respingerlo/richiedere conservazione esatta delle cache. Fino alla decisione, **tutto rimane intatto**.
