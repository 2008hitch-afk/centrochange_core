# CENTROCHANGE-MVP-FUNCTIONAL-ACCEPTANCE-AUDIT

**Esito complessivo: PARTIAL. Non è ancora dimostrato che tutto l'MVP promesso sia completo e utilizzabile dai ruoli cliente.** Il nucleo operativo e i flussi economici simulati superano prove reali sul DEV. Restano lacune di copertura funzionale, di accessibilità delle funzioni approvate e di collaudo. Non è emerso un nuovo errore di calcolo contabile nei casi eseguiti. Questo rapporto non attribuisce accettazione Owner né completa GOAL-02.

Audit del 14 ottobre 2026 UTC, sul DEV già installato. Nessun deploy, riavvio, migrazione, clone, modifica del prodotto o aggiornamento GitHub. Le proposte sotto sono soltanto locali.

## 1. Risposta alla domanda Owner e conteggi

Il registro ufficiale contiene **50 capability storiche/delivery**: **44 attive** e **6 rinviate o sostituite**. Per evitare che il registro nasconda requisiti approvati successivamente, l'inventario aggiunge due righe esplicite: allegati amministrativi manuali dallo scope Finance e requisiti globali di utilizzabilità/localizzazione dalla UAT Owner. Queste sono etichette di audit, non nuove capability o nuovi requisiti.

**Unità di conteggio: 46 voci di accettazione MVP**, composte da 44 capability attive e 2 requisiti espliciti trasversali. Non sono 46 schermate, endpoint o test. Ogni macro-capability comprende più condizioni, specificate nella matrice e nelle prove. I dettagli POS/report/export non vengono contati di nuovo fuori dalla capability di appartenenza.

| Esito consentito | Voci MVP | Interpretazione |
|---|---:|---|
| PASS | **40** | Comportamento implementato e provato nel perimetro sintetico dichiarato; non giudizio Owner |
| PARTIAL | **6** | 029, 042, 047, 050, SCOPE-DOC, UAT-GLOBAL: dettagli sotto |
| FAIL | **0** | Nessun nuovo malfunzionamento di prodotto dimostrato nei casi effettivamente eseguiti |
| MISSING | **0 macro-voci totalmente assenti** | Ci sono sottopercorsi mancanti/inaccessibili: allegati cliente, POS distinto e report standard. Sono PARTIAL perché le infrastrutture/funzioni circostanti esistono |
| BLOCKED | **0 macro-voci interamente non verificabili** | Restano prove specifiche BLOCKED: sezione 6. Non sono state trasformate in PASS |
| FUTURE/OUT OF SCOPE | **6 righe del registro**, escluse dai 46 | 015 sostituita da 041–050; 021/031/032/036/037 rinviate. Ulteriori esclusioni esplicite sotto |

Non è corretto concludere «tutto funziona» dai 40 PASS. In particolare, i PASS contabili riguardano registrazioni reali nel database DEV, controllate e poi annullate con rollback; non provano una nuova sessione completa di operatore, tra più richieste HTTP, con tutte le registrazioni definitive.

## 2. Fonti e precedenza

Fonte cliente: `2008hitch-afk/hitch-client-discovery`, commit **`32f70bb7b615bc27ac5eb28de4c90d3db07e76c6`**. [Provenienza di 34 documenti, con hash e URL immutabili](source-provenance.json).

Sono stati confrontati:

- manifest HC-0005 e `IMPLEMENTATION-001`: GOAL-02 attivo, Missione C sospesa, GOAL-03 non autorizzato;
- Discovery `CLIENT-REQUESTS-SNAPSHOT` e `RUN-001-CLIENT-EVIDENCE`: riduzione del reinserimento pazienti, conteggio sedute per professionista e passaggi amministrativi manuali;
- scope Finance/Admin **REV3**, baseline eseguibile, matrice ruoli/accettazione, modello degli stati;
- decisioni su identità centrali, centro unico con dimensione sede, catalogo, appuntamento canonico, package ledger, 48h, accounting, banca/POS, report e documenti;
- DECISION-053: prezzo alla data prenotazione; DECISION-054: soglia N per coppia paziente/professionista; DECISION-059 prevale sulla 058 e rinvia #78;
- repository applicativo: `AGENTS.md`, README, ARCHITECTURE, SECURITY, DECISIONS, baseline runtime, roadmap GOAL-01→05, capability map, completion report GOAL-02 e acceptance criteria delle issue;
- tracker #69, issue #136/#139, PR #140, report #127/#133 e UAT precedenti; #63/#66/#68 rimangono accettate, senza riapertura.

Gli stati storici dei documenti non vengono confusi con quelli attuali. Il vecchio completion report e `RUNTIME-BASELINE.md` descrivono anche versioni 16.31/16.32; il runtime verificato è **16.50.0**. `runtime_validated: false` nella capability map è una fotografia iniziale di pianificazione, non una misura aggiornata. Issue #23 chiusa non implica Owner Acceptance: manifest e tracker mantengono il gate finale aperto.

