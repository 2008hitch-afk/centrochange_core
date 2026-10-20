# Issue #134 — aggiornamento cumulativo italiano: verifica DEV live

**Esito:** `DEV_UPDATED_WITH_GAPS`. Un solo aggiornamento DEV eseguito con l'autorizzazione Owner del commento `6299811074`. L'applicazione resta installata e accessibile; non è stata ripristinata la baseline. La localizzazione globale resta **PARTIAL**, e la review visiva Owner è ancora aperta.

## Identità e integrità

| Voce | Risultato |
|---|---|
| PR #145 DRAFT autorizzata | HEAD `23cef489ee063c48f47807260e0c00e4ff70e82b` |
| Source applicativo installato | `e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec` |
| Executor | `infra/issue134_cumulative_install.py`, SHA-256 `05b1210ca2b6ebc4cea96e1b7c93b4e1977ea829885e1589929506e12fa29b20` |
| Overlay | SHA-256 `1eb642e2634312cbd53d033fbe4490bed34b1235e470b644f1ae5283aad2ce41` |
| Nuova immagine | `sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e` sui sei servizi applicativi |
| Servizi | 9/9 attivi; database e Redis originali conservati |
| Finestra UTC | 20 ottobre 2026, 19:44:16–23:44:16; recupero fino alle 00:44:16 del 21 ottobre |
| Dati sintetici | fingerprint prima/dopo e dopo il collaudo `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd` |

L'executor ha registrato checkpoint di immagini/configurazione e backup cifrato completo verificato nel proprio report privato. Ha controllato schema, autorizzazioni, sei hook, asset, origini Socket.IO, Centro A attivo e Centro B inattivo. **30 controlli critici** e **19 funzionali** in sola lettura sono PASS; gli accessi Guest e ruoli non autorizzati restano 403. I test mutativi contabili e 38 controlli di sicurezza con fixture sono **BLOCKED** dal gate di cleanup documentato: non sono stati attribuiti PASS.

## Verifica Chromium e PDF sul DEV installato

| Ambito | Evidenza | Stato |
|---|---|---|
| Navigazione sette ruoli, desktop/mobile | 128/128 stati route pronti; 14 sessioni, zero errori JavaScript | PASS tecnico |
| Form nativi | 22/22 aperture desktop/mobile; dopo il refresh cache mirato anche i quattro stati Fattura paziente/professionista con «Importo in lettere» italiano | PASS apertura; UX complessiva PARTIAL |
| Stampa Fattura paziente | HTML 200, titolo browser italiano, date GG/MM/AAAA, nessuno dei vecchi `Sales Invoice`, `Billed To`, `Subtotal`, `No.` | PASS |
| PDF reale Frappe | HTTP 200, `%PDF-`, 19.586 byte, una pagina estraibile; «Fattura paziente», «Subtotale», «Seduta», «Italia» e importo in lettere italiano; vecchi termini inglesi assenti | PASS |
| Permesso PDF | Professionista Alfa riceve HTTP 403 sulla stessa fattura | PASS |
| Liste Finanza dopo cache | 24 stati lista; 200 occorrenze di date europee, zero ISO, secondi o AM/PM nel testo raccolto | PASS mirato |
| Agenda | Screenshot desktop/mobile del DEV byte-identici alle immagini baseline approvate del candidato | PASS invariata |
| Errori e validazioni | Dinieghi API verificati; compilazione/salvataggio con fixture non eseguiti in questa installazione | PARTIAL |

Screenshot live sintetici: [Agenda desktop](cumulative-live-2026-10-20/agenda-desktop.png), [Agenda mobile](cumulative-live-2026-10-20/agenda-mobile.png), [Fattura paziente](cumulative-live-2026-10-20/sales-invoice.png), [Fattura professionista](cumulative-live-2026-10-20/purchase-invoice.png), [Stampa](cumulative-live-2026-10-20/invoice-print.png). Il PDF e gli inventari completi restano in evidenza privata del server; nessun documento reale o credenziale è stato pubblicato.

## Cache Frappe v16.50: causa, intervento e verifica

