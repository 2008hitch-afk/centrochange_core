# Matrice ridondanze e campi — Issue #75, revisione Owner 20/10/2026

Categorie: **ESSENZIALE** (necessario nel compito), **CONTESTUALE** (per stato), **AVANZATO** (apribile su richiesta), **TECNICO** (per ruoli competenti/audit), **NON PERTINENTE** (candidato a riduzione dalla vista ordinaria, previa prova). La classificazione riguarda la presentazione: non cancella dati, funzioni o permessi. **Agenda esclusa da questa matrice di intervento.**

| Area / elemento osservato | Ruolo | Categoria | Evidenza | Intervento candidato | Ordine |
|---|---|---|---|---|---|
| Paziente: nome e stato | Direzione, autorizzati | ESSENZIALE | [Form live](screenshots/patient-form.png) | Nome leggibile prima dell'ID canonico. | 1 |
| Paziente: ID ripetuto in titolo, nome e pannello | Direzione, autorizzati | TECNICO | stesso screenshot | ID secondario e copiabile; tracciabilità preservata. | 1 |
| Paziente: contatti e soggetto fiscale | Direzione, autorizzati | ESSENZIALE / CONTESTUALE | Form Patient live | Raggruppare per compito/ruolo; non nascondere campi necessari a fatturazione o salvataggio. | 1 |
| Paziente: storia clinica | Professionisti/ruoli pertinenti | AVANZATO / RISERVATO | tab nativa nel Form | Visibilità e controllo server-side invariati. | 1 |
| Paziente: «Invita come utente» | Direzione, autorizzati | AVANZATO | screenshot live | Verificare uso e permesso; collocare tra dettagli accessi se non ordinario. | 1 |
| Anagrafiche: «Assegna», «Tag», «Condividi» | Direzione | TECNICO | [Patient](screenshots/patient-form.png), [Practitioner](screenshots/practitioner-form.png) | Valutare riduzione nella vista cliente, mantenendo strumenti necessari e Administrator. | 1–2 |
| Professionista: nome, stato, utente/struttura | Direzione | ESSENZIALE / CONTESTUALE | [Form live](screenshots/practitioner-form.png) | Intestazione umana e collegamenti raggruppati. | 2 |
| Professionista: `Charges`, `Free Followup Details`, indirizzi tecnici | Direzione | AVANZATO / TECNICO | sezioni DOM live | Tradurre/raggruppare solo dopo verifica campi obbligatori. | 2 |
| Fattura: documento, soggetto, stato, totale, residuo, scadenza | Direzione/Finance/Commercialista | ESSENZIALE | [Form live](screenshots/invoice-form.png) | Riepilogo presente; migliorare soggetto e prestazione. | 3 |
| Fattura: `customer`, `cc_center`, `posting_date` come chiavi | Cliente | TECNICO | testo DOM Sales Invoice | Nomi tecnici secondari tramite estensione supportata, senza occultare audit. | 3 |
| Fattura: `Total Quantity`, `Sales Taxes and Charges`, arrotondamenti | Direzione/Finance | AVANZATO / TECNICO | DOM live | Raggruppare dettagli per ruolo/stato; Finance e Administrator completi. | 3 |
| Fattura annullata: saldo e cronologia | Finance/Commercialista | CONTESTUALE | screenshot live | Chiarire che residuo storico non suggerisce nuovo incasso; cronologia integra. | 3 |
| Nominativi demo tipo `CC-HTTP-UAT...` | Tutti, nelle viste native | TECNICO | screenshot sintetici | Nome descrittivo da dati disponibili o limite demo dichiarato; nessun reseed qui. | 1–4 |
| Liste native: ID come filtro primario, toolbar tecnica | Direzione/Finance | AVANZATO / TECNICO | [Sales Invoice List](screenshots/invoice-list.png) | Preferire soggetto/stato/data; mantenere ricerca ID avanzata. | 3–4 |
| Purchase Invoice: `Immutable Incoming Source`, `Claimed Landed Cost...` | Finance | AVANZATO / TECNICO | DOM live | Tradurre/raggruppare dopo verifica contabile. | 4 |
| Payment Entry: `Payment Type`, `Mode of Payment`, `Writeoff` | Finance | ESSENZIALE / CONTESTUALE / AVANZATO | DOM live | Italiano e progressione documento→importo→allocazione. | 4 |
| Bank Transaction: ID, allocato/non allocato, fee | Finance | CONTESTUALE / AVANZATO | DOM live | Priorità a entrata/uscita, data, conto e stato. | 4 |
| Item Price: tempi di approvvigionamento | Direzione | NON PERTINENTE alla tariffa ordinaria | DOM live | Dettagli tecnici se non richiesto dal flusso ERPNext. | 4 |

Le 11 Form native hanno superato l'apertura read-only il 19/10, ma la riduzione di ogni campo richiede prova di salvataggi e ruoli. Report professionisti e Anagrafica Professionista restano distinti. Nessuna proposta cambia l'Agenda.
