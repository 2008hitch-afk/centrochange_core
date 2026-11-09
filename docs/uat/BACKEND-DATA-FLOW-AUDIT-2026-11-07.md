# Centro Change — Audit backend Frappe, Healthcare, ERPNext (sola lettura)

## Esito definitivo — 09/11/2026

Codex ha eseguito l'audit dopo l'installazione della SHA `6e982a2715dc3aec89b3f7c65e52c3aa995d45a8`: **47 PASS, 0 FAIL**. La correzione orari `9:00`/`09:00` ha eliminato i due falsi negativi precedenti; i 35 appuntamenti e i loro stati corrispondono alla ricetta. I 35 collegamenti economici, i 18 Patient→17 Customer, i 4 professionisti e le 10 ricevute (€392) risultano coerenti. Le autorizzazioni sono state verificate e gli stati contabili e di invio restano vuoti.

La migrazione ha disattivato il job nativo Healthcare che interferiva con `AppointmentMixin.validate`; `centrochange_core.operations.automation.catch_up` resta attivo. I due job falliti l'8–9/11 sono **antecedenti** alla correzione. Il `ConnectionError` del controllo aggiornamenti Frappe dell'8/11 è un evento storico DNS distinto, da seguire solo se ricorrente.

Backup cifrato e restore su clone: **PASS secondo report operatore**. GitHub: CI **3/3 PASS** sulla SHA installata, verificata indipendentemente. Database e produzione non modificati dalla sola attività documentale. **Questo audit è concluso: non eseguire di nuovo se non richiesto e non utilizzare il seeder.** Le istruzioni sottostanti descrivono la procedura originale e non autorizzano un nuovo deploy.

---

**Situazione iniziale, 07/11/2026:** STAGING già popolato da Codex alla SHA installata
\`254af1505dc56ae9123ce64469f856cefabf61d4\`. Non effettuare un altro seed:
\`presentation_seed.apply\` NON deve essere invocato. PR #205 DRAFT, produzione intatta.

**Scopo:** stabilire con **prove del database reale** che il percorso
\`User → Healthcare Practitioner → CC Patient Assignment → Patient → Customer →
Patient Appointment → CC Economic Source Link → CC Operational Receipt →
Report cliente/Report professionisti\`
sia coerente e autorizzato, senza produrre nuovi dati, fatture, incassi,
transazioni fiscali, notifiche o SMS.

## Evidenze, in ordine

1. **Ambiente e componenti (lettura):** nome del sito Frappe, hash/commit
   realmente installato, \`bench version\`, \`bench --site "$SITE" list-apps\`,
   stato del scheduler e dei worker (\`bench doctor\`), presenza Frappe /
   ERPNext / Healthcare / centrochange_core, hooks effettivamente caricati,
   campi nativi ed estesi, log recenti degli errori (solo riepilogo tecnico,
   senza dati personali). Distinguere problemi già noti o storici da errori
   successivi al caricamento.
2. **Audit database senza modifiche:** usare
   \`infra/audit_presentation_backend_readonly.py\` dalla PR #205. È uno script
   **standalone**, non una API web: può essere ottenuto dal repository in una
   cartella temporanea e eseguito in un *bench console* già inizializzato sul
   sito STAGING. **Non serve deploy/merge/installazione del nuovo codice solo per l'audit.**
   Leggere lo script ed eseguire prima il controllo statico:
   \`python3 -m unittest discover -s tests -p test_presentation_backend_audit.py\`.
   Validare con \`python3 -m py_compile infra/audit_presentation_backend_readonly.py\`.
3. **Esecuzione sicura:** individuare il vero container/processo e \`$SITE\`
   da configurazione, senza ipotesi. Copiare **solo** il file audit in \`/tmp\`
   nel contesto dove \`bench console\` è disponibile (ad esempio tramite
   \`git show\` della PR, senza cambiare checkout in uso). Dentro
   \`bench --site "$SITE" console\`, eseguire una singola riga Python:

   \`\`\`python
   exec(compile(open("/tmp/cc-backend-audit-readonly.py", encoding="utf-8").read(), "/tmp/cc-backend-audit-readonly.py", "exec"), {"__name__": "__main__"})
   \`\`\`

   Il controllo rifiuta siti diversi dal \`cc_presentation_site\` configurato,
   utenze non Administrator e siti non sintetici. In caso di errore non
   modificare codice o dati; raccogliere solo tipo di errore ed elemento
   verificato. Non chiedere o divulgare credenziali.
4. **Controlli obbligatori del report JSON:** tutti \`PASS\`, inclusi:
   Frappe hooks, ERPNext Customer/Supplier/Cost Center, utenti professionisti
   abilitati e membership attiva, permessi che impediscono a un professionista
   di leggere pazienti di altri e clienti fiscali, 18 Patient → 17 Customer
   senza duplicati (Laura per Alice e Pietro Caruso), 35 appuntamenti con
   professionista, data, prezzo e durata esatti, 35 fotografie
   \`CC Economic Source Link\` con Customer e Supplier corretti, 10 ricevute
   con allocazioni valide per **392,00 €**, report cliente e professionisti
   conciliati a **39.200 centesimi**; nessun Payment Entry, GL, fattura, coda
   email o transazione fiscale. Controllare modalità pubbliche in sede e
   online senza modificare il catalogo.
5. **Conferma dinamica di flusso:** i test automatici \`presentation-clone\`
   su SHA installata erano **PASS**. Se un problema del database attuale
   richiede riprodurre una modifica, farlo **su clone isolato ripristinato
   dal backup**, non sullo STAGING già popolato. La prova deve coprire nuovo
   Patient → Customer, appuntamento, chiusura, ricevuta, proiezione economica
   e report, oltre a un salvataggio Patient con Customer terzo che non cambia
   i dati del Customer. Non correggere o aggiungere record sullo STAGING
   per far passare i test.
6. **Consegna:** evidenza dell'hash installato, \`bench version\`, app e
   dipendenze, esito hooks/schema, elenco dei check JSON con conteggi,
   segnali diagnostici worker/scheduler, eventuali anomalie con criticità e
   causa, esito prova clone/CI, conferma che lo STAGING è rimasto invariato.
   Nessun elenco di dati clinici, CF, email vere o log contenenti PII.

**Gate:** se un controllo \`FAIL\`, fermarsi e fornire una diagnosi mirata.
Nessun \`migrate\`, \`bench restart\`, \`seed\`, \`apply\`, \`commit\` o
\`set-config\` è autorizzato da questo incarico. Nessun cambiamento in
produzione. Un risultato CI PASS non sostituisce l'esecuzione dell'audit
in sola lettura sui dati veri dello STAGING.
