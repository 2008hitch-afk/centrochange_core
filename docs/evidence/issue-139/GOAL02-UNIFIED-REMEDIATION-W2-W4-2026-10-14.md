# GOAL-02 #139 — candidato W2–W4, verifica senza deploy (14/10/2026)

**Stato: PARTIAL.** Le modifiche W2–W4 sono versionate sulla PR #140 DRAFT ma non installate sul DEV. Le prove browser qui sotto usano la versione DEV corrente o un CSS candidato iniettato solo nella sessione di prova; non sono un PASS live del candidato. Dati Owner, Site, Compose e immagini non modificati.

Ultimo controllo read-only: nove servizi `centrochange-dev` attivi, `assets_json` in stato `MATCH` (69 mapping, zero differenze, file CSS presenti), impronta dei dati Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3` e `Communication` `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`, invariate. I sei servizi applicativi servono ancora l'immagine baseline `centrochange-single:goal02-abc-fixture-83f8f4f`; il candidato PR #140 non è stato distribuito.

## W2 — sede operativa

- `Branch.cc_operational` è proposto come Custom Field versionato con default **0 (non operativa)**, così una migrazione incompleta non rende Centro B prenotabile. `set_operational` è riservato alla Direzione, richiede motivo, scrive audit e consente riattivazione solo con lista esplicita nella configurazione del Site. Una stringa di configurazione non vale come allowlist.
- Guard server-side per nuove operazioni in Agenda, disponibilità, prenotazione pubblica, amministrazione e Finance; i selettori mostrano soltanto sedi operative. `Gestione → Centri` espone lo stato alla Direzione. La route pubblica restituisce un errore generico se la sede è inattiva, evitando la divulgazione dello stato interno.
- Test offline positivi e negativi per stato, replay, ruoli, guard e default fail-closed. **Non è stata eseguita la migrazione e Centro B non è stata disattivata sul Site.** Il gate Owner dovrà autorizzare una finestra controllata per migrazione, attivazione auditata di Centro A e permanenza inattiva di Centro B, con snapshot e recupero dei dati. La sola disponibilità del campo non soddisfa #135 live.
- Inventario Frappe read-only sul Site corrente: due `Branch` sintetici, `CC-HTTP-UAT0000001 A` e `CC-HTTP-UAT0000001 B`. Dopo la migrazione con default 0 entrambe le sedi sarebbero temporaneamente non operative; il percorso esecutivo deve quindi impedire traffico applicativo fino all'attivazione auditata di A. Senza checkpoint DB e autorizzazione specifica per migrazione/transizione non si esegue il deploy W2.

## W3 — date/ore e storia

- Helper Europe/Rome per calendario e intervalli su cambio ora legale/solare (5 test). Nessuna conversione del valore canonico DB/API. Le azioni seduta presentate dalla UI rispettano stato e ruolo; il backend rimane autoritativo (7 test).
- I campi ora dell'Agenda (prenotazione, spostamento, disponibilità, assenza) propongono `HH:mm` 24 ore con validazione browser indipendente dalla lingua del sistema. Prova Chromium `en-US` e `it-IT`: `09:00` e `23:59` validi, `09:00 AM` e `24:00` rifiutati. È ancora una verifica del candidato, non della versione servita.
- 44 messaggi di errore/validazione dei tre servizi di prenotazione, disponibilità e primo incontro sono resi in italiano direttamente sul server, mantenendo le condizioni e le classi di errore esistenti. La ricerca statica trova ancora numerosi messaggi inglesi nelle altre aree, soprattutto Finance: non si considera conclusa la localizzazione globale.
- Altri 65 messaggi server-side di Banca, TS, SdI e adapter fiscale simulato sono stati resi in italiano senza cambiare controlli, autorizzazioni o trasporto fiscale. Totale di questo ciclo: 109 messaggi; restano aperti gli altri moduli Finance/Operations e il collaudo degli error path live.
- Altri 84 messaggi di fatture pazienti, fatture fornitori/XML ricevuti, accordi di pagamento e compensi professionisti sono stati localizzati. Totale di questo ciclo: **193 messaggi**. I controlli di importo, fonte, idempotenza e audit non sono stati modificati; la restante superficie backend deve ancora essere inventariata e provata live.
- Altri 55 messaggi dei percorsi operativi (sedute, note, pacchetti, conferme, ricerca e disponibilità del workspace) sono stati tradotti. Totale: **248 messaggi** server-side. I messaggi dinamici e le risposte native Frappe/ERPNext richiedono ancora un retest per ruolo e per error path.
- Altri 38 messaggi dei controlli di accesso, audit e ciclo di vita degli account sono in italiano. Totale: **286 messaggi** server-side localizzati senza modificare i predicati o le classi di errore. I messaggi tecnici DEV e quelli nativi non sono presentati come coperti.
- Altri 58 messaggi di allegati contabili, adapter nativo, report e coda amministrativa sono stati localizzati. Totale: **344 messaggi** server-side nel candidato. Rimangono da verificare le stringhe dinamiche, i DocType esposti e le risposte native; la #134 resta aperta fino ai test live di successo ed errore.
- Altri 11 messaggi delle route web cliente e dei DocType Centro Change sono stati tradotti. Totale: **355 messaggi** server-side; esclusi messaggi dei fixture/test DEV. La copertura è basata su inventario di `frappe.throw` letterali, non dimostra ancora assenza di inglese in errori dinamici o upstream.
- Un controllo automatico impedisce la reintroduzione di `frappe.throw` letterali evidentemente inglesi nei moduli runtime cliente. Non è un traduttore e non sostituisce test degli error path, messaggi generati dinamicamente o Frappe nativo.
- La cronologia eventi seduta è letta da API esistenti con isolamento per paziente/professionista; note e revisioni sono distinte. Due test offline controllano isolamento e forma dei dati.
- La localizzazione globale di errori, picker, stampa e superfici native richiesta da #134 resta **non completata e non collaudata live**. Nessun PASS W3 globale.

## W4 — resa mobile e chiarezza contabile

- Il test nativo ora misura badge di stato effettivamente tagliati da antenati con overflow nascosto. Sulla versione DEV servita a 390×844: **6 FAIL su 11 liste** (`Patient`, `Healthcare Practitioner`, `Sales Invoice`, `Purchase Invoice`, `Payment Entry`, `Bank Transaction`); 5 PASS. Il difetto è il risultato `display:table` di Frappe più largo del contenitore mobile. A 390 px il badge di `Sales Invoice` superava il bordo visibile della tabella.
- CSS candidato circoscritto alle List View cliente fino a 575,98 px: risultato e righe occupano la larghezza disponibile. La prova Chromium con sola iniezione temporanea di questa regola dà **11/11 PASS** sul controllo geometrico; nello screenshot di `Sales Invoice` i badge «Bozza», «In ritardo» e «Pagata» sono completi. La prova non equivale a test live dopo distribuzione. Screenshot privati: `issue139-w4-baseline-20261014/` e `issue139-w4-css-preview-20261014/` nel vault `browser-evidence` del server.
- Report economico pazienti: il residuo zero non è più colorato come allarme; il rosso resta riservato a saldi positivi. Restano da verificare sulla versione installata i flussi Finanza, TS/SdI, la navigazione completa e tutti i ruoli.
- Liste TS/SdI simulate: la colonna «Esito / verifica» distingue un esito acquisito, un problema classificato, l'assenza di tentativi e un tentativo da consultare; evita il trattino ambiguo segnalato dall'Owner. Quattro stati testati offline; il contenuto live resta da verificare.
- Dettaglio seduta cancellata: la proiezione già autorizzata include ora il fatto `cc_late_cancellation`; la scheda distingue cancellazione tardiva, stato economico operativo e documento contabile, rinviando a Storico per autore e motivo. Non calcola un nuovo addebito e non modifica i valori canonici.
- Selettori condivisi: un elenco breve resta `<select>` nativo; oltre otto opzioni usa il combobox ricercabile esistente, con etichetta del campo e selezione da tastiera. Le opzioni provengono ancora dalle API autorizzate; il widget non amplia i permessi.

## Test ed evidenze

- `python3 -m unittest discover -s infra/tests -p 'test_*.py' -q`: 38 PASS.
- `node infra/tests/issue139_rome_date.cjs`: 5 PASS; `node infra/tests/issue139_session_actions.cjs`: 7 PASS.
- `node infra/browser/issue139_time_control.cjs`: `en-US` e `it-IT` PASS con Chromium reale.
- `node infra/tests/issue139_fiscal_outcome.cjs`: 4 stati fiscali simulati PASS.
- `node infra/browser/issue139_long_select.cjs`: desktop/mobile PASS per elenco breve nativo, ricerca, tastiera, stato vuoto e valore canonico selezionato.
- `node --check` sui JS modificati e sul browser runner, `compileall` sui moduli Python modificati, `git diff --check`: PASS.
- Il CSS candidato è stato testato in Chromium senza scrivere al runtime. **I test W5 delle 128 combinazioni e 38 controlli sintetici sul candidato non sono stati eseguiti:** richiedono prima installazione autorizzata, preflight, checkpoint e rollback.
- Il runner W5 riusato dalla #137 ora separa errori asset, API e realtime e misura i badge tagliati. Un errore API o socket.io resta FAIL; non viene attribuito falsamente a un bundle CSS. Il confronto completo sarà eseguito solo sulla versione candidata effettivamente servita.
- Prova read-only di classificazione sulla Direzione DEV corrente: 23/23 route rimangono FAIL per realtime, 0 failure asset e 0 failure API, 0 richieste mutative inattese. Le risposte 400 della connessione socket.io vengono attribuite a realtime anziché a JS/CSS. **Questo è un baseline diagnostico, non il retest W5 del candidato.**

## Gate operativo ancora necessario

La #139 non autorizza deploy, migrazione, riavvii né modifica dei dati Owner. Prima della richiesta di gate: chiudere le correzioni source ancora pertinenti, preparare un unico executor con candidate SHA, confronto Compose/immagini, fingerprint prima/dopo, test live e rollback. La correzione socket.io richiede applicare l'alias di rete versionato al solo frontend; non è stata applicata. La PR rimane DRAFT e nessuna Owner acceptance è dichiarata.
