# CENTROCHANGE-MVP-DEV-FIRST-FINAL-STATUS — 19 ottobre 2026

## Stato operativo e perimetro

**DEV aggiornato e accessibile, con lacune funzionali residue.** L'unico aggiornamento autorizzato in questo incarico ha installato il sorgente applicativo `3429f7d292c8c5961a119a6e97dccb02e0a86eec` sui sei servizi applicativi del progetto `centrochange-dev`. Immagine effettivamente servita: `sha256:65b73c46610f086a1bfe156b17072e007cfc3cfa00501a3c6c2a64d3ef7bccf4`. I nove servizi sono attivi; database e Redis sono healthy. Nessuna seconda installazione o rollback è stata eseguita. L'executor di questa installazione è fissato dal commit locale `26165109f9c8ab0fec8fa91acf13f9b883083782`, SHA-256 `f07a8c2702440661c5239a97f9e73f9fda42ce7a7b53f8d9e3dbbcab62731db8`.

Prima dell'attivazione: checkpoint, backup cifrato verificato, controllo di recuperabilità, nove servizi, sei hook, permessi e impronta dati PASS. Rapporto privato: `issue139-install-runs/20261019T144310Z-3188271/report.json` sotto `/home/empv26/.local/state/centrochange-single/`. Il rapporto conferma `DEV_UPDATED_WITH_GAPS`, essenziali PASS e nessun rollback. L'immagine conserva la precedente correzione #79. La correzione locale successiva delle intestazioni contabili e della vista XML **non è installata**.

## Risultato delle 46 capability

**41/46 PASS documentati:** 40 PASS ereditati dall'audit funzionale, non rieseguiti indiscriminatamente, più CC-CAP-047 passato sul DEV attuale. Delle sei lacune originali: **1 PASS, 4 PARTIAL, 1 BLOCKED**. La matrice aggiornata è `capability-matrix-completion.csv`. I 40 PASS storici non equivalgono a 40 nuovi collaudi live in questo incarico.

| Capability | Stato | Prova sul DEV installato | Limite concreto |
|---|---|---|---|
| CC-CAP-029 — italiano/export | PARTIAL | CSV Finanza, Pazienti, Agenda, Professionisti, Libro giornale e Bilancio di verifica scaricati nel browser; autorizzazioni 200/403 coerenti; date europee nei report che hanno una data | GL/TB contengono ancora intestazioni ERPNext inglesi. Correzione locale non distribuita. |
| CC-CAP-042 — carta/POS | BLOCKED | Codice e prove offline presenti; nessuna scrittura contabile nella campagna finale | La precedente collisione MariaDB 1020 e il cleanup del ledger nativo non sono dimostrati sicuri. Pagamento, saldo e replay non sono PASS live. |
| CC-CAP-047 — report contabili | PASS | Chromium Finance e Commercialista: GL 13 righe/15 colonne, TB 6 righe/10 colonne; CSV 200, mobile senza overflow, nessun errore JS; Professionista 403 | Localizzazione delle intestazioni registrata in CC-CAP-029. |
| CC-CAP-050 — suite/fixture | PARTIAL | 95 test offline pregressi PASS; 30 controlli critici read-only PASS; cleanup esatto della fixture allegati PASS | 38 controlli mutativi sicurezza e fixture Finance rimangono non eseguiti in sicurezza. |
| SCOPE-DOC — allegati privati | PARTIAL | Browser API: nuovo XML sintetico, PDF privato, persistenza dopo refresh, download Finance e Commercialista 200, Professionista 403; 7 controlli PASS, cleanup esatto PASS | Il form di allegato sulla fattura non è stato azionato; la vista XML servita non esponeva il form. Fix locale non distribuito. |
| UAT-GLOBAL — ruoli/mobile/salvataggi | PARTIAL | Sette shell e screenshot, 30 controlli read-only, precedenti 128 route/22 List-Form, report contabili desktop/mobile | Salvataggi nuovi per ciascun ruolo e review visiva Owner non sono provati. |

