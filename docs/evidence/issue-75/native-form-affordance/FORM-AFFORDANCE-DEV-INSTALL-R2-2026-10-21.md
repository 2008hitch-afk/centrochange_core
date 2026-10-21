# PR #146 — secondo aggiornamento DEV autorizzato

**Esito: DEV installato con verifiche essenziali PASS; login Direzione rinviato.** Nessun rollback e nessun secondo tentativo in questa esecuzione. La PR resta DRAFT.

## Identità e controllo

- Source applicativo immutato: `1f88207c6a71c4bf0252b912fe83313337cab16f`.
- Executor corretto: SHA-256 `96d478260c549e3635ed1dba8878468c21f8500648dd203ad4d042fa98f0c7db`.
- Overlay: SHA-256 `96ea961b9dc16dc94807bf22e29d46368b881341b59244117fd9d53514dd9bb5`.
- Immagine nuova effettivamente servita dai sei servizi applicativi: `sha256:6d6f9d2e65d0b16974e6b04aeaaf6d1210f071448ace5276689ebc9652bc2f7b` (`centrochange-single:issue75-form-affordance-r2`). Tre servizi tecnici DB/Redis conservati.
- Baseline verificata prima: source `e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec`, image `sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e`, 9/9 servizi, due centri, fingerprint dati `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`.
- Nuovo gate privato separato dal tentativo precedente: apertura UTC `2026-10-21T09:34:05Z`, scadenza operativa `13:34:05Z`, recupero `14:34:05Z`. `DRY_RUN_PASS` prima dell'avvio.

## Correzione del gate browser

La fixture privata del 12/10 contiene una password Direzione precedente al reset Owner. Solo quel login è stato rinviato al collaudo successivo. Il nuovo runner read-only ha mantenuto gli altri sette profili, compreso Guest: **27/27 controlli critici PASS e 15/15 controlli funzionali PASS** sulla baseline prima del deploy; il medesimo runner ha superato il gate dopo l'installazione. Il wrapper rifiuta un controllo critico assente o fallito. Administrator tecnico: PASS separato. Nessuna password, ruolo, policy applicativa o dato è stato modificato per superare il test. I test mutativi contabili e i 38 controlli sintetici preesistenti rimangono esplicitamente `BLOCKED` nel report dell'executor, non vengono presentati come PASS.

## Installazione e prove live

1. Checkpoint configurazione/immagini rollback creato; backup cifrato nativo di database, file pubblici, file privati e configurazione creato, decifrato e verificato con SHA-256. Materiale privato conservato fuori Git.
2. Build esatta del delta applicativo di tre file, controllo del template Nginx come utente runtime, attivazione dei sei servizi. Nessuna migrazione o modifica schema; Centro A attivo e Centro B inattivo conservati.
3. Asset: 3/3 file applicativi diretti verificati, 69 mapping del manifest. CSS consegnato via HTTP dal frontend: SHA-256 `607617228542c80e52ad461215bb848927db6ab41c70635ea0ac826c129e64f0`, uguale al sorgente e al file nel container.
4. Proxy realtime e Origins verificati dall'executor. HTTP `/login`: 200. Servizi: **9/9 attivi**.
5. Fingerprint dati Owner/Communication identiche a prima; schema, permessi e sei hook di sicurezza verificati dall'executor. Nessuna fixture persistente creata dalla prova browser read-only.
6. Chromium sul DEV servito, senza regole CSS di anteprima: Paziente e Sales Invoice, List/Form, desktop 1440 e mobile 390: **8/8 PASS**. Paziente: 10 campi editabili e zero bordi mancanti a entrambe le larghezze. Fattura Finance: 19 controlli read-only per larghezza; nessun PASS di modifica contabile dichiarato. Icone sovradimensionate: 0; overflow orizzontale: 0.
7. Agenda in sessione Segreteria, desktop/mobile: sette colonne giorno, due righe professionista, nessun overflow del documento. Nessuna modifica a griglia, flussi o codice Agenda.

Il primo comando browser post-installazione con CSS vuoto è stato `BLOCKED` dal runner Playwright perché `addStyleTag` richiede contenuto non vuoto; non era un difetto dell'applicazione. La ripetizione con un commento CSS senza regole ha prodotto gli 8/8 PASS sopra. Nessun secondo deploy è stato eseguito.

## Evidenze e limite

Report privato dell'executor: `~/.local/state/centrochange-single/issue75-form-affordance-install-runs/20261021T093417Z-1090583/report.json`. Screenshot e risultati Chromium privati: `~/.local/state/centrochange-single/browser-evidence/issue75-live-r2-noop/`. Non pubblicare fixture, segreti, backup o report grezzi.

La nuova grafica è pronta per la **verifica visiva Owner**. Restano da completare il login e il percorso Direzione con la credenziale aggiornata, e il giudizio visivo Owner sulle restanti Form. L'installazione tecnica non costituisce accettazione GOAL-02 o cliente.
