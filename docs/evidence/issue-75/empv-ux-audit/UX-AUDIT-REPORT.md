# Centro Change — audit UX completo per Issue #75

**Data:** 19/10/2026. **Esito:** `PARTIAL — problemi di comprensibilità confermati; proposta in attesa di review Owner`. Nessuna modifica applicativa o al DEV. L'audit valuta compiti, gerarchia e terminologia; i PASS tecnici di #139 restano validi per caricamento/rendering, non equivalgono a usabilità approvata.

## Baseline ed evidenze

- Branch isolato `issue-75/empv-ux-audit`, da PR #141 `1465b451f2eb4e33881c1de4da1e1f47d3ef70d4`; PR #140 DRAFT `7f9784f3711f5bb7ef3bbc9498dc016db8f9f6da` consultata. DEV read-only: 9/9 servizi, immagine `centrochange-single:client-demo-cf0eff7` = `sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834`.
- Fonti: [#75](https://github.com/2008hitch-afk/centrochange_core/issues/75), [#76](https://github.com/2008hitch-afk/centrochange_core/issues/76), [#77](https://github.com/2008hitch-afk/centrochange_core/issues/77), [#79](https://github.com/2008hitch-afk/centrochange_core/issues/79), [#134](https://github.com/2008hitch-afk/centrochange_core/issues/134), [#135](https://github.com/2008hitch-afk/centrochange_core/issues/135), [#136](https://github.com/2008hitch-afk/centrochange_core/issues/136), [#137](https://github.com/2008hitch-afk/centrochange_core/issues/137), [#139](https://github.com/2008hitch-afk/centrochange_core/issues/139), `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md`, `docs/ui/ISSUE-75-NATIVE-FIRST-SCREEN-MATRIX-2026-10-12.md`, `docs/uat/FINAL-PERMISSION-MATRIX.md`, AGENTS e governance.
- Riutilizzati 87 screenshot e JSON read-only del sweep corrente, sette account e viewport 1440/390. Nuova prova Chromium read-only su Professionista A/C e fattura paziente Direzione; nuova prova 11/11 List→Form su Patient, Healthcare Practitioner, Item, Item Price, Sales Invoice, Purchase Invoice, Payment Entry, Bank Transaction, Appointment Type, CC Center Service, CC Package Template. Queste prove non eseguono salvataggi e non misurano tempo/errore dei compiti umani.
- Screenshot selezionati sotto `screenshots/` provengono da Chromium sul DEV, con dataset sintetico. Dati/credenziali del browser restano in directory privata. Nessun ID storico RC22 usato.
- Inventario delle **23 destinazioni** e delle varianti di ruolo: [UX-SCREEN-INVENTORY.md](UX-SCREEN-INVENTORY.md). Sintesi numerica sanificata: [UX-EVIDENCE-SUMMARY.json](UX-EVIDENCE-SUMMARY.json). La prova dei due prototipi isolati ha dato 16/16 controlli Chromium a 390/1440 px, zero errori JavaScript e zero overflow; questo prova solo il prototipo, non il prodotto.

## Esito per area

| Area | Compito utente e dato essenziale | Riscontro osservato | Problema UX e impatto | Priorità / verifica futura |
|---|---|---|---|---|
| Login, ingresso, sidebar | Arrivare alla prima attività autorizzata; capire dove si è | Agenda per operativi, Finanza per f/t; un solo link attivo nei campioni #137 | «Inizio» e «Agenda» possono essere equivalenti; ridondanza semantica. | P1; test percorso reale per ruolo e deep link. |
| Agenda / disponibilità | Vedere sedute e slot, agire secondo stato | A/B: griglia settimanale 1/1 e `+ Prenota`; C: 0/0 con messaggio; mobile scroll sette giorni | L'attività professionale imminente non è il primo oggetto. La griglia vuota occupa quasi tutta la prima schermata. `+ Prenota` richiede verifica di scopo e permesso. | P0; walkthrough e test API/ruolo prima di cambiare azione. |
| Ricerca pazienti / anagrafica | Trovare persona e distinguere ricerca da gestione | Rotte separate; Form Patient leggibile, 11/11 native PASS tecnico | Nome sintetico/ID ripetuti, pannello tecnico e «Invita come utente» vicini al lavoro ordinario; rischio di selezione sbagliata. | P0; nome primario, ID secondario, prova per Segreteria/Direzione. |
| Anagrafica professionisti vs Report professionisti | Gestire persona vs analizzare attività | Due rotte ed etichette distinte; Form apre | ID di fixture domina nome nel Form; la vista operativa del Professionista è invece nell'Agenda, non nel Report. | P1; task test distinto per manager e professionista. |
| Catalogo, tariffe e configurazioni | Gestire servizio, prezzo e regole autorizzate | Item, Item Price, Appointment Type, CC Center Service, CC Package Template: List/Form aprono | Il PASS di rendering non prova quali campi siano superflui. Serve inventario per compito prima di un'altra riduzione. | P1; review guidata di Form/validazioni, nessun campo canonico eliminato. |
| Fatture pazienti | Capire soggetto, stato, importo, saldo e prossima azione | Riepilogo e consiglio presenti, ma screenshot live mostra soggetto `CC-MVP...`; DOM visibile include `customer`, `cc_center`, `Total Quantity`, `Sales Taxes and Charges`, ecc. | Dettagli ERPNext tecnici e inglese dentro il percorso primario; prestazione codificata. L'utente vede molti dati senza sapere quali usare. | P0; compito di lettura/azione su bozza, pagata, annullata; test visuale e accessi. |
| Fatture professionisti, incassi/pagamenti, banca | Individuare soggetto, documento, stato e prossima azione | Rotte native e Banca dedicate aprono per ruoli ammessi | Necessaria stessa gerarchia informativa della fattura paziente; non dedurre esito UX da 200/DOM. | P1; walkthrough Finance/Commercialista, verificare campi obbligatori. |
| SdI/TS simulati, report | Capire che non c'è invio reale; consultare risultati | Rotte nel menu e rendering PASS | Copy/stati da verificare con utenti; non dichiarare comprensione solo da screenshot. | P1; scenari di stato ed errori simulati. |
| Notifiche, audit, accessi | Capire evento, autore e azione permessa | Raggiungibili dai ruoli previsti nel sweep | Termine/ID tecnici possibili; permessi invariati. | P2; task di consultazione e tracciabilità. |

### Undici native: separazione netta dei problemi

L'asset/CSS rotto riportato in #136 e affrontato in #139 **non è stato riprodotto** nel nuovo test: 11/11 Form visibili, nessun overflow significativo nel runner. Rimane il debito di gerarchia e linguaggio. Il caso verificato in dettaglio è Sales Invoice; Patient e Healthcare Practitioner sono stati ispezionati visivamente. Per le altre otto Form la classificazione di ogni campo è ancora `DA VALIDARE CON OPERATORE`, non un PASS UX.

## Punti ad alto impatto dimostrati

1. **Professionista:** la settimana corrente può essere vuota pur esistendo sedute future; un operatore deve cercare manualmente ciò che è da completare. [Screenshot live](screenshots/professional-agenda-mobile.png) e JSON read-only privato. Il [prototipo](prototypes/professionista-prima-dopo.html) propone una lista operativa che riutilizzi solo API/permessi esistenti; non promette nuovo backend.
2. **Fattura:** il riepilogo cliente è utile, ma il Form continua con campi in inglese e chiavi tecniche visibili. [Screenshot live](screenshots/invoice-form.png) e testo DOM live. L'ID paziente sintetico domina l'intestazione. Il [prototipo](prototypes/fattura-paziente-prima-dopo.html) tiene i dettagli contabili accessibili, senza rimuovere documenti canonici.
3. **Anagrafiche:** Patient e Healthcare Practitioner mostrano nomi fixture tecnici e pannelli nativi «Assegna/Tag/Condividi». [Patient](screenshots/patient-form.png), [Healthcare Practitioner](screenshots/practitioner-form.png). Priorità alla leggibilità; l'uso di questi strumenti va confermato prima di ridurli.

Confronti illustrativi: [Professionista live mobile](screenshots/professional-agenda-mobile.png) → [proposta mobile](screenshots/prototype-professional-390.png) / [desktop](screenshots/prototype-professional-1440.png); [Fattura live](screenshots/invoice-form.png) → [proposta desktop](screenshots/prototype-invoice-1440.png) / [mobile](screenshots/prototype-invoice-390.png). Le immagini «proposta» sono prototipi statici, non screenshot di funzionalità installate.

## Ambito e limiti

L'analisi applica la direzione **Frappe native-first**, Tabler come riferimento estetico. La scelta tecnica per ciascun intervento segue: configurazione Workspace/Form/List → script e traduzioni supportati → pagina Frappe dedicata soltanto per flussi operativi che lo richiedono. Nessun CSS di framework è condizione per il PASS. Nessun controllo visivo sostituisce permessi server-side.

I dati demo con codici lunghi sono sintetici, ma non sono stati modificati. L'audit non ha misurato successo, errori o tempo con un professionista reale. I prototipi sono ipotesi isolate: la loro approvazione richiede review Owner e poi validazione con ruoli competenti. Non è `OWNER VISUAL PASS`, non chiude #75 o GOAL-02.
