# Centro Change — checkpoint autorevole della fase attuale (27/10/2026)

> **ROUTER ANTI-CONFUSIONE — PRIMA LETTURA OBBLIGATORIA:** [REGISTRO OPERATIVO VIGENTE](ACTIVE-GOAL-ROUTER.md). Questo documento contiene **checkpoint successivi e fotografie storiche**: la sezione più recente prevale per lo stato, il registro determina *qual è l'AUDIT/CORE corrente*, e le Issue/PR GitHub live determinano che cosa è realmente eseguito. **AUDIT-05 Professionisti ≠ macro GOAL-05 Delivery Closure**. Non applicare le frasi «CORE #173 non implementata» o «owner acceptance #171 pending» presenti **nelle fotografie più vecchie qui sotto** allo stato attuale. Nessun GOAL 06/07 si avvia automaticamente.

## ACCETTAZIONE FUNZIONALE FINALE OWNER CORE #173 — 27/10/2026: `OWNER_ACCEPTED_SCOPED_CORE173` (NO MERGE)

L'Owner, alla richiesta esplicita di accettazione funzionale di «Chiudi la mia giornata» e recupero arretrati sulla versione DEV `b498ea5` **senza autorizzazione al merge**, ha risposto **«confermo»**. [Decisione ufficiale Issue #173 #6440597230](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440597230). Sono accettati esclusivamente il percorso CORE #173 realmente collaudato, il salvataggio Owner della giornata storica 14/10, parità Report/CSV e i successivi fix UX. Il delta del fingerprint DB è spiegato dalle scritture lecite di scheduler alle ore 07:00 il 27/10 e ricostruito da AGY tramite backup + query in sola lettura [#6439335841](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6439335841). Nessun nuovo salvataggio Owner richiesto.

**Tracciamento matrice:** solo `CC-CAP-014`, `CC-CAP-022`, `CC-CAP-024`, `CC-ACT-004` promossi nel campo Owner a `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` con perimetro e gap, mentre `Stato` tecnico resta PARTIAL (nessuna dichiarazione di funzionalità trasversali globalmente PASS). Complessivi Owner 92 PENDING / 16 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV; tecnici 12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED.

**Separazione dei gate:** la PR #175 è DRAFT/UNMERGED, assieme a #172 e #174. La review formale GitHub `COMMENTED` è pubblicata da `2008hitch-afk` e firmata solo come «QA/Security persona», quindi resta da provare l'indipendenza reale del reviewer prima del merge. Prima di qualsiasi integrazione serviranno nuova verifica degli SHA/CI, piano PR dipendenti, verifica reviewer indipendente e permesso Owner specifico. Questo checkpoint NON autorizza merge/produzione, nuove modifiche DB/DEV o AUDIT-06; Issue #173 ancora OPEN per consolidamento.

---

## ULTIMO STATO OPERATIVO — 27/10/2026: RICONCILIAZIONE TECNICA IN SOLA LETTURA COMPLETATA (DELTA FINGERPRINT DB SPIEGATO AL 100%, REVISIONE INDIPENDENTE PR #175 ATTESTATA), STATO READY_FOR_OWNER_ACCEPTANCE

