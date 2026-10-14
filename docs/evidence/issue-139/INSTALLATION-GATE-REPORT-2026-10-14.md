# #139 — INSTALLATION_GATE_REPORT — 14/10/2026

**Esito aggiornato: EXECUTOR_REPAIR_PASS / RESTORE_REHEARSAL_PASS; installazione DEV non ancora avviata.** La successiva decisione Owner nella issue #139 autorizza una sola installazione immediata dopo i gate tecnici, con finestra UTC ricavata dall’ora effettiva di avvio. La PR #140 resta DRAFT. Questo rapporto non dichiara W5 PASS, `READY_FOR_OWNER_VISUAL_UAT` o accettazione Owner.

## Candidato e baseline verificati

- Sorgente applicativo esatto: `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f` sulla linea PR #140, discendente dall'applicazione installata `83f8f4f97b74e25e73710b6fc3667be0ae473fce`; #78/#128 non è antenato. Il delta applicativo è di 57 file aggiunti/modificati, senza cancellazioni. I commit successivi di questa PR aggiungono soltanto executor, test e questo rapporto: il gate rifiuta variazioni ulteriori al codice applicativo.
- Unico DEV: progetto `centrochange-dev`, nove servizi attivi, sei immagini applicative `sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af`, un Site `centrochange.local`, Frappe/ERPNext 16.50.0. Impronta Owner `e9dc4980b849362b77e394d6e9c2baf7cc33d413097bc41d8156dae8ed4128f3`; `Communication` `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`.
- Hash normalizzati di schema/config `a6e45ecfb3ac9bf08f5d51d1123cb928de828580df2bf7b21e3fe3c865c89375` / `6db58e4d24377f9ebf2aa0c35c0e22633c1e44aa262521250ae72cc4c76f1eb2`; permessi effettivi `97af394ec1d9b4fe18b551282c2ecec40b5b70558e0d4968dfadf341ec66b52c`. Questi valori entrano nel gate di rollback.
- Sei hook guard/lingua presenti una sola volta, #79 CSS originale con hash `f3ab9d5ddf9f15e63b576a5656331169067af6d722cdea6d79b8c5ca644fe27d`. Cache `assets_json` in stato `MATCH` con file presenti: **non è prevista una seconda invalidazione CSS** se il controllo resta verde. Due Branch sintetici A/B esistenti; `cc_operational` non è ancora installato.
- Telemetria al dry-run: disco Docker libero circa 52,9 GiB; PSI memoria full avg10 0,0%, I/O full avg10 0,0%; contatore host OOM 22, usato come baseline e da verificare invariato. Il gate richiede almeno 8 GiB di riserva disco e 3 GiB `MemAvailable`; non cambia soglie, protezioni o risorse.

## Executor versionato

`infra/issue139_install_gate.py` — **SHA-256 `e44be980328860fdaf250032e54219f3c6c0dba1380a7c34a9c67d27ba4b5970`**. L'override `infra/compose.issue139_candidate.yaml` — SHA-256 `1bbef44f4bab86e014bd805be1001870558c4066515037218054f61aa1a5d4ac` — cambia soltanto l'immagine dei sei servizi applicativi e l'alias `centrochange.local` sulla rete privata del frontend. Nessun cambio DB/Redis/volumi/porte/limiti/permessi Docker. Le dipendenze eseguibili del gate hanno SHA pinati nello script. `--dry-run` è predefinito nel piano di verifica; `--execute` richiede un file privato con candidato, hash executor e finestra Owner esatti. Un secondo tentativo incontra il tag candidato/override già presenti e viene rifiutato.

Sequenza dopo il gate Owner: preflight read-only → checkpoint env/Compose/Site config e tag delle sei immagini → build derivata dall'immagine verificata con soli 57 file del commit applicativo → secondo preflight → fermo controllato di frontend, websocket, worker e scheduler (backend isolato resta disponibile al solo executor) → backup nativo completo di DB, file pubblici/privati e config, cifrato AES-256/GPG e verificato in vault privato → selezione persistente dell'override → migrazione supportata `bench --site centrochange.local migrate` → attivazione di A tramite `set_operational` con audit, motivo e gate temporaneo → revoca dell'allowlist temporanea → riavvio backend e cinque servizi applicativi → verifica asset, DNS realtime, nove servizi, sorgenti, hook, permessi e dati → W5.

Non viene eseguito `bench build`: il delta UI di #139 usa file `public/` serviti dal link dell'app nel nuovo container; il manifest dei bundle upstream rimane quello verificato. Il postcheck confronta hash dei file pubblici serviti e mapping cache/manifest. Qualsiasi divergenza ferma l'installazione e avvia il rollback.

### Transizione sedi senza finestra di accesso errata

`Branch.cc_operational` viene creato con default 0. Durante la migrazione il frontend e i job sono fermi. L'executor **verifica che sia A sia B siano inizialmente inattive**, configura soltanto A nella allowlist del Site, usa la funzione server-side `set_operational(A, 1, motivo)` in sessione tecnica `Administrator`, registra `CENTER_OPERATIONAL_STATE` con prima 0 → dopo 1, quindi azzera l'allowlist e verifica A=1/B=0 e un solo audit coerente **prima** di riaprire traffico. L'attore tecnico è esplicito; non si impersona il demo manager. Il test offline copre l'attivazione della prima sede anche quando nessun'altra è attiva, replay, motivo, ruolo e divieto di disattivare l'ultima sede. Nessun dato Centro B viene eliminato.

### Recupero

