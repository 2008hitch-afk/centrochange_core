# Centro Change — localizzazione italiana sul DEV, collaudo live

## Esito

**DEV AGGIORNATO: SÌ. LOCALIZZAZIONE: PARTIAL. CLIENT_DEMO_READY_FOR_OWNER_REVIEW: NO.**
L'unico aggiornamento autorizzato è rimasto installato; nessun secondo deploy o rollback.
La stampa fattura resta in parte inglese e la generazione PDF fallisce, perciò non è corretto dichiarare la localizzazione completa o una demo cliente finale pronta.

## Identità, finestra e integrità

- Autorizzazione Owner: [commento #134](https://github.com/2008hitch-afk/centrochange_core/issues/134#issuecomment-6287400481).
- Source installato `0e6299d8a5507cc5d7dde46336870c0cd6667718`; executor SHA-256 `17683dda3ac6397c5e68e9295b36862f2fe626bed0bcfa19add79a5e13f15033`; overlay SHA-256 `8da3285db7b15e01dadb878a0a2fc0d72bd21ee11669ee39e036117bd269cb1f`.
- Immagine applicativa servita nei sei servizi: `sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5`. Gli altri tre servizi tecnici sono invariati; 9/9 container attivi.
- Gate privato aperto il **20/10/2026 09:04:21 UTC / 11:04:21 Europe/Rome**, limite operativo 13:04:21 UTC, recupero 14:04:21 UTC. Report executor concluso alle 09:07:26 UTC con `DEV_UPDATED_WITH_GAPS`.
- Checkpoint e backup cifrato verificato di database, file pubblici/privati e configurazione: `/home/empv26/.local/state/centrochange-single/issue134-italian-install-runs/20261020T090434Z-4048595/` (privato, nessun backup in Git).
- Fingerprint Owner/Communication pre e post: `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd` / `a13e25cf97b4bfa76856038614ec3e99380c086fc83c322db0958490ff19ac81`; confermati di nuovo dopo il browser. Schema, permessi, guard essenziali, Centro A attivo e Centro B inattivo invariati.
- Executor: verifica asset 6 file e manifest 69 mapping; login dei sette ruoli e Administrator; negazioni API/ruolo critiche PASS. Le suite mutative contabili e i 38 controlli mutativi non sono stati rieseguiti perché il cleanup concorrente del ledger non è ancora verificato; non sono segnati PASS. I 46/46 MVP restano PASS **storici**, non ri-eseguiti in questo collaudo.

## Risultati Chromium effettivi

| Controllo | Esito | Evidenza |
|---|---|---|
| 11 Form nativi × desktop/mobile | **22/22 aperture PASS**, 0 errori JS, 0 occorrenze delle 46 stringhe mirate nella superficie etichette/campi | `issue134_locale_sweep.cjs`, JSON privato `locale-sweep.json` |
| Navigazione per sette ruoli × desktop/mobile | **128/128 visite PASS**, 0 errori JS; nessun match nel vocabolario mirato di titoli, pulsanti e placeholder | `issue134_client_surface_post.cjs`, JSON privato `client-surfaces.json` |
| Secondo pass sui Form, inclusi testo attività e orari | 11/11 aperti; **residui rilevati** sotto | `issue134_native_residual_post.cjs`, JSON privato `native-residual.json` |
| Report contabili | Finance e Commercialista: Libro giornale 13 righe, Bilancio di verifica 6; desktop/mobile, CSV e JS PASS | `mvp_devfirst_reports_ui.cjs` |
| Export leggibili | CSV accessibili secondo ruolo, intestazioni italiane dove previste, date europee; dinieghi 403 per ruoli non autorizzati | `mvp_devfirst_exports_readonly.cjs` |
| Printview fattura contabilizzata | HTTP 200 ma **FAIL localizzazione**; stessa resa con `_lang=it` | `issue134_documents_post.cjs`, [screenshot](live/invoice-print-it.png) |
| PDF fattura | **FAIL HTTP 500** (`OSError`, `wkhtmltopdf`: `ConnectionRefusedError`) | `issue134_documents_post.cjs`; nessun PDF dichiarato PASS |
| Agenda approvata | **PASS identità screenshot**, SHA-256 desktop e mobile uguali byte per byte alla baseline #75; file Agenda invariati | [desktop](live/agenda-desktop.png), [mobile](live/agenda-mobile.png) |

Screenshot aggiuntivi: [Professionista](live/practitioner-desktop.png), [Fattura nel Form](live/invoice-form-desktop.png). Contengono solo dati sintetici.

## Residui italiani puntuali

1. **Attività di Form nativi:** `Last Edited By Administrator` osservato in Tipo seduta, Servizio centro, Modello pacchetto, Fattura professionista, Incasso/Pagamento e Movimento bancario. La traduzione CSV di `Last Edited By` esiste, ma il sorgente Frappe pinned usa la chiave completa `Last Edited By {0}`; la prima scansione di sole etichette non includeva l'attività laterale.
2. **Fattura di vendita / stampa nativa:** `Sales Invoice`, `Billed To`, `Subtotal`, `No.` e `EUR One Hundred only.` restano visibili anche con `_lang=it`; il nome dimostrativo del servizio contiene `Session`. La route produce date europee ma la localizzazione è incompleta. L'hook già esistente `localize_print_labels` limita la sostituzione a selettori che non coprono questi nodi del print format effettivo; `_lang=it` non risolve l'importo in lettere. [Schermata reale](live/invoice-print-it.png).
3. **Fattura professionista / Form nativo:** l'ora `11:05:49` appare con secondi, contro il requisito HH:mm. Una prima cattura di Fattura paziente mostra anche un campo `22:23:57` nelle sezioni tecniche prima del completamento dei componenti custom. Non si altera il formato canonico del database.
4. **Fattura paziente / transizione:** la prima cattura, eseguita subito dopo la comparsa del `.form-layout`, mostrava la descrizione nativa inglese `Issue a debit note against an existing Sales Invoice...`; dopo il refresh asincrono della presentazione cliente la guida italiana era presente. Il test UX precedente produceva quattro falsi FAIL perché non attendeva `.cc-finance-context`; una prova successiva ha verificato la guida in italiano, senza cambiare l'app.
5. **PDF fattura:** `wkhtmltopdf` non completa il rendering: la risposta registra `ConnectionRefusedError`. Nel backend `centrochange.local:80` e `:8082` rifiutano la connessione, mentre `frontend:8080` è raggiungibile. Il printview HTML è accessibile per fattura contabilizzata e ruolo Finance, perciò il problema PDF è nel percorso interno del renderer. Nessun cambio di rete o runtime aggiuntivo è stato applicato.
6. **Errori, tooltip, stati vuoti, notifiche, email demo:** i percorsi visitati e le negazioni di accesso hanno etichette italiane e HTTP coerenti, ma non ogni messaggio è stato provocato in tutti gli stati. Esito **PARTIAL**, senza presumere la copertura completa.

Il tentativo di stampa di una fattura annullata ha dato 403 sia per Direzione sia per Finance. La prova documentale sopra usa invece una fattura sintetica contabilizzata, HTTP 200; il 403 dell'annullata non viene interpretato come difetto di localizzazione né aggirato cambiando permessi.

## Azioni e limiti

La correzione delle stringhe nell'attività richiede una nuova chiave contestuale CSV; la stampa richiede un adattamento versionato del formato/hook supportato da Frappe e il PDF una soluzione riproducibile per l'origin interno usato da `wkhtmltopdf`. Questi cambiamenti richiederebbero **un nuovo candidato applicativo o una mutazione infrastrutturale e un secondo aggiornamento**, esclusi dall'autorizzazione consumata. Nessuno è stato applicato al DEV. L'Agenda resta invariata.

Il DEV è accessibile all'Owner tramite il tunnel SSH privato già adottato; nessun accesso cliente pubblico o credenziale è stato pubblicato. La review Owner può esaminare l'italiano delle schermate operative già aggiornate, ma la presentazione cliente finale deve considerare le limitazioni di stampa/PDF e le stringhe residue sopra.
