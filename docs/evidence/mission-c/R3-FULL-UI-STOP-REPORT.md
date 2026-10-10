# Missione C #109 — R3, stop del guard prima della chiusura del gate

**Esito: `MISSION-C-R3: BLOCKED`; `READY_FOR_OWNER_UAT: NO`.** Questo rapporto è append-only rispetto a C1/C2/C3 e agli stop R1/R2. Le PR #107, #111, #112 e #115 restano DRAFT. Nessun merge, cutover, upgrade RC22, provider reale o produzione.

## Codice e runtime provati

- Prodotto PR #112, branch `issue-109/unified-desk-prototype`, commit finale `d9c09e1d44795b068b4869c013263531dc53a936`. Layer OCI C109 `sha256:6855661acef0f98978cc969e3f12e418b68ff2744d5b47f625bc8afde5acdbae`, label di revisione coincidente. Stack dipendente dalla PR draft #107: Frappe/ERPNext 16.50.0, Healthcare 16.6.1, Builder 1.35.1, pin R5 invariati.
- Laboratorio sintetico isolato `centrochange-c109`, site `b99.local`, porta locale 8109, 2 GiB runtime e 512 MiB QA seriale. L'URL Desk era disponibile durante i test; **dopo lo stop automatico non è più disponibile**. UAT RC22 sulla porta 8082 è rimasta HTTP 200.
- R3 ha corretto un difetto reale della UI Disponibilità: il vecchio editor inviava un solo giorno a `availability.set_schedule`, sostituendo e perdendo gli altri giorni ricorrenti. Il nuovo editor carica tutte le fasce del professionista, ne consente aggiunta/rimozione e invia la settimana completa; l'assenza rimane indipendente. Commit `d35704f`, `b6b7d60` e `d9c09e1`. L'ultimo commit evita di mostrare le fasce del primo professionista mentre il selettore è ancora vuoto. Il layer versionato include ora anche `workspace.css`. Nessun backend, ruolo, accounting o permission model è stato modificato.

## Verifiche effettive sul layer finale

| Area | Risultato R3 |
|---|---|
| Catalogo nativo | 7/7 List e Form, **Chromium fresco per ogni pagina**: Item, Item Price, Appointment Type, CC Center Service, CC Package Template, Patient, Healthcare Practitioner. Item Price: nota sintetica salvata e ripristinata, prezzo invariato. |
| Agenda e ruoli | Direzione: navigazione e dettagli; A vede una sola riga/solo dati A, B una sola riga/solo B, C nessuna seduta; nessun errore JS. Report→seduta rimane nel Desk e apre il dettaglio operativo. |
| Sedute e anagrafiche | Riapertura/richiusura, nota organizzativa, creazione paziente, ricerca, attivazione/disattivazione professionista: PASS. Nota privata di A: lettura A 200, B/C/Segreteria/Direzione 403 via accesso diretto. |
| Disponibilità e pacchetti | Assenza 19 ottobre riflessa nella griglia; editor settimanale cinque fasce → sei → cinque, con ripristino esatto; assegnazione sintetica di pacchetto e storico: PASS. |
| Finance | Fattura sintetica contabilizzata e pagata tramite Desk; Sales Invoice finale `docstatus=1`, outstanding 0 e Payment Entry nativa rilevata. Le nove viste Finance passano per Segreteria, Finance e Accountant; Accountant senza azioni di scrittura. Soglia manager N=1 HTTP 200, Finance HTTP 403. Coda amministrativa: priorità modificata e ripristinata. Banca/SdI/TS mutativi R2 passati sul precedente layer: nessuna nuova prova mutativa R3. |
| Report | Report Pazienti: totale fatturato = somma delle fatture, sedute = record, residuo = somma fatture aperte. Report Professionisti: KPI sedute = righe drill-down. Periodo visibile. Payer condiviso **NON VERIFICATO sul dataset C109**, che non contiene una riga shared. |
| Audit/notifiche | Vista audit mostra eventi R3 recenti; before/after della membership e della coda conservati; soglia con evento append-only. Vista notifiche carica; nessuna conferma primo incontro o retry fallito presente nel dataset, quindi retry **NON VERIFICATO**. |
| Stampa/export/sessione | Riepilogo stampa HTTP 200 senza note private; quattro CSV UI (Agenda, Finance, Professional, Patient) scaricati; logout → login; Guest Desk → login e primo incontro pubblico HTTP 200. |
| Sicurezza/browser/layout | **69/69** HTTP server-side sul layer finale: sette ruoli, centro incrociato, A/B/C, note, query/report/export. Direzione: 28 controlli funzionali con tutte le aree. Mobile 390px: Agenda, booking, Finance e Pazienti senza overflow documentale. Nessun nuovo OOM durante queste suite. |
| Prenota→sposta→cancella sul layer finale | **NON COMPLETATO**: primo harness riutilizzava un intervallo R2 già occupato; il secondo, con data sintetica nuova, è stato interrotto dal guard all'avvio del container QA. Il percorso R2 era PASS sull'immagine precedente, ma non viene attribuito al layer finale. |

