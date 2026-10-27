# Centro Change — REGISTRO OPERATIVO VIGENTE / instradamento GOAL e AUDIT

**Fotografia iniziale:** 26/10/2026. **Scopo:** evitare che un agente, ChatGPT o Codex riparta dalla roadmap MVP storica oppure confonda i numeri degli AUDIT funzionali con quelli dei macro-GOAL di consegna. Questo è l'**indice di ingresso alla fase corrente**; NON sostituisce prove, decisioni e gate nelle Issue collegate.

> **ISTRUZIONE OBBLIGATORIA ALLA RIPRESA:** PRIMA di proporre un GOAL, rispondere a «dove siamo?», aggiornare una matrice o inviare AGY ad agire, controllare **live** le Issue e le PR qui elencate. Questo file è una fotografia versionata, non uno stato in tempo reale. Il codice e le attestazioni dinamiche sono su GitHub. In assenza di nuova verifica non dichiarare PASS, deploy, merge o accettazione.

## FASE OPERATIVA VIGENTE — 27/10/2026: PREPARAZIONE PRE-MERGE IN CORSO, NON MERGE

L'Owner, dopo `OWNER_ACCEPTED_SCOPED_AUDIT05` #171 e `OWNER_ACCEPTED_SCOPED_CORE173` #173, ha risposto **«Ok procediamo» alla sola PREPARAZIONE del consolidamento**, con merge da autorizzare **separatamente**. [**Mandato unico AGY e stop gate Issue #173 #6440788497**](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440788497); [tracker generale #156 aggiornato](https://github.com/2008hitch-afk/centrochange_core/issues/156#issuecomment-6440805094). Non confondere `OWNER_ACCEPTED` con `MERGED` o un vecchio macro-GOAL.

**Prontezza GitHub verificata:** #172 `a3e41a10287639a7c200992e45c3173b8ea33b46` base `main`, 55 commit/164 file cumulativi; #175 `b498ea5689255a95f64c20275fefd32957e4818f` figlia di #172, 5 commit/41 file; #174 documentale `46db1ffdde05e61bd7b6892bd5b18cce6dbec730` figlia **anch'essa di #172** (non di #175), 46 commit/17 file. Tutte `OPEN/DRAFT/UNMERGED`, mergeable allo snapshot corrente **ma non verificate nell'ordine di integrazione**. **Sei immagini prova** sotto `docs/evidence/issue-173/dev-*.png` si sovrappongono fra #175 e #174; controllare hash/bytes e matrice 110/18 prima di proporre merge. La PR #172 raccoglie più aree precedenti, quindi prima verificare esattamente il delta verso main.

**Blocco di governance:** review GitHub PR #172 = 0; review formale PR #175 = `COMMENTED` dall'account **autore** `2008hitch-afk` sotto dicitura «QA/Security persona» (quindi indipendenza NON attestata); review PR #174 = 0. Il reviewer dev'essere **effettivamente indipendente dall'implementatore, identificabile e attribuibile**, non una persona simulata. Se non disponibile, `BLOCKED_INDEPENDENT_REVIEW` e richiedere un unico sblocco. Codex può effettuare analisi git diff / CI / review e simulare la sequenza **#172→#175→#174** solo su clone o branch locale isolato senza pubblicazione. **Nessun merge, rebase/force-push, cambio HEAD accettata, DRAFT→READY, deploy DEV/produzione, pulizia dati storici o avvio AUDIT-06 autorizzati.** Successivo stato `MERGE_GATE_READY` o `BLOCKED_WITH_EVIDENCE`; poi decisione Owner separata e specifica.


---

## DECISIONE OWNER VIGENTE — 27/10/2026: `OWNER_ACCEPTED_SCOPED_CORE173` / GATE MERGE SEPARATO

**ACCETTAZIONE FUNZIONALE FORMALE:** Owner ha risposto **«confermo»** alla richiesta esplicita di accettare CORE #173 «Chiudi la mia giornata» e recupero arretrati sulla versione DEV `b498ea5689255a95f64c20275fefd32957e4818f`, **senza autorizzare merge**. [Issue #173 decisione canonica #6440597230](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440597230); [PR #175 notifica #6440617282](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6440617282). Sono PASS Owner chiusura/recupero 14/10, Report/CSV, avviso economico, POS, calendario condiviso e leggibilità. Delta fingerprint `20aa6...` → `a5d098...` ricostruito e riconciliato secondo [rapporto AGY #6439335841](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6439335841): blocco scheduler Auto Locked ore 07 del 27/10 su una seduta Pending 26/10 più un audit append-only, nessuna perdita dichiarata; fonte codice Frappe coerente. ChatGPT non ha eseguito accesso VPS o letto i backup.

