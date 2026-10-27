# Centro Change — REGISTRO OPERATIVO VIGENTE / instradamento GOAL e AUDIT

**Fotografia iniziale:** 26/10/2026. **Scopo:** evitare che un agente, ChatGPT o Codex riparta dalla roadmap MVP storica oppure confonda i numeri degli AUDIT funzionali con quelli dei macro-GOAL di consegna. Questo è l'**indice di ingresso alla fase corrente**; NON sostituisce prove, decisioni e gate nelle Issue collegate.

> **ISTRUZIONE OBBLIGATORIA ALLA RIPRESA:** PRIMA di proporre un GOAL, rispondere a «dove siamo?», aggiornare una matrice o inviare AGY ad agire, controllare **live** le Issue e le PR qui elencate. Questo file è una fotografia versionata, non uno stato in tempo reale. Il codice e le attestazioni dinamiche sono su GitHub. In assenza di nuova verifica non dichiarare PASS, deploy, merge o accettazione.

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
