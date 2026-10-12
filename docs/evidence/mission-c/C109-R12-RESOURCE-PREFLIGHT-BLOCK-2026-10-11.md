# C109-R12 — arresto prima dell'attivazione per prerequisito risorse

**Esito:** `MISSION-C: PARTIAL`; R12 **non avviata e non consumata**. Questo rapporto corregge il limite non rilevato nel rapporto offline pre-R12: il gate del runtime era stato simulato con volumi/reti R12 già presenti, ma non era stata integrata la loro preparazione sotto i quattro guard.

## Identità e controlli read-only

Al 2026-10-11 21:25–21:27 UTC, il checkout tecnico `issue-109/unified-desk-prototype` era pulito alla HEAD `5e5cf819c472a8089e6bc083333970ce6e76c68f`, uguale alla PR #112 DRAFT; PR #107 resta DRAFT a `d50299f8d9ad32640259ff1c3a1fded47db5c447`. Immagine OCI locale `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00` con label applicativa `e2fd728ecf6acdb0e0ab26379820df6905dd5521`. Il report offline documenta 88/88 test PASS: non attribuiti a un runtime R12.

RC22: nove container applicativi previsti in esecuzione, `GET /api/method/ping` HTTP 200 con latenza osservata circa 23 ms. È stata fatta soltanto questa verifica sanitaria e l'inventario Docker read-only; nessun login, query applicativa o test mutativo RC22. Host: MemAvailable circa 5,5 GiB; disco libero circa 43 GiB; swap zero; OOM host 7; PSI I/O full avg10 0,24% e memoria full avg10 0% al campione iniziale. Nessun container C109 attivo nell'inventario osservato.

Le cinque copie sintetiche R10 e le due reti R10 sono presenti; `recovery-verification.json` R10 dichiara il confronto dei file regolari, directory e link con la fonte fermata e la possibilità di abbandonare R10. Non è stato ripetuto un hash completo in questa verifica. **Non esistono cinque volumi, due reti o root privata R12.** Le risorse R10 e le originali devono restare intatte.

## Impedimento concreto

`infra/c109_r12_preflight.py` è l'unico ingresso verificato per il rilascio applicativo. Avvia i quattro guard e poi chiama `c109_gated_start.precreate_gate()`, che richiede già presenti e corrispondenti i cinque volumi e le due reti elencati nella Compose R12. Il codice non crea né clona queste risorse. Il test integrato offline ha fornito risposte Docker simulate per risorse già esistenti: non ha verificato una copia reale dei dati.

Preparare le copie **prima** dell'ingresso R12 richiederebbe una fase Docker/I/O esterna al launcher verificato; i quattro guard con monitor RC22 non sarebbero ancora attivi. Avviarli separatamente durante la copia non è integrabile nel launcher invariato, che rifiuta marker già presenti e tenta di lanciare nuovamente gli scope. Riutilizzare i volumi R10 come destinazione writable altererebbe le copie conservate. Un clone manuale o wrapper ad hoc ripeterebbe proprio la divergenza tra procedure che ha fermato R10/R11 e contrasterebbe con il mandato di usare esclusivamente il percorso verificato.

Non è stata registrata una finestra effettiva, poiché nessuna preparazione mutativa o attivazione è stata iniziata. Nessun volume, rete, container, file di attivazione o database è stato creato/modificato; nessuna deroga PSI è stata applicata. La singola attivazione Owner resta non consumata, ma **non è eseguibile in sicurezza con il codice/risorse attuali**.

## Delta minimo per lo sblocco

Integrare nella medesima procedura versionata R12, **dopo** l'avvio e la verifica dei quattro guard e **prima** del `precreate_gate`, una fase di creazione e copia seriale delle cinque risorse sintetiche R12. Ogni helper deve partire inerte con limite verificato prima della copia, restare sotto monitor RC22/eventi/RAM/OOM/disco e PSI I/O misurato secondo l'eventuale deroga Owner, e verificare contenuti/integrità senza scrivere su R10/originali. Le reti dedicate vanno verificate prima del rilascio applicativo. Il fallimento deve fermare solo R12, conservando sorgenti e prove, senza retry. Rigenerare il manifest SHA-256 del contratto, rieseguire la simulazione integrata con preparazione >30 s e casi STOP, quindi registrare nuova HEAD e digest sulla issue prima di ogni mutazione.

Questo delta cambia la HEAD `5e5cf81` e il percorso offline attestato; richiede una revisione/autorizzazione Owner esplicita prima di consumare l'unico tentativo R12. Non sono richiesti cambi prodotto, permessi, RC22 o limiti di sicurezza. La matrice delle 24 aree, nove profili e confronto C3 restano **NOT TESTED in R12**.