**STATO ATTUALE:** `AUDIT-05 #171 OWNER_ACCEPTED_SCOPED` e `CORE #173 OWNER_ACCEPTED_SCOPED_CORE173` **funzionalmente accettati**; **PR #172/#175/#174 OPEN/DRAFT/UNMERGED**; Issue #173 lasciata OPEN solo per preparazione e autorizzazione specifica del consolidamento. Nessuna produzione, nessun nuovo deploy, nessun GOAL successivo autorizzato. Il prossimo lavoro possibile è **gate consolidamento GitHub** (non è avvio AUDIT-06): verificare diff/CI alle HEAD, review di persona effettivamente indipendente, compatibilità branch dipendenti #172 → #175 e documentale #174, ordine merge, rollback/asset/documentazione e decisione Owner successiva. **La review COMMENTED della PR #175 è pubblicata dall'account GitHub `2008hitch-afk` con etichetta «QA/Security persona»: l'effettiva indipendenza dall'implementatore non è ancora provata.** Non falsificare review, non inferire APPROVED o merge autorizzato.

**Matrice CSV del checkpoint aggiornata SOLO per 4 requisiti pertinenti:** `CC-CAP-014`, `CC-CAP-022`, `CC-CAP-024`, `CC-ACT-004` ora `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` con perimetro note di prova, `Stato` tecnico invariato per tutti. Conteggi tecnici 12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED = 110; Owner 92 PENDING / 16 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV. **Accettazione di CORE #173 ≠ completamento globale di quei 4 requisiti né dei 110 requisiti.** La fonte primaria dello stato è sempre Issue/PR live; sezioni datate precedenti qui sotto sono archivi cronologici.

---

## CHECKPOINT DI GOVERNO POST-RICONCILIAZIONE — 27/10/2026

