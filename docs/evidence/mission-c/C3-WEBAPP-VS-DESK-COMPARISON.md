# C3 — Confronto osservato, non accettazione

**PARTIAL**. Dati sintetici equivalenti nello stesso clone TARGET/#107, CentroA,28/09–04/10 e Finance28/09–31/10. La webapp confrontata è quella della baseline TARGET nel clone: RC22 reale rimane CURRENT e non è stata aggiornata. I risultati R5 esistenti non vengono attribuiti a nuovi test C.

| Aspetto | Webapp | Desk prototipo | Valutazione |
|---|---|---|---|
| Agenda / dati |9 card canoniche|9 card canoniche|Parità sul periodo osservato|
| Geometria / mobile |Nessun document overflow|Drift0px desktop/tablet/mobile, scroll interno|Entrambe funzionali|
| Navigazione settimana |Già baseline R5, non ritestata qui|Precedente/successiva PASS|C non ripete tutta la regressione webapp|
| Dettaglio seduta |Pannello persistente, tab e azioni complete|Dialog nativo con storia e note organizzative in lettura|Webapp più completa|
| Ricerca paziente |Controllo singolo già baseline|Autocomplete server bounded + tastiera PASS|Modello canonico invariato|
| Pazienti |Percorso webapp completo baseline|7 pazienti, storia in Dialog|Primo percorso reale, non parity totale|
| Finance |Riepilogo completo e molte azioni già validate R5|KPI +3 fatture canoniche +Dialog residuo|Stesso servizio, UI Desk parziale|
| Ruoli |Baseline segregata, non ritest totale in C|69 controlli HTTP PASS; A/B/C browser PASS|Desk non concede nuovi diritti|
| UI italiana / identità |Tabler approvato, labels umane|Contenuti CC italiani; chrome nativo ancora tecnico/inglese|Gap Desk dichiarato|
| Disponibilità, report, banca, TS/SdI, admin |Già implementati nella webapp|C1 classificati, conversione Desk non completata|Non dichiarare equivalenza|
| Manutenzione |Frontend dedicato più esteso|Page/Dialog/Sidebar supportati, servizi riusati|Meno shell custom; rischio API/markup upstream e adattamento UI da misurare|
| Riproducibilità |Baseline R5 documentata|Delta OCI versionato, clone esclusivo e Page sync|No patch runtime, laboratorio conservato spento|

## Percorsi e azioni osservati

Agenda→seduta:1 click in entrambe; Desk mostra Dialog, webapp dettaglio laterale. Agenda→Pazienti→storia:2 click Desk. Finance→fattura:1 click dal riepilogo Desk. Prenota:1 click apre Dialog, poi ricerca e selezione tastiera; booking completo non eseguito. Nessun conteggio inventato dei flussi mutativi o dell'intera giornata operativa.

Tempo osservato: Desk login + prima vista3876ms; webapp prima vista già autenticata271ms. **Non comparabili come benchmark**: diversa fase/auth/cache e un solo campione. Nessuna conclusione prestazionale statistica.

## Sicurezza e limiti del confronto

Guard nativi CC applicati anche dal Desk: no cross-center, A/B own only, C nessuna seduta, report Finance negati ai professionisti, note private negate a Segreteria/Finance/Manager. UI hiding non è la prova: vedere security-results.json. Non verificati in C tutti i percorsi print/export/query né tutti i flussi mutativi; nessun PASS globale sicurezza o usabilità.

Browser19/20 verifiche registrate PASS,1 FAIL nel test Direzione che non fissa CentroA; ulteriore navigazione Finance arrestata da OOM QA. Fallimento conservato senza correggere retroattivamente i risultati. Esecuzione C interrotta, nessun confronto completo f/t né test interattivo Owner.

## Raccomandazione consultiva

Mantenere webapp primaria e Desk sperimentale: esiste un primo percorso reale, ma non evidenza sufficiente per cutover. Prima di ampliare C, separare QA per ruolo in processi Chromium nuovi e fissare il centro nel test Direzione; eventuale redistribuzione dei2.5GiB deve restare nello stesso tetto ed essere registrata in nuova attivazione. Non aumentare limiti/soglie automaticamente. La decisione definitiva rimane Owner/C4.
