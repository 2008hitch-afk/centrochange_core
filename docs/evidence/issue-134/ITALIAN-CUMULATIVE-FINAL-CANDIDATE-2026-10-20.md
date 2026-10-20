# Issue #134 — candidato cumulativo italiano e PDF

**Stato: READY_FOR_ONE_FINAL_LOCALE_DEPLOY (candidato isolato).** Nessun nuovo aggiornamento del DEV condiviso è stato eseguito. La localizzazione globale resta **PARTIAL** fino a installazione, prove live e review Owner.

## Identità e confini

- PR #145 DRAFT, issue #134; base DEV verificata: source `1b7ffc465ff699de163f9536ab04d4dde4da54e3`, immagine `sha256:d7315cb85d3d51ed6510b9d0f6f1b9b2be639cb2d637f67a57790136f5e55257`, 9/9 servizi.
- Source candidato: `7760e92963f0e3875acafeda32d14cd25802fa70`.
- Executor futuro: `infra/issue134_cumulative_install.py`, SHA-256 `ca283f8b98d912d706a55198085716e5f41a1a62572ce7f5ebc6fc39c6d034e4`; overlay `infra/compose.issue134_cumulative.yaml`, SHA-256 `1eb642e2634312cbd53d033fbe4490bed34b1235e470b644f1ae5283aad2ce41`.
- L'executor richiede un **nuovo** gate Owner privato legato a source e SHA, 4 ore operative più 1 ora di recupero; conserva backup cifrato, checkpoint, controlli di integrità, sei soli servizi applicativi e un rollback. Il gate del deploy precedente non è riutilizzabile.

## Difetto → causa → modifica → prova

| Difetto | Causa confermata sulla versione pinned | Modifica versionata | Prova |
|---|---|---|---|
| Titolo «Sales Invoice», `Session`, `Nos`, `Italy` nella stampa | Il print builder standalone genera titolo e celle proprie, fuori dal solo template inizialmente adattato | `website_brand.py`: sostituzioni presentazionali circoscritte alla fattura sintetica e titolo italiano; valori canonici intatti | Clone: HTML/PDF 200, firma `%PDF-`, 1 pagina estraibile; nessuna delle quattro etichette nel testo PDF; test pinned 14/14 |
| Importo in lettere inglese nei Form Fattura | Frappe 16.50 non usa il formatter DocField per il controllo nativo read-only Small Text/Data | `locale_presentation.py` GET read-only con allowlist e controllo `read`; `cc_finance_form.js` mostra importo italiano nel riepilogo già esistente dopo risposta autorizzata e nasconde il campo duplicato al solo cliente | Browser clone: Sales/Purchase Invoice desktop/mobile «Cento euro e zero centesimi»; test API consentito a Finance e negato al Professionista; Administrator tecnico invariato |
| Date lista native in ISO e etichette poco chiare | Formatter/list header nativo esponeva valore e label grezzi | `cc_catalog_finance_list.js`: date italiane, filtro ISO canonico, soggetto leggibile; `it.csv` amplia le chiavi effettive | Test List View e browser clone; nessuna modifica a DB/API |
| Tooltip «Practitioner» in Tipi di seduta | La List View non caricava l'estensione; il tooltip nativo usa il valore grezzo anche quando il badge è tradotto | Hook `doctype_list_js` e formatter circoscritto, mantenendo `data-filter=allow_booking_for,=,Practitioner` | DOM reale: «Prenotabile per: Professionista»; test del filtro canonico |
| «Servizio: Session» nella conferma demo | Dettaglio conferma usa `confirmationText`, separato dalle notifiche comuni | Localizzazione della sola resa della conferma in `workspace.js`; payload conservato | DOM reale: «Servizio: Seduta»; confronto Agenda desktop/mobile e test che esclude ogni modifica alla logica Agenda |
| Stati e motivi audit/operativi inglesi | Valori tecnici originali usati come label principali | `audit_view.js`, `ui_labels.js`, catalogo: riepilogo italiano, originale sempre consultabile | Inventario browser delle viste principali e avanzate |

## Verifiche eseguite

- Rehearsal integrale isolata precedente: 128 visite browser dei sette ruoli su desktop/mobile e 80 stati Form, 0 errori, HTML e PDF fattura reali PASS. Evidenza privata `issue134-locale-clone/20261020T150741Z-209829`.
- Rehearsal finale delle sole superfici cambiate: `issue134-locale-clone/20261020T185918Z-404078/summary.json` = **PASS**, 20 stati di route, 24 stati Form, 0 errori browser, HTML/PDF 200, `%PDF-`, 1 pagina estraibile, clone eliminato, impronta del DEV identica prima/dopo. Testo e screenshot privati in `issue134-cumulative-locale/20261020T185918Z-404078`.
- Inventario generico del testo realmente reso: 412 elementi unici (main, sezioni, tab, dettagli, tooltip, placeholder e titolo browser); due hint inglesi classificati manualmente sotto. Il matcher serve a ordinare il riesame, non a conferire PASS automatici.
- Test locali: 18 test Python del catalogo/clone/executor; 14 test Python su Frappe pinned del print/API; unit test List View, inventario Chromium, locale e cinque casi date/DST. Tutti PASS nell'ultima esecuzione; `git diff --check` pulito.
- Agenda: source di griglia, stile e navigazione invariato. L'unica riga cambiata nel modulo condiviso riguarda il testo della **conferma in Notifiche**. Screenshot reali [desktop](cumulative-final/agenda-desktop.png) e [mobile](cumulative-final/agenda-mobile.png) confrontati con la baseline: sette giorni, due professionisti, filtri e azioni invariati.
- Esempi di resa finale: [fattura paziente](cumulative-final/sales-invoice.png), [fattura professionista](cumulative-final/purchase-invoice.png), [stampa fattura](cumulative-final/invoice-print.png). Solo dati demo sintetici; nessun PDF, dump o segreto nel repository.

## Limiti residui osservati

1. `1 Filter Applied` è il **tooltip** del filtro nella List View Catalogo. Frappe 16.50 lo costruisce letteralmente in `filter_list.js` senza `__()`: il catalogo italiano non può intercettarlo. Una sostituzione DOM permanente dipenderebbe da un dettaglio interno upstream; la voce principale «Filtri» e la pagina restano italiane. Questo tooltip va verificato nel DEV live e valutato dall'Owner; non è dichiarato risolto.
2. `Item ...` e valori storici come `Unpaid`, `Cancelled`, `Draft`, `Type of Document` compaiono nel **dettaglio storico nativo Version** di una fattura annullata. Sono snapshot audit canonici preesistenti, non etichette di compilazione; l'operatore vede già il riepilogo italiano della fattura. Non alteriamo o occultiamo la traccia. La presentazione storica resta un limite UX esplicito.
3. Errori di compilazione di ogni variante ERPNext, stampe diverse dalla fattura campione, export/email demo e tutte le schermate sul **nuovo DEV** richiedono il collaudo dopo installazione. Non sono dichiarati PASS globale sulla sola rehearsal.

## Gate successivo

Richiedere una sola autorizzazione Owner per installare **esattamente** source `7760e92963f0e3875acafeda32d14cd25802fa70` con l'executor e l'overlay sopra identificati sull'unico `centrochange-dev`. Prima della modifica: dry-run, verifica 9/9 servizi e fingerprint, gate privato con UTC effettiva, backup cifrato e checkpoint; dopo: PDF/ruoli/Agenda/italiano/permessi/integrità. Nessun merge o GOAL-03. L'Owner visual PASS resta separato.