## Diagnosi mirata e correzioni locali

La patch applicativa installata risolve le due regressioni note: Trial Balance passava un centro di costo serializzato JSON e riceveva HTTP 417; ora usa la lista nativa prevista dalla versione ERPNext pinned. `attachments.list_for_document` filtrava su `File.is_remote_file`, proprietà calcolata non presente come colonna SQL; ora usa `is_private=1` e URL locale privato, eliminando HTTP 500 nella lista.

Durante il test allegati, il primo timeout dipendeva dal runner: la vista XML non inseriva `attachmentPanel`, pur essendo il DocType permesso dal servizio. Un PDF sintetico inizialmente malformato ha prodotto `PdfReadError`; il runner ora genera un PDF con xref valido, verificato dal parser `pypdf` pinned. Frappe aggiunge un suffisso al nome del file per garantirne l'unicità: cleanup e asserzioni sono stati corretti per accettare soltanto quel file sotto il documento e il tag esatti. Il test finale è **7/7 PASS** e il cleanup **2 File + 2 CC Audit Event PASS**. La vista XML locale ora riusa il pannello allegati esistente, senza creare un nuovo servizio o permesso.

Le intestazioni effettivamente servite da GL/TB includono `Account`, `Debit`, `Credit`, `Voucher Type`. Il sorgente locale usa ora etichette italiane per le colonne note della versione pinned, lasciando invariati fieldname, valori, API e CSV canonico. I test offline nuovi coprono etichette e riuso del pannello. Sono modifiche versionate locali **non ancora nell'immagine attiva**; non è stato tentato un secondo aggiornamento.

## Evidenze, integrità e limiti

- Chromium reale: `reports-ui.json` (GL/TB desktop e mobile per Finance/Commercialista, screenshot), `exports-readonly.json`, `export-remaining.json`, `attachment-CC-MVP-ATT-92072c1998/report.json`, `attachment-live.json`; tutti sotto `browser-evidence/mvp-devfirst-3429f7d-targeted/` nella directory privata dello stack. Nessun dato o credenziale di test è pubblicato.
- Test offline mirati delle nuove correzioni: `test_mvp_devfirst_remaining.py` **2/2 PASS** e `test_native_report_fiscal_year.py` **2/2 PASS**; sintassi dei quattro runner Chromium e `git diff --check` PASS. I 95 test offline generali erano già PASS al preflight e non sono stati ripetuti senza necessità.
- L'impronta applicativa dopo il cleanup finale coincide con quella prima della prova; i file e gli eventi della fixture sono assenti. Lo scheduler ha creato separatamente un evento `ADMIN_EXCEPTION_DETECTED` per la riconciliazione amministrativa programmata, portando il conteggio audit da 137 a 138. Identità del database, digest Communication e impronta permessi sono invariati; l'impronta applicativa globale comprende l'evento scheduler e quindi differisce dal checkpoint pre-installazione. L'evento schedulato è stato preservato, non attribuito alla fixture.
- La prova POS resta isolatamente `BLOCKED`. Nessuna fattura contabilizzata, Payment Entry o ledger è stata creata da questa campagna. Il precedente errore MariaDB 1020 non è dichiarato risolto.
- I problemi grafici non critici restano separati dai gate essenziali; nessun difetto critico nuovo di sicurezza, integrità o servizi è stato osservato.

Accesso Owner invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@srv2033673`, poi `http://127.0.0.1:8082/app/cc-unified-desk?cc_view=agenda`. Credenziali demo restano nel canale privato esistente, non in Git.

**Esito: DEV-FIRST operativo; MVP 41/46 PASS documentati, 1/6 lacune chiusa.** PR #141 rimane DRAFT; nessun merge, produzione o GOAL-03. Le correzioni locali successive richiederanno un distinto aggiornamento del DEV per essere collaudate live. L'accettazione Owner GOAL-02 non è dichiarata.
