# CENTROCHANGE-MVP-FUNCTIONAL-COMPLETION-REPORT

**Esito: PARTIAL — candidato locale implementato e verifiche offline superate; le sei voci restano da collaudare sul runtime DEV.**

Data: 15 ottobre 2026 UTC. Branch locale dedicato `audit/mvp-functional-completion`, derivato dalla baseline dell’audit e dal candidato applicativo installato. Nessun deploy, reset, migrazione, riavvio, scrittura o test mutativo sul DEV; nessuna pubblicazione o modifica GitHub.

## Baseline e conteggi

L’audit originale è preservato senza modifiche in `CENTROCHANGE-MVP-FUNCTIONAL-ACCEPTANCE-AUDIT-2026-10-14.md` e `capability-matrix.csv`. La sua baseline rimane **40 PASS / 6 PARTIAL**, su **46 voci MVP** (44 capability attive e 2 requisiti trasversali approvati). Sei voci future/out of scope non fanno parte del conteggio.

Le sei PARTIAL originali, confermate leggendo matrice e report:

| Voce | Lacuna verificata dall’audit | Intervento nel candidato | Stato dopo questo lavoro |
|---|---|---|---|
| CC-CAP-029 | CSV con intestazioni inglesi e date ISO | Intestazioni italiane, date `GG/MM/AAAA`, orari `HH:mm`, metodo di pagamento nei report finance/paziente/professionista/agenda | PARTIAL — test offline; download e valori runtime da verificare |
| CC-CAP-042 | Un pagamento non consentiva la scelta esplicita del metodo carta/POS | Selezione nativa Mode of Payment; il server risolve e valida il conto associato alla società; il Payment Entry conserva il metodo; UI espone il campo. Il fingerprint legacy resta invariato senza metodo esplicito e lega il metodo nelle richieste POS | PARTIAL — accettazione backend/browser aggiunta, non eseguita su Frappe live |
| CC-CAP-047 | General Ledger e Trial Balance non erano raggiungibili con un’interfaccia sicura | Servizio read-only con allowlist di due report, società/centro di costo forzati sul centro operativo, periodo limitato, massimo 2.000 righe, CSV sicuro e accesso finance/Commercialista; nessun riuso dell’endpoint report generico | PARTIAL — test di accettazione aggiunti; esecuzione su ERPNext 16.50 non fatta |
| CC-CAP-050 | Test obsoleti su ID RC22/fixture e messaggi inglesi; viaggio browser completo non ripetuto | Test aggiornati a record e ruoli correnti; regressione riapertura usa fixture isolata rollback-only; rimosso riscrittura in memoria della suite | PARTIAL — suite offline PASS; suite Frappe/browser non eseguita |
| SCOPE-DOC | Nessun percorso ordinario per allegati amministrativi manuali | Upload di PDF/JPG/PNG privati via File nativo, limite 5 MB, associazione a fatture/movimenti ammessi, controllo sede/permesso, motivo e audit | PARTIAL — guard e scenario browser aggiunti; persistenza e download autorizzati richiedono DEV |
| UAT-GLOBAL | Export/localizzazione e selettore multiplo mobile; accettazione visiva Owner aperta | Correzione del layout mobile per select multipli senza trasformare la semantica multi-valore; export italiano/europeo; schermate finanziarie mostrano allegati e report | PARTIAL — controllo sorgente/sintassi, senza Chromium; review visiva Owner resta separata |

La matrice di avanzamento dei sei elementi è `capability-matrix-completion.csv`. Non trasforma l’evidenza statica o offline in PASS funzionale. Gli altri 40 PASS sono riportati come esiti dell’audit del 14 ottobre e non sono stati rieseguiti né rivalutati in questa consegna.

## Modifiche implementate