La matrice delle 24 aree C1, con stato rigoroso dopo R3, segue. `PARTIAL` non equivale ad acceptance. Gli esiti R2 sulla precedente immagine sono conservati nel rapporto R2.

| Area C1 | Stato al termine R3 |
|---|---|
| Agenda | IMPLEMENTED_TESTED |
| Prenota/sposta/cancella | PARTIAL: R2 PASS, retest R3 fermato |
| Seduta/storico/note | IMPLEMENTED_TESTED |
| Pazienti | PARTIAL: anagrafica/ricerca/storico provati, shared payer report non provato |
| Professionisti | IMPLEMENTED_TESTED per viste, lifecycle e isolamento |
| Disponibilità | IMPLEMENTED_TESTED |
| Servizi/prezzi/pacchetti | PARTIAL: sette native List/Form e Item Price write, altre scritture Catalogo non provate |
| Contabilità/registri | PARTIAL: guard/report scoped, percorsi nativi completi non provati |
| Fatture pazienti/fornitori | PARTIAL: emessa+pagata paziente, rettifica/credito e fornitore via UI R3 non provati |
| Incassi/pagamenti | PARTIAL: Payment Entry paziente sì, tutti i pagamenti fornitore UI R3 non provati |
| Banca/riconciliazione | PARTIAL: R2 mutativo PASS, non ripetuto sul layer finale |
| Report Centro/Professionisti/Pazienti | PARTIAL: reconciliation dei casi provati, shared payer non disponibile nel dataset C109 |
| Report contabili nativi generici a ruoli limitati | BLOCKED_BY_OWNER_DECISION: guard 403 conservato; report CC scoped disponibili |
| SdI simulato | PARTIAL: R2 mutativo PASS, finale R3 vista/guard soltanto |
| TS simulato | PARTIAL: R2 mutativo PASS, finale R3 vista/guard soltanto |
| Audit/registro | IMPLEMENTED_TESTED per eventi R3 discriminanti |
| Accessi/centri | IMPLEMENTED_TESTED per membership disable/restore e lifecycle professionista |
| Compensi/coda | PARTIAL: soglia e coda provate, override/comparison UI R3 non provati |
| Notifiche/job | PARTIAL: vista sì, retry/worker non esercitati R3 |
| Login/logout | IMPLEMENTED_TESTED |
| Primo incontro pubblico | NOT_APPLICABLE_PUBLIC_DEV: separato; Guest HTTP 200 |
| Stampa/export | IMPLEMENTED_TESTED per print e quattro CSV positivi; negativi inclusi nei guard |
| Validazione DEV | NOT_APPLICABLE_PUBLIC_DEV |
| Cutover/identità globale | BLOCKED_BY_OWNER_DECISION: Decision-004, fuori Missione C |

## Safety stop discriminante

Alle **12:35 UTC del 10 ottobre 2026**, il monitor R3 ha scritto `CAP_NOT_ENFORCED` e ha arrestato i soli container C109. Nell'istante campionato il nuovo container QA era già visibile con `memory.max=max`, `memory.current=1,282,048` byte e zero eventi OOM; `docker inspect` conferma invece `HostConfig.Memory=536,870,912` e `MemorySwap=536,870,912`. Il QA termina con exit 137 perché il guard lo ha fermato, `OOMKilled=false`. È plausibile una finestra transitoria nell'applicazione del cgroup durante `docker run`, ma il perché esatto **non è ancora verificato**. Nessun override del guard o retry R3 è stato eseguito.

Misure dell'intera R3: host `oom_kill` **7→7**; MemAvailable minima 4,752,039,936 byte; PSI memoria full massima 0.53%, PSI I/O full massima 3.52%; picco runtime 1,076,744,192 byte su cap 2 GiB; picco QA campionato 303,878,144 byte prima del container transitorio; minimo disco libero 36,793,401,344 byte, superiore alla riserva 4 GiB. I **137/137 container protetti** sono identici al preflight per ID, immagine, stato, avvio, restart, mount e reti; nessun alert di eventi protetti. RC22 HTTP 200 finale, C109 fermo (HTTP non disponibile). Volumi, dati sintetici e immagini C109 conservati.

Il piano #110 §8.2(5) richiede stop dopo **qualsiasi** safety/watchdog stop, anche senza OOM; per questo non si riavvia il laboratorio nella presente attivazione. La proposta minima per un nuovo gate Owner è una **nuova attivazione separata** che avvii prima un container QA dedicato già limitato a 512 MiB, ne verifichi `memory.max` e `memory.swap.max` stabilizzati **prima** di lanciare Chromium; poi esegua un processo browser fresco per ciascuna suite/pagina all'interno del cgroup già verificato, serialmente. Restano invariati 2 GiB runtime + 512 MiB QA, soglie PSI/OOM/disco, e stop su un solo evento. Questo è un suggerimento, non un'autorizzazione o un retry eseguito.

Risultati JSON sintetici e screenshot sono in `r3/results/` e `r3/screenshots/` con checksum `r3/SHA256SUMS`; fixture privata, password, log grezzi e campioni Docker completi restano fuori Git. Screenshot e dati identificano soltanto il laboratorio sintetico.
