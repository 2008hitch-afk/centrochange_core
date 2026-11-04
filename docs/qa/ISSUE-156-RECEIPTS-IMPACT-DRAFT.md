# Incassi operativi — analisi preliminare, non pronta per UAT

Baseline: `3cf75abc6766e404e35961021b8fafb18243a4f1`. Mandato Owner: tracker #156, commento #6627551926. Questa analisi iniziale non costituisce review indipendente.

## Esperienza prevista

L'utente Amministrazione/Direzione apre la card della seduta, vede numero e importo delle sedute aperte e raggiunge Pagamenti. Qui seleziona una o più sedute, distribuisce l'importo (anche parziale), indica data, metodo e causale, conferma e vede il residuo aggiornato e la registrazione nello storico. Nessuna fattura viene generata automaticamente. Il calendario rimane invariato.

## Confini del modello esistente

* `CC Settlement` è uno storico binario e non rappresenta importi o allocazioni parziali; `record_settlement` richiede la riapertura in stato `Auto Locked`.
* `collections._debts` tratta la fattura inviata come fonte autorevole, mentre la seduta senza fattura usa l'intero snapshot o `cc_paid`. Una nuova allocazione va considerata senza sommare nuovamente le due rappresentazioni.
* `receivables.receipt` registra e contabilizza un pagamento contro una sola fattura inviata. Non è un registro operativo pre-fattura e non deve essere richiamato per simulare l'incasso richiesto.
* `receivables.draft` e `submit` non conoscono eventuali futuri incassi operativi: occorre definire e testare un comportamento fail-closed per evitare che la successiva fatturazione o l'incasso contabile presentino il valore già ricevuto come ancora interamente da incassare. La riconciliazione fiscale resta esclusa dal mandato.
* `collections.require_booking` è richiamato anche da chiusura e prenotazione; l'eliminazione del blocco deve includere riprogrammazione, proiezioni UI e notifiche, senza rimuovere controlli di accesso o disponibilità.
* `enqueue_notice` e `deliver` possono entrambi creare il Notification Log; chiave evento e vincolo univoco limitano duplicazioni ma non dimostrano da soli correttezza di destinazione e retry.

## Vincoli per la futura implementazione

Serve una registrazione immutabile con chiave di idempotenza e allocazioni in centesimi, transazione e lock coerenti con le scritture su sedute e fatture, controllo di sede/paziente e verifica delle fatture esistenti. Vanno coperti simultaneità, replay identico e diverso, pagamenti storici binari, fatture già emesse e importi non riconciliabili, correzione/reversal e accesso diretto non autorizzato. Evitare assegnazioni o saldi contabili inventati. Le scelte di migrazione e rollback devono preservare gli eventi e non modificare STAGING prima del suo gate.

## Stato

L’implementazione e le prove sono documentate nella PR. Questo documento resta un’analisi iniziale, non un’autorizzazione al deploy né una review indipendente.
