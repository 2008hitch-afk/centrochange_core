# Matrice ridondanze e campi — Issue #75

Categorie: **ESSENZIALE** (necessario nel compito), **CONTESTUALE** (mostrare per stato), **AVANZATO** (apribile su richiesta), **TECNICO** (conservare per ruoli competenti/audit), **NON PERTINENTE** (candidato a rimozione dalla vista cliente, previa prova). La classificazione riguarda la presentazione: non cancella dati, regole o permessi.

| Area / elemento osservato | Ruolo | Categoria | Evidenza | Impatto e intervento minimo | Priorità |
|---|---|---|---|---|---|
| Agenda settimanale vuota come primo piano | Professionista | CONTESTUALE | Screenshot live `professional-agenda-mobile.png`; ruolo C mostra 0/0 | Preferire «Oggi / da completare» con accesso alla griglia esistente; verificare disponibilità dei dati già esposti. | P0 |
| «+ Prenota» in Agenda A/B | Professionista | CONTESTUALE, autorizzazione da verificare | Browser live, bottone visibile; C non lo vede | Chiarire se apre un flusso già autorizzato; se non autorizzato correggere la visibilità e testare API. Nessuna nuova capacità. | P0 |
| «Inizio» e «Agenda» verso stesso contesto | Tutti gli operativi | NON PERTINENTE se duplicati | Menu live A/B e Direzione | Unificare etichetta/destinazione mantenendo deep link autorizzati. | P1 |
| Selettore «Professionisti (1/1)» per un solo professionista | Professionista | NON PERTINENTE nella vista personale | Browser live A/B | Nascondere solo il controllo ridondante, mantenendo il filtro dove più risorse sono autorizzate. | P1 |
| Scheda Paziente: nome leggibile e stato | Direzione, autorizzati | ESSENZIALE | `patient-form.png` | Mettere nome leggibile prima dell'ID canonico. | P0 |
| Scheda Paziente: ID ripetuto in titolo, nome e pannello laterale | Direzione, autorizzati | TECNICO | `patient-form.png` | Rendere ID secondario/copiabile; preservare tracciabilità. | P0 |
| Scheda Paziente: «Invita come utente» | Direzione, autorizzati | AVANZATO | `patient-form.png` | Verificare uso e permesso; spostare in dettagli accessi se non parte dell'anagrafica ordinaria. | P1 |
| Scheda Professionista: nome/utente/struttura | Direzione | ESSENZIALE / CONTESTUALE | `practitioner-form.png` | Intestazione umana, collegamenti professionali raggruppati. | P1 |
| Sidebar nativa «Assegna», «Tag», «Condividi» nelle anagrafiche | Direzione | TECNICO | `patient-form.png`, `practitioner-form.png` | Valutare riduzione nella vista cliente; conservare strumenti ove necessari e per Administrator. | P1 |
| Fattura: documento, soggetto, stato, totale, residuo, scadenza | Direzione/Finance/Commercialista | ESSENZIALE | `invoice-form.png` | Il riepilogo è presente; migliorare nome soggetto e descrizione servizio. | P0 |
| Fattura: `customer`, `cc_center`, `posting_date` e nomi campo esposti | Cliente | TECNICO | testo DOM live di Sales Invoice | Rimuovere dalla lettura visiva/assistiva della vista cliente via estensione supportata, non tramite sostituzione indiscriminata del DOM. | P0 |
| Fattura: `Total Quantity`, `Sales Taxes and Charges`, `Use Company default Cost Center for Round off` | Direzione/Finance | AVANZATO / TECNICO | testo DOM live; oltre 20 etichette nel Form | Raggruppare dettagli contabili espandibili per Finance, lasciare audit/Administrator completi. | P0 |
| Fattura annullata: saldo e attività cronologica | Finance/Commercialista | CONTESTUALE | `invoice-form.png` | Esplicitare che il residuo visualizzato non è azione d'incasso; mantenere cronologia e documento annullato. | P1 |
| Nominativi demo tipo `CC-HTTP-UAT...` in paziente, servizio e fattura | Tutti | TECNICO | screenshot live, dati sintetici persistenti | Presentare alias descrittivi da dati già disponibili o documentare limite dei dati demo; nessun reseed in questo incarico. | P0 |
| Liste native: ID come filtro primario, toolbar e icone tecniche | Direzione/Finance | AVANZATO / TECNICO | `invoice-list.png` | Preferire soggetto/stato/data; mantenere filtro ID avanzato. | P1 |
| Report professionisti vs Anagrafica professionisti | Direzione/Finance | ESSENZIALE, funzioni distinte | rotte live `/app/healthcare-practitioner` e `cc_view=professional` | Etichette già distinte: preservarle; non unirle. | P2 |

Le altre viste native (Purchase Invoice, Payment Entry, Bank Transaction, Item, Item Price, Appointment Type, CC Center Service, CC Package Template) hanno superato 11/11 apertura List→Form nella prova read-only del 19/10, ma **non** una revisione campo per campo. Classificazioni dettagliate richiedono walkthrough con operatori Finance/Segreteria prima di nascondere campi o azioni.