- Pagamento singolo paziente/fornitore: aggiunta selezione Mode of Payment ERPNext e risoluzione server-side del conto, con verifica che il metodo sia attivo, abbia una sola mappatura per società e usi un conto attivo, di dettaglio, Bank/Cash e della valuta corretta. Il conto fornito non può contraddire quello del metodo scelto. Il metodo entra nella chiave di idempotenza solo quando è specificato; le richieste legacy mantengono il fingerprint precedente. Rimangono le regole di importo, residuo, audit e controller contabile nativo.
- Report contabili: nuova superficie interna Finance che espone solo Libro giornale e Bilancio di verifica read-only. Accesso limitato ai ruoli finance esistenti, al centro operativo scelto e alla società/centro di costo configurati; periodo massimo 366 giorni, esercizio fiscale verificato per Trial Balance, risultati limitati e CSV con celle protette da formula.
- Allegati: servizio circoscritto al File nativo e a Sales Invoice, Purchase Invoice, Bank Transaction e CC Incoming Invoice. File privato locale, tipi/formati controllati, dimensione massima, lettura subordinata alla lettura del documento e autorizzazione di scrittura Finance sul centro; evento audit con motivo. Restano attivi i guard File generici e il blocco dei file pubblici/remoti.
- Export e presentazione: intestazioni in italiano, date europee, orari a 24 ore, categorie/stati localizzati e metodo di pagamento incluso negli export pertinenti. Il controllo multi-select conserva la selezione di insieme su mobile.
- Test: fixture finance del browser usa una fattura sintetica identificata dal tag del test, non la prima fattura persistente del dataset; cleanup usa i record esatti dei centri sintetici. Aggiornati test obsoleti per banca, confronto compensi, audit e riapertura sedute; la riapertura prepara ora dati sintetici e usa rollback. La frase italiana dell’errore DST è attesa dal test. Il probe non altera più il sorgente dei test in memoria.

## Test eseguiti in questa consegna

| Controllo | Esito |
|---|---|
| `python3 -m compileall -q app/centrochange_core/centrochange_core infra` | PASS |
| `node --check infra/browser/finance.cjs` | PASS |
| `node --check infra/browser/native_reports.cjs` | PASS |
| `node --check infra/browser/bank_trace.cjs` | PASS |
| `python3 -m unittest discover -s infra/tests -p 'test_*.py'` | PASS — 63 test |
| `git diff --check` | PASS |
| Test source-level dei confini POS, report, File privati, fixture e multi-select | PASS — inclusi nei 63 test offline |

Non eseguiti: chiamate Frappe/ERPNext, test di controller, suite browser Playwright, download/permessi File effettivi e test end-to-end con commit. Eseguirli contro il DEV comporterebbe scritture persistenti del dataset Owner; nessun ambiente clone è autorizzato. Di conseguenza POS, report nativi e allegati sono implementazioni candidate, non funzionalità dimostrate operative.

## Processi interessati

Sono stati preparati scenari browser per: fattura sintetica → pagamento parziale con metodo nativo → residuo; file PDF sintetico collegato alla stessa fattura → verifica negata a un professionista; report standard → export CSV; saldo e riconciliazione bancaria già presenti nel flusso Finance. Gli acceptance backend verificano anche replay, payload diverso sullo stesso idempotency key, conto non corrispondente, report fuori allowlist/centro/esercizio e ruolo professionista negato.

Questi scenari sono **test aggiunti**, non test funzionali eseguiti. Nessuna catena viene dichiarata PASS in questa consegna.

## Limiti e piano unico

1. Eseguire il candidato su un ambiente Frappe isolato/versione pinned o, con autorizzazione separata, applicarlo al DEV con fixture sintetiche e cleanup verificato; eseguire le acceptance backend e browser per pagamento POS, report, allegati e ruoli.
2. Verificare il recupero dei file privati e la negazione degli accessi diretti non autorizzati, inclusi byte download e metadati.
3. Eseguire le suite aggiornate `CC-CAP-050` senza modifiche runtime non tracciate; confrontare i risultati con i 14 esiti non-zero del report iniziale.
4. Eseguire Chromium desktop/mobile per layout multi-select e stringhe/localizzazione; la valutazione visiva e l’accettazione restano Owner.
5. Solo dopo tali test, aggiornare gli stati delle sei righe. Nessun requisito di provider, addebito effettivo o invio fiscale reale è stato aggiunto.

## Candidato e repository

La baseline applicativa installata documentata nell’audit è `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`; l’attuale lavoro è un delta locale sopra la linea PR #140, in branch dedicato. Il DEV descritto dall’audit: progetto singolo `centrochange-dev`, nove servizi attivi, sei servizi applicativi sulla stessa immagine `sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc`, Frappe/ERPNext 16.50.0; nessuna modifica runtime in questa consegna.

Moduli principali toccati: `finance/receivables.py`, `finance/incoming.py`, `finance/native_adapter.py`, `finance/native_reports.py`, `finance/attachments.py`, `finance/files.py`, `finance/reporting.py`, `finance/patient_reporting.py`, `operations/reporting.py`, `public/js/finance_workspace.js`, `public/js/search_select.js`, relative acceptance/backend/browser e regressioni fixture.

Commit implementazione: `d41ac30` (`feat(mvp): close functional audit gaps in candidate`), branch locale non pubblicata. Nessuna PR o issue GitHub è stata modificata: il mandato non autorizza pubblicazioni GitHub. Il commit documentale successivo contiene questo rapporto e la matrice di avanzamento.
