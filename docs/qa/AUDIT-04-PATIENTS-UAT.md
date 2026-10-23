# AUDIT-04 — Pazienti: oracle di accettazione

**Issue:** #167. **Baseline:** `fa4ea4033e95301c25271d88d7d8c008b035f5c0` (`main`, 23/10/2026). **Ambiente di scrittura:** esclusivamente Site/DB temporanei e isolati. **Stato:** `PASS_ISOLATED_REAL` per gli scenari esercitati nel [rapporto tecnico](AUDIT-04-PATIENTS-TECHNICAL-REVIEW.md); Owner `PENDING`, DEV `NOT_TESTED` per questo candidato.

Le verifiche UI sintetiche sono `PASS_OFFLINE`; soltanto una sessione Frappe/MariaDB isolata può diventare `PASS_ISOLATED_REAL`. I test del DEV condiviso richiedono un gate Owner successivo. Nessun esito è accettazione Owner.

| ID | Azione da provare nell'interfaccia | API/DocType canonici | Ruoli, contesto e negativo obbligatorio |
|---|---|---|---|
| CC-CAP-003/019 | Ricerca nome/cognome/codice, profilo con nome/email, modifica ammessa e persistenza | `workspace.patient_search`, `profiles.patient_detail/patient_save`; Marley `Patient` | M modifica; S/P leggono soltanto paziente autorizzato. Verificare 403 IDOR e stale `expected_version`; Guest/Finance senza contesto negati. Nessuna creazione standalone o Customer fiscale arbitrario (DECISION-063). |
| CC-CAP-004 | Assegna, revoca, riassegna con motivazione; mostra stato e storico | `security.lifecycle.set_assignment/reassign`, `workspace.patient_history`; `CC Patient Assignment`, `CC Audit Event` | M/S in centro operativo. Old practitioner inattivo deve fallire senza nuovo grant; P revocato perde accesso diretto. Verificare CSRF/POST. |
| CC-CAP-005/033/038/039 | Isolamento A/B su lista, scheda, API diretta, note, pacchetti, audit | `require_context`, query/record hooks, `Patient`, `CC Center Membership`, `CC Patient Assignment` | M/S/P, Finance, Accountant e Guest. Due centri operativi *solo nel clone*. Accesso a ID dell'altro centro: 403 e nessun testo riservato in risposta/DOM/export. DECISION-018 consente scoperta di identità per UID esatto nei limiti approvati. |
| CC-CAP-006.c/020 | Sedute cronologiche e timeline selezionabile con attore/motivo/prima-dopo, stato e data italiani | `workspace.patient_history/appointment_events`; `Patient Appointment`, `CC Audit Event`, `CC Settlement` | M/S/P soltanto per record autorizzati. Verificare endpoint con appointment dell'altro centro; storico >100 dichiarato troncato. |
| CC-CAP-017/018 | Nuova nota, rettifica append-only, versione/autore/data; organizzativa distinta da privata | `notes.add_note`, `workspace.patient_history`; `CC Organizational Note`, `CC Private Note` | P assegnato può privata; M/S non ne vedono testo. Verificare diretta REST/list/report/DOM/export, post-revoca e rettifica cross-context negati. |
| CC-CAP-016; CC-ACT-001/003 | Emissione da template, validità, professionista dedicato, saldo; rettifica motivata | `packages.issue/adjust/balance`, `workspace.patient_history`; `CC Package Template`, `CC Patient Package`, `CC Package Ledger` | M/S secondo guard server. Chiave uguale ritentata = un evento; seconda azione intenzionale = nuova chiave/evento. Centro/ruolo/modello non valido negati; saldo non negativo. |
| CC-ACT-002 | Riserva, consumo, rilascio e retry package tramite seduta | `booking.book`, lifecycle seduta, `operations.packages`; `CC Package Ledger`, `Patient Appointment` | Regressione mirata AUDIT-03, nessuna riscrittura Agenda. Verificare atomicità su failure e centro/servizio/professionista. |

**Dipendenze:** DECISION-005/006/011/018/034/063; #74/#79/#134/#135/#136. Centro B storico resta inattivo sul DEV (#135); nel clone sono ammessi solo centri e utenti UAT identificati. La separazione `Patient` operativo / `Customer` fiscale è invariata. DECISION-059 rinvia la correzione retroattiva dell'orario.

**Criteri di chiusura tecnica:** percorso UI completo desktop 1440×900 e mobile 390×844; API positive/negative con sessione e CSRF Frappe; persistenza, replay, rollback e segregazione; screenshot sintetici; fixture e risorse isolate rimosse per ID verificato; CI su SHA esatto; reviewer indipendente senza finding Critical/Important; matrice aggiornata. Senza tutte le prove: `PARTIAL`, non `READY_FOR_OWNER_UAT`.

## Prosecuzione UX-04: criteri indipendenti

| Difetto | Accettazione | Fonte / prova richiesta |
|---|---|---|
| UX-04-01 | Scheda Patient con un solo titolo nominativo, senza chip generico o ID tecnico in testata; campi e azioni autorizzate invariati | Browser Frappe desktop/mobile, `profiles.patient_detail`, accesso diretto negato fuori centro |
| UX-04-02 | Topbar compatta con pulsante ricerca; campo e risultati compaiono solo su richiesta; focus, Escape, tastiera, viewport e filtro A/B funzionano | Browser desktop/mobile, `workspace.patient_search`, Guest e IDOR negati |
| UX-04-03 | Un Patient con nome e cognome reali mostra la stessa identità in lista, ricerca, Agenda, report e scheda. Per `CC-HTTP`/`CC-MVP-POS` senza nome completo: etichetta esplicita con discriminatore stabile, mai un Customer fiscale spacciato per Patient. API e permessi usano sempre ID canonici | Proiezioni `bootstrap`, `patient_search`, `agenda`; test per Patient fuori bootstrap 500, cognome mancante, refresh e due centri |

Questa prosecuzione non riapre gli audit funzionali di Agenda o Finanza e non autorizza mutazioni sul DEV. Prima dell'installazione occorre includere nel candidato il routing Premium primario già attivo sul DEV via PR #169.