L'accounting non è fuori scope per effetto della vecchia CC-CAP-015: lo scope Finance approvato e le capability 041–050 lo hanno incluso. Gli adapter SdI/TS sono provati esclusivamente in simulazione, come previsto per GOAL-01/02. Il trasporto reale resta fuori dal presente gate DEV, pur appartenendo alle successive attività di consegna/produzione.

## 3. Baseline effettivamente verificata

- Repository/PR #140 DRAFT: **`7f9784f3711f5bb7ef3bbc9498dc016db8f9f6da`**, verificato contro GitHub; candidato applicativo **`0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`**.
- Audit locale: branch `audit/mvp-functional-20261014`, worktree `/tmp/centrochange-mvp-functional-audit`. Il checkout `/home/empv26/src/centrochange_core` è più vecchio, branch #97, e non è stato usato come baseline applicativa.
- Unico progetto `centrochange-dev`, **9 servizi attivi**. I sei servizi applicativi servono **`sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc`**, tag `centrochange-single:issue139-realtime-v2`.
- Frappe/ERPNext **16.50.0**, Healthcare **16.6.1**, Builder **1.35.1**. Site `centrochange.local`, stesso database applicativo; sei hook sicurezza/lingua presenti.
- Centro A operativo; Centro B inattivo. `require_operations(B)` rifiuta tutti e sette i ruoli demo, inclusa Direzione. Nessuna nuova sede o modifica permessi.
- I risultati W5 della **terza installazione**, sulla medesima immagine, sono riusati: 128/128 visite browser, 22/22 coppie List/Form, 38/38 controlli HTTP di sicurezza e autenticazione realtime. Non si riusano i risultati dei tentativi conclusi con rollback come prova dello stato attuale.