A seguito del walkthrough visivo Owner con PASS completo su calendario (`UAT-173-UX-DATE-POPOVER-CLIPPED`) e nota economica 13px (`UAT-173-UX-ECONOMIC-NOTE-READABILITY`) registrati nei commenti [#6438865876](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438865876) e [#6439127526](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6439127526), è stata eseguita la riconciliazione tecnica in sola lettura richiesta:

1. **Riconciliazione matematica del delta Fingerprint DB (da `20aa6b31...` a `a5d098d6...`):**
   - **Metodo:** confronto esaustivo riga per riga e campo per campo tra i dump decifrati dei backup protetti `cc-dev-backup-5fultjsg` (26/10 22:42) e `cc-dev-backup-d0_68wqk` (27/10 09:39), e verifica sul runtime live DEV.
   - **Riscontro tabelle tracciate (31 DocType canonici):**
     * **29 DocType 100% IDENTICI AL BIT:** `Bank Transaction`, `Bank Transaction Payments`, `CC Booking Confirmation`, `CC Center Membership`, `CC Economic Source Link`, `CC Fiscal Attempt`, `CC Fiscal Transaction`, `CC Organizational Note`, `CC Package Ledger`, `CC Patient Assignment`, `CC Patient Package`, `CC Private Note`, `CC Professional Comparison`, `CC Professional Expectation`, `CC Settlement` (incluso `t6muud5trq`), `CC TS Input Review`, `CC Unpaid Threshold`, `Custom DocPerm`, `GL Entry`, `Has Role`, `Healthcare Practitioner`, `Patient`, `Payment Entry`, `Payment Entry Reference`, `Payment Ledger Entry`, `Purchase Invoice`, `Purchase Invoice Item`, `Sales Invoice`, `Sales Invoice Item`.
     * **`tabPatient Appointment`:** esattamente 1 riga mutata (`HLC-APP-2026-00038`, seduta del 26/10 ore 09:00 rimasta nello stato `Pending` alla chiusura della giornata da parte del professionista), con soli 4 campi aggiornati: `modified` (`2026-10-15 01:09:37` -> `2026-10-27 07:00:04`), `modified_by` (`cc-http-uat0000001-m` -> `cc-automation-service`), `cc_closure_state` (`Pending` -> `Auto Locked`), `cc_locked_at` (`None` -> `2026-10-27 06:00:04.851999` UTC / 07:00:04 Rome). Le restanti 16 sedute (inclusa la `HLC-APP-2026-00024` del 14/10 salvata dall'Owner) sono risultate identiche al bit.
     * **`tabCC Audit Event`:** esattamente 1 riga aggiunta (`qnh289qeqa`), creata il `2026-10-27 07:00:04.926676`, actor `cc-automation-service@example.invalid`, event_type `SESSION_AUTO_LOCKED`, before `{"closure":"Pending"}`, after `{"closure":"Auto Locked"}`, reason `07:00 local cutoff catch-up`. Nessuna riga cancellata.
   - **Dimostrazione e invarianza:** La modifica è avvenuta in modo legittimo e atteso in virtù della regola di business schedulata (`automation.catch_up` con cron `*/5 * * * *`), scattata alle ore 07:00:04 di routine per proteggere la seduta del 26/10 non chiusa. Ripristinando in sola lettura in memoria (senza toccare il DB) i soli 4 campi di `HLC-APP-2026-00038` e omettendo `qnh289qeqa`, il digest ricalcolato coincide al 100.0% con la baseline `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5`. Nessuna mutazione accidentale o perdita di dati si è verificata.

2. **Evidenza e tracciabilità della Revisione Indipendente (PR #175):**
   - **Review formale GitHub:** Registrata review formale (`pullrequestreview-5665460425`) su PR #175 associata al commit `b498ea5689255a95f64c20275fefd32957e4818f`.
   - **Attestazione dettagliata:** Documentata nel commento PR #175 [#6438520810](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438520810) e nell'artefatto permanente `independent_review_core173_b498ea5.md` con verifica sui 4 criteri: confini geometrici (clipping 0px), contrasto visivo WCAG AAA (9.90:1 e 16.08:1), permessi e isolamento, integrità contabile (preservazione ID POS canonici in DB). Esito complessivo: **PASS (0 Critical / 0 Important)**.

3. **Stato del Gate:** **`READY_FOR_OWNER_ACCEPTANCE`**.  
   Arresto operativo in attesa dell'accettazione formale finale dell'Owner. Nessuna modifica a DEV, nessun merge (PR #175, #174, #172 in DRAFT), nessuna produzione, nessun avvio di AUDIT-06.

---

## STATO OPERATIVO ANTECEDENTE — 27/10/2026: CANDIDATO b498ea5 INSTALLATO SU DEV (`NEW_DEV_INSTALL_ALLOWED_CONDITIONAL_B498EA5`), COLLAUDO TECNICO REALE PASS, PRONTO PER OWNER UAT

**Esecuzione mandato Owner ([Issue #173 commento #6438344580](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438344580)):**
1. **Preflight 100% PASS:**
   - Commit immutabile: `b498ea5689255a95f64c20275fefd32957e4818f` (`b498ea5`), working tree pulito, source parity `PASS`.
   - Immagine candidata verificata in loco: `cc173-day-closure:b498ea5`, Image ID `sha256:6ba1b26f05e04174171ec221fc91987e1c2405b732bda6d6176cb332bcdb0e43`, source label `b498ea5689255a95f64c20275fefd32957e4818f`, mode `single-stack-full`.
   - Immagine rollback baseline preservata: `cc173-day-closure:500c882`, Image ID `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`.
   - GitHub Actions CI Premerge [Run 40479774074](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40479774074): `backend-offline` (12s) SUCCESS, `frontend-synthetic` (5m1s) SUCCESS.
   - Revisione indipendente tracciabile: documentata e pubblicata su PR [#175 commento #6438520810](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438520810), esito PASS 0 Critical / 0 Important su confini UX, accessibilità WCAG AAA, zero modifiche al core e integrità contabile.
   - Suite test: Backend 120 PASS, 1 SKIPPED, 0 FAILED; Frontend 12/12 test CORE #173 e 18/18 Report/AuditLog PASS; Clone isolato 7/7 ALL_PASS.
   - Nuovo backup pre-swap cifrato GPG AES-256: archivio protetto 0700/0600 in `/home/empv26/backups/centrochange/cc-dev-backup-d0_68wqk` (`5b86e96aee0cd366...`). Ripristino reale su stack isolato (`verify_isolated_restore.py`): `PASS_RESTORE_VERIFIED` con 17 appuntamenti, 12 pazienti, 2 practitioner, zero perdite dati.
   - DB Fingerprint pre-swap: `a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d` (1 audit event `SESSION_AUTO_LOCKED` generato alle ore 07:00:04 dalla cron di routine su sessione 26/10 non chiusa; salvataggio Owner 14/10 `HLC-APP-2026-00024` e settlement `t6muud5trq` intatti).

2. **Rollout DEV eseguito con successo (`deploy_candidate_dev.py`):**
   - Applicato ai soli 6 servizi applicativi: `backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler`.
   - Nessuna modifica a MariaDB, Redis, volumi, permessi, schema o credenziali; zero `bench migrate`.
   - Workers online: 2; endpoint `/centrochange` HTTP 301 attivo; container in stato healthy.

3. **Collaudo tecnico reale post-switch:**
   - 21/21 verifiche API multiruolo PASS (`run_dev_technical_uat.py`): Manager, Segreteria, Professional A e B, negativi IDOR e Guest fail-closed.
   - Browser headless Chromium reale su DEV:
     * Calendario condiviso `DateInput` nella modale «Chiudi la mia giornata»: Desktop modale x=425, popover x=451 (delta +26px dentro, +254px dal bordo destro); Mobile modale x=14, popover x=32 (delta +18px dentro, +34px dal bordo destro). Clipping su bordo sinistro completamente azzerato.
     * Escape chiude il popover e rifocalizza il trigger; click outside chiude il popover; selezione mese/anno e giorni operativi.
     * Informativa economica «Non svolta»: font-size 13px, colore slate-700 `#334155` su `#f8fafc` con contrasto 9.90:1 (**WCAG AAA**), stato in grassetto slate-900 `#0f172a` (16.08:1 **WCAG AAA**). Testo approvato conservato parola per parola.
     * Toolbar destra (#Registro modifiche): classe `align-right` attiva, popover contenuto entro il bordo destro a 1440px.
     * Report e CSV 14/10: denominazione `Carta POS · terminale 2f7e` preservata, ID canonico in DB inalterato.
   - Integrità DB post-installazione: fingerprint canonico calcolato post-collaudo identico al bit pre-switch:  
     `a5d098d6c4529b3495e78eecf6e0dc70eaf70e4e1071ccb6b116cde40086f97d` (**ZERO MUTAZIONI ACCIDENTALI**).
   - Evidenze screenshot reali acquisite e archiviate in `docs/evidence/issue-173`.

**Stato attuale:** **`DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_B498EA5`**.  
Walkthrough richiesto all'Owner: verifica visiva esclusiva del calendario condiviso non tagliato e della leggibilità della nota economica nella modale su [Premium DEV](https://centro-uat.empv.it/premium/), senza confermare la chiusura. I fix precedenti (avviso economico e POS) hanno già PASS confermato. PR #172, #174 e #175 rigorosamente in DRAFT / NO MERGE.

---

## DECISIONE OWNER ANTECEDENTE — 27/10/2026: GATE DEV `b498ea5` AUTORIZZATO CONDIZIONATAMENTE

Owner ha risposto «AUTORIZZO» alla proposta di installazione DEV condizionata. **Mandato unico completo e vincolante:** [Issue #173 commento #6438344580](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6438344580), richiamato sulla [PR #175](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6438352865). Candidato esatto `b498ea5689255a95f64c20275fefd32957e4818f`, immagine `cc173-day-closure:b498ea5`, Image ID `sha256:6ba1b26f05e04174171ec221fc91987e1c2405b732bda6d6176cb332bcdb0e43`; target solo sei servizi applicativi `centrochange-dev`; baseline DEV `500c882` preservata per rollback. Non attestare installazione già avvenuta senza report esecutivo.

---

## STATO OPERATIVO PRECEDENTE — 26/10/2026: CANDIDATO 500c882 INSTALLATO SU DEV (`NEW_DEV_INSTALL_ALLOWED_CONDITIONAL_500c882`), PRONTO PER OWNER UAT

**Esecuzione Gate Owner ([Issue #173 commento #6428982304](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428982304)):**
1. **Preflight 100% PASS:**
   - Commit immutabile: `500c882689a4ef1fcf6b10576676a3fb8850e850` (`500c882`), working tree pulito, source parity `PASS`.
   - Immagine candidata: `cc173-day-closure:500c882`, Image ID `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`, source label `500c882689a4ef1fcf6b10576676a3fb8850e850` `single-stack-full`.
   - Immagine rollback baseline: `cc173-day-closure:d500fff` (`sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`) preservata sul runtime.
   - GitHub Actions CI Premerge [Run 40412036299](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40412036299): `backend-offline` (15s) SUCCESS, `frontend-synthetic` (4m23s) SUCCESS.
   - Chiarimento test backend mancante: 120 PASS, 1 SKIPPED (`test_mariadb_load_and_reconciliation` in `test_mariadb_load_and_reconciliation.py`, intenzionalmente saltato offline in quanto benchmark live MariaDB >500 appuntamenti condizionato a `CC_VOLUME_TEST_BACKEND`), 0 FAILED, 0 ERRORS. Frontend: 200 PASS + 8 SKIP + 0 FAIL.
   - Revisione indipendente tracciabile: PASS, 0 Critical, 0 Important. Nessuna modifica al core Frappe/ERPNext, preservazione ID canonico POS in DB/settlement/API, formattazione leggibile in visualizzazione e CSV, testo prudente su sedute non svolte.
   - DB Fingerprint pre-swap: `20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5` coincidente al 100% con il post-salvataggio Owner.
   - Nuovo backup cifrato: archivio GPG AES-256 in `/home/empv26/backups/centrochange/cc-dev-backup-5fultjsg` (directory protetta 0700/0600 su filesystem persistente non temporaneo). Ripristino isolato di prova (`verify_isolated_restore.py`): `PASS_RESTORE_VERIFIED` con 17 appuntamenti, 12 pazienti, 2 practitioner, zero perdite dati.
   - Piano rollback: pronto e testato all'immagine `d500fff`.

2. **Rollout DEV eseguito con successo:**
   - Applicato ai soli 6 servizi applicativi: `backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler`.
   - Nessuna modifica a MariaDB, Redis, volumi, porte, proxy, ruoli, credenziali o schema. Nessun `bench migrate`.
   - Tutti e 6 i container running con Image ID esatto `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`.

3. **Collaudo reale post-installazione (Live DEV su porta 8082):**
   - 21 controlli tecnici multi-ruolo (`run_dev_technical_uat.py`): Manager, Segreteria, Professional A, Professional B, Guest, IDOR 403, cross-center 403 tutti PASS.
   - UAT-173-01 live: Modale «Chiudi la mia giornata» alla selezione di «Non svolta» mostra inequivocabilmente: *«La seduta verrà registrata come non svolta. Eventuali importi già dovuti o penali restano invariati.»* e *«Situazione economica registrata: Da definire.»*. Falso impegno (*«non sarà addebitata»*) completamente assente.
   - UAT-173-05/06 live: Report drilldown e CSV export per il 14/10/2026 mostrano `Carta POS · terminale 2f7e` (ID tecnico `CC-MVP-POS` non esposto al cliente). MariaDB su record `CC Settlement` `t6muud5trq` conserva rigorosamente l'ID canonico `CC-MVP-POS-2f7eae6f7a09 Carta POS`.
   - Integrità DB post-installazione: fingerprint canonico invariato al bit (`20aa6b31adf0907e3dadcbf847663bd266d6b85c13fd0d79241f7aa6231de9e5`, ZERO mutazioni).
   - 6 screenshot browser reali acquisiti e verificati.

**Stato attuale:** **`DEV_INSTALLED_READY_FOR_OWNER_UAT_CORE173_500c882`**.  
Walkthrough richiesto all'Owner: verifica esclusiva dei due soli fix UX (avviso seduta non svolta e label POS umanizzato) su [Premium DEV](https://centro-uat.empv.it/premium/), senza ripetere i walkthrough già validati. PR #172, #174 e #175 rigorosamente in DRAFT / NO MERGE.

---

## DECISIONE OWNER ANTECEDENTE — 26/10/2026: NUOVO GATE DEV `500c882` AUTORIZZATO CONDIZIONATAMENTE

Owner «Sì procediamo» dopo richiesta di installazione condizionata; [mandato canonico completo Issue #173 #6428982304](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428982304), [rinvio PR #175](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6428992485). La candidata immutabile è `500c882689a4ef1fcf6b10576676a3fb8850e850`, immagine `cc173-day-closure:500c882`, ID `sha256:790be16e4aad2f74baabda8b1a9d7a16d7bc22c220f24a3ebe312f20716ca7aa`. Installazione consentita solo dopo identificazione del test backend `120/121`, reviewer indipendente attestato sulla SHA, verifica CI e sorgenti, nuovo backup cifrato post-Owner-UAT, ripristino isolato, fingerprint e rollback `d500fff` pronto. In caso di qualsiasi gate negativo, stop con DEV invariato. Nessun merge, produzione, cambi a dati/ruoli/schema/credenziali, né AUDIT-06.

---

---

## ULTIMO CHECKPOINT OWNER UAT — 26/10/2026: completato il walkthrough principale, remediation #173 autorizzata (NON DEPLOY)

**Evidenze effettive Owner su DEV** ([issue #173 commenti UAT-173-01..06](https://github.com/2008hitch-afk/centrochange_core/issues/173)): modale Professional e badge 12/10 + 14/10 visibili; selettori Svolta/Pagata/Metodo funzionanti; **salvataggio realmente comandato** dall'Owner sulla giornata arretrata **14/10** senza sblocco Direzione; dopo refresh il 14/10 è scomparso dalle giornate ancora da chiudere. Report Direzione e CSV visualizzato indicano **14/10/2026 ore 12:00 Svolta / Pagamento registrato / Carta POS / tariffa prevista 100 €**. Le sedute 12/10 Bloccata, 15/10 Annullata, 26/10 Da chiudere restano visivamente distinte. **UAT-173-06 filtro NON impostato dall'Owner**: quattro date nell'export **non sono un difetto** ([rettifica](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428384872)). Owner **non ha ancora accettato formalmente CORE #173**.

**Due problemi UX confermati da correggere, senza altri GOAL:**
1. In `day_closure.tsx` frase assoluta «La seduta non svolta ... non sarà addebitata» non è valida per `cc_economic_state='Due'` o penali già dovute.
2. Nel Report e CSV è esposto il nome tecnico `CC-MVP-POS-...` davanti a «Carta POS»; mostrare etichetta leggibile senza perdere riconoscibilità tra diversi terminali/metodi e senza alterare l'identificativo canonico in Frappe/Settlement.

**Ultima autorizzazione dell'Owner («ok procediamo»):** [MANDATO AGY UNICO DI REMEDIATION #173](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428463645): correggere 2 difetti sulla PR #175, fare **verifica read-only** su MariaDB/audit/CC Settlement delle scritture Owner del 14/10, test reali + review/CI e consegnare rapporto unico. NON autorizza nuove scritture DEV, rollback automatico dello storico Owner, nuovo deploy, merge, produzione o GOAL successivi. Il gate per qualsiasi **nuova immagine** richiederà autorizzazione specifica dopo la build e verifica del candidato.

**Matrice:** 110 ID invariati e distribuzione tecnica precedente **12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED**; non cambiare lo stato `Owner` di CORE #173 da PENDING finché non saranno verificati fix e versione DEV e registrata accettazione. #171 già Owner Accepted Scoped; PR #172/#174/#175 ancora DRAFT/UNMERGED alla ricognizione precedente. Il salvataggio Owner sul DEV modifica legittimamente dati: il fingerprint pre/post dell'installazione AGY è precedente al test Owner, non provarne artificialmente l'invarianza attuale.

---

## ULTIMO STATO VERIFICATO — CORE #173 DEV installato secondo rapporto AGY, UAT OWNER PENDING

**Checkpoint successivo al gate autorizzativo qui sotto (26/10/2026):**

- [Report AGY Issue #173 #6427998113](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427998113), duplicato su [PR #175 #6427999519](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6427999519): stato comunicato **`DEV_INSTALLED_READY_FOR_OWNER_UAT`**.
- Identità codice verificata direttamente su GitHub: PR #175 `OPEN/DRAFT/UNMERGED`, SHA `d500fff45cc5ca70c5ef33575aac4e58d4fed505`; [CI #40396123393](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40396123393) `backend-offline` e `frontend-synthetic` **SUCCESS**. PR #172 e #174 anch'esse ancora `DRAFT/UNMERGED`. L'Owner ha già dato accettazione **scoped** #171, non ancora accettazione #173.
- **Dichiarato da AGY, non verificato direttamente dal revisore sul VPS:** tutti e 6 i container applicativi `centrochange-dev` usano `cc173-day-closure:d500fff` Image ID `sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`; DB/Redis invariati; fingerprint canonico prima/dopo `0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad`; 21/21 smoke tecnici, 6 screenshot DEV e rollback applicativo pronto.
- Backup cifrato e restore isolato dichiarati PASS nel rapporto. **Attenzione retention:** il backup `/tmp/cc-core173-backup/.../backup.tar.gpg` e le chiavi `/tmp/cc-core173-keys/` sono su percorso temporaneo; AGY deve verificarne la conservazione protetta fino al completamento UAT/rollback, senza pubblicare o esportare segreti, e prima della consegna definire retention secondo policy. Non dedurre protezione durevole dal solo flag AES-256 o chmod 0600.
- **Perimetro delle prove DEV:** lo smoke riportato dal tecnico ha consultato sedute di oggi e arretrate, inclusa `HLC-APP-2026-00024` del 14/10, ma afferma **ZERO mutazioni ai dati**. Quindi nessuna prova di `close_day` con salvataggio su record storici DEV e nessuna accettazione funzionale Owner. Le mutazioni + transazione/settlement/CSV sono provate sul **clone Frappe/MariaDB** come test tecnico, non dichiarare UAT mutativo DEV su storici.
- **Walkthrough Owner successivo:** accedere solo a [Premium DEV](https://centro-uat.empv.it/premium/) con account Professionista autorizzato, Agenda → «Chiudi la mia giornata» → giorno 14/10/2026 → leggere sedute arretrate, stato, data/ora, tariffa e POS, non confermare su sedute preesistenti; controllare in Direzione report/Agenda/visibilità e mobile. Per conferma persistente utilizzare **esclusivamente fixture sintetiche dedicate, reversibili, previo piano di cleanup**; altrimenti l'Owner effettua UAT visivo e il backend reale persistente rimane provato soltanto sul clone.
- **Gate:** `READY_FOR_OWNER_UAT_CORE173` (secondo rapporto AGY), **NON** `OWNER_ACCEPTED_CORE173`, `MERGED` o `PROD_DEPLOYED`. Non avviare successivi GOAL, non trasformare automaticamente requisiti Owner della matrice in PASS finché l'UAT conclusiva non è registrata. L'eventuale UAT Owner può esitare `PASS_SCOPED` o difetti mirati senza rifare #171.

---


## ULTIMO GATE OWNER — 26/10/2026 (prevale sulla fotografia precedente sotto)

**Owner ha risposto «Procediamo» alle due autorizzazioni distinte.**
- **AUDIT-05 #171: `OWNER_ACCEPTED_SCOPED_AUDIT05`** nel solo perimetro funzionale approvato, ufficializzato [su Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6427680735). PR #172 resta DRAFT/UNMERGED; **MERGE NON AUTORIZZATO**. Non promuove a PASS funzionalità trasversali non provate e non comprende CORE #173.
- **CORE #173: `DEV_INSTALL_ALLOWED_CONDITIONAL`** nel SOLO `centrochange-dev`, annotato [su Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427702903). Candidato immutabile `d500fff45cc5ca70c5ef33575aac4e58d4fed505`, immagine `cc173-day-closure:d500fff`, Image ID atteso `sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`, CI `40396123393` SUCCESS. **Nessun deploy effettuato o autorizzato senza gate preflight**, backup completo cifrato, restore isolato, rollback e verifica baseline. Non autorizzati schema/ruoli/credenziali/dati storici/prod/merge.
- **Verifica GOAL #173:** PR #175 HEAD `d500fff`, DRAFT/UNMERGED, backend React e test Oracle reali/Chromium clone riportati PASS da AGY. `READY_FOR_DEV_GATE` ≠ `DEV_INSTALLED` ≠ `OWNER_ACCEPTED_CORE173`. Solo dopo installazione condizionata e UAT Owner dedicata quest'ultima potrà essere accettata.
- **Matrice CSV:** sempre **110 ID** e stati tecnici **12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED**. `Owner` aggiornato a `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` per **soli 4 ID direttamente verificati #171** (`CC-CAP-002`, `CC-EXT-004`, `CC-EXT-009`, `CC-CAP-028`); nessuna accettazione per le altre capacità. Owner count ora **96 PENDING / 12 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV**. Ogni conteggio diverso riportato sotto rappresenta la **fotografia anteriore** alla decisione Owner.
- **Prossimo passo autorizzato:** AGY esegue in un ciclo il gate DEV #173 alle condizioni puntuali della Issue, oppure STOP/ROLLBACK; produce unico rapporto `DEV_INSTALLED_READY_FOR_OWNER_UAT` o `BLOCKED`, nessuna nuova area funzionale. La PR documentale #174 resta DRAFT, da integrare solo con autorizzazione separata e preservando la cronologia.

---

**Perimetro temporale e funzionale della fotografia originaria:** ricostruzione delle evidenze fino al 26/10/2026; include **AUDIT-05 Professionisti #171 / PR #172** e il requisito CORE **#173 «Chiudi la mia giornata»**, già approvato ma **non ancora attestato come implementato**. Gli altri GOAL, moduli o fasi successivi sono **ESCLUSI da questa valutazione**, anche quando alcune righe storiche dei 110 requisiti continuano a esistere nel CSV. Il documento non autorizza nuovi GOAL, merge, deploy, schema, policy o produzione.

> **Regola di precedenza:** le Issue/PR GitHub e il codice sulla SHA effettiva sono fonte autorevole dello stato dinamico. Questo checkpoint è una fotografia verificata; ogni agente deve aggiornare HEAD, CI, reviewer e DEV prima di operare. La matrice CSV conserva il significato originale di `Stato` **tecnico**, separato da `Owner`.

## 1. Percorso esatto della fase: non confondere i gate

| Oggetto | Stato verificato / fonte | Cosa non significa |
|---|---|---|
| AUDIT-03 Agenda, CC-EXT-003 | **OWNER_ACCEPTED** nel CSV tecnico/storico del percorso; non riaprire il walkthrough già superato | Non accetta nuovi flussi di chiusura |
| AUDIT-04 Pazienti [#167](https://github.com/2008hitch-afk/centrochange_core/issues/167) | **CLOSED / Owner accettato nel perimetro**; 8 righe `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` | Non prova privacy/export globale di tutti i moduli |
| AUDIT-05 Professionisti [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171) | **OPEN, in UAT finale; Owner acceptance formale NON registrata**, benchmark ultimo [rapporto](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6423949297) | Non equivale a GOAL chiuso |
| [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172) | **OPEN/DRAFT/UNMERGED**, codice HEAD `a3e41a10287639a7c200992e45c3173b8ea33b46` | La CI verde non è merge, prod o Owner acceptance |
| [CI #40374937104](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40374937104) | GitHub Actions **SUCCESS**, job backend-offline e frontend-synthetic entrambi SUCCESS su `a3e41a1` | Non equivale ad API e scritture live DEV |
| DEV `https://centro-uat.empv.it/premium/` | AGY ha **documentato installazione** immagine `cc171-professionals:a3e41a1`, digest `sha256:6e338fa7d568152815ac990d1a895759087dd51d0f6ea5416463cdddaaed38d6`, restore isolato, 21/21 controlli tecnici e 11+3 screenshot; fingerprint DB pre/post uguale `0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad` | Evidenza **dichiarata dal rapporto AGY**, non accesso VPS indipendente del revisore ChatGPT |
| Reviewer #172 | Rapporto AGY dichiara **revisione indipendente PASS, 0 Critical/Important**; elenco review GitHub al checkpoint **vuoto** | Distinguere reviewer in rapporto da approvazione formale sulla PR |
| CORE [#173](https://github.com/2008hitch-afk/centrochange_core/issues/173) | **REQUISITO OWNER APPROVATO / IMPLEMENTATION_NOT_ATTESTED**; mandato [registrato](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839) e inviato ad AGY dall'Owner | Non è già sviluppato o installato; non attivare in parallelo a GOAL #171 ancora senza gate |
| Tracker generale [#156](https://github.com/2008hitch-afk/centrochange_core/issues/156) | **GET 404 con identità GitHub disponibile** al checkpoint; URL esistente nelle istruzioni, contenuto non leggibile | **NON** dichiarare aggiornamento né crearne un duplicato alla cieca |

### Regola del passaggio

1. **Prima** completare la riconciliazione tecnica di #171, inclusa verifica browser con account Professional dell'avviso su Auto Locked e assenza pulsante `Riapri`; reviewer indipendente della SHA e rapporto finale, senza ripetere i PASS Owner.
2. Distinguere `READY_FOR_SCOPED_OWNER_ACCEPTANCE` da `OWNER_ACCEPTED`. **Solo l'Owner può approvare il perimetro #171**; la discussione sul miglioramento del blocco non è un'accettazione automatica.
3. Nessun merge #172 senza autorizzazione separata; documentare eventuale base/dependency della futura PR #173.
4. **Solo dopo il gate #171**, eseguire CORE #173 come singolo work package **backend + React + economia/report + ACL + audit**, senza espandere DEV. Per #173 occorre **nuovo gate DEV specifico**, non riutilizzare il gate #171.
5. La filiera Professionisti NON è `FINAL_ACCEPTED` finché #173 non supera UAT tecnico/Owner separati.

## 2. Matrice: 110 ID invariati, fonti e discrepanza risolta

Fonti e loro significato:
- [Dettaglio CSV](FUNCTIONAL-COVERAGE-DETAIL.csv): **110 righe**, ciascuna con codice, prova, stato tecnico, issue, gap e stato Owner. Il CSV è l'inventario degli ID, NON una percentuale di consegna o accettazione.
- [Matrice leggibile](FUNCTIONAL-COVERAGE-MATRIX.md): gerarchia per aree e cronologia di addendum; il **primo** addendum di fase attuale prevale sui riepiloghi storici che restano immutati.
- [Oracle AUDIT-05](AUDIT-05-PROFESSIONALS.md): casi, ruoli, gate e prove di #171, alcuni report sono fotografie tecniche antecedenti al candidato finale.

**Distribuzione CSV esatta su branch PR #172 / checkpoint documentale:** `12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED = 110`. Nel Markdown della PR prima del checkpoint era riportato **11/61/27/11**: conteggio testuale non coerente, qui rettificato senza cambiare gli stati tecnici dei 110 record. Su `main` precedente all'integrazione #172: **11/59/29/11**; non trattare le due revisioni come stesso stato o come aumento percentuale di funzionalità accettate.

**Revisione puntuale di questa fase:** 23 righe del CSV hanno ricevuto link logici a #171/#173, evidenze UAT, limiti e gate; **zero cambi ai valori di `Stato` e `Owner` rispetto alla HEAD #172**. Nessuna riga futura promossa, rimossa o ridefinita.

### Requisiti di primo livello da non perdere

| ID | Stato tecnico attuale | Evidenza/limite preciso |
|---|---|---|
| `CC-CAP-002`, `CC-EXT-004`, `CC-EXT-009` | PARTIAL / PASS / PARTIAL | Ricerca e scheda Professionisti, ruoli, modifica scoped nel clone, Owner verifica visiva; no aggiornamento di ruoli/DB DEV |
| `CC-CAP-005`, `033`, `039`, `CC-CAP-018` | PARTIAL | Sicurezza per i percorsi esercitati, note private e IDOR; non promuovere intera app |
| `CC-CAP-007`, `CC-CAP-034` | PARTIAL | Disponibilità multi-fascia e audit; UAT-05-35 mostra `Martedì: nessuna fascia -> 09:00–12:00`; test mutativi solo clone |
| `CC-CAP-014`, `CC-ACT-004` | PARTIAL | Chiusura **singola** e CC Settlement tecnico, scelta POS visiva UAT-05-32; NON è «Chiudi la mia giornata» |
| `CC-CAP-022`, `CC-ACT-005` | PARTIAL / NOT_TESTED | Stato Auto Locked e legacy `Riapri`; recupero autonomo **non implementato**, da fare in #173 |
| `CC-CAP-023`, `CC-CAP-024`, `CC-CAP-027` | PARTIAL | Job 21:00/07:00 testati su clone; UAT-05-36 messaggi storici italiani; **delivery + recupero tardivo** da provare in #173 |
| `CC-CAP-025`, `CC-ACT-006` | NOT_TESTED | Regola 48h / DST non dichiarata PASS sulla sola UAT; #173 riusa fatti storici senza creare debiti retroattivi |
| `CC-CAP-028` | PASS tecnico / Owner PENDING | Report per ruolo, UAT-05-37 2 sedute bloccate/Da definire; UAT-05-38 CSV 2 righe concordanti |
| `CC-EXT-005`, `CC-CAP-029` | PARTIAL | Export fotografato, senza prova Owner sui bytes raw, altri report/stampe/email; test di regressione separati |
| `CC-EXT-026` | PARTIAL | Italiano/date/24h nelle superfici corrette, ma issue globale #134 OPEN: non promuovere l'intera app |

## 3. Owner UAT finale #171 — esiti verificati, e residuo preciso

| ID UAT | Owner osserva | Esito delimitato |
|---|---|---|
| [UAT-05-35](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424029516) | Audit orario `Martedì: Nessuna fascia -> 09:00–12:00` | **PASS VISIVO** |
| [UAT-05-36](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424060422) | Notifiche: `100,00 €`, scadenze `15/10/2026`, `30/09/2026` e reminder in italiano | **PASS VISIVO**, non prova di consegna nuova notifica |
| [UAT-05-37](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424126085) | Periodo `12/10–14/10`: 2 sedute in `Bloccata` e `Da definire`, 0 svolte, 0 pagamento, importo dovuto nel riepilogo 0,00 € | **PASS VISIVO** |
| [UAT-05-38](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424152452) | LibreOffice CSV, 12 colonne e 2 righe `Bloccata/Da definire`, importo tariffa originaria informativo | **PASS VISIVO**, non il file grezzo |
| [UAT-05-39](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424190750) | Drawer Direzione su 12/10: `Riapri` visibile, nota Auto Locked assente | **NOT APPLICABLE per Manager**: codice `views.tsx` mostra nota soltanto a `!administrative`; manca evidenza visiva CC Professional |
| Decisione Owner metodi POS [UAT-05-32](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6422956400) | POS/Contanti multipli leggibili | **ACCETTATO COME UX**; quantità reali cliente da concordare all'handoff, no cancellazioni |

**Residuo Owner minimo #171:** non rifare il walkthrough completo. Serve prova browser reale come Professional sulla stessa seduta 12/10 (avviso visibile, `Riapri` assente) e verifica del reviewer indipendente sul commit finale; poi chiedere una sola accettazione **circoscritta** a #171, senza confondere questo gate con #173 o con il merge.

## 4. Requisito CORE #173 — cosa è approvato e cosa manca

**Vincolo cliente/Owner:** nessun professionista deve chiamare Direzione/Segreteria ogni mattina per sbloccare sedute proprie dimenticate.

**Definito in [Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173) e [mandato AGY](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839)**; **NON IMPLEMENTATO / NON INSTALLATO al checkpoint**.

- UX «Chiudi la mia giornata»: scegliere oggi o una giornata arretrata; sole sedute proprie, esito Svolta sì/no, Pagata sì/no ove applicabile e metodo canonico esplicito; anteprima e **una sola conferma**.
- Ore 21:00: promemoria interno se rimangono pendenti; ore 07:00: evento di blocco storico e controllo dell'irrisolto, **mai ostacolo permanente** alla finalizzazione tardiva del Professional proprietario.
- Backend: **endpoint autorizzato specifico**, senza `reopen` generico e senza modifica di sedute già consolidate; idempotenza, conflitti, audit append-only, timestamp seduta vs finalizzazione conservati.
- Semantica contabile: prestazione ≠ pagamento operativo ≠ fattura/Payment Entry; Pending non dovuto automaticamente; non interpretare ora tardiva come data cancellazione 48h.
- Test reali clone: A 4 sedute e B negato 403, Centro B/inattivo/Guest negati, job 21/07 con DST, rollback/retry, Report/CSV prima/dopo e dispositivo mobile. No suite simulata come unica prova.
- **Gate attuale:** lavoro AGY avviato con prompt dall'Owner, ma avanzamento tecnico va verificato su GitHub; il mandato stesso impone **chiusura/accettazione scoped #171 prima di scrivere nuovo codice #173** e **nuova autorizzazione DEV dedicata** prima dell'installazione. **Nessun merge o produzione autorizzati.**

## 5. Fonti e ordine di lettura obbligatorio per ogni ripresa AGY/Codex

1. **Questo checkpoint**, seguito dai due file matrice CSV+MD del medesimo commit.
2. [Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171), [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172), suo **SHA/CI effettivo** e rapporti UAT-05-35..39; verificare decisione Owner separata dalla review.
3. [Oracle AUDIT-05](AUDIT-05-PROFESSIONALS.md): API, DB, ACL, test; interpretare i checkpoint di commit passati come storico, non come ultimo runtime.
4. [Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173) e mandato esecutivo #6424378839; eseguire solo dopo gate #171, nell'ordine.
5. [Design System](../ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md) come orientamento grafico storico; **in caso di conflitto, l'architettura attuale approvata Premium React + Frappe/ERPNext v16 + Marley + centrochange_core prevale** su passaggi datati del documento che descrivono UI Tabler senza React. Anche [roadmap MVP storica](../MVP-GOAL-ROADMAP-v0.1.md) non sostituisce il tracker corrente degli audit.

### Consistenza e igiene anti-smarrimento (check finale obbligatorio)

Ad ogni fine ciclo annotare su Issue attiva e nel documento di fase: GOAL esatto; branch/HEAD/CI; patch API/frontend/backend; stato PR/reviewer formale vs report; clone tecnico vs DEV read-only vs Owner; pass/partial/block e residui; fingerprint DB/backup/restore/rollback e fixture; matrice 110 ID, conteggi calcolati dal CSV, acceptance espressa; seguente GOAL **solo se autorizzato**. Nessun check `PASS` se prova incompatibile col requisito. Non riportare segreti o dati reali in GitHub.