**L'Owner non ha ancora accettato formalmente la CORE #173.** Tutto il walkthrough visivo è PASS, delta fingerprint DB riconciliato secondo confronto AGY fra backup e runtime (1 appuntamento `Pending → Auto Locked` alle 07:00 più 1 audit append-only) e sorgente scheduler GitHub coerente. L'insieme è `READY_FOR_OWNER_FUNCTIONAL_ACCEPTANCE`, non `OWNER_ACCEPTED`, `MERGED` né `PRODUCTION`. [Audit aggiornato Issue #173 #6440523846](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440523846).

**Review PR #175:** ora esiste una **review formale COMMENTED** su SHA `b498ea5`, autore GitHub `2008hitch-afk`, corpo «Code & Security Review Auditor (QA / Security persona)» PASS. Il solo titolo/ruolo non prova l'indipendenza reale dall'implementatore: **non chiamarla indipendentemente verificata**. Prima di un eventuale merge dimostrare revisore distinto tramite evidenza attribuibile (o decisione eccezione esplicita Owner), senza falsificare approvazioni. Non ripetere i test Owner né attivare altri GOAL.

---

## RICONCILIAZIONE TECNICA IN SOLA LETTURA E REVISIONE PR #175 COMPLETATE — 27/10/2026: STATO READY_FOR_OWNER_ACCEPTANCE

A seguito del walkthrough visivo Owner con PASS completo su calendario (`UAT-173-UX-DATE-POPOVER-CLIPPED`) e nota economica 13px (`UAT-173-UX-ECONOMIC-NOTE-READABILITY`) registrati nei commenti [#6438865876](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438865876) e [#6439127526](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6439127526), è stata eseguita la riconciliazione tecnica in sola lettura richiesta:
1. **Delta Fingerprint DB (da `20aa6b31...` a `a5d098d6...`) spiegato al 100% matematicamente:**
   - 29 su 31 DocType tracciati sono risultati **identici al bit**.
   - Nessun dato storico o scrittura Owner (inclusi appuntamento 14/10 `HLC-APP-2026-00024` e settlement `t6muud5trq`) è stato modificato o corrotto.
   - Il delta è causato **esclusivamente** dall'esecuzione programmata alle **ore 07:00:04 Europe/Rome del 27/10/2026** del job di routine Frappe `centrochange_core.operations.automation.catch_up` con actor `cc-automation-service@example.invalid`:
     * Aggiornati 4 campi su `HLC-APP-2026-00038` (seduta del 26/10 ore 09:00 rimasta non chiusa dal professionista): `modified`, `modified_by`, `cc_closure_state` (`Pending` -> `Auto Locked`) e `cc_locked_at`.
     * Aggiunto 1 record in `tabCC Audit Event`: `qnh289qeqa` (`SESSION_AUTO_LOCKED`, motivo: `07:00 local cutoff catch-up`).
   - Ripristinando in sola lettura in-memory questi due elementi sul dataset live, il fingerprint ricalcolato coincide al 100.0% con la baseline `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5`.
2. **Revisione Indipendente PR #175 documentata e rintracciabile:**
   - Attestazione dettagliata pubblicata come review formale GitHub (`pullrequestreview-5665460425`), commento PR #175 [#6438520810](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438520810) e report di audit del repository (`independent_review_core173_b498ea5.md`), esito PASS 0 Critical / 0 Important.
3. **Stato del Gate:** **`READY_FOR_OWNER_ACCEPTANCE`**.
   - Nessun comando mutativo su DEV. Nessun merge (PR #175, #174 e #172 in DRAFT). Nessuna produzione e nessun avvio di AUDIT-06.

---

## OWNER UAT CORE #173 — 27/10/2026: TUTTI I FIX VISIVI PASS, RESTA SOLO CONCILIAZIONE DATI / REVIEW

**Nuovo screenshot Owner:** `Non svolta` selezionato sulla seduta del 26/10, testo economico leggibile e stato «Da definire» evidenziato → `UAT-173-UX-ECONOMIC-NOTE-READABILITY = PASS_OWNER_VISUAL`. Lo screenshot Owner precedente mostra calendario ottobre completamente contenuto → `UAT-173-UX-DATE-POPOVER-CLIPPED = PASS_OWNER_VISUAL_DESKTOP`. I 2 fix precedenti «frase non addebitata» e «Carta POS leggibile» hanno già PASS Owner. **Il walkthrough visivo #173 è concluso; non richiedere altri test Owner né nuovi deploy.** Fonte [Issue #173 commento #6439127526](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6439127526).

**Residuo di gate tecnico, senza mutazioni:** riconciliare `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5` (fingerprint dopo precedente UAT/swap) con `a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d` (pre/post nuovo swap), identificando in sola lettura causa, schema fingerprint e righe/campi/attori/timestamp, ipotesi scheduler Auto Locked ore 07:00 NON verificata. Verificare anche l'identità e indipendenza del reviewer dichiarato sulla PR, dove non risultano review formali. Nessuna accettazione funzionale generale, merge, produzione o AUDIT-06 senza prova e successiva decisione Owner. Stato: `CORE173_UX_OWNER_VISUAL_PASS / TECHNICAL_RECONCILIATION_PENDING`, PR #175 DRAFT `b498ea5`.

---

## OWNER RECHECK `b498ea5` — 27/10/2026: CALENDARIO DESKTOP PASS, NOTA ECONOMICA ANCORA DA MOSTRARE

**Prove Owner:** due screenshot della modale `Chiudi la mia giornata` su DEV con immagine installata secondo AGY `b498ea5`. **Calendario 27/10:** mese, anno, griglia e comandi totalmente entro i bordi della modale, nessun taglio sinistro → `PASS_OWNER_VISUAL_CALENDAR_DESKTOP`. **Giornata 26/10:** seduta ore 09:00 e pulsanti `Svolta / Non svolta` visibili, ma **`Non svolta` non selezionato** → la nuova informativa economica non è visibile, dunque `PENDING_OWNER_VISUAL_ECONOMIC_NOTE_READABILITY`. Prossimo unico step Owner: cliccare solo `Non svolta` su 26/10, valutare font/contrasto del messaggio, fare screenshot, chiudere senza salvare. [Risultato documentato su Issue #173 #6438865876](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438865876).

**Resta aperta, separatamente, la riconciliazione del fingerprint DEV precedente `20aa6b31...` vs pre-swap `a5d098d6...` ([Issue #173 #6438773327](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438773327)).** Il test grafico non costituisce prova d'integrità DB. `CORE173_OWNER_ACCEPTANCE_PENDING`, PR #172/#174/#175 DRAFT/UNMERGED, nessun merge, produzione o AUDIT-06 autorizzato.

---

## DEV AGGIORNATO CON CANDIDATA b498ea5 — 27/10/2026: CANDIDATO b498ea5 INSTALLATO CON SUCCESSO SU DEV (`DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_B498EA5`)

Eseguito il mandato Owner di gate condizionato [Issue #173 commento #6438344580](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438344580).
- **Preflight 100% PASS:** SHA `b498ea5689255a95f64c20275fefd32957e4818f`, Image ID `sha256:6ba1b26f05e04174171ec221fc91987e1c2405b732bda6d6176cb332bcdb0e43` verificata sul runtime; CI Premerge Run `40479774074` SUCCESS; Independent Review attestata e pubblicata su PR #175 (commento #6438520810) con esito PASS 0 Crit / 0 Imp; test backend 120 PASS / 1 SKIP; test frontend e clone isolato 7/7 ALL_PASS; nuovo backup cifrato GPG AES-256 (`cc-dev-backup-d0_68wqk`, `PASS_RESTORE_VERIFIED`); baseline DB pre-swap `a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d` (1 audit event generato alle 07:00:04 dalla cron di routine per auto-lock sessione 26/10; salvataggio Owner 14/10 intatto); rollback rapido a `500c882` pronto.
- **Rollout eseguito sui soli 6 servizi applicativi:** `backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler` ricreati con `cc173-day-closure:b498ea5`. Nessuna alterazione a DB, Redis, schema o credenziali.
- **Collaudo tecnico reale PASS:** 21/21 controlli API multiruolo PASS; browser Chromium reale su DEV attesta confinamento geometrico del popover calendario nella modale (Desktop +26px dentro, Mobile +18px dentro, clipping 0px), Escape/outside click funzionanti, nota economica 13px colore `#334155` contrasto 9.90:1 WCAG AAA. Fingerprint DB post-swap identico al bit (`a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d`, zero mutazioni).
- **Stato:** **`DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_B498EA5`**. L'Owner deve verificare **esclusivamente** il calendario non tagliato e la leggibilità della nota nella modale, senza confermare. Nessun merge, nessuna produzione, nessun nuovo GOAL.

---

## REPORT AGY SUCCESSIVO AL GATE — 27/10/2026: `b498ea5` INSTALLATO SU DEV SECONDO AGY, OWNER VISUAL UAT PENDING

**Fonte:** [report AGY #6438707905](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438707905) / [PR #175 #6438709647](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438709647). L'operatore dichiara swap riuscito su sei servizi `centrochange-dev` alla immagine `cc173-day-closure:b498ea5` (ID `sha256:6ba1b26f05e04174171ec221fc91987e1c2405b732bda6d6176cb332bcdb0e43`) e UAT tecnico 21/21, calendario dentro modale desktop/mobile, nota economica contrasto elevato, backup nuovo e restore isolato, DB/Redis non toccati. CI `40479774074` due job SUCCESS verificata GitHub; PR #172/#174/#175 DRAFT/UNMERGED. **Nessuna ispezione diretta ChatGPT del VPS.** `CORE173_OWNER_ACCEPTANCE_PENDING`. Owner deve vedere solo calendario e leggibilità nota, con modale chiusa senza scritture.

**ATTENZIONE INTEGRITÀ DATI — verifica READ-ONLY aperta** ([Issue #173 #6438773327](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438773327)): fingerprint baseline canonica precedentemente attestata `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5`; preflight nuovo `a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d`, invariato **solo durante** lo swap `b498ea5`. Origine e autorizzazione del delta non ancora riconciliate nel report: **non** certificare integrità globale, GOAL accettato, merge o produzione prima della riconciliazione. Nessun reset/rollback o mutazione per «riparare» la prova. Reviewer indipendente dichiarato in [commento PR #6438520810](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438520810), ma reviewer con identità distinta dall'implementatore da attestare prima del merge (zero reviews formali GitHub). AUDIT-06 non autorizzato.

---

## ULTIMA DECISIONE OWNER — 27/10/2026: `b498ea5` AUTORIZZATO AL SOLO GATE DEV CONDIZIONATO

**Nuovo stato autorizzativo prevalente:** [Issue #173 #6438344580](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438344580), in seguito a risposta Owner «AUTORIZZO». **Candidata unica** commit `b498ea5689255a95f64c20275fefd32957e4818f`, immagine `cc173-day-closure:b498ea5` ID `sha256:6ba1b26f05e04174171ec221fc91987e1c2405b732bda6d6176cb332bcdb0e43`; sei soli servizi `centrochange-dev`. Baseline DEV precedente `500c882` da preservare per rollback. Questo **non attesta nuova installazione già effettuata**. Preflight bloccante: clean commit/source parity/CI `40479774074` SUCCESS, revisione indipendente provata sulla SHA (non basta la frase PASS), test veri, backup cifrato nuovo e restore isolato, fingerprint canonico live atteso `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5`, rollback; su FAIL **STOP DEV invariato**. Solo if PASS fare swap 6 servizi + UAT browser desktop/mobile, DateInput in altre schermate, leggibilità e ACL/CSV, fingerprint invariato. **Owner verifica alla fine solo calendario e nota economica**. Niente merge/produzione/DB storico/schema/ruoli/credenziali/altro AUDIT/accettazione implicita. [PR #175 gate richiamato qui](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438352865).

---

## OWNER UAT COMPLETATO SUI DUE FIX — 27/10/2026: PASS AVVISO ECONOMICO E METODO POS; UX FINITURA #173 APERTA

Nuovo screenshot Owner sulla data 26/10, seduta ore 09:00 con `Non svolta` **selezionata ma senza conferma/salvataggio**: visibili messaggio economico prudente e «Situazione economica registrata: Da definire». **`UAT-173-FINAL-01 PASS_OWNER_VISUAL`**. Già Owner confermato punto 2 POS `UAT-173-FINAL-02 PASS_OWNER_VISUAL`. **I due difetti iniziali risolti su immagine `500c882`.**

**Rimane `FAIL_OWNER_VISUAL_CALENDAR_CLIPPING`**, calendario condiviso `DateInput` che esce/taglia il margine sinistro nella modale, e **osservazione `UAT-173-UX-ECONOMIC-NOTE-READABILITY`** per testo economico troppo piccolo/poco contrastato. **NON DECLARARE `CORE173_OWNER_ACCEPTED`**. [Unico mandato tecnico di finitura su Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6437654512): correggere popover comune + leggibilità, test browser desktop/mobile e altri DateInput, CI/reviewer e preparare nuova candidata; **STOP prima di qualsiasi nuovo deploy** fino a un gate DEV esplicitamente autorizzato. Nessun altro GOAL né merge.

---

## OWNER UAT POST-DEV — 27/10/2026: POS CONFERMATO, CALENDARIO TAGLIATO, MESSAGGIO ECONOMICO DA VERIFICARE

L'Owner ha dichiarato «**punto 2 va bene**»: la presentazione POS del Report della CORE #173 su immagine DEV `500c882` è **PASS_OWNER_VISUAL**, senza implicare nuova lettura indipendente del CSV. **NUOVO BUG UX** fotografato nella modale «Chiudi la mia giornata»: calendario `DateInput` / `cc-date-popover` **tagliato sul margine sinistro della modale desktop** (`UAT-173-UX-DATE-POPOVER-CLIPPED`). La correzione deve considerare il componente riusabile e gli altri form Premium, con regressioni desktop/mobile; **NON autorizza nuovo deploy/merge**. Il controllo Owner del testo «Non svolta» è **PENDING**: nello screenshot 26/10 era visibile il pulsante, ma non ancora selezionato. Chiudere senza premere conferma su dati esistenti; test informativo possibile selezionando `Non svolta` il 26/10 e leggendo il messaggio. Stato complessivo `CORE173_OWNER_ACCEPTANCE_PENDING`, non GOAL chiuso. **[Issue #173, osservazione Owner #6437494426](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6437494426)**.

---

## ULTIMO REPORT LIVE — 26/10/2026: CORE #173 `500c882` DEV INSTALLATO SECONDO AGY, OWNER UAT MIRATO PENDING

**L'ultima evidenza, successiva al gate condizionato qui sotto, è [rapporto AGY Issue #173 #6429206418](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6429206418) / [PR #175 #6429210219](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6429210219).** AGY attesta il PASS del preflight e l'installazione in DEV della *sola* immagine `cc173-day-closure:500c882` (SHA `500c882689a4ef1fcf6b10576676a3fb8850e850`, ID `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`) sui sei servizi applicativi. Restano DB/Redis/schema invariati; nuovo backup cifrato dopo Owner UAT e restore isolato riportati PASS; fingerprint dominio pre/post `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5` invariato; test DEV multiruolo 21/21 e verifica due UX fix PASS secondo AGY. CI GitHub `40412036299` entrambi i job SUCCESS. **ChatGPT non ha eseguito controlli direttamente sul VPS:** la prova d'installazione è il rapporto operatore, non una ispezione runtime indipendente.

**Test di regressione:** backend `120 PASS, 1 SKIP` (`test_mariadb_load_and_reconciliation` benchmark live intenzionalmente escluso dalla suite offline), frontend `200 PASS, 8 SKIP`; zero FAIL riportati. AGY dichiara reviewer indipendente PASS, ma **la PR #175 non presenta review formale GitHub** alla verifica, per cui prima del merge va resa rintracciabile l'identità e la prova del reviewer indipendente. Nessun blocco automatico del walkthrough Owner visivo limitato.

**PASSAGE ATTUALE:** `DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_500c882` **secondo AGY**, **NON** `CORE173_OWNER_ACCEPTED`. Prossima azione autorizzata: Owner effettua **solo** lettura visiva di (1) «Non svolta» con messaggio economico prudente, **senza confermare**, (2) Report Direzione e CSV 14/10 con `Carta POS · terminale 2f7e`. Registrare UAT senza rifare i test precedenti. PR #172/#174/#175 ancora DRAFT/UNMERGED. AUDIT-06 non autorizzato; nessuna produzione.

---

## DECISIONE OWNER PIÙ RECENTE — 26/10/2026: GATE DEV `500c882` AUTORIZZATO SOLO CONDIZIONATAMENTE

**Fonte live e vincolante:** [Issue #173 — Gate Owner #6428982304](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428982304) e [PR #175 — rinvio al gate](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6428992485). Owner «Sì procediamo»: **autorizzato l'intervento DEV soltanto se tutti i controlli preflight PASS**. Candidato esatto `500c882689a4ef1fcf6b10576676a3fb8850e850`, immagine `cc173-day-closure:500c882`, digest `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`; sei soli servizi applicativi `centrochange-dev`, precedente `d500fff` conservato per rollback. **Non significa che la nuova immagine sia stata installata**.

Prima del rollout: spiegare 120/121 test backend, distinguere 200 PASS/8 SKIP Playwright, reviewer indipendente realmente attestato sulla SHA, CI correlata, backup cifrato **nuovo dopo scritture Owner** e restore isolato, fingerprint DEV post-UAT `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5` da confrontare a baseline live, rollback pronto. Gate FAIL ⇒ `BLOCKED_DEV_UNCHANGED`; se rollout PASS ⇒ smoke browser/API/ACL/CSV + fingerprint e `DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_500c882`; regressione ⇒ rollback dei soli servizi e report `BLOCKED_SAFE_ROLLBACK`. Nessun dato storico, DB, Redis, schema, ruoli, credenziali, merge, produzione o AUDIT successivi autorizzati. **Owner acceptance CORE #173 ancora PENDING**.

---

## 1. QUAL È IL PROGRAMMA CORRENTE — SENZA AMBIGUITÀ

Il lavoro attuale è il **percorso di audit funzionali Premium React, una interfaccia/area alla volta**, con SOP v1.1 GOAL-DRIVEN e CORE cliente strettamente associati. Quando l'Owner dice **«goal 5»** nel contesto di questi walkthrough intende **AUDIT-05 Professionisti (Issue #171)** e il completamento collegato di **CORE #173**, **non** il «GOAL-05 — Delivery Closure & Continuity» della vecchia roadmap MVP.

| Unità in sequenza di fase | Fonte | Stato e limiti al checkpoint |
|---|---|---|
| AUDIT-03 — Agenda | Matrice #110, `CC-EXT-003` | Accettazione Owner registrata nel percorso UAT precedente; non ripetere |
| AUDIT-04 — Pazienti | [Issue #167](https://github.com/2008hitch-afk/centrochange_core/issues/167) | CLOSED, OWNER_ACCEPTED nel proprio perimetro, non riaprire |
| **AUDIT-05 — Professionisti / Accessi** | [Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171), [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172) | **OWNER_ACCEPTED_SCOPED** con [decisione](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6427680735); PR #172 ancora DRAFT/UNMERGED; non confondere acceptance con merge/chiusura del codice |
| **CORE #173 — «Chiudi la mia giornata» e arretrati** | [Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173), [PR #175](https://github.com/2008hitch-afk/centrochange_core/pull/175) | **UNITÀ CORRENTE DA TERMINARE**. DEV `d500fff` installato secondo [report AGY](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427998113); Owner UAT-173-01..06 svolti; **2 soli difetti UX confermati** e controllo READ-ONLY dati post-save; [mandato finale](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428463645) autorizzato. **OWNER_ACCEPTANCE #173 ancora PENDING**. Nuova immagine richiede proprio gate DEV |
| **AUDIT-06 — Servizi, catalogo, prezzi e disponibilità** | **Unicamente** §«Prossimo area pianificata» della [Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171) | **PIANIFICATO COME SUCCESSIVO, NON AVVIATO E NON AUTORIZZATO**. Alla verifica 26/10 non risulta una Issue AUDIT-06 dedicata. Non usarlo come mandato operativo |
| AUDIT-07 e ulteriori | Nessun programma univoco degli ID futuri verificato alla data del checkpoint | **DA FORMALIZZARE SOLO CON DECISIONE OWNER E MATRICE**, senza inventare nomi, ordine o stato. Le aree nel CSV restano inventariate ma non rinumerate automaticamente |

**STOP dopo questo perimetro:** nessun salto dall'AUDIT-05 a «GOAL-05 consegna cliente» e nessuna attivazione di 06/07/produzione. Le vecchie UAT con numero 05/06 e i macro-GOAL 01–05 NON sono sinonimi degli AUDIT.

## 2. STATO DI LAVORO EVIDENCE-BASED — SOLO FASE ATTUALE

- **Sviluppo #171:** [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172) branch `issue-171/professionals-audit`, SHA `a3e41a10287639a7c200992e45c3173b8ea33b46`; DRAFT/UNMERGED al checkpoint. `OWNER_ACCEPTED_SCOPED_AUDIT05` **non** significa `MERGED`, `ISSUE_CLOSED` o accettazione globale delle 110 righe.
- **Sviluppo #173:** [PR #175](https://github.com/2008hitch-afk/centrochange_core/pull/175) branch `issue-173/day-closure-recovery`, base #172, SHA di ultimo candidato DEV `d500fff45cc5ca70c5ef33575aac4e58d4fed505`; DRAFT/UNMERGED al checkpoint. CI sul candidato [40396123393](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40396123393) SUCCESS. Il rapporto AGY dichiara DEV `cc173-day-closure:d500fff`, Image ID `sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`, 21/21 smoke e backup/restore isolato. **ChatGPT non ha ispezionato il VPS**.
- **Prove Owner #173:** apertura modale e arretrati; selettori Svolta/Pagata/Metodo; Owner **ha realmente comandato il salvataggio** della giornata arretrata 14/10/2026; al refresh il badge 14/10 è sparito, Report Manager e CSV mostrano 14/10 ore 12:00 **Svolta / Registrato / Carta POS / 100 €**. Sono PASS **visivi e di interazione**; occorre ancora sola lettura del record/Settlement/audit per attestare la persistenza server-side post-Owner.
- **Difetti confermati ancora OPEN in #173:** (1) frase UI «Non svolta ... non sarà addebitata» erroneamente assoluta in presenza di importi/penali `Due`; (2) codice tecnico `CC-MVP-POS-...` mostrato in Report e CSV. **NON è un bug il filtro CSV**: Owner ha chiarito che non lo aveva impostato, [rettifica #6428384872](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428384872).
- **Ultima istruzione AGY autorizzata:** [mandato unico #6428463645](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428463645): 2 fix UX su #175, verifiche DB DEV **solo lettura**, test su clone e browser, reviewer+CI, preparare nuovo candidato. **Non autorizzati** nuovo deploy DEV della nuova immagine, merge, modifica dati storici, ruoli, schema, credenziali, produzione, avvio altre aree.
- **Documentazione:** [PR #174](https://github.com/2008hitch-afk/centrochange_core/pull/174) docs-only DRAFT/UNMERGED, basata su #172. [Checkpoint dettagliato](CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md), [CSV 110 requisiti](FUNCTIONAL-COVERAGE-DETAIL.csv), [matrice leggibile](FUNCTIONAL-COVERAGE-MATRIX.md). Il primo è **cronologia dettagliata**, non deve essere letto dal basso ignorando gli aggiornamenti più recenti. La matrice CSV distingue `Stato` tecnico da `Owner`; ultimo conteggio su branch docs: **110 ID, 12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED**; Owner 96 PENDING / 12 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV. Non trasformare una percentuale di conteggio in percentuale di prodotto completo.

## 3. ORDINE DI AUTORITÀ E DOCUMENTI STORICI

1. **Owner:** decisioni specifiche e successive, interpretate nel perimetro originario, con condizioni esplicite; produzione e merge sempre gates separati.
2. **GitHub dinamico:** issue attiva #173 e commenti recenti, Issue #171, PR #175/#172/#174, SHA reale, CI effettiva e report delle prove; se c'è conflitto tra istruzioni di date differenti, fermarsi e riconciliare la più recente autorizzazione *pertinente*.
3. **Questo indice** per la scelta del GOAL attivo e della prossima fase; [checkpoint esteso](CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md) e matrice per tracciabilità/evidenze.
4. **`docs/MVP-GOAL-ROADMAP-v0.1.md`, 03/10/2026:** **ROADMAP MACRO DI ORIZZONTE / STORICA PER L'ATTUALE WORKFLOW**. Il suo GOAL-05 è «Delivery Closure» e non è la fase Professionisti. Può restare come riferimento per production readiness/go-live/handover **quando saranno esplicitamente avviati**, ma NON si può utilizzare come current goal, inferire che dopo «5» il prodotto sia finito, o ignorare gli audit funzionali correnti.
5. **`README.md` e `AGENTS.md`:** devono rimandare qui per la scelta del lavoro attivo; eventuali vecchie affermazioni del tipo «current GOAL-02» si interpretano **soltanto come baseline storica**, mai come mandato odierno.

**Non modificare o dichiarare aggiornato il tracker #156 se non è effettivamente accessibile**: al checkpoint ha restituito 404 con l'identità GitHub corrente. Non creare duplicati alla cieca.

## 4. CHECKLIST ANTI-DERIVA PER OGNI NUOVA CHAT / AGY

1. Identifica l'unità funzionale attiva per **nome + issue** (`AUDIT-05 #171 → CORE #173`) prima di usare «GOAL N».
2. Rileggi **live** #173, #171, PR #175/#172/#174, ultimi commenti Owner e commit/CI, oltre al CSV del branch documentale; non assumere che la chat precedente sia l'ultima.
3. Rispondi distinguendo `CODICE`, `CI`, `CLONE REALE`, `DEV INSTALLATO`, `UAT OWNER`, `ACCETTATO`, `MERGE`, `PRODUZIONE`: un successo a un gate NON promuove automaticamente gli altri.
4. Nessun «GOAL successivo» se nome/scope e autorizzazione Owner non sono entrambi documentati su GitHub; non trattare AUDIT-06 pianificato come già autorizzato, non inventare 07+.
5. Non riavviare test Owner già passati, non riaprire Issue passate; un solo mandato Codex completo e ciclo fix/test/reviewer/gate.
6. Prima di finalizzare la fase #173: audit post-save read-only, due UX fix, CI/reviewer sul nuovo commit, nuova immagine gated per DEV, SOLO recheck Owner dei due fix, acceptance Owner circoscritta, piano di merge separato e riconciliazione documentale; nessuna nuova area in parallelo.
7. A GOAL concluso, aggiornare **questo indice + checkpoint + CSV + Issue**, registrando stato e prossimo GOAL **solo se esplicitamente autorizzato**. Non lasciare PR/fixture/backend incompiuti o prod dichiarata per inferenza.

**Nota di conservazione:** è vietato sovrascrivere retroattivamente prove e decisioni storiche; correggere i riferimenti di navigazione e aggiungere checkpoint successivi datati. Il branch che contiene questo indice è documentale (#174) e non conferisce di per sé permesso di merge.
