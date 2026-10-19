# Inventario delle 23 destinazioni Direzione e delle varianti di ruolo

Metodo: le 23 rotte uniche della sidebar Direzione sono state censite dal browser live; i menu di Segreteria (14), Finance (10), Commercialista (5), Professionista A/B/C (4) sono sottoinsiemi/varianti autorizzate. Per ogni riga: compito; dati/ingressi; azione/esito; costo cognitivo osservato o da verificare. Le condizioni `DA VALIDARE` non sono PASS UX. Nessun form è stato salvato durante l'audit.

| Schermata | Ruoli campionati | Compito e informazioni essenziali | Dati da inserire / azione primaria / risultato atteso | Ridondanza o punto oscuro | Stato UX |
|---|---|---|---|---|---|
| Agenda | m,s,a,b,c | Sedute, orario, stato, paziente autorizzato | Filtri data/professionista; aprire seduta o azione consentita; conferma di stato | Per professionista prevale griglia vuota, non lavoro da svolgere; `+ Prenota` da chiarire | PROBLEMA P0 |
| Ricerca pazienti | m,s,a,b,c | Trovare paziente autorizzato e assegnazioni | Cerca, seleziona, visualizza risultato; eventuali azioni approvate | Ricerca e anagrafica distinte; etichetta chiara ma task test necessario | DA VALIDARE |
| Anagrafica pazienti | m | Identità, contatti, stato e dati fiscali pertinenti | Modifica autorizzata, salva, rileggi | ID sintetico ripetuto; pannelli tecnici | PROBLEMA P0 |
| Anagrafica professionisti | m | Identità, stato, collegamenti professionali | Modifica autorizzata, salva, rileggi | ID domina nome; sezioni inglesi `Charges`/`Free Followup Details` presenti nel DOM | PROBLEMA P1 |
| Disponibilità | m,s,a,b,c | Slot e giorni disponibili | Selezione consentita, conferma | Professionista ha bisogno di collegamento diretto con proprie sedute | DA VALIDARE |
| Notifiche | m,s,a,b,c | Evento, tempo, priorità | Apri/segna secondo permesso; risultato chiaro | Terminologia e stati vuoti da walkthrough | DA VALIDARE |
| Finanza | m,s,f | Scopo delle funzioni economiche | Apri documento/flusso; esito coerente | Menu approvato; non ridisegnarlo | DA VALIDARE |
| Fatture pazienti | m,s,f,t | Soggetto, numero, stato, totale, residuo e prestazioni | Filtra, apri, azione per stato autorizzata | Etichette tecniche/inglesi nel Form; nominativo sintetico | PROBLEMA P0 |
| Fatture professionisti | m,s,f,t | Fornitore, documento, importo, stato | Filtra, apri, verifica importo/pagamento | `Immutable Incoming Source`, `Tax Id`, `Claimed Landed Cost...`, `Additional Discount` nel Form; cosa è essenziale dipende dal ruolo | PROBLEMA P1 |
| Incassi e pagamenti | m,s,f | Verso del pagamento, soggetto, documento, importo, residuo | Registra solo se autorizzato, verifica allocazione | `Payment Type`, `Mode of Payment`, `Unallocated Amount`, `Writeoff` in inglese/tecnici | PROBLEMA P1 |
| Movimenti bancari | m,s,f | Entrata/uscita, conto, data, collegamento e residuo | Apri, controlla riconciliazione | `Transaction ID`, `Allocated/Unallocated Amount` nel Form | PROBLEMA P1 |
| Banca | m,s,f | Movimenti da riconciliare | Scegli documento permesso, verifica esito | L'azione va spiegata per stato, senza inventare riconciliazioni | DA VALIDARE |
| SdI simulato | m,s,f | Stato di simulazione, problema e documento | Consulta/azione simulata consentita | Dichiarazione «simulato» da rendere inequivoca in ogni stato | DA VALIDARE |
| TS simulato | m,s,f | Stato di simulazione, problema e documento | Consulta/azione simulata consentita | Come SdI; nessun invio reale | DA VALIDARE |
| Report professionisti | m,s,f,t | Attività/posizione professionisti, periodo | Filtra, legge/export autorizzato | Non confondere con anagrafica o vista operativa del professionista | DA VALIDARE |
| Report economico pazienti | m,s,f,t | Posizione economica, periodo | Filtra, legge/export autorizzato | Termini e riferimenti da task test | DA VALIDARE |
| Gestione accessi | m | Utente, ruolo, ambito | Modifica autorizzata, verifica effetto | Non usare sola visibilità UI come sicurezza | DA VALIDARE |
| Servizi (`Item`) | m | Nome, categoria, descrizione e tariffe | Modifica autorizzata, salva | Tab Dettagli/Tariffe/Collegamenti; dettagli avanzati già presenti | PARZIALE |
| Tariffe (`Item Price`) | m | Servizio, listino, valuta, prezzo, validità | Inserisce prezzo, salva | `Tempi di approvvigionamento` non pertinente al compito ordinario | PROBLEMA P1 |
| Tipi di seduta (`Appointment Type`) | m | Durata, prenotabilità, servizio | Modifica autorizzata, salva | Tab Fatturazione/Codifiche mediche: contestuali o avanzate | PARZIALE |
| Servizi del centro | m | Centro e tipo seduta | Associa, salva | Form compatto; verifica etichette/stato vuoto | DA VALIDARE |
| Modelli pacchetto | m | Nome, servizio, sedute incluse | Definisce modello, salva | Form compatto; verifica comprensibilità del risultato | DA VALIDARE |
| Registro modifiche | m | Evento, autore, entità, tempo | Filtra e consulta audit | ID tecnici utili alla tracciabilità ma non come unica descrizione | DA VALIDARE |

## Form nativi: campi osservati nel runtime pinned

Il probe read-only del 19/10 ha letto sezioni/etichette visibili senza modificare dati. `Patient`: Dati paziente, soggetto fiscale, recapiti e storia clinica; **essenziali** nome/stato e dati richiesti dal flusso, **avanzati/riservati** storia clinica. `Healthcare Practitioner`: Dati principali e collegamenti; `Charges`, `Free Followup Details`, indirizzi in inglese sono **avanzati/tecnici** da verificare prima della riduzione. `Sales Invoice`: riepilogo **essenziale**, tasse/arrotondamenti **avanzati** per Finance, chiavi campo **tecniche**. `Purchase Invoice`: fornitore/importo/scadenza **essenziali**, landed cost/supplier source **avanzati/tecnici**. `Payment Entry`: verso/soggetto/importo/riferimento **essenziali**, writeoff/allocazioni **contestuali o avanzati**. `Bank Transaction`: data/conto/entrata/uscita/stato **essenziali**, ID/fee **avanzati**. `Item`: categoria/descrizione **essenziali**. `Item Price`: listino/valuta/prezzo/validità **essenziali**, lead time **non pertinente alla vista ordinaria**. `Appointment Type`: durata/prenotabilità **essenziali**, codifiche mediche **contestuali**. `CC Center Service`: centro/tipo seduta **essenziali**. `CC Package Template`: nome/servizio/sedute incluse **essenziali**.

Campi obbligatori e dipendenze di salvataggio vanno convalidati con metadati Frappe pinned e prova su fixture prima di nasconderli. Questo inventario non autorizza la rimozione di nessun campo.
