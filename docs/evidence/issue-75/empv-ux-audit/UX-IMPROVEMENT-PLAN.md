# Piano UX corretto — decisione Owner richiesta

**Issue #75, correzione vincolante Owner del 20/10/2026.** Questo documento sostituisce la proposta precedente della PR #142. **Agenda esclusa dagli interventi:** griglia, struttura visiva, navigazione, filtri, visualizzazioni e flussi rimangono invariati per tutti i ruoli, compreso Professionista. Nessuna implementazione o distribuzione è autorizzata da questo piano. La #139 mantiene il proprio backlog tecnico.

## Ordine delle aree da progettare

| Ordine | Schermata e ruoli | Problema osservato | Intervento candidato, solo presentazione | Meccanismo preferito | Verifica prevista |
|---|---|---|---|---|---|
| 1 | **Anagrafica Paziente** — ruoli già autorizzati | ID di fixture ripetuto in titolo, nome e pannello; anagrafica, fiscale e clinico sullo stesso piano; strumenti nativi vicini al compito ordinario. | Nome e stato in evidenza; campi obbligatori e recapiti pertinenti raggruppati; ID canonico secondario e copiabile; fiscale e storia clinica disponibili secondo permessi invariati. | `title_field`, List View Settings, Customize Form/Property Setter, traduzioni e Form Script supportati, solo se necessari. | Ricerca → scheda → modifica consentita → salvataggio → refresh; campi obbligatori e accessi diretti verificati. |
| 2 | **Anagrafica Professionista** — Direzione/gestori autorizzati | Nome sintetico/ID dominante; `Charges`, `Free Followup Details` e altri campi inglesi; dati principali e collegamenti dispersi. | Nome, stato e collegamenti pertinenti in apertura; contatti comprensibili; sezioni tecniche accessibili quando servono. Tenere distinta questa anagrafica dal Report professionisti e dalla vista operativa. | Configurazione Form/List nativa, traduzioni e script supportati; Administrator completo. | Trovare stato, utente/struttura e contatto; modifica autorizzata, persistenza e campi richiesti. |
| 3 | **Fatture pazienti** — Direzione, Segreteria, Finance, Commercialista secondo ruolo | Riepilogo presente, ma soggetto e prestazioni mostrano codici; chiavi tecniche e campi ERPNext in inglese nel Form. | Soggetto, documento, data, stato, totale, residuo e prestazioni come primo piano; prossima azione per stato; contabilità/audit accessibili ai ruoli autorizzati. | Personalizzazioni native List/Form, Property Setter/traduzioni, script circoscritti. | Bozza, contabilizzata, pagata/parziale e annullata: lettura, azioni permesse, documenti intatti, Accountant in sola lettura. |
| 4 | **Altre schermate native ERPNext** — ruoli autorizzati | Purchase Invoice, Payment Entry, Bank Transaction, catalogo, tariffe e configurazioni contengono etichette inglesi o campi tecnici non pertinenti al compito principale. | Per ogni Form distinguere essenziale, contestuale, avanzato e tecnico; priorità a soggetto, stato, importo, riferimento e azione; mantenere avanzati e audit. | List/Form Customize, traduzioni, Workspace e Client Script supportati; pagina dedicata solo se il nativo non copre il flusso. | Per le altre otto Form: compito guidato, campi obbligatori, errori, permessi, salvataggio, persistenza e confronto desktop/mobile. |

## Sequenza dopo eventuale approvazione

1. Owner valuta i [prototipi Paziente](prototypes/anagrafica-paziente-prima-dopo.html), [Anagrafica Professionista](prototypes/anagrafica-professionista-prima-dopo.html) e [Fattura](prototypes/fattura-paziente-prima-dopo.html). Il precedente prototipo sulla sostituzione dell'Agenda è ritirato.
2. Con operatori autorizzati, confermare campi indispensabili e avanzati, soprattutto per contabilità e informazioni cliniche. Nessun campo canonico o obbligatorio va eliminato per estetica.
3. Solo dopo decisione Owner, implementare su branch dedicato con estensioni Frappe native e versionate. Preservare API, permessi server-side, schema, dati, storico, contabilità e Administrator.
4. Verificare compiti reali con browser e API: apertura, modifica consentita, validazione, salvataggio, refresh, errori, accessi diretti, desktop/mobile e tastiera. Un PASS di rendering non basta per PASS UX.
5. Un eventuale aggiornamento DEV condiviso richiede gate operativo separato con preflight, checkpoint e recupero.

## Decisione Owner richiesta

Approvare o correggere **i tre prototipi nativi e l'ordine 1→4**. In particolare decidere quali campi avanzati devono restare subito visibili a Direzione, Finance e Commercialista. L'Agenda non è oggetto della decisione: resta invariata per vincolo Owner.
