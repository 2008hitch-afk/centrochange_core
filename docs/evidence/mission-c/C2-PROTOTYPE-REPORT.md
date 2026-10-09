# C2 — Prototipo Unified Desk

**PARTIAL — laboratorio arrestato per OOM del browser, nessun riavvio.**

Issue #109, piano #110. Prodotto in draft #112 (stacked su #107), evidenze in draft #111. Nessun merge, cutover, modifica RC22 o promozione TARGET.

## Sorgenti e riproducibilità

Branch `issue-109/unified-desk-prototype`, commit effettivamente caricato `6c2801c` (SHA completo in image-proof.json). Baseline prodotto #107 `d50299f8d9ad32640259ff1c3a1fded47db5c447`; upstream pin invariati: Frappe16.50.0 `f20f92d29706510551b4438cc196b0323a7f1a92`, ERPNext16.50.0 `7474d9e786277383de1242ab882f16856d17a9c9`, Healthcare16.6.1 `dda107b26e3a0fe1dbd65c7257371235de054a04`, Builder1.35.1 `37e958bc4f801d06d0438c21b97b42c45c4eaa51`.

Immagine C finale `sha256:c932e75841a0119363da07c11abeb6223f1fb7c99905250e4255753cbcb282ef`; base R5 `sha256:342dd48b649aae93fe2e9cc080e44b1ff622b11c900bd084b636af3f2e4624a7`. QA Playwright1.58.2 `sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3`.

Nuova Page standard `cc-unified-desk`, Sidebar standard di modulo, Page/Date/Select/Autocomplete/Dialog ufficiali. Nessuna modifica hook, guard, ruolo, master o contabilità. Nessun codice applicativo bind-mount, nessuna patch manuale al container. `infra/mission_c_image.py` genera il delta OCI COPY-only dai file committati, riusando i blob R5 già caricati; non ricompila le dipendenze. Il primo delta era 40KB.

La sync usa `frappe.reload_doc('centro_change_core','page','cc_unified_desk',force=True)` e `reload_doc(...,'sidebar','centro_change',force=True)`, seguita da commit/clear_cache sul solo clone. Non richiede schema migration generale. L'identità Administrator è usata soltanto per installare gli artefatti standard, mai per eseguire i flussi business dei ruoli.

## Ambiente e isolamento

Compose `centrochange-c109`, porta `127.0.0.1:8109`, site `b99.local` in **nuovi volumi C esclusivi**, non nel runtime B. DB/assets/sites R5 puliti e spenti copiati read-only, senza avviare/modificare R5. Nuova rete interna e rete HTTP dedicate, nessun collegamento ai DB protetti. Config validata prima della creazione; nessuna collisione di nomi/porte/volumi. Credenziali fixture/config rimangono fuori Git in directory privata.

Sorgenti misurate: DB423.4MB, assets39.73MB, site0.873MB. Budget incrementale3GiB, riserva4GiB; live iniziale12.88GiB. Runtime limiti aggregati2GiB, browser512MiB, totale2.5GiB. Non è stata necessaria una build completa. Nuova attivazione autonoma e limitata documentata in C2-ACTIVATION.json, distinta dalle finestre B.

## Flussi realmente verificati

| Controllo | Esito | Evidenza |
|---|---|---|
| Syntax JS / JSON standard | PASS | node --check, JSON parsing |
| Login Segreteria e Page Desk reale | PASS | route `/desk/centro-change/cc-unified-desk`, DOM e screenshot |
| Agenda canonica | PASS | 9 card =9 record autorizzati, settimana28/09–04/10 |
| Geometria desktop/tablet/mobile | PASS | drift0px,7 giorni uguali, no document overflow |
| Settimana precedente/successiva | PASS |28/09→05/10→28/09 |
| Dettaglio Seduta/Storico/Note | PASS | dati canonici, nessun corpo privato per Segreteria |
| Ricerca paziente no-result e tastiera | PASS | unico Autocomplete, selezione nome canonico, generation guard |
| Pazienti e storia | PASS |7 pazienti autorizzati, drill-down reale |
| Finance / fatture / residuo | PASS |3 fatture =3 documenti canonici, dettaglio da Sales Invoice |
| A/B/C browser | PASS |1 professionista ciascuno A/B, C nessuna seduta |
| Sicurezza HTTP | PASS |69/69 controlli, sette ruoli, centro, native list, report/export e note private |
| Direzione browser | FAIL nel harness / da discriminare | attesa hardcoded2 righe senza fissare CentroA; non attribuita automaticamente al prodotto |
| Finance/Accountant browser | NON VERIFICATO | browser OOM durante cambio ruolo f |
| Booking/sposta/cancella e incasso mutativi | NON VERIFICATO | Dialog implementati; nessuna esecuzione mutativa provata in C |
| Tutte le superfici Finance/SdI/TS/admin | NON VERIFICATO nel Desk | matrice C1, webapp preservata; nessuna falsa parità |

I 69 controlli HTTP non includono un PASS preventivo di ogni print/export nativo né la copertura completa dei sei hook sulla nuova immagine: il backend non è cambiato, ma le evidenze R5 restano baseline, non nuovi test C. Primo test security aveva un'aspettativa sbagliata sul report nativo Manager: la mancanza dei ruoli contabili ERPNext comporta403 anche per quel principal. Prima esecuzione conservata; ultima versione richiede403, nessun grant aggiunto.

## Difetti e limiti

Corrette durante il prototipo: envelope `patient_search.patients`, label umane, percorso standard Sidebar annidato, focus del close control nei Dialog HTML. Il primo test browser ha tentato Escape prima della completa apertura/focus; il test usa ora il controllo close nativo. Non si dichiara per questo dimostrato il flusso Escape. Un avvio QA durante ricreazione C ha ricevuto empty response: errore orchestrazione isolato, non RC22.

Non ancora implementati nel Desk: disponibilità visuale, filtro professionisti, tab Note con editing, tutti i drill-down/report avanzati, banca/TS/SdI/admin. Collegamenti espliciti alla webapp completa sono transitori, non prova di conversione nativa. Il chrome Desk mantiene testi tecnici/inglesi e identità sintetiche secondarie: limite di conformità italiana/UX, nessuna accettazione globale.

## Stop obbligatorio

Il container browser ha raggiunto esattamente il limite512MiB; Docker State.OOMKilled=true, contatore host oom_kill +1. Nessun OOM dei servizi C backend/db né dei protetti osservato. Monitor ha fermato tutti e soli i container C109. Host memory PSI full massimo0%, some0.12%; IO full massimo78.55% durante copia limitata, stabilizzato prima dei test. OOM è locale al budget QA: non prova esaurimento RAM host.

Tutti i container/volumi/immagini C sono conservati e **spenti**. RC22 HTTP200 e identità/stato/start/restart/reti dei137 container protetti invariati. Nessun riavvio automatico né soglia allentata.
