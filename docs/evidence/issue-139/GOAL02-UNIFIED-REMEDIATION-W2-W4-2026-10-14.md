# GOAL-02 #139 — candidato W2–W4, verifica senza deploy (14/10/2026)

**Stato: PARTIAL.** Le modifiche W2–W4 sono versionate sulla PR #140 DRAFT ma non installate sul DEV. Le prove browser qui sotto usano la versione DEV corrente o un CSS candidato iniettato solo nella sessione di prova; non sono un PASS live del candidato. Dati Owner, Site, Compose e immagini non modificati.

## W2 — sede operativa

- `Branch.cc_operational` è proposto come Custom Field versionato. `set_operational` è riservato alla Direzione, richiede motivo, scrive audit e consente riattivazione solo con lista esplicita nella configurazione del Site. Una stringa di configurazione non vale come allowlist.
- Guard server-side per nuove operazioni in Agenda, disponibilità, prenotazione pubblica, amministrazione e Finance; i selettori mostrano soltanto sedi operative. `Gestione → Centri` espone lo stato alla Direzione. La route pubblica restituisce un errore generico se la sede è inattiva, evitando la divulgazione dello stato interno.
- Test offline positivi e negativi per stato, replay, ruoli e guard. **Non è stata eseguita la migrazione e Centro B non è stata disattivata sul Site.** Occorrono gate separati Owner per installazione/migrazione e per la transizione persistente di Centro B; la semplice disponibilità del campo non soddisfa #135 live.

## W3 — date/ore e storia

- Helper Europe/Rome per calendario e intervalli su cambio ora legale/solare (5 test). Nessuna conversione del valore canonico DB/API. Le azioni seduta presentate dalla UI rispettano stato e ruolo; il backend rimane autoritativo (7 test).
- I campi ora dell'Agenda (prenotazione, spostamento, disponibilità, assenza) propongono `HH:mm` 24 ore con validazione browser indipendente dalla lingua del sistema. Prova Chromium `en-US` e `it-IT`: `09:00` e `23:59` validi, `09:00 AM` e `24:00` rifiutati. È ancora una verifica del candidato, non della versione servita.
- 44 messaggi di errore/validazione dei tre servizi di prenotazione, disponibilità e primo incontro sono resi in italiano direttamente sul server, mantenendo le condizioni e le classi di errore esistenti. La ricerca statica trova ancora numerosi messaggi inglesi nelle altre aree, soprattutto Finance: non si considera conclusa la localizzazione globale.
- La cronologia eventi seduta è letta da API esistenti con isolamento per paziente/professionista; note e revisioni sono distinte. Due test offline controllano isolamento e forma dei dati.
- La localizzazione globale di errori, picker, stampa e superfici native richiesta da #134 resta **non completata e non collaudata live**. Nessun PASS W3 globale.

## W4 — resa mobile e chiarezza contabile

- Il test nativo ora misura badge di stato effettivamente tagliati da antenati con overflow nascosto. Sulla versione DEV servita a 390×844: **6 FAIL su 11 liste** (`Patient`, `Healthcare Practitioner`, `Sales Invoice`, `Purchase Invoice`, `Payment Entry`, `Bank Transaction`); 5 PASS. Il difetto è il risultato `display:table` di Frappe più largo del contenitore mobile. A 390 px il badge di `Sales Invoice` superava il bordo visibile della tabella.
- CSS candidato circoscritto alle List View cliente fino a 575,98 px: risultato e righe occupano la larghezza disponibile. La prova Chromium con sola iniezione temporanea di questa regola dà **11/11 PASS** sul controllo geometrico; nello screenshot di `Sales Invoice` i badge «Bozza», «In ritardo» e «Pagata» sono completi. La prova non equivale a test live dopo distribuzione. Screenshot privati: `issue139-w4-baseline-20261014/` e `issue139-w4-css-preview-20261014/` nel vault `browser-evidence` del server.
- Report economico pazienti: il residuo zero non è più colorato come allarme; il rosso resta riservato a saldi positivi. Restano da verificare sulla versione installata i flussi Finanza, TS/SdI, la navigazione completa e tutti i ruoli.
- Liste TS/SdI simulate: la colonna «Esito / verifica» distingue un esito acquisito, un problema classificato, l'assenza di tentativi e un tentativo da consultare; evita il trattino ambiguo segnalato dall'Owner. Quattro stati testati offline; il contenuto live resta da verificare.
- Dettaglio seduta cancellata: la proiezione già autorizzata include ora il fatto `cc_late_cancellation`; la scheda distingue cancellazione tardiva, stato economico operativo e documento contabile, rinviando a Storico per autore e motivo. Non calcola un nuovo addebito e non modifica i valori canonici.

## Test ed evidenze

- `python3 -m unittest discover -s infra/tests -p 'test_*.py' -q`: 36 PASS.
- `node infra/tests/issue139_rome_date.cjs`: 5 PASS; `node infra/tests/issue139_session_actions.cjs`: 7 PASS.
- `node infra/browser/issue139_time_control.cjs`: `en-US` e `it-IT` PASS con Chromium reale.
- `node infra/tests/issue139_fiscal_outcome.cjs`: 4 stati fiscali simulati PASS.
- `node --check` sui JS modificati e sul browser runner, `compileall` sui moduli Python modificati, `git diff --check`: PASS.
- Il CSS candidato è stato testato in Chromium senza scrivere al runtime. **I test W5 delle 128 combinazioni e 38 controlli sintetici sul candidato non sono stati eseguiti:** richiedono prima installazione autorizzata, preflight, checkpoint e rollback.

## Gate operativo ancora necessario

La #139 non autorizza deploy, migrazione, riavvii né modifica dei dati Owner. Prima della richiesta di gate: chiudere le correzioni source ancora pertinenti, preparare un unico executor con candidate SHA, confronto Compose/immagini, fingerprint prima/dopo, test live e rollback. La correzione socket.io richiede applicare l'alias di rete versionato al solo frontend; non è stata applicata. La PR rimane DRAFT e nessuna Owner acceptance è dichiarata.