Al primo sweep live quattro stati Form fallivano: il nuovo `cc_finance_form.js` era presente su disco e servito via HTTP, ma la scheda non richiedeva l'API `locale_presentation.invoice_words`. Anche i tooltip nativi «1 Filter Applied» e «Prenotabile per: Practitioner» erano ancora visibili. La lettura del sorgente pinned `frappe/desk/form/meta.py` ha mostrato la cache Redis `doctype_form_meta::<DocType>` contenente il vecchio JavaScript; il `FormMeta(cached=False)` della nuova immagine conteneva il codice aggiornato. La precedente pulizia di hook e traduzioni non invalidava queste chiavi.

La procedura versionata `infra/issue134_refresh_form_meta.py` ha verificato immagine, nove servizi, sette differenze esatte e fingerprint, poi ha invalidato **soltanto sette chiavi FormMeta**: Item, Item Price, Appointment Type, Sales Invoice, Purchase Invoice, Payment Entry e Bank Transaction. Nessun Site, record, permesso o servizio è stato modificato. Verifica successiva: `DRY_RUN_PASS`, zero chiavi stale, fingerprint invariato. Un nuovo Chromium senza cache ha trovato 36 stati mirati senza errori, i due tooltip italiani e «Importo in lettere» nei Form Fattura desktop/mobile.

## Residui realmente osservati

1. **Patient, tab Riepilogo:** testo del heatmap nativo `This is based on transactions against this Patient. See timeline below for details`, desktop/mobile. Il sorgente pinned Healthcare chiama `_()`, ma `FormMeta.__dashboard` è memorizzato nella chiave `doctype_form_meta::<DocType>` senza variante per lingua; una cache compilata in inglese viene riusata dall'utente italiano. Il catalogo in sé traduce correttamente il testo.
2. **Item, tab Collegamenti:** heatmap nativo `This is based on stock movement. See` e link `Stock Ledger`, desktop/mobile, con la stessa causa di cache interlingua del dashboard ERPNext.
3. **Item, tab Tariffe:** aiuto HTML upstream delle unità in inglese e valori UOM canonici `Nos`; l'aiuto HTML non passa dal catalogo al render. La denominazione persistita `Nos` non è stata cambiata.
4. **Audit e documenti sintetici storici:** JSON tecnici e stati/identificativi canonici inglesi conservati per tracciabilità; le schermate di presentazione principale non li trasformano in dati nuovi.
5. **Validazioni e messaggi interattivi:** i casi non mutativi disponibili sono coperti parzialmente; non è stata eseguita una campagna di salvataggi o nuove fixture per evitare rischio al dataset Owner.

I residui 1–3 richiedono un'ulteriore personalizzazione presentazionale del sorgente e quindi **un nuovo deploy**; non sono stati patchati nel container e non è stato eseguito un secondo aggiornamento. Come richiesto dal mandato, il commit **`13bf636a45ba68e644e93c664d9a0efe20f817a7` è soltanto una correzione locale NON INSTALLATA**: localizza il messaggio del dashboard per l'utente cliente dopo il refresh nativo e l'aiuto HTML delle unità mediante `frm.set_df_property`, preservando link e valori canonici. `node infra/tests/test_issue75_native_ux.cjs` è PASS, ma manca una prova browser su runtime aggiornato per quel commit. La scelta usa gli [hook Form Script e l'API `set_df_property` documentati da Frappe](https://docs.frappe.io/framework/user/en/api/form), verificati anche nel sorgente Frappe 16.50 pinned. Non dichiarare localizzazione globale PASS sulla base di CSV, PDF o test offline.

## Demo e accesso

Il DEV risponde soltanto su `127.0.0.1:8082`; nessuna nuova porta pubblica. L'Owner usa il tunnel e le credenziali demo del [runbook](../../uat/CLIENT-DEMO-RUNBOOK-2026-10-19.md). I **12/12 percorsi** hanno route raggiungibili nel browser e prove funzionali precedenti; **nessuno dei 12 flussi con scrittura è stato rieseguito integralmente** in questo collaudo di localizzazione. I 46/46 PASS MVP sono evidenza storica, non nuovi test di questa installazione.

**Stato per review:** il DEV aggiornato è utilizzabile e pronto a una verifica visiva Owner dei percorsi principali. `CLIENT_DEMO_READY_FOR_OWNER_REVIEW = NO` nel criterio rigoroso di italiano completo, per i testi upstream avanzati sopra elencati e le validazioni non coperte live. Il commit successivo di correzione è nel repository ma NON nel DEV. Nessun Owner visual PASS, accettazione cliente, merge, produzione o GOAL-03.
