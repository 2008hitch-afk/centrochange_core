# Piano UX operativo — decisione Owner richiesta

**Stato:** proposta per #75; fermarsi prima di modificare il prodotto. #139 mantiene il proprio backlog tecnico; qui sono elencati solo problemi di compito, comprensibilità e presentazione osservati.

| Priorità | Schermata / ruolo | Intervento minimo candidato | Meccanismo preferito | Verifica di accettazione |
|---|---|---|---|---|
| P0 | Agenda Professionista A/B/C | Primo piano «Oggi / da completare / prossime», link alla griglia esistente; stato vuoto utile. Chiarire `+ Prenota` contro la matrice permessi prima di intervenire. | Workspace o pagina Frappe già esistente; riuso endpoint e controlli server-side. | A/B trovano la prossima seduta e l'esito senza guida; C vede nessuna assegnazione; API vietate restano vietate. Desktop/mobile/tastiera. |
| P0 | Sales Invoice, Direzione/Finance/Commercialista | Nome soggetto e servizio leggibili prima dell'ID, riepilogo per stato, dettagli contabili espandibili; tradurre label cliente e rimuovere chiavi campo dalla lettura visiva. | Property Setter/traduzioni/List/Form Script supportati, CSS circoscritto. | Bozza/pagata/annullata distinguibili; nessuna azione errata; Finance/Commercialista e Administrator conservano dettagli/audit. |
| P0 | Patient e Healthcare Practitioner | Nome primario e ID secondario, gruppi pertinenti, pannelli tecnici solo quando necessari. | `title_field`, List View Settings, Form Customize/Property Setter, traduzioni. | Selezione della persona corretta, salvataggio e accessi diretti invariati. |
| P1 | Item/Item Price/configurazioni | Raggruppare essenziale/avanzato dopo inventario con operatori. | Personalizzazioni native versionate. | Creazione/modifica autorizzate, validazioni e campi ERPNext necessari preservati. |
| P1 | Purchase Invoice/Payment Entry/Bank Transaction e Banca | Ripetere pattern «cosa guardo → cosa posso fare → come procedo» per stato. | Native Form/List prima, pagine dedicate esistenti per riconciliazione. | Documento, importo, saldo, riferimento e risultato chiari; nessun flusso contabile alterato. |
| P1 | Ricerca, Agenda, TS/SdI, report | Copy e stato vuoto coerenti, italiano e date locali nelle viste cliente. | Traduzioni, Form/Client Scripts, componenti esistenti. | Task assistiti e accessibilità; formati API/database invariati. |
| P2 | Sidebar «Inizio»/«Agenda», notifiche/audit | Rimuovere sola ridondanza semantica, migliorare etichette evento. | Workspace/navigazione esistente. | Un unico percorso riconoscibile senza perdere deep link o tracciabilità. |

## Sequenza proposta dopo approvazione

1. Validare i due prototipi con Owner e 1–2 rappresentanti dei ruoli Professionista e Finance. Annotare quali campi/azioni sono davvero necessari; per Finance verificare esempi bozza, pagata, annullata.
2. Redigere inventario campo-per-campo per le otto native non ispezionate in profondità. **Non eliminare** i campi classificati tecnici; definire esposizione per ruolo e stato.
3. Implementare in un branch distinto il primo gruppo P0 con estensioni Frappe supportate. Conservare permessi, API, documenti canonici, audit, schema e dati. Predisporre migrazione riproducibile solo se strettamente necessaria e approvata.
4. Eseguire test automatici di sicurezza e task test browser reali: navigazione, apertura, modifica consentita, validazione, persistenza, errori, refresh, desktop/mobile, tastiera. Misurare esito e facilità del compito; il rendering tecnico da solo non basta.
5. Per installare sul DEV condiviso chiedere gate operativo specifico con preflight, checkpoint e rollback. Questo audit non autorizza deploy.

## Decisione Owner richiesta

Approvare o correggere **la direzione dei due prototipi e l'ordine P0→P2**, soprattutto la priorità a una vista Professionista «Oggi / da completare» e alla lettura della fattura per stato. La review deve decidere quali informazioni contabili restano visibili per Direzione, Finance e Commercialista. Nessun intervento applicativo è stato avviato.
