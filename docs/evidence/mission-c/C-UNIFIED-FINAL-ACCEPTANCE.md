# Missione C #109 — gate tecnico corrente (2026-10-10)

**Esito: `PARTIAL / READY_FOR_OWNER_UAT: NO`.** Questo non è un collaudo finale: il laboratorio isolato è stato fermato al superamento del guard PSI I/O e non viene riavviato nella stessa attivazione. Nessun merge, cutover o intervento su RC22.

## Sorgente e perimetro

- PR prodotto draft #112, stacked su #107. La Page applicativa caricata nel laboratorio ha SHA-256 `1ff40b4fb595442699f679355a0df01d7a1d89c7241869a1e4d2c37256fb7df9`, identico al sorgente del commit prodotto `12a19f5`. Immagine: `sha256:2a5a97ab6b2328bf81ddd544c40c1bb178dffcd86fcc9cc4a596ebd65a3feabd`.
- La matrice delle 24 aree e le scelte native-first motivate sono in `C1-NATIVE-FIRST-REALIGNMENT-REVIEW.md`; lo stato area per area è in `C-UNIFIED-IMPLEMENTATION-STATUS.md`. La Page attuale mantiene cinque controller della vecchia webapp incorporati nel Desk; le List native sono link additivi. Quindi la soluzione non soddisfa ancora l'architettura finale native-first né la completezza GOAL-02.
- Site sintetico `b99.local`, frontend isolato `127.0.0.1:8109` **ora spento**. RC22 `127.0.0.1:8082` rimane separato e operativo.

## Esiti effettivamente osservati sulla candidata

| Controllo | Esito | Evidenza discriminante |
| --- | --- | --- |
| Bootstrap otto servizi C109 | PASS limitato al bootstrap | Otto host cgroup con cap numerici attesi e swap zero prima di ogni release; DB/Redis healthy; frontend HTTP200. |
| QA prima di Chromium | PASS | Container QA 512 MiB/swap zero, PID/cgroup host verificato; `oom=0`. |
| Login Desk sintetico | PASS | Browser fresco: Agenda caricata, titolo corretto, zero page errors. |
| List native Manager | PASS limitato alla navigazione | Patient, Healthcare Practitioner, Item, Item Price, Appointment Type, Sales Invoice, Payment Entry: sette pagine aperte, zero page errors e no overflow desktop. Nessuna scrittura o verifica CRUD attribuita a questo test. |
| Sicurezza ruolo A/B/C, Finance, Segreteria; API dirette | NON VERIFICATO sulla presente immagine | Lo stop è avvenuto prima dei negative test. I risultati R3 restano storici, senza promozione alla nuova candidata. |
| Prenota/sposta/cancella, Finance end-to-end, report, notifiche, stampa/export | NON VERIFICATO sulla presente immagine | Scenari non avviati dopo il guard. |
| Mobile/tablet, prestazioni e confronto C3 completo | NON VERIFICATO | Nessuna misura conclusiva sulla presente immagine. |
| Guardrail e RC22 | PASS per l'arresto; gate futuro aperto | PSI I/O full picco 1,36%; C109/QA fermati, OOM host invariato, RC22 HTTP200/nove ID invariati. Inventario eventi protetti generato con ID corti: correggere prima di una nuova attivazione. |

Gli screenshot [`desk-smoke-synthetic.png`](unified-bootstrap-20261010/desk-smoke-synthetic.png) e [`native-patient-synthetic.png`](unified-bootstrap-20261010/native-patient-synthetic.png) sono reali dal laboratorio, con soli dati inventati. Mostrano il confronto ancora aperto: il Desk incorporato conserva il look Centro Change, mentre la List Healthcare nativa usa ancora chrome/label upstream e identificativi tecnici. La disponibilità di una List nativa non è di per sé conformità UX o prova di sicurezza. Le evidenze browser JSON complete, la fixture sintetica con credenziali e i log di telemetria restano nell'archivio privato fuori Git: `/home/empv26/.local/state/centrochange-c109-unified-bootstrap-r2-20261010/app-run/`.

## Blocco e ripresa minima

La seconda attivazione si è conclusa alle **15:38:26 UTC** per il gate prudenziale PSI I/O; nessun OOM e nessuna modifica a RC22. Non usare l'URL 8109 come candidato UAT. Prima di una nuova attivazione: usare la nuova correzione offline `infra/c109_protected_inventory.py` e verificarne la generazione con ID completi, analizzare il profilo I/O osservato e documentare una nuova finestra controllata senza allentare le soglie. Poi proseguire il refactoring native-first delle 24 aree e rieseguire **sulla stessa immagine finale** flussi, ruoli, API, browser desktop/mobile e confronto RC22. Solo dopo quei PASS si potrà proporre `READY_FOR_OWNER_UAT`; la scelta UI e il cutover restano all'Owner.
