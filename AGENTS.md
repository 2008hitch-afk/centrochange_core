# AGENTS.md — Centro Change

## ATTIVAZIONE OWNER AUDIT-06 — 27/10/2026 (perimetro isolato, nessun DEV)

- L'Owner ha detto **«Ok procediamo»** dopo la rinumerazione consecutiva della roadmap. È aperta l'[Issue **#177 — AUDIT-06 Servizi/catalogo/prezzi/disponibilità**](https://github.com/2008hitch-afk/centrochange_core/issues/177) come unico GOAL attivo per analisi, sviluppo su branch dedicato, CI e UAT su ambiente isolato secondo SOP v1.1. **Nessuna installazione DEV, nuovo container/VPS, schema/DocPerm/ruoli, dati, merge o produzione autorizzati**. In mancanza di gate DEV esplicito, uscita `READY_FOR_DEV_GATE`, non `PASS_DEV`.
- [**PR #176**](https://github.com/2008hitch-afk/centrochange_core/pull/176) mantiene la nuova numerazione consecutiva 01–14 (finanza 12, compensi/fiscale 13); è **DRAFT/UNMERGED**, e l'esecuzione di #177 non la autorizza al merge. Riconciliare roadmap e baseline prima di pubblicare PR di prodotto.
- Restano veri i merge già verificati #172→#175→#174 su `main` `39be56b`; il DEV non ha automaticamente ricevuto quella HEAD. La matrice CSV 110×18 non cambia per la sola attivazione del GOAL.

## AGGIORNAMENTO OWNER VINCOLANTE — 27/10/2026: NUMERAZIONE CONSECUTIVA AUDIT

- PR #172, #175, #174 sono già integrate su `main` (HEAD `39be56b99319fc7aae3a612fb9052badfe8b9880`), issue #171/#173 chiuse; **merge non significa installazione DEV/prod**. Le sezioni pre-merge seguenti rimangono solo storiche.
- **Nuova istruzione Owner che SOSTITUISCE il precedente riordino senza rinumerazione:** AUDIT futuri numerati consecutivamente **01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14**. **Ex 10→08 (Report), ex 11→09 (Archivi), ex 12→10 (Accessi e registro), ex 13→11 (Primo incontro), ex 08→12 (Finanza), ex 09→13 (Compensi/fatture passive/SdI/TS).** I vecchi 01–07 e 14 non cambiano.
- **Riferimenti univoci:** [matrice sezione C](docs/qa/FUNCTIONAL-COVERAGE-MATRIX.md) e [router corrente](docs/qa/ACTIVE-GOAL-ROUTER.md). Per nuovo GOAL usare i numeri CANONICI; nei report/Issue precedenti al riordino interpretare i vecchi numeri tramite la mappa, senza rinominare testimonianze già accettate o cambiare numeri Issue/PR. Nessun nuovo AUDIT avviato/autorizzato automaticamente.
- **Scope invariato:** mantenere intatti requisiti, fonte dati, permessi, test ed evidenze. Il semplice cambio numerazione non autorizza modifiche software, DB, runtime, schemi, credenziali, DEV/prod o merge. Il CSV rimane 110 ID × 18 colonne, non modificato.

---

## PRIORITÀ STATO OWNER PIÙ RECENTE — 27/10/2026

[**CORE #173 `OWNER_ACCEPTED_SCOPED_CORE173`**](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440597230) su DEV `b498ea5`, **AUDIT-05 #171 `OWNER_ACCEPTED_SCOPED`**. È completata l'accettazione funzionale del perimetro verificato, **non** il merge né il gestionale globale. **La prossima unità NON è automaticamente AUDIT-06**: prima serve gate di consolidamento per PR #172→#175 e docs #174, con reviewer realmente indipendente identificabile, CI coerenti, ordine PR e **nuovo permesso Owner specifico**. Le PR sono DRAFT/UNMERGED e Issue #173 OPEN. La review formale della PR #175 è `COMMENTED` dall'account GitHub `2008hitch-afk` con descrizione «QA/Security persona»: **non confonderla con una review approvativa indipendente attestata**. Non eseguire merge/produzione/nuovi deploy/nuovo GOAL su generiche dichiarazioni di accettazione. Leggere per primo il [router](docs/qa/ACTIVE-GOAL-ROUTER.md) + Issue/PR LIVE. Le sezioni storiche sotto descrivono gate precedenti e non annullano questa decisione.

---

## ROTTA CORRENTE — OBBLIGATORIA PRIMA DI OGNI ALTRA INFORMAZIONE (26/10/2026)

**Leggere per primo `docs/qa/ACTIVE-GOAL-ROUTER.md` e controllare LIVE le Issue/PR specificate.** Il file determina quale AUDIT/CORE sia in corso; non riprendere il percorso operativo dal vecchio `docs/MVP-GOAL-ROADMAP-v0.1.md`, né dalle sezioni storiche di questo `AGENTS.md` che chiamano «current GOAL-02». I macro-GOAL MVP 01–05 e gli AUDIT funzionali (03, 04, 05, 06...) **sono numerazioni diverse**.

**Active execution al checkpoint:** AUDIT-05 Professionisti **#171** `OWNER_ACCEPTED_SCOPED`, PR #172 DRAFT non merged; work package **CORE #173** «Chiudi la mia giornata» e recupero tardivo in remediation finale UAT ([mandato Owner #6428463645](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428463645)), PR #175 DRAFT, DEV precedente `d500fff` installato secondo AGY. **Nuovo gate DEV condizionato AUTORIZZATO dall'Owner il 26/10 sulla SOLA immagine `cc173-day-closure:500c882`** ([dettagli completi su Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428982304)): AGY può installare soltanto dopo test/reviewer, backup post-UAT e restore isolato, verifica fingerprint e rollback tutti PASS; altrimenti STOP. **NON è un deploy già effettuato**, né merge/produzione. PR documentale #174 ancora DRAFT. Solo `AUDIT-06 Servizi/catalogo/prezzi/disponibilità` è **pianificato** in #171 come successivo, **non è avviato né autorizzato**; AUDIT-07+ non formalizzati. Non confondere `goal 5` usato dall'Owner per l'AUDIT-05 con il macro `GOAL-05 Delivery Closure` dello storico MVP.

**Precedenza:** decisione Owner specifica e più recente + Issue/PR/CI live → registro operativo vigente → checkpoint corrente e matrice 110 ID → documentazione storica. Mai dedurre `OWNER_ACCEPTED` da `CI PASS`, `CLONE PASS` da mock o `MERGED` da `DEV INSTALLED`. Niente altri GOAL, merge, produzione, permessi/schema/dati storici senza gate. Aggiornare registro e Issue quando cambia la fase, senza inventare numeri/nomi delle aree future.


Queste istruzioni valgono per Codex e per qualsiasi agente operativo che modifica questo repository.

## Prima di sviluppare

Leggere nell'ordine:

1. `docs/qa/ACTIVE-GOAL-ROUTER.md` + Issue/PR attive **live**
2. `README.md` (leggere le sezioni storiche come storico)
3. `ARCHITECTURE.md`
4. `SECURITY.md`
5. `docs/DECISIONS.md`
6. `docs/RUNTIME-BASELINE.md`
7. la issue GitHub assegnata e l'ultimo mandato Owner specifico

## Ruolo operativo

Codex è il **runtime engineer / implementer**. Deve verificare sul runtime ciò che non può essere dimostrato dal solo codice o dalla documentazione.

Per ogni task:

1. leggere issue, acceptance criteria e dipendenze;
2. verificare lo stato del runtime prima di mutare;
3. creare branch dedicato;
4. implementare il minimo necessario;
5. eseguire test automatici e manuali pertinenti;
6. produrre evidenze sintetiche;
7. aprire PR collegata all'issue;
8. indicare `PASS`, `PARTIAL` o `FAIL` senza sovrastimare il risultato.

## Regole non negoziabili

- Non modificare direttamente il core di Frappe, ERPNext o Builder.
- Non patchare container running manualmente come soluzione permanente.
- Non introdurre dipendenze da altri progetti/clienti.
- È consentito riusare **pattern infrastrutturali generalizzati**, non dati, business logic o codice client-specific non autorizzato.
- Nessun secret, password, token, backup, dump DB o dato cliente reale in Git.
- DEV/test usano solo dati sintetici o esplicitamente sanitizzati.
- Ogni controllo di sicurezza critico deve essere server-side e testato anche via API/accesso diretto.
- Ogni retry o job critico deve essere progettato per idempotenza.
- Non considerare una UI nascosta come un controllo di autorizzazione.
- Non dichiarare compliance GDPR sulla sola base di controlli tecnici.

## Native-first

Per ogni requisito valutare nell'ordine:

1. funzionalità nativa Frappe/ERPNext con fit corretto;
2. estensione supportata del nativo;
3. app ufficiale Frappe pertinente;
4. custom pulito in `centrochange_core`;
5. integrazione esterna solo se necessaria.

Se il nativo introduce semantica errata, rischio di sicurezza, UX significativamente peggiore o forte upgrade risk, preferire custom pulito.

### Direzione frontend dedicato — HC-0005 DECISION-060 (21/10/2026)

L'Owner ha **approvato la direzione architetturale** di un frontend React dedicato per le superfici operative Centro Change, con UX ispirata a Fresha e brand originale Centro Change. Questa direzione **sostituisce la preferenza UI nativa Frappe** del 12/10/2026, ma **non** il principio native-first per funzionalità backend, DocType, contabilità, autorizzazione e audit.

Fonte canonica: `2008hitch-afk/hitch-client-discovery/clients/HC-0005/decisions/DECISION-060-premium-react-frontend-architecture.md` (stato APPROVATO). Riusare Frappe/ERPNext/Marley/`centrochange_core` come backend autorevole; il frontend va integrato su API protette e verificate, preferibilmente sul sito Frappe esistente previa validazione.

**La decisione non autorizza implementazione né avvio del macro-goal**. In assenza di mandato operativo specifico, limitarsi ad analisi e proposta: niente installazioni, modifiche al server, PR di prodotto, merge, cutover o GOAL-03. Mantenere immutati gli stati delle PR esistenti e le limitazioni su dati reali e provider.

### Mandato isolato autorizzato — HC-0005 DECISION-061 (21/10/2026)

**Aggiornamento successivo:** l'Owner ha approvato il macro-goal `CENTROCHANGE-PREMIUM-FRONTEND-REBUILD` su [issue #148](https://github.com/2008hitch-afk/centrochange_core/issues/148), con [HC-0005 DECISION-061](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-061-authorize-premium-react-frontend-macro-goal.md). La clausola precedente rimane come **confine storico della sola DECISION-060** e non deve essere interpretata come diniego del nuovo mandato.

**Perimetro originario della DECISION-061:** Codex, quando avviato esplicitamente dall'Owner, poteva lavorare autonomamente su frontend React e test nel solo **branch/worktree e sviluppo isolato autorizzato**, creando sottoissue e PR DRAFT, usando skill/librerie gratuite solo dopo review/pin/licenze. Deve leggere `docs/ui/PREMIUM-FRONTEND-MACRO-GOAL-v1.md`, `docs/ui/PREMIUM-FRONTEND-SKILLS-LICENSES-v1.md` e `.agents/skills/centrochange-premium-ui/SKILL.md`. Reindirizzare il lavoro UI sovrapposto di #139 senza cancellarne rehearsal, test o prove storiche.

**Limiti originari della DECISION-061:** nessuna nuova installazione o mutazione del DEV condiviso, clone server senza autorizzazione specifica, merge di codice prodotto, cambio UI primaria, cutover, dati reali, provider reali, acquisti, GOAL-03, produzione o approvazione UAT implicita. Il current goal di delivery resta documentato come GOAL-02 con disallineamento issue #23 chiusa vs manifest ACTIVE; questa autorizzazione è un **macro-goal frontend specifico**, non una promozione di fase.

**Aggiornamento 22/10/2026:** le successive DECISION-062 (single-stack), 063 (API scoped), 064 (primo tentativo DEV), 065 (secondo tentativo) e 066 (fix/retest/continue) sono approvate nel registro HC-0005. Hanno autorizzato interventi DEV delimitati e documentati in #148/PR #150; il divieto DEV della sola DECISION-061 non va applicato retroattivamente a tali interventi. Ogni nuova operazione runtime richiede comunque il proprio gate applicabile. Il consolidamento GitHub corrente (#156, PR #149/#150/#159/#160) **non autorizza** merge, deploy, migrate sul DEV, modifica di schema/ruoli, attivazione `cc_premium_primary` o produzione. Consultare sempre le decisioni canoniche HITCH e l'issue attiva: questo riepilogo non conferisce nuovi permessi.





## Documentazione upstream e verifica della versione pinned

Questa regola vale per **tutti i macro-goal** del progetto, inclusi GOAL-01, GOAL-02, GOAL-03, GOAL-04 e GOAL-05.

Per ogni funzione o integrazione che dipende da Frappe, ERPNext, Healthcare/Marley, Builder o altre dipendenze upstream, Codex deve:

1. consultare la documentazione ufficiale pertinente prima di introdurre comportamento custom o assumere semantica nativa;
2. verificare che la documentazione sia compatibile con la **versione effettivamente pinned** nel progetto;
3. quando la documentazione non è sufficiente o può riferirsi a una versione diversa, verificare anche il codice sorgente ufficiale della versione/tag/commit pinned;
4. confermare sul runtime pinned i comportamenti critici che non sono dimostrabili in modo affidabile dalla sola documentazione o dal solo sorgente;
5. preferire API, hook, DocType, workflow e punti di estensione ufficialmente supportati rispetto a patch, monkey-patch o dipendenze da dettagli interni non garantiti;
6. documentare in issue/PR/evidenza ogni divergenza significativa tra documentazione ufficiale, sorgente pinned e comportamento runtime osservato.

Ordine di autorità:

- le decisioni business e di delivery approvate per HC-0005 definiscono **cosa** il sistema deve fare;
- la documentazione ufficiale e il sorgente upstream pinned definiscono il comportamento tecnico supportato e i meccanismi disponibili;
- l'evidenza runtime della versione pinned verifica **come** quel comportamento opera realmente nel nostro ambiente;
- una fonte upstream non può sovrascrivere una decisione business approvata;
- se documentazione, sorgente pinned e runtime sono in conflitto materiale, Codex deve fermarsi, produrre evidenza e richiedere una decisione invece di inferire silenziosamente.

Non usare automaticamente la documentazione della versione più recente come prova valida per una versione pinned precedente.

## Git workflow

- una issue per unità di lavoro;
- branch suggerito: `issue-<n>/<slug>`;
- nessun lavoro diretto su `main` dopo il bootstrap iniziale;
- PR obbligatoria;
- niente merge se gli acceptance criteria critici non hanno evidenza;
- evitare commit che mescolano refactor non richiesti e feature;
- documentare migrazioni e cambi schema.

## Evidenze minime in PR

- issue collegata;
- runtime/versioni usate;
- file/moduli cambiati;
- comandi principali eseguiti;
- test automatici;
- test manuali rilevanti;
- risultato `PASS / PARTIAL / FAIL`;
- rischi o unknown residui;
- screenshot/log sintetico solo quando utile e senza dati sensibili.

## Confine ChatGPT ↔ Codex

ChatGPT prepara architettura, issue, acceptance criteria e review.
Codex esegue runtime, implementazione e test.
GitHub è il canale di coordinamento.

Se una decisione architetturale non è ancora definita, Codex deve produrre evidenza e una **raccomandazione**, non trasformarla autonomamente in decisione finale.

## Implementation mode — HC-0005

L'implementazione del MVP Centro Change è autorizzata dal gate HC-0005 DECISION-052.

Prima di scrivere feature code, Codex deve chiudere `WP-00 / M0 — Reproducible Clean Runtime` (issue #21).

Le 40 capability storiche sono evidenza architetturale da riusare: non vanno ridiscusse da zero, ma i relativi scenari decisivi devono diventare regression test del prodotto quando pertinenti.

Le capability Finance/Admin `CC-CAP-041..050` derivano dal delivery design approvato e richiedono nuova implementazione/evidenza.


## Macro-goal execution — STORICO DI INIZIO OTTOBRE, NON GATE ATTIVO

**Questa sezione in origine indicava GOAL-02 (#23) come current macro-goal della roadmap MVP del 03/10/2026. È una fotografia storica e non comanda più il lavoro funzionale odierno.** La rotta attiva e i suoi gate sono nel [registro operativo](docs/qa/ACTIVE-GOAL-ROUTER.md). Le decisioni storiche DECISION-055 e DECISION-056 restano tracciate nel percorso MVP, ma non permettono di saltare #173 o avviare 03/04/05 macro né gli AUDIT 06/07. Codex continua a lavorare in autonomia all'interno del GOAL *attivo e autorizzato* secondo SOP v1.1, fermandosi soltanto ai gate materiali. Nessun merge o produzione automatica.


## Cross-client Goal Learning Extraction

Per la policy HITCH approvata, questo progetto partecipa alla knowledge base tecnica:

`2008hitch-afk/erpnext-frappe-delivery-knowledge`

Alla fine di ogni macro-goal ERPNext/Frappe, Codex deve eseguire una **Goal Learning Extraction**.

Deve:

1. rileggere issue, PR, test, failure, fix e fonti upstream usate nel goal;
2. estrarre soltanto conoscenza tecnica generalizzabile;
3. eliminare nomi, client_id, regole business, URL del progetto cliente, dati personali, secret e dettagli identificativi;
4. creare/aggiornare esclusivamente learning con `status: CANDIDATE` sotto `learnings/candidates/` del repository comune;
5. usare il template e la governance del repository comune;
6. dichiarare `NO_GENERALIZABLE_LEARNING` nel completion report se non emerge nulla di riutilizzabile;
7. non promuovere mai autonomamente un learning a `APPROVATO`.

Nei nuovi lavori è consentito consultare come generalized learning soltanto elementi `APPROVATO`; essi restano consultivi e devono essere verificati rispetto a documentazione ufficiale, sorgente pinned e runtime corrente.


## GOAL-02 startup overlay

GOAL-02 is authorized by HC-0005 DECISION-056.

At GOAL-02 startup Codex must:

1. treat GOAL-01 as the accepted DEV baseline;
2. inspect `2008hitch-afk/erpnext-frappe-delivery-knowledge/learnings/approved/`;
3. load only generalized learnings explicitly approved there and pertinent to the current UAT-readiness work;
4. keep generalized learnings advisory and reverify version-sensitive behavior against official upstream documentation, pinned source and runtime;
5. use synthetic deterministic demo/UAT data only;
6. produce a named reproducible UAT candidate, client validation guide, known-limitations register, evidence package and GOAL-02 Completion Report;
7. perform Goal Learning Extraction before proposing GOAL-02 Done.

No production, real data, provider credentials, real SdI/TS traffic, GOAL-03 execution or automatic stack merge is authorized by DECISION-056.
