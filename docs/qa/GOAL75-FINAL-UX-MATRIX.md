# GOAL 75 — matrice ciclo correttivo

Baseline 8a3d6b96e82d0a0970beb0a828bac0adc83f103c, PR #193. Target di sviluppo isolato; nessun deploy.

| Archivio | Ruoli visibili (server autorevole) | Azioni esistenti | Pattern baseline → criterio | API e rischio |
| --- | --- | --- | --- | --- |
| Pazienti | operativi autorizzati; modifica Manager | cerca, dettaglio, modifica | drawer + modale → pagina + modifica in pagina | profiles.patient_detail/save; scope, versione, audit |
| Professionisti | Manager/Professionista; modifica Manager | cerca, dettaglio, modifica | drawer + modale → pagina + modifica in pagina | profiles.practitioner_detail/save; scope, versione, audit |
| Articoli | Manager | cerca, dettaglio, modifica | drawer + modale → pagina + modifica in pagina | catalog; versione, audit |
| Tariffe | Manager | cerca, dettaglio, crea, modifica | drawer + modale → pagina + modifica in pagina | catalog; prezzi storici invariati |
| Tipi seduta | Manager | cerca, dettaglio, crea, modifica | drawer + modale → pagina + modifica in pagina | catalog; versione, audit |
| Servizi del centro | Manager | cerca, dettaglio, crea, modifica | drawer + modale → pagina + modifica in pagina | catalog; scope centro |
| Modelli pacchetto | Manager | cerca, dettaglio, crea, modifica | drawer + modale → pagina + modifica in pagina | catalog; versione, audit |
| Fatture pazienti | finanza autorizzata | dettaglio, stampa se consentita | drawer + anteprima → senza sovrapposizione | finance document, sola lettura |
| Fatture professionisti | finanza autorizzata | dettaglio, stampa se consentita | drawer + anteprima → senza sovrapposizione | finance document, sola lettura |
| Pagamenti | finanza autorizzata | dettaglio, stampa se consentita | drawer + anteprima → senza sovrapposizione | finance document, sola lettura |
| Movimenti bancari | finanza autorizzata | dettaglio | drawer → pagina di dettaglio | finance.reporting.records, sola lettura |

Criteri trasversali: nessuna nuova API o fonte dati; conferma esplicita, motivo, diff e versione; focus/tastiera e ritorno alla ricerca, desktop/mobile; test positivi/negativi server-side sul clone; audit note distinto per tipo canonico, raw preservato; Agenda senza mutazioni lifecycle. Smoke regressione per componenti condivisi, rilevazione overlay; screenshot sintetici.

## Altre superfici con overlay

- Agenda: il drawer rapido cliente è richiesto dall'Owner; le azioni ordinarie sono inline. Solo il blocco pagamento apre una conferma contestuale sopra il drawer: è un'interruzione di sicurezza con deroga circoscritta, non l'editor anagrafico; conservarla e collaudare annulla/permessi senza cambiare regole economiche.
- Paziente operativo: pagina completa e modale di modifica, senza drawer sottostante; API profilo canonica condivisa con Archivi.
- Servizi: drawer breve di sola lettura, rimanda al catalogo canonico; nessun editor sovrapposto.
- Registro: singolo drawer di dettaglio, nessun editor.
- Finanza: drawer di dettaglio con azioni inline; la creazione è una modale indipendente. I workflow finanziari rinviati non vengono ampliati.
- Accessi: modale indipendente con conferma interna, nessun drawer di dettaglio sottostante.
- `MasterArchive` è preview sintetica in memoria, non la superficie `ScopedArchive` usata sul sito reale; mantiene la propria indicazione di preview e non costituisce una seconda fonte dati.
- Nelle tre sezioni finanziarie stampabili di `ScopedArchive` il dettaglio è ora a pagina; la sola anteprima di stampa usa una modale, senza drawer sottostante. I movimenti bancari rimangono sola lettura.