Al primo errore dopo il fermo, l'executor interrompe W5, ferma i sei servizi applicativi, ripristina env/Compose/immagini e, se la migrazione è iniziata, il DB e i file dal backup nativo cifrato; ripristina il Site config originale, poi riapre i servizi. Verifica immagini, HTTP, sei hook, fingerprint Owner/Communication, schema/config e permessi. Se il processo si interrompe prima del rollback, `--recover --checkpoint-dir <directory privata>` usa il medesimo gate Owner durante l'ora di recupero e non installa nuovamente il candidato. I report raw, backup e screenshot rimangono in directory private `0700`, fuori Git. Il report pubblico contiene solo impronte, conteggi ed esiti.

## Verifiche eseguite senza toccare il DEV

- `sudo -n python3 -I infra/issue139_install_gate.py --dry-run`: **PASS**; nove servizi, due sedi, 57 file delta, origine immagini, sei hook, hash #79, cache CSS, Site, fingerprint dati/schema/permessi e diff Compose verificati in sola lettura.
- `python3 -B -m unittest discover -s infra/tests -p 'test_*.py' -q`: **45 PASS** (inclusi gate Owner, delta Compose, append/ripristino env, sequenza rollback DB prima del frontend, attivazione della prima sede inattiva). `node --check` e AST Python: PASS. `git diff --check`: PASS.
- Rehearsal isolato su file **esclusivamente sintetico**: backup cifrato GPG → decifrato → SHA identico, 5000 byte; PASS. Il mock della sequenza di recovery dimostra una sola chiamata al ripristino DB prima della riapertura frontend. Nessun Site o database clonato sul server.
- **Stato storico al primo gate:** il restore dell'esatto Site non era ancora provato. La rehearsal completa dell'executor corretto è documentata nell'addendum e supera questo limite.

## Piano W5 dopo autorizzazione

1. Il runner #137 ripete almeno **128 combinazioni** di route per sette account (`m/s/a/b/c/f/t`) su 1440×900 e 390×844, con screenshot privati, errori JS, CSS/asset MIME/HTTP, API, realtime, overflow, badge tagliati, sidebar e richieste mutative inattese. Nessuna route è PASS per il solo HTTP 200.
2. Il runner nativo apre **11 liste e 11 prime schede** su entrambi i viewport; l'Administrator verifica il Desk tecnico e Guest deve ricevere 401/403 sull'API Patient. Verificare a mano i difetti visuali non completamente codificabili nella suite, confrontando gli screenshot Owner #136.
3. `infra/issue137_safe_security_run.py` esegue i **38 controlli sintetici** con fixture e cleanup esatto, confrontando fingerprint Owner/Communication prima/dopo. Controlli cross-professional, cross-center, URL/API diretti, note riservate, audit e ruoli restano server-side. Nessun provider fiscale reale.
4. Un FAIL significativo su asset, realtime, permessi, dati, migrazione o ruolo provoca **un solo rollback**. Difetti grafici non critici vanno riportati con evidenza; la suite non deve trasformare FAIL in PASS. Dopo un rollback, nessun retry automatico.

## Decisione Owner aggiornata

La decisione successiva nella issue #139 autorizza **una sola installazione controllata immediata** sul DEV dopo PASS di isolamento, restore executor e preflight. Il gate privato usa l'ora UTC effettiva di avvio, massimo 4 ore operative più 1 ora di recupero. Nessun merge, produzione, GOAL-03 o Owner visual PASS implicito.

## Addendum: vero percorso executor ripristinato in clone isolato

L'executor corregge i due `chown` a `frappe:root` e verifica prima di ogni copia l'identità Unix dell'immagine pinned: UID 1000, GID 0, gruppo `root` presente e gruppo `frappe` assente. `infra/issue139_restore_guard.py` riscrive e valida anche le destinazioni `container:path`, non solo gli argomenti `container`; rifiuta altri servizi DEV, target inattesi e comandi Docker fuori dallo scope. Tre test positivi/negativi nuovi PASS.

La nuova rehearsal usa il backup nativo completo e cifrato del Site sintetico, catturato nella prova precedente e ancora identico agli attuali fingerprint del DEV. Il command trace fail-closed ha verificato **24 comandi** di `restore_backup()` prima della creazione del clone; nessuno indirizza `centrochange-dev-*`. La stessa guard ha protetto l'esecuzione effettiva di `restore_backup()` nel clone con rete Docker interna, volumi propri e nessuna porta pubblica. Risultato `RESTORE_REHEARSAL_PASS`: DB, file pubblici/privati, configurazione, schema, ruoli, permessi, sei hook e due sedi corrispondono al Site sorgente; HTTP 200 e integrità invariata dopo il riavvio del clone. Tutti i container, volumi e network della rehearsal sono stati rimossi. Il DEV non è stato riavviato né migrato. Evidenze raw private: `~/.local/state/centrochange-single/issue139-restore-rehearsal/cc139-restore-20261014180948/`.

Dopo la rehearsal: **50 test Python offline PASS**, `git diff --check` PASS, dry-run executor PASS; nove servizi, cache CSS, sei hook e fingerprint Owner/Communication invariati. La limitazione precedente sul restore non provato è quindi superata per l'executor corretto. W5 sul candidato resta da eseguire dopo l'installazione.

L'Owner ha autorizzato il deploy condizionato immediato nella issue #139; la sezione precedente che chiedeva una finestra calendario separata è superata da tale decisione. Il file gate privato deve essere creato con ora UTC effettiva di avvio, durata massima 4h operative + 1h recupero e SHA-256 executor sopra indicato.
