# Fixture Agenda demo — CREAZIONE COMPLETATA, NON RIPETERE

Questa procedura descrive l’intervento autorizzato dall’Owner ed eseguito il 4 novembre sul solo sito sintetico `centro-uat.empv.it`. Non ripetere la creazione. Scopo: rendere visibili quattro appuntamenti dimostrativi nella settimana 2–8 novembre senza modificare righe preesistenti. Nessuna modifica a ruoli, schema, provider, PR #203 o produzione.

## Operazioni proposte

| Data | Direttore | Modalità | Orario candidato | Identità sintetica / chiave richiesta |
|---|---|---|---|---|
| 05/11/2026 | Marco | Sede | 09:00 | `ccdemo-1105-m-sede@example.invalid` / `ccdemo-1105-m-sede-v1` |
| 05/11/2026 | Francesca | Online | 09:00 | `ccdemo-1105-f-online@example.invalid` / `ccdemo-1105-f-online-v1` |
| 06/11/2026 | Marco | Sede | 09:00 | `ccdemo-1106-m-sede@example.invalid` / `ccdemo-1106-m-sede-v1` |
| 06/11/2026 | Francesca | Online | 09:00 | `ccdemo-1106-f-online@example.invalid` / `ccdemo-1106-f-online-v1` |

Il 4 novembre, al controllo delle 15:50 UTC, i quattro orari risultavano disponibili; devono essere controllati di nuovo immediatamente prima della scrittura. Non sono prenotazioni. Per il 4 novembre non sono risultati slot in sede per i due direttori: non forzare prenotazioni retrodatate o fuori disponibilità. Le identità indicate saranno nuove, con nomi esplicitamente dimostrativi e sesso anagrafico `Other`; non usare persone o email reali.

## Preflight e creazione, solo dopo GO

1. Confermare sito, immagine `cc75-ux:3cf75ab`, `cc_synthetic_dev=1`, `cc_uat_demo=1`, Company sintetica e percorso di conferma simulata. Se qualsiasi controllo fallisce, STOP. Non modificare la configurazione per farlo passare.
2. Verificare l'assenza delle quattro email nel solo perimetro sintetico; se un'email o una chiave esiste già senza manifest di proprietà coerente, STOP e non riutilizzarla. Verificare disponibilità e collisioni con l'API di primo incontro per ogni combinazione, e annotare la situazione iniziale di Email Queue, fatture, Payment Entry e ledger.
3. Conservare fuori da Git, in file protetto, un manifest con i quattro payload esatti sopra, chiavi, date/ore e stato di avanzamento. Trasmettere solo a esplicito GO la POST autorizzata `centrochange_core.scheduling.public_booking.first_meeting`: 20 minuti, EUR 0, dati `example.invalid`, richiesta stabile per ogni riga. La procedura non crea la successiva seduta da 45 minuti.
4. Dopo ogni esito salvare nel manifest l'ID restituito e verificare in sola lettura paziente creato, corrispondenza dell'email esatta, centro, direttore, modalità, ora, prezzo e durata, una sola conferma simulata, una sola riga Agenda e assenza di variazioni in Email Queue e registri contabili. Un retry deve ripetere esattamente lo stesso payload e la stessa chiave: l'esito atteso è `replay=true` e stesso ID. Non ricalcolare un altro slot usando una chiave già utilizzata. Se l'esito è incerto, verificare il manifest prima di ritentare; non inventare un'altra chiave.
5. Se un controllo o un salvataggio fallisce, STOP: mantenere l'inventario di quanto effettivamente creato, non cancellare né alterare altre righe, e riportare gli ID sintetici mediante canale protetto. Non dichiarare pronta l'Agenda corrente finché le verifiche non sono complete.

## Pulizia proposta, effetto e limite

La sola operazione standard verificata è **cancellazione logica**, non eliminazione: `centrochange_core.operations.lifecycle.cancel` con account operativo autorizzato, motivazione `CCDEMO1105 synthetic cleanup`, e soli ID presenti nel manifest dopo nuovo controllo puntuale di email, chiave, centro e tariffa 0. Ripetere la cancellazione sul medesimo ID restituisce `replay=true` senza duplicare l'evento; ciò è stato verificato su due prenotazioni nel clone isolato.

**Limite materiale:** la cancellazione conserva pazienti, appuntamenti, conferme e audit; nel clone della versione attuale l’Agenda ha continuato a mostrare entrambi gli appuntamenti cancellati. La rimozione fisica completa non è stata dimostrata sicura per queste fixture su UAT condiviso. Non usare il distruttore di fixture generico su Centro A o sui pazienti preesistenti e non cancellare righe SQL manualmente. La pulizia effettiva richiede una decisione separata e un metodo verificato; se non accettabile, non creare le fixture e usare la settimana 28/09–04/10.

## Prova preparatoria realmente eseguita

Il 4 novembre è stato avviato un sito Frappe/MariaDB monouso, con la stessa immagine `cc75-ux:3cf75ab`, sorgente baseline `3cf75ab`, sole fixture sintetiche e configurazione catalogo propria del clone. Con Playwright sono stati confermati due colloqui (Marco/sede e Francesca/online) per indirizzi `example.invalid`. Per entrambi: persistenza su Patient Appointment, 20 minuti / 0 EUR, un solo appuntamento per paziente e una sola conferma simulata; replay della stessa richiesta senza duplicati; ricerca Agenda e presenza visuale di ciascun evento e relativa card. Prima/dopo invariati Email Queue, Sales Invoice, Payment Entry, GL Entry e Payment Ledger Entry. Nessuna richiesta è stata inviata per questi test all'UAT condiviso.

Le stesse due righe test-owned sono state cancellate due volte sul solo clone: prima cancellazione e replay corretti; entrambe le card cancellate sono rimaste visibili nell'Agenda e lo storico è rimasto conservato. Le quattro righe proposte sopra non sono state create né simulate tutte insieme; disponibilità e chiavi proposte restano da verificare. Il clone e le proprie risorse temporanee sono stati rimossi dopo le prove.

## Esecuzione UAT autorizzata — 4 novembre 2026

I quattro appuntamenti sono stati creati rispettivamente come `HLC-APP-2026-00083`, `HLC-APP-2026-00084`, `HLC-APP-2026-00085` e `HLC-APP-2026-00086`, nell’ordine della tabella. Il manifest protetto di proprietà, payload e risultato è `/home/empv26/.local/state/centrochange/uat-demo-20261105.json` (permessi `0600`). I controlli prima e dopo ogni scrittura hanno confermato configurazione demo, slot, direttori, assenza di duplicati, una sola conferma simulata, invarianti di Email Queue, SMS Log e registri contabili e impronte invariate per anagrafiche e appuntamenti preesistenti. Le quattro card sono state aperte nel browser nell’Agenda reale. Nessuna cancellazione è stata eseguita sull’UAT; la pulizia logica resta una procedura successiva da pianificare, con storico conservato.
