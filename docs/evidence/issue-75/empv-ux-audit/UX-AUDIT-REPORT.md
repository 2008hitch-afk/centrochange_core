# Centro Change — audit UX completo per Issue #75

**Data:** 19/10/2026; **revisione vincolante Owner:** 20/10/2026. **Esito:** `PARTIAL — problemi di comprensibilità nelle viste native confermati; piano corretto in attesa di review Owner`. Nessuna modifica applicativa o al DEV. **Agenda invariata e fuori dagli interventi**, anche per il Professionista. La precedente proposta «Oggi / Da completare / Prossime sedute» è ritirata. I PASS tecnici di #139 valgono per caricamento/rendering, non per usabilità approvata.

## Baseline ed evidenze

- Branch isolato `issue-75/empv-ux-audit`, da PR #141 `1465b451f2eb4e33881c1de4da1e1f47d3ef70d4`; PR #140 DRAFT `7f9784f3711f5bb7ef3bbc9498dc016db8f9f6da` consultata. DEV read-only: 9/9 servizi, immagine `centrochange-single:client-demo-cf0eff7` = `sha256:5a9351bf68eb7e76b805a14ebcf966de57420546dfd11c8ed41b2f4a82119834`.
- Fonti: [#75](https://github.com/2008hitch-afk/centrochange_core/issues/75), [#76](https://github.com/2008hitch-afk/centrochange_core/issues/76), [#77](https://github.com/2008hitch-afk/centrochange_core/issues/77), [#79](https://github.com/2008hitch-afk/centrochange_core/issues/79), [#134](https://github.com/2008hitch-afk/centrochange_core/issues/134), [#135](https://github.com/2008hitch-afk/centrochange_core/issues/135), [#136](https://github.com/2008hitch-afk/centrochange_core/issues/136), [#137](https://github.com/2008hitch-afk/centrochange_core/issues/137), [#139](https://github.com/2008hitch-afk/centrochange_core/issues/139), `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md`, `docs/ui/ISSUE-75-NATIVE-FIRST-SCREEN-MATRIX-2026-10-12.md`, `docs/uat/FINAL-PERMISSION-MATRIX.md`, AGENTS e governance.
- Riutilizzati 87 screenshot e JSON read-only del sweep corrente, sette account e viewport 1440/390. Nuova prova Chromium read-only su Professionista A/C e fattura paziente Direzione; nuova prova 11/11 List→Form su Patient, Healthcare Practitioner, Item, Item Price, Sales Invoice, Purchase Invoice, Payment Entry, Bank Transaction, Appointment Type, CC Center Service, CC Package Template. Queste prove non eseguono salvataggi e non misurano tempo/errore dei compiti umani.
- Screenshot selezionati sotto `screenshots/` provengono da Chromium sul DEV, con dataset sintetico. Dati/credenziali del browser restano in directory privata. Nessun ID storico RC22 usato.
- Inventario delle **23 destinazioni** e delle varianti di ruolo: [UX-SCREEN-INVENTORY.md](UX-SCREEN-INVENTORY.md). Sintesi numerica sanificata: [UX-EVIDENCE-SUMMARY.json](UX-EVIDENCE-SUMMARY.json). I prototipi attivi sono esclusivamente native-first: Anagrafica Paziente, Anagrafica Professionista e Fattura paziente. Le vecchie verifiche del prototipo Agenda non sono evidenza della proposta corrente.

## Esito per area

| Area | Compito utente e dato essenziale | Riscontro osservato | Problema UX e impatto | Priorità / verifica futura |
|---|---|---|---|---|
| Anagrafica Paziente | Identificare persona, stato, recapiti e dati necessari | Patient Form leggibile, 11/11 native PASS tecnico | Nome sintetico/ID ripetuti, pannello tecnico e «Invita come utente» vicini al compito ordinario. | **Ordine 1**; nome primario, ID secondario, prova per ruoli autorizzati. |
| Anagrafica Professionista | Gestire persona e collegamenti professionali, distinta dal Report | Healthcare Practitioner Form apre | ID di fixture domina nome; sezioni `Charges` e `Free Followup Details` in inglese. | **Ordine 2**; gerarchia e terminologia native. |
| Fatture pazienti | Capire soggetto, stato, importo, saldo e prossima azione | Riepilogo presente, ma soggetto `CC-MVP...` e campi `customer`, `cc_center`, `Total Quantity`, `Sales Taxes and Charges` visibili | Dettagli tecnici/inglese nel percorso primario; prestazione codificata. | **Ordine 3**; compiti su bozza, pagata, annullata e permessi. |
| Altre Form native | Servizi, tariffe, fatture professionisti, incassi e movimenti bancari | Item, Item Price, Appointment Type, CC Center Service, CC Package Template, Purchase Invoice, Payment Entry e Bank Transaction aprono | Etichette inglesi e campi tecnici da classificare per compito; il rendering non prova usabilità. | **Ordine 4**; review campo per campo e salvataggi autorizzati. |
| Altre viste cliente già presenti | Ricerca, Finanza, report, notifiche e audit | Rotte del sweep raggiungibili | L'audit conserva le evidenze; nessun nuovo intervento incluso nel piano corretto. | Fuori dal piano di semplificazione corrente. |

### Undici native: separazione netta dei problemi

L'asset/CSS rotto riportato in #136 e affrontato in #139 **non è stato riprodotto** nel nuovo test: 11/11 Form visibili, nessun overflow significativo nel runner. Rimane il debito di gerarchia e linguaggio. Il caso verificato in dettaglio è Sales Invoice; Patient e Healthcare Practitioner sono stati ispezionati visivamente. Per le altre otto Form la classificazione di ogni campo è ancora `DA VALIDARE CON OPERATORE`, non un PASS UX.

## Punti ad alto impatto dimostrati

1. **Paziente:** nome fixture/ID ripetuti e pannelli nativi accanto ai dati ordinari. [Form live](screenshots/patient-form.png) → [prototipo native-first](prototypes/anagrafica-paziente-prima-dopo.html).
2. **Anagrafica Professionista:** ID predominante e sezioni inglesi tecniche. [Form live](screenshots/practitioner-form.png) → [prototipo native-first](prototypes/anagrafica-professionista-prima-dopo.html). La vista operativa Professionista non è oggetto del piano.
3. **Fattura:** il riepilogo è utile, ma il Form mostra campi inglesi e chiavi tecniche. [Form live](screenshots/invoice-form.png) → [prototipo native-first](prototypes/fattura-paziente-prima-dopo.html), con dettagli contabili ancora accessibili.

Confronti illustrativi: [Paziente proposto desktop](screenshots/prototype-patient-1440.png) / [mobile](screenshots/prototype-patient-390.png); [Anagrafica Professionista proposta desktop](screenshots/prototype-practitioner-1440.png) / [mobile](screenshots/prototype-practitioner-390.png); [Fattura proposta desktop](screenshots/prototype-invoice-1440.png) / [mobile](screenshots/prototype-invoice-390.png). Le immagini «proposta» sono statiche, non funzionalità installate.

## Ambito e limiti

L'analisi applica la direzione **Frappe native-first**, Tabler come riferimento estetico. La scelta tecnica per ciascun intervento segue: configurazione Workspace/Form/List → script e traduzioni supportati → pagina Frappe dedicata soltanto per flussi operativi che lo richiedono. Nessun CSS di framework è condizione per il PASS. Nessun controllo visivo sostituisce permessi server-side.

I dati demo con codici lunghi sono sintetici, ma non sono stati modificati. L'audit non ha misurato successo, errori o tempo con operatori reali. I tre prototipi nativi sono ipotesi isolate; Chromium ha verificato 30/30 controlli di confronto/interazione a 390/1440 px, senza errori JavaScript né overflow. La loro approvazione richiede review Owner e poi validazione con ruoli competenti. Non è `OWNER VISUAL PASS`, non chiude #75 o GOAL-02.
