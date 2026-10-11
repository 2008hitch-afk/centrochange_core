# Missione C — stato implementazione delle 24 aree

**Issue #109, prodotto PR draft #112.** Base storica R3: prodotto `d9c09e1`, immagine `sha256:6855661acef0f98978cc969e3f12e418b68ff2744d5b47f625bc8afde5acdbae`. La revisione native-first e il gate offline sono successivi e **non** ancora in un'immagine collaudata. `MISSION-C: PARTIAL / READY_FOR_OWNER_UAT: NO`; C109 fermo. Questo registro conserva i PASS storici senza trasferirli alla nuova HEAD.

| # | Area | Evidenza R3 sulla vecchia immagine | Stato nuova HEAD / lavoro discriminante residuo |
| --- | --- | --- | --- |
| 1 | Agenda | PASS griglia, ruoli A/B/C, dettagli | Custom Desk giustificata; controller ancora incorporato dalla webapp, refactor diretto e browser finale da eseguire |
| 2 | Prenota/sposta/cancella | R2 PASS, R3 interrotto | `PARTIAL`; tripla mutazione su immagine finale, collisioni/idempotenza/audit |
| 3 | Seduta/storico/note | PASS R3, private note negative | Controller ancora wrapped; riprovare su prodotto finale |
| 4 | Pazienti | Anagrafica/ricerca/storico R3 | `PARTIAL`; List native Manager introdotta ma non testata, shared payer e ruoli limitati |
| 5 | Professionisti | Lifecycle e isolamento R3 | List native Manager introdotta ma non testata; self/direct e Segreteria |
| 6 | Disponibilità | Editor cinque→sei→cinque e assenza R3 | Custom editor da estrarre nel Desk, regressione finale |
| 7 | Servizi/prezzi/pacchetti | 7/7 List/Form native, Item Price write/restore R3 | `PARTIAL`; altre scritture Catalogo e ledger pacchetto su immagine finale |
| 8 | Contabilità/registri | Guard/report scoped R3 | `PARTIAL`; native List/Form complete e negative cross-center |
| 9 | Fatture pazienti/fornitori | Sales Invoice emessa+pagata R3 | `PARTIAL`; rettifica/credito, fornitore, native List/Form e servizi CC |
| 10 | Incassi/pagamenti | Payment Entry paziente R3 | `PARTIAL`; pagamenti fornitore, actor/permessi, native read |
| 11 | Banca/riconciliazione | Mutazione R2 su layer precedente | `PARTIAL`; reconcile/undo e native Bank List su finale |
| 12 | Report Centro/Professionisti/Pazienti | KPI/drill-down alcuni casi R3 | `PARTIAL`; payer condiviso, negative export e periods su finale |
| 13 | Report ERPNext generici non Manager | 403 via guard R3 | `BLOCKED_BY_OWNER_DECISION`; mantenere 403, nessun grant |
| 14 | SdI simulato | Mutazioni R2 precedente | `PARTIAL`; simulazioni e payload/negative su finale |
| 15 | TS simulato | Mutazioni R2 precedente | `PARTIAL`; correction chain e negative su finale |
| 16 | Audit/registro | Eventi R3, before/after | List nativa Manager introdotta ma non testata; verificare campi/export/direct |
| 17 | Accessi/centri | Membership e lifecycle R3 | Workflow custom invariato; retest finale revoca e direct negatives |
| 18 | Compensi/coda | Soglia e priorità R3 | `PARTIAL`; override/comparison Manager vs Finance su finale |
| 19 | Notifiche/job | Vista R3 | `PARTIAL`; retry/idempotenza su fixture discriminante |
| 20 | Login/logout | PASS R3 | Riprovare su nuova immagine e sette ruoli+Guest |
| 21 | Primo incontro pubblico | Guest HTTP200 R3 | `NOT_APPLICABLE_PUBLIC_DEV`; separato, non migrare nel Desk |
| 22 | Stampa/export | Print + quattro CSV R3 | Native print/export dove autorizzati; negative su finale |
| 23 | Validazione DEV | Fuori UI cliente | `NOT_APPLICABLE_PUBLIC_DEV`; resta separata |
| 24 | Cutover/identità globale | Decision-004 webapp primaria | `BLOCKED_BY_OWNER_DECISION`; confronto C3 e nuova scelta Owner |

Il codice nuovo nella #112 include soltanto navigazione verso List native per ruoli già ammessi, senza mutare permessi o servizi. Tutti gli altri controller incorporati restano transitori. Il piano tecnico è nella review `C1-NATIVE-FIRST-REALIGNMENT-REVIEW.md`; non chiamare l'interfaccia finale completa finché le aree PARTIAL e il gate cgroup non sono chiusi con evidenza sulla stessa immagine.

**Aggiornamento 2026-10-10, candidata `12a19f5`:** il bootstrap isolato e il primo smoke/browser nativo sono passati, ma il collaudo è stato fermato alle 15:38 UTC da PSI I/O full ≥1% (picco 1,36%). Le sette List native osservate dimostrano navigazione, non la chiusura funzionale delle aree 4–10. Le righe `PARTIAL`, `NON VERIFICATO` e `BLOCKED_BY_OWNER_DECISION` qui sopra restano tali. Il dettaglio è in `C-UNIFIED-FINAL-ACCEPTANCE.md`; `READY_FOR_OWNER_UAT` rimane **NO**.

**Aggiornamento offline 2026-10-11:** la HEAD successiva elimina il fetch/parse website nel Desk, genera quattro frammenti statici condivisi e usa la List nativa per Audit Manager. Queste sono modifiche architetturali **STATIC PASS** (27 test offline, sintassi JS/Python), senza immagine o test runtime sulla nuova HEAD. Le aree 1–3, 4–6, 8–12 e 14–19, 22 rimangono `PARTIAL/NON VERIFICATO` per i flussi e permessi; l'area 16 richiede prova List/Form/export/direct per tutti i ruoli. Le decisioni Owner per 13 e 24 non sono cambiate. Il report `C-UNIFIED-OFFLINE-READINESS-2026-10-11.md` contiene matrice dei cinque ingressi, analisi I/O e scenario completo. `READY_FOR_OWNER_UAT: NO`.

**Aggiornamento Desk cliente, 2026-10-11:** la PR draft #112 aggiunge asset Desk globali tramite hook supportati, differenziati per ruolo, e prepara un test read-only del confine tecnico HITCH/cliente. I controlli offline risultano 44/44 e sette profili simulati PASS. Il rapporto `C109-NATIVE-DESK-PARITY-2026-10-11.md` aggiorna la parità per tutte le 24 aree. La demo visuale già attiva usa un'immagine precedente: nessuna riga `PARTIAL` diventa PASS per effetto di questi controlli offline. `READY_FOR_OWNER_UAT: NO`.