Evidenze: [stato finale](runtime-final.json), [letture funzionali](readonly-runtime.json), [report installazione corrente](../issue-139/GOAL02-UNIFIED-REMEDIATION-REPORT-2026-10-14.md#terza-installazione-distinta--stato-dev-corrente).

## 4. Prove eseguite e loro significato

| Prova | Esito osservato | Cosa dimostra / limite |
|---|---|---|
| 22 entrypoint storici sul DEV | 8 uscite 0, 14 uscite nonzero | Quattro precondizioni RC22 obsolete e dieci suite bloccate dalla stessa asserzione linguistica. Non sono 14 difetti di prodotto |
| `operations.integration_acceptance.run`, con adattamento locale della sola asserzione linguistica | **PASS: 189 controlli nominati, 177 etichette distinte** | Catena reale scheduling/operazioni/Finance/banca/fatture/compensi/report/SdI/TS. Etichette ripetute rappresentano anche attori diversi; non sono 189 funzionalità |
| Ricerca, report Professionista/Paziente, matrice ruoli, conferma prenotazione | **PASS: 46 controlli nominati** | Risultati e scope verificati sul dataset attuale; confronti economici con record nativi; alcuni test in rollback |
| Confine Desk tecnico | **PASS: 7 ruoli × 7 tipi tecnici** | Nessun accesso cliente a configurazioni tecniche; Administrator separato |
| Sette master/configurazioni native | **PASS: 7 cicli insert→save→reload** | Patient, Healthcare Practitioner, Item, Item Price, Appointment Type, CC Center Service, CC Package Template, su record nuovi e rollback. Ruolo tecnico Administrator, non attribuito automaticamente a tutti i ruoli cliente |
| HTTP read-only sette ruoli | **28 osservazioni registrate** | Ricerca/Finanza coerenti con ruolo; due report contabili standard 403 anche a m/s/f/t. Questa parte evidenzia il gap, non un PASS generale |
| Registro e banca sul dataset corrente | **PASS** | Eventi realmente esistenti, sei ruoli negati sul registro; movimento riconciliato conserva documento, soggetto e importo |
| Chromium dettagli Banca/confronto | **PASS: 4 criteri × 2 viewport** | Desktop 1440 e mobile 390: documento e importo reali, nessun secondo match, conferma/motivo richiesti per annullo senza eseguirlo, selettore con ID canonici. Nessuna scrittura business o errore JS |
| Allegato manuale nuovo su fattura, invocazione guard prima insert | **PARTIAL funzionale** | Rifiuto effettivo per m/s/f/t; nessun file inserito. Il percorso ordinario approvato non è disponibile in questo servizio |
| Integrità | **PASS** | 107 tabelle/tipi business e relativi figli: hash completi uguali prima/dopo integrazione; stessa verifica sulle prove native. Impronta generale finale uguale all'inizio audit |

Dettagli: [integrazione e tutte le etichette](integrated-runtime.json), [suite supplementari](supplemental-suites.json), [master nativi](native-runtime.json), [HTTP](http-readonly.json), [browser](browser-readonly.json), [esiti iniziali conservati](initial-suite-results.json).

La prima chiamata `bench execute` maschera l'eccezione originale con `NameError: name 'centrochange_core' is not defined` nel fallback di Frappe. La diagnosi ha usato il primo traceback: il prodotto rifiuta correttamente un orario DST ambiguo con messaggio italiano; `surfaces_acceptance.py` cerca ancora la frase inglese `Ambiguous or nonexistent`. Nel processo di audit è stata adattata **soltanto quell'asserzione del test**, conservando tipo d'errore e rifiuto. Nessun modulo di prodotto è stato modificato, distribuito o sostituito; la suite originale continua a richiedere una correzione futura nel repository.

Le prove supplementari con ID RC22 sono state sostituite nell'audit da identificazione dei record correnti, senza modificare il prodotto: tracciabilità banca, eventi registro e confronto fatture. Il vecchio test `reopen_acceptance` non è stato trasformato in requisito di correzione storica: #78 è rinviata. Le correzioni ordinarie di chiusura sono invece coperte dalla suite operativa.

## 5. Processi completi verificati

| Processo | Esito | Evidenza sostanziale |
|---|---|---|
| Intake paziente→assegnazione→ricerca/accesso→revoca | PASS | Una sola identità e assegnazione, UID/replay, input invalido senza residui, accesso precedente revocato |
| Disponibilità→prenota→Agenda→sposta→cancella | PASS | Intervalli e assenze, collisioni, stessa seduta, snapshot invariato, stato/cancellazione; concorrenza HTTP riusata da W5 |
| Pacchetto→riserva→cancellazione o svolgimento→saldo | PASS | Rilascio a 48h, consumo tardivo/svolto, rinuncia append-only, saldo senza doppio consumo |
| Seduta→chiusura→fonte economica→fattura→incassi→report | PASS nel rollback integrato | Sales Invoice e GL reali, residuo parziale/totale, origine seduta conservata, aggregati riconciliati, fatto Paid operativo distinto |
| Insoluto→blocco prossima seduta→override→incasso | PASS | Blocco server, differimento auditato senza eliminare il debito, scadenza e rivalutazione corretti |
| Movimento→candidato/ambiguità→riconciliazione→storno | PASS | Payment Entry/allocazione/GL, residui coerenti; cancellazione ripristina debito; UI attuale mantiene fattura Beta e 60 EUR |
| XML ricevuto→fornitore→classificazione→Purchase Invoice→pagamento | PASS in simulazione | Originale privato, doppioni e XML non sicuro respinti/classificati, submit esplicito, passività e pagamento, rettifica con originale conservato |
| Sedute→soglia N→compenso→confronto fattura→coda | PASS | N=0/1/2/5 e coppie indipendenti, sospeso/unknown, override, incasso/storno rivalutano; OK/REVIEW e riferimenti esatti |
| Documento→SdI simulato→retry/esito→correzione | PASS in simulazione | XML, tentativi e protocollo sintetico immutabili, dedupe, tre tentativi e catena correzione |
| Spesa→revisione opposizione/eligibilità→TS simulato→correzione | PASS in simulazione | Versioni persistite nella transazione, unknown bloccato, retry e risultato distinti da SdI, coda aggiornata |
| Condizione amministrativa→assegna→rinvia→riappare/chiude | PASS | Identità condizione e audit preservati, nessun doppione, chiusura/ripristino coerenti con fonte |
| Primo incontro pubblico→identità/seduta→conferma | PASS in simulazione | HTTP W5 con fixture e cleanup, Communication locale immediata e replay; nessun SMTP |
| Tutto il viaggio con operatore browser e commit tra ogni fase | BLOCKED in questo audit | I preparatori HTTP Finance storici scrivono anche configurazioni contabili condivise. Non vengono eseguiti indiscriminatamente sul dataset Owner; non si spaccia il rollback transazionale per quella prova |

I test integrati leggono i record appena salvati, eseguono i controller ERPNext reali e controllano GL/Payment Ledger/valori; non sono mock di HTTP 200. Il clock sintetico è confinato alle fixture temporali. La prova non qualifica carico, valute estere, più rate, provider reali o un'intera giornata reale di scheduler.

## 6. Gap e test BLOCKED, senza confondere prodotto e collaudo

| ID audit | Priorità / categoria | Riscontro e impatto | Azione proposta, non eseguita |
|---|---|---|---|
| G1 | P1 — funzione CORE incompleta | DECISION-031 richiede carta/POS con `Mode of Payment`/conto appropriato. `receivables.pay` e `incoming.pay` non accettano il metodo per pagamento; la UI non lo propone. I 3 Payment Entry demo hanno metodo nullo. Incasso/banca funzionano, ma distinzione contante/carta per operazione non dimostrata | Progettare il minimo percorso contabile native-first per scelta/metodo e conto autorizzato; fixture non-Owner contante/POS/bonifico, residui e report. Nessuna integrazione acquirer richiesta |
| G2 | P1 — funzione CORE non raggiungibile | DECISION-033 include report contabili standard ERPNext. General Ledger e Trial Balance restituiscono 403 per tutti i sette account demo, inclusi Direzione/Finance/Commercialista. I report custom funzionano | Concordare un accesso/report nativo con scope corretto o equivalente esplicitamente accettato; mai rimuovere il guard SQL o ampliare permessi per tentativi. Test totale/drill-down e cross-center |
| G3 | P1 — funzione CORE incompleta | REV3/DECISION-034 includono allegati manuali di ricevute/PDF/scansioni. La guard `finance.files.protected` respinge i nuovi allegati di fatture senza contesto di servizio; i servizi trovati gestiscono XML fiscali. Nessun percorso ordinario per allegare il PDF è provato | Aggiungere/proporre servizio di allegato privato per parent autorizzato e immutabilità, riusando File nativo. Test upload/download, tipi, ownership, lettura contabile e dinieghi. Nessun OCR richiesto |
| G4 | P1 — gate di collaudo incompleto | Dieci suite concatenate non attraversano Finance con la loro asserzione inglese originale. Quattro test usano vecchi ID/date RC22. Il runner integrato originale non è verde sul candidato attuale | Aggiornare test per assert semantici/lingua prevista e lookup fixture. Confermare cleanup prima di nuove suite HTTP mutative. La patch del test in memoria è evidenza dell'audit, non fix distribuito |
| G5 | P2 — UX/localizzazione | CSV Finance genera `kind,name,date...`, `Sales Invoice` e `2026-09-29`, in contrasto con export umano italiano/GG-MM-AAAA. Confronto mobile taglia importo/stato nelle opzioni. W5 aveva già notato alcuni label nativi inglesi e doppio stato attivo Inizio/Agenda | Unificare output umano e selettori senza cambiare valori canonici; retest visivo Owner #75/#79/#80/#134 |
| G6 | P2 — copertura UI funzionale | Le 22 List/Form provano rendering; i 7 cicli di save di questo audit sono controller backend con Administrator. Non dimostrano edit/save browser per ogni ruolo e scheda | Fixture proprie e test browser List→Form→salva→rileggi con ruolo previsto. Non concedere a Direzione il setup tecnico escluso dal profilo approvato |

Non si propone alcun nuovo accesso alle note riservate. G2/G3 richiedono rispettare la policy esistente e una review del percorso autorizzato; l'audit non concede automaticamente nuovi permessi.

**Prove specifiche BLOCKED o non completate:**

1. Viaggio economico completo con commit e browser/API in richieste separate: il preparatore `finance.dev_profile.setup` modifica Company/CC Finance Settings e il preparatore HTTP esegue commit; non è dimostrata l'assenza di effetti condivisi. Il runner rollback ha invece vietato ogni commit e verificato tutti i record.
2. Pagamento carta/POS distinto dall'incasso di default: manca un percorso client collaudabile; non viene inventata una configurazione del conto o un nuovo permesso.
3. Fruizione dei report standard con ruoli cliente: 403 provato, quindi nessun risultato contabile di tali report è dichiarato PASS.
4. Upload amministrativo manuale: guard negativa provata prima della scrittura; nessun test positivo inventato e nessun file Owner modificato.
5. Runner originali bloccati da lingua e ID RC22: risultati negativi conservati, senza etichettarli come FAIL applicativi.
6. Tutti i form modificati/salvati in Chromium con ogni ruolo, assieme a tutti gli stati contabili: non provati dalle sole 128 visite/22 coppie.
7. Esecuzione autonoma dei reminder alle reali 21:00/07:00 lungo una giornata: non attesa né forzata; logica testata con clock sintetico, sei job configurati attivi. `last_execution` non prova da solo consegna di ogni job.

Questi limiti impediscono una dichiarazione universale di completezza. Non annullano i PASS dei singoli percorsi e delle condizioni realmente esercitate.

## 7. Integrità e dati persistenti

Prima e dopo ogni prima suite il fingerprint business di checkpoint è risultato uguale. Per la prova integrata adattata e i master nativi è stato aggiunto il controllo **dei valori completi di 107 DocType/tabelle**, inclusi figli, File, documenti/ledger contabili, note, assegnazioni e configurazioni. Nessun `ignore_permissions` aggiuntivo è stato introdotto dal runner; le suite preesistenti utilizzano setup tecnico esplicito e poi ruoli applicativi nei controlli pertinenti.

- Fingerprint Owner a inizio audit/fine: **`3d20b50fa303d52fb9b4a467b12425303a87fcb7b8d36ce82559e1a2c5174671`**.
- Communication: **`b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`**, invariato.
- 9 Patient, 2 Healthcare Practitioner, 13 Patient Appointment, 4 Sales Invoice, 1 Purchase Invoice, 3 Payment Entry, 2 Bank Transaction, 134 CC Audit Event, 2 Booking Confirmation, 4 Fiscal Transaction, 0 Professional Comparison.
- Il checkpoint dell'audit è successivo alla consegna della terza installazione: comprende un ulteriore evento `APPOINTMENT_BOOKED` già presente prima dei test. Non si confronta falsamente la baseline audit con i 133 eventi del precedente report di deploy.
- Nessun reset/reseed, pulizia generica o modifica persistente dei record business. Login/sessioni e normali log tecnici non sono inclusi nella promessa di immobilità del dataset.
- Per le suite rollback i commit sono vietati nel processo; un tentativo interrompe la prova. Il rollback elimina le scritture DB e i callback post-commit. Non vengono lanciati provider reali.

Questo controllo non è un hash byte-per-byte dell'intero database, dei log e della cache. Non è una prova di backup nuova; riusa le evidenze cifrate/restore già concluse. [Hash completi dei record](business-record-integrity.json).

## 8. Funzionalità fuori MVP e decisioni ancora esterne

- CC-CAP-015 è sostituita dalle nuove capability Finance; non esclude più fatture/incassi dall'MVP.
- Patient Progress/analytics cliniche, sito pubblico branded completo e relativo Builder/Git restano rinviati.
- DR/qualifica upgrade di produzione restano gate successivi; la rehearsal recente è evidenza tecnica riusata, non avvio GOAL-03.
- **#78 / PR #128:** correzione dell'orario di seduta già storica esclusa dall'MVP da DECISION-059. Non è un difetto da riaprire per chiudere questo audit.
- Optional: live bank feed/open banking, POS/acquirer automatico, matching professionista riga-per-riga avanzato, dunning multistep, gestione avanzata dei costi, forecast/tesoreria, OCR, approvazione spese formale, budget, portale commercialista dedicato, payment link/gateway, analytics eccezioni e checklist close periodica.
- Dati fiscali reali, credenziali/provider SdI/TS, SMTP reale, attestazione commercialista e produzione restano fuori dal collaudo sintetico GOAL-02. La mancanza di invio reale non viene etichettata come errore del simulatore.
- `indicative_margin=null` non viene convertito in zero o dichiarato errore senza una policy di calcolo definita; lo scope lo richiede dove definito. Gli importi sconosciuti/sospesi e le configurazioni mancanti restano espliciti.

## 9. Piano unico di correzione proposto

1. **Allineare scope e copertura dei tre sottopercorsi CORE** G1–G3. Definire il percorso minimo contanti/POS, report standard autorizzati e allegati amministrativi. Usare strutture native; nessun backend parallelo, acquirer o ampliamento implicito dei ruoli.
2. **Rendere affidabile il gate funzionale** G4/G6: correggere solo test/fixture obsoleti, preparare fixture contabili completamente proprie con verifica anche di Company/settings/file/ledger e cleanup esatto. Aggiungere un viaggio operatore completo attraverso richieste distinte con risultati persistiti e poi rimossi esclusivamente per ownership verificata.
3. **Chiudere localizzazione e utilizzo** G5: export umano italiano, selettori mobile leggibili, label e spiegazioni. Conservare i contratti API/DB/fiscali e i PASS operativi.
4. **Owner UAT finale mirata:** un solo percorso concordato: paziente sintetico→prenotazione→chiusura→fattura→incasso/metodo→report, poi XML professionista→confronto→pagamento/banca; consultare audit e simulazioni fiscali. Separare risultato funzionale e review visiva.

Le proposte di aggiornamento GitHub sono pronte come testo nel rapporto: tracker #69 per matrice e gate; #75/#79/#80/#134 per G5/G6; #77 per review del percorso report senza rimuovere protezioni; collegare G1–G3 al perimetro #39/#46 e scope Finance, senza riaprire automaticamente issue chiuse. #62 e #81 hanno evidenza attuale positiva per i dettagli provati; #71 registro attuale positivo; #73 conferma simulata positiva. Non chiudere issue né attribuire Owner PASS automaticamente.

**Decisione successiva raccomandata:** review Owner/HITCH di questo inventario e autorizzazione di un unico pacchetto di completamento per i gap effettivi. Non servono nuove missioni preparatorie, cloni o reinstallazioni per discutere il quadro. Nessun aggiornamento GitHub è stato eseguito, come richiesto.

## 10. Accesso ed evidenze ripetibili

DEV disponibile tramite tunnel privato già previsto:

```sh
ssh -N -L 8082:127.0.0.1:8082 empv26@srv2033673
```

Aprire `http://127.0.0.1:8082/app/cc-unified-desk?cc_view=agenda` con le credenziali demo già consegnate nel canale sicuro. Finance/Commercialista usano la destinazione Finanza autorizzata. Nessuna password è nel rapporto.

Screenshot nuovi: [Banca desktop](screenshots/bank-trace-1440.png), [Banca mobile](screenshots/bank-trace-390.png), [confronto desktop](screenshots/comparison-1440.png), [confronto mobile](screenshots/comparison-390.png). La lettura visiva conferma il riferimento fattura/importo banca e il taglio delle etichette del selettore mobile. Il PASS tecnico del browser non è un PASS visivo di quel difetto.

I probe locali sono in `infra/audit/`: `mvp_rollback_probe.py`, `mvp_native_rollback_probe.py`, `mvp_readonly_probe.py`, `mvp_http_readonly.py`, `mvp_finance_readonly.cjs`. Non modificano l'app installata. La sola compatibilità linguistica del test è esplicita nel sorgente del probe. Il probe nativo usa il preambolo comune del probe rollback fino al commento `# The pinned product`, poi esegue le prove native al posto dell'integrazione. I log completi restano privati in `~/.local/state/centrochange-single/mvp-functional-audit-20261014/`; screenshot raw in `browser-evidence/mvp-functional-20261014/`.

I probe backend sono stati inviati su stdin a `docker exec -i -e FRAPPE_STREAM_LOGGING=1 -w /home/frappe/frappe-bench/sites centrochange-dev-backend-1 /home/frappe/frappe-bench/env/bin/python`. Nessun file è stato copiato nel container. Chromium usa Playwright locale esistente: `NODE_PATH=/tmp/cc-browser-qa/node_modules`, librerie `/tmp/cc-browser-libs/usr/lib/x86_64-linux-gnu`; non è disponibile un browser plugin locale collegato al DEV. Nessuna dipendenza installata per l'audit.

Prima di una ripetizione mutativa va ricontrollata la baseline e la compatibilità della fixture: i comandi di prova non sono una nuova autorizzazione a cambiare il runtime o i dati Owner.

## 11. Matrice requisito → implementazione → test → esito → evidenza

La matrice completa è incorporata qui sotto e disponibile anche in [CSV](capability-matrix.csv) e [JSON](capability-matrix.json). I percorsi applicativi sono relativi a `app/centrochange_core/centrochange_core`; i percorsi `infra/` al repository. W5 identifica esclusivamente la terza installazione corrente. Le fonti originali puntuali sono nel registro di provenienza e nelle sezioni 2/6.

| ID | Funzionalità | Implementazione¹ | Ruoli | Esito | Prova / limite | Evidenza |
|---|---|---|---|---|---|---|
| CC-CAP-001 | Runtime e isolamento DEV | `infra/compose.yaml` | Tecnico | PASS | Nove servizi, immagini e hook; baseline installata e W5 riusati | runtime-final.json |
| CC-CAP-002 | Identità professionista e utente | `security/lifecycle.py` | Direzione; setup tecnico | PASS | Creazione nativa, assegnazioni, cambio principal e disabilitazione con revoca | integrated-runtime.json; native-runtime.json |
| CC-CAP-003 | Anagrafica paziente centrale | `operations/workspace.py` | Segreteria/Direzione; setup tecnico | PASS | Intake e UID univoco, replay, rollback creazione non valida, salvataggio nativo | integrated-runtime.json; native-runtime.json |
| CC-CAP-004 | Assegnazione paziente/professionista | `security/lifecycle.py` | Direzione/Segreteria secondo azione | PASS | Riassegnazione e revoca effettive; accessi precedenti negati | integrated-runtime.json; supplemental-suites.json |
| CC-CAP-005 | Segregazione appuntamenti | `security/permissions.py` | Professionisti assegnati | PASS | Own/cross record, liste, API, revoca centro; HTTP W5 sulla stessa immagine | integrated-runtime.json; W5 |
| CC-CAP-006 | Appuntamento e seduta canonica | `scheduling/booking.py; operations/lifecycle.py` | Operativi autorizzati | PASS | Prenota, sposta, cancella, chiude; stessa identità, replay e stati controllati | integrated-runtime.json |
| CC-CAP-007 | Disponibilità ricorrente e assenze | `scheduling/availability.py` | Professionista proprio; Direzione | PASS | Creazione/modifica orari, assenza nativa, cancellazione assenza, disponibilità ripristinata | integrated-runtime.json |
| CC-CAP-008 | Collisioni e concorrenza | `scheduling/booking.py` | Operativi autorizzati | PASS | Conflitti paziente/professionista; W5 HTTP: una sola prenotazione concorrente e una unità pacchetto | integrated-runtime.json; W5 |
| CC-CAP-009 | Primo incontro pubblico limitato | `scheduling/public_booking.py` | Guest, route approvate | PASS | HTTP reale W5: route vincolata, creazione una volta, replay, route arbitraria/disabilitata negata | W5; supplemental-suites.json |
| CC-CAP-010 | Sedute successive solo backend | `scheduling/public_booking.py; security/api.py` | Operativi autenticati | PASS | W5 nega prenotazione pubblica successiva e bypass portale Marley | W5 |
| CC-CAP-011 | Catalogo servizi centrale per sede | `scheduling/booking.py; centro_change_core/doctype/cc_center_service` | Setup tecnico; consultazione autorizzata | PASS | Item e tipo seduta creati/salvati; servizio disabilitato rifiutato; CC Center Service salvato | native-runtime.json; integrated-runtime.json |
| CC-CAP-012 | Listini e prezzi | `scheduling/booking.py` | Setup tecnico; uso operativo | PASS | Item Price salvato e riletto; selezione tariffa alla data prenotazione | native-runtime.json; integrated-runtime.json |
| CC-CAP-013 | Snapshot servizio/durata/prezzo | `scheduling/booking.py` | Operativi autorizzati | PASS | Cambio tariffa/catalogo non riscrive seduta; tampering rifiutato; spostamento conserva snapshot | integrated-runtime.json |
| CC-CAP-014 | Pagato operativo e metodo informativo | `operations/lifecycle.py` | Operativi autorizzati secondo stato | PASS | Correzioni ordinate e audit, replay, separazione dall'incasso contabile | integrated-runtime.json |
| CC-CAP-016 | Pacchetti e ledger | `operations/packages.py` | Operativi autorizzati | PASS | Assegna, riserva, consuma, rilascia, rettifica; concorrenza ultima unità e audit | integrated-runtime.json; native-runtime.json; W5 |
| CC-CAP-017 | Note organizzative | `operations/notes.py` | Operativi autorizzati | PASS | Note operative nel contesto; storico e isolamento; contenuti esclusi dalla stampa allowlist | integrated-runtime.json |
| CC-CAP-018 | Note professionali riservate | `operations/notes.py` | Solo autore professionista autorizzato | PASS | Revisioni append-only; altri professionisti, Segreteria, Direzione e Administrator senza corpo riservato | integrated-runtime.json; supplemental-suites.json; W5 |
| CC-CAP-019 | Scheda paziente unificata | `operations/workspace.py` | Operativi autorizzati | PASS | Anagrafica, agenda, storico e note nel medesimo scope; reporting contabile separato | integrated-runtime.json; supplemental-suites.json |
| CC-CAP-020 | Storico paziente | `operations/workspace.py` | Operativi autorizzati | PASS | Feed non vuoto con revisioni proprie, esclusione note altrui e controllo centro | integrated-runtime.json |
| CC-CAP-022 | Chiusura giornaliera | `operations/lifecycle.py` | Professionista/operativi autorizzati | PASS | Chiusura e stato economico, consumo unità una volta, modifica chiusa negata | integrated-runtime.json |
| CC-CAP-023 | Reminder ore 21 | `operations/automation.py` | Job e destinatario autorizzato | PASS | Clock sintetico locale, catch-up/replay una volta; Notification Log locale realmente inserita | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-024 | Auto-lock ore 07 | `operations/automation.py` | Job; correzione autorizzata | PASS | Boundary e retry, blocco server delle azioni professionista, scheduler configurato | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-025 | Disdetta 48h e rinuncia economica | `operations/lifecycle.py` | Operativi; deroga solo autorizzati | PASS | 48h esatte tempestiva; un microsecondo meno tardiva/dovuta; DST; rinuncia conserva fatto storico | integrated-runtime.json |
| CC-CAP-026 | Riapertura e correzioni governate | `operations/lifecycle.py` | Segreteria/Direzione secondo policy | PASS | Riapertura auditata/idempotente e dinieghi; escluso spostamento storico #78 per DECISION-059 | integrated-runtime.json |
| CC-CAP-027 | Notifiche e comunicazioni simulate | `operations/notifications.py; operations/booking_confirmation.py` | Destinatario; recovery Direzione | PASS | Communication primo incontro, failure/retry/replay; Notification Log; nessun Email Queue/invio reale | supplemental-suites.json; integrated-runtime.json |
| CC-CAP-028 | Reporting operativo | `operations/reporting.py` | Scope operativo del ruolo | PASS | Totali confrontati con record Agenda, stampa senza note, CSV formula-safe | integrated-runtime.json |
| CC-CAP-029 | Export e stampa autorizzati | `operations/reporting.py; finance/reporting.py` | Ruoli autorizzati | PARTIAL | Controlli di accesso e dati corretti; CSV umano conserva intestazioni inglesi e date ISO, contro #134 | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-030 | Dashboard direzionale | `operations/reporting.py; finance/reporting.py` | Direzione; Finance per contabilità | PASS | Aggregati riconciliati; unknown distinti da zero; margine non inventato senza policy | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-033 | Modello generale permessi | `security/guards.py; security/permissions.py` | Sette ruoli, Guest, Administrator | PASS | Matrice ruoli, revoca, centro inattivo, segregazione clinica/contabile e setup tecnico | supplemental-suites.json; readonly-runtime.json; http-readonly.json; W5 |
| CC-CAP-034 | Audit business immutabile | `security/audit.py; security/audit_view.py` | Direzione per registro | PASS | Modifica/cancellazione audit negate; attore/motivo/prima-dopo; eventi attuali trovati e altri ruoli negati | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-035 | Backup DB/file/config | `infra/issue139_install_gate.py` | Tecnico | PASS | Backup cifrato e recupero completo già provati nella rehearsal/installazione 14 ottobre; non ripetuti | W5; THIRD-DEV-INSTALLATION-READINESS-REPORT |
| CC-CAP-038 | Autorizzazione API/web | `security/api.py; finance/request_guard.py` | Tutti i ruoli | PASS | REST/direct/API/export e Guest; controlli server attivi; sei hook presenti | http-readonly.json; runtime-final.json; W5 |
| CC-CAP-039 | Regressione anti-leakage | `security/dev_acceptance.py; infra/security_acceptance.py` | Sette ruoli/Guest | PASS | 38 test HTTP attuali riusati, note/finance/cross-center e namespace protetti | W5; supplemental-suites.json |
| CC-CAP-040 | Deploy riproducibile | `infra/issue139_install_gate.py` | Tecnico | PASS | Immagine e candidato identificati, backup/installazione/rollback già provati; nessuna modifica audit al runtime | runtime-final.json; W5 |
| CC-CAP-041 | Bridge e master contabili | `finance/bridge.py` | Finance/Segreteria/Direzione; Commercialista lettura | PASS | Patient/Customer, Practitioner/Supplier, centro/Cost Center; correzione append-only e snapshot | integrated-runtime.json |
| CC-CAP-042 | Fatture pazienti, crediti e incassi | `finance/receivables.py; finance/native_adapter.py` | Finance/Segreteria/Direzione | PARTIAL | Bozza/GL, singola/aggregata, incasso parziale/totale, credito/cancel/reissue PASS; metodo carta/POS per singolo pagamento non coperto dal servizio/UI | integrated-runtime.json; readonly-runtime.json |
| CC-CAP-043 | Banca, scadenze e solleciti base | `finance/banking.py; finance/collections.py` | Finance/Segreteria/Direzione | PASS | Import dedupe, match/ambiguità, pagamento, reversal, blocco insoluti, differimento con debito invariato | integrated-runtime.json; browser-readonly.json; readonly-runtime.json |
| CC-CAP-044 | XML ricevuti e fatture professionisti | `finance/incoming.py` | Finance/Segreteria/Direzione; Commercialista lettura | PASS | XML privato, mapping, doppioni/XXE, bozza/submit, pagamento, annullo/rettifica, IVA sintetica | integrated-runtime.json |
| CC-CAP-045 | Compensi e confronto ricevuto | `finance/professional_economics.py` | Finance/Direzione; Commercialista lettura | PASS | Soglie N=0/1/2/5 per coppia, sospensione/override, rivalutazione incasso/storno, confronto OK/REVIEW | integrated-runtime.json; supplemental-suites.json; browser-readonly.json |
| CC-CAP-046 | Coda amministrativa | `finance/admin_queue.py` | Amministrativi autorizzati | PASS | Condizioni deduplicate, assegnazione, priorità, scadenza, rinvio/riapparizione, chiusura automatica e riapertura | integrated-runtime.json |
| CC-CAP-047 | Report Finance, ruoli e audit | `finance/reporting.py; finance/patient_reporting.py; finance/request_guard.py` | Finance/Segreteria/Direzione/Commercialista | PARTIAL | Viste Centro/Professionista/Paziente riconciliate; General Ledger e Trial Balance nativi non raggiungibili dai ruoli cliente | integrated-runtime.json; supplemental-suites.json; http-readonly.json |
| CC-CAP-048 | Adapter SdI simulato indipendente | `finance/sdi.py; finance/fiscal.py` | Finance/Direzione secondo azione | PASS | XML/protocollo simulato, successo/rifiuto/retry/limite, correzione, inbound e payload privato | integrated-runtime.json |
| CC-CAP-049 | Adapter TS ordinario simulato | `finance/ts.py; finance/fiscal.py` | Revisione Direzione; azioni Finance consentite | PASS | Eligibilità/opposizione persistenti per versione, retry/correzione, esiti e coda; nessun invio reale | integrated-runtime.json |
| CC-CAP-050 | Verifica integrata e readiness MVP | `operations/integration_acceptance.py; infra/integrated_acceptance.py` | Tecnico e successiva review Owner | PARTIAL | 189 controlli backend reali PASS dopo adattamento test; vecchi gate falliscono per lingua/ID e il viaggio HTTP/browser completo con commit non è riprovato in sicurezza | integrated-runtime.json; initial-suite-results.json |
| SCOPE-DOC | Allegati amministrativi manuali: PDF, ricevute, scansioni | `finance/files.py; File nativo` | Amministrativi autorizzati | PARTIAL | Guard prima insert rifiuta nuovo PDF privato su fattura; nessun servizio ordinario di allegato individuato. XML fiscali invece presenti e provati. | readonly-runtime.json |
| UAT-GLOBAL | Interfaccia operativa coerente, italiana e utilizzabile | `public/js; public/css; centro_change_core/page/cc_unified_desk` | Sette ruoli cliente | PARTIAL | 128 route e 22 List/Form già PASS; confronto mobile taglia le etichette, CSV inglese/ISO e altri residui. Review Owner non sostituita. | browser-readonly.json; screenshots/comparison-390.png; W5 |
| CC-CAP-015 | Percorso accounting storico sostituito da 041–050 | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
| CC-CAP-021 | Patient Progress/clinical analytics | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
| CC-CAP-031 | Sito pubblico branded completo | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
| CC-CAP-032 | Builder/Git per sito pubblico rinviato | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
| CC-CAP-036 | DR completo come requisito di release produzione | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
| CC-CAP-037 | Qualifica upgrade come requisito di release produzione | `Rinvio/sostituzione approvati` | Non pertinente al gate corrente | FUTURE/OUT OF SCOPE | Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03. | docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml |
