# Centro Change — Matrice requisiti ↔ UI Premium ↔ backend (audit #157)

## ATTIVAZIONE OWNER AUDIT-06 — 27/10/2026 (perimetro isolato, nessun DEV)

- L'Owner ha detto **«Ok procediamo»** dopo la rinumerazione consecutiva della roadmap. È aperta l'[Issue **#177 — AUDIT-06 Servizi/catalogo/prezzi/disponibilità**](https://github.com/2008hitch-afk/centrochange_core/issues/177) come unico GOAL attivo per analisi, sviluppo su branch dedicato, CI e UAT su ambiente isolato secondo SOP v1.1. **Nessuna installazione DEV, nuovo container/VPS, schema/DocPerm/ruoli, dati, merge o produzione autorizzati**. In mancanza di gate DEV esplicito, uscita `READY_FOR_DEV_GATE`, non `PASS_DEV`.
- [**PR #176**](https://github.com/2008hitch-afk/centrochange_core/pull/176) mantiene la nuova numerazione consecutiva 01–14 (finanza 12, compensi/fiscale 13); è **DRAFT/UNMERGED**, e l'esecuzione di #177 non la autorizza al merge. Riconciliare roadmap e baseline prima di pubblicare PR di prodotto.
- Restano veri i merge già verificati #172→#175→#174 su `main` `39be56b`; il DEV non ha automaticamente ricevuto quella HEAD. La matrice CSV 110×18 non cambia per la sola attivazione del GOAL.

> **DECISIONE OWNER VIGENTE — 27/10/2026: ROADMAP AUDIT 01–14 CON NUMERAZIONE CONSECUTIVA.** Gli AUDIT precedentemente etichettati 10, 11, 12 e 13 diventano rispettivamente 08, 09, 10 e 11; quelli finanziari precedentemente 08 e 09 diventano **12 e 13**, subito prima di **14**. Gli AUDIT 01–07 e 14 restano invariati. Fonte: [tabella canonica sezione C](#c-indice-audit--numerazione-canonica-consecutiva-01-14). I riferimenti ai vecchi numeri nei checkpoint già pubblicati sono **storici**, non nuove autorizzazioni. I 110 requisiti/18 colonne del CSV restano invariati. Nessun nuovo AUDIT, deploy DEV/prod o merge implicitamente autorizzato.

## DECISIONE OWNER — 27/10/2026: RINUMERAZIONE DELLA ROADMAP FUTURA

L'Owner ha **precisato e sostituito** la precedente istruzione di riordinare senza rinumerare: i numeri **DEVONO essere consecutivi 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14**. Finanza (ex 08) è **AUDIT-12** e Compensi/fatture passive/SdI/TS (ex 09) è **AUDIT-13**; entrambi vengono dopo Primo incontro pubblico (ora **AUDIT-11**) e prima della UAT finale (**AUDIT-14**). Tutte le altre etichette future seguono la conversione qui registrata:

| Vecchio AUDIT (roadmap 27/10 prima della rinumerazione) | Nuovo AUDIT | Area |
|---|---|---|
| 10 | **08** | Report e dashboard |
| 11 | **09** | Archivi (11 liste e 11 schede) |
| 12 | **10** | Gestione accessi e registro modifiche |
| 13 | **11** | Primo incontro pubblico (Guest) |
| 08 | **12** | Finanza, fatture, incassi e banca |
| 09 | **13** | Compensi, fatture passive, SdI/TS e coda amministrativa |

**Regola di continuità:** il codice attuale identifica l'area nella roadmap corrente, mentre la vecchia etichetta compare soltanto per rintracciare documenti e discussioni storiche. Non rinominare Issue GitHub, report, commit, prove o GOAL già completati; non fare sostituzioni globali nei documenti cronologici. Una sola area alla volta; nuovo AUDIT-06 non autorizzato. Nessun cambiamento a requisiti, scope, test, ruoli, schema, runtime e CSV. PR #172, #175 e #174 già MERGED su `main` `39be56b`, Issue #171/#173 chiuse, nessun nuovo deploy implicito.

## CHECKPOINT STORICO PRE-MERGE — 27/10/2026: CORE #173 `OWNER_ACCEPTED_SCOPED_CORE173`

Conferma formale dell'Owner [Issue #173 #6440597230](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6440597230) dopo completamento walkthrough UX e riconciliazione tecnica AGY: **«Chiudi la mia giornata» e recupero arretrati** accettati nel solo perimetro DEV `b498ea5`. Nel [CSV](FUNCTIONAL-COVERAGE-DETAIL.csv), **4 ID** mappati al percorso CORE #173 diventano `OWNER_ACCEPTED_FUNCTIONAL_LIMITED`: `CC-CAP-014` (pagamento operativo e settlement), `CC-CAP-022` (chiusura e recupero tardivo, **non tutta la riapertura**), `CC-CAP-024` (Auto Locked ore 07 con audit e recupero, **non reminder end-to-end**), `CC-ACT-004` (chiusura con Svolta/Pagata/metodo), con evidenze e lacune residue esplicite. Le altre righe, come `CC-CAP-023` reminder ore 21, `CC-CAP-025` regole disdetta 48h, `CC-CAP-029` export/stampa/email globali, rimangono nello stato precedente.

**Invarianti:** 110 righe, 18 colonne, 110 ID unici; tecnici **12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED**; Owner **92 PENDING / 16 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV**. `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` indica precisamente il sottoperimetro della nota; non trasforma tutto il requisito in PASS. Nessun merge consentito: PR #172/#175/#174 DRAFT/UNMERGED, review formalizzata ma indipendenza effettiva da attestare prima del gate merge, nessuna produzione o AUDIT-06 autorizzati. La [rotta operativa](ACTIVE-GOAL-ROUTER.md) prevale sui checkpoint storici sotto.

---

## CHECKPOINT STORICO — 26/10/2026

- [AUDIT-05 #171 OWNER_ACCEPTED_SCOPED](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6427680735): accettazione limitata al perimetro Professionisti validato; nel CSV soltanto `CC-CAP-002`, `CC-EXT-004`, `CC-EXT-009`, `CC-CAP-028` ora `OWNER_ACCEPTED_FUNCTIONAL_LIMITED`. Le restanti righe trasversali restano parziali/pending.
- [CORE #173 DEV_INSTALL_ALLOWED_CONDITIONAL](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427702903): immagine esatta `cc173-day-closure:d500fff` su `d500fff45cc5ca70c5ef33575aac4e58d4fed505`, solo sei servizi applicativi DEV; vietati merge, prod, schema/DocPerm, ruoli e dati storici. **NON ancora DEV installato/OWNER_ACCEPTED CORE**. PR #175 DRAFT, #172 DRAFT, #174 docs-only DRAFT.
- Stati tecnici invariati `12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED` (110 requisiti). Conteggio campo `Owner` **96 PENDING / 12 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV**.
- [Checkpoint corrente completo](CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md) prevale su stati/commit/gate **storici** riportati sotto. Nessun GOAL successivo in valutazione.


## CHECKPOINT CORRENTE — 26/10/2026: AUDIT-05 #171 → CORE #173 (solo fase attuale)

**LEGGERE PRIMA:** [Current Phase — Audit05 / CORE173](CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md) e la [matrice CSV 110 requisiti](FUNCTIONAL-COVERAGE-DETAIL.csv) dello stesso commit. Questa sezione **prevale sugli addendum storici sotto**, che descrivono commit e gate precedenti. Nessuna analisi dei GOAL successivi è inclusa in questo checkpoint; le loro righe restano preservate senza essere rivalutate.

- **Stato tecnico esatto CSV #172:** **12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED = 110**, zero duplicati, 18 colonne invarianti. **Stato Owner distinto**: 100 PENDING, 8 OWNER_ACCEPTED_FUNCTIONAL_LIMITED, 1 OWNER_ACCEPTED, 1 OWNER_APPROVED_DEV. Questi conteggi non sono percentuali di prodotto completato.
- **Perché differiva:** la matrice precedente su `main` aveva **11/59/29/11**, mentre il primo addendum della PR #172 riportava **11/61/27/11**. Quest'ultimo era **testualmente obsoleto**: il CSV attuale della PR #172 ha 12/60/27/11. Non modificare status funzionali sulla base della sola differenza tra branch.
- **#171 AUDIT-05:** Issue OPEN, PR #172 DRAFT/UNMERGED HEAD `a3e41a10287639a7c200992e45c3173b8ea33b46`, [CI #40374937104](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40374937104) SUCCESS. DEV installato secondo [rapporto AGY](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6423949297); UAT Owner [#35](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424029516), [#36](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424060422), [#37](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424126085), [#38](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424152452) PASS **visivi e circoscritti**. [#39](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424190750): nota di Auto Locked non prevista per account Manager, recheck Professional o prova browser tecnico ancora da attestare; review GitHub formale non presente. **Owner acceptance #171 ancora PENDING**. Nessun merge/prod.
- **#173 CORE:** «Chiudi la mia giornata» e recupero tardivo senza sblocco quotidiano della Direzione **APPROVATI COME REQUISITI MA NON IMPLEMENTATI** al checkpoint. [Mandato esecutivo](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839) inviato ad AGY; esecuzione sequenziale solo dopo gate #171. Non usare lo stato `Auto Locked` legacy per dichiarare la funzione già svolta. Nuovo gate DEV separato.
- **Stati affidabili:** `PASS_TECHNICAL_CLONE` (API/DB isolati) ≠ `PASS_DEV_READ_ONLY` ≠ `PASS_OWNER_VISUAL` ≠ `OWNER_ACCEPTED` ≠ `MERGED` ≠ `PRODUCTION`.


## AUDIT-05 Professionisti — checkpoint tecnico #171 (24/10/2026)

La [PR DRAFT #172](https://github.com/2008hitch-afk/centrochange_core/pull/172) verifica directory, scheda, modifica scoped e **account Professionista** secondo i due addendum Owner della [Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171). L'oracle completo è nel [rapporto AUDIT-05](AUDIT-05-PROFESSIONALS.md). Il clone Frappe/MariaDB isolato ha provato chiusura pagata/non pagata, disponibilità propria, note riservate, reminder/lock con clock controllato, segregazione e report. La verifica dello SHA finale, la CI, la review indipendente finale e il gate DEV restano separati; nessuna accettazione Owner è implicita.

Al **checkpoint storico iniziale** si indicavano **11 PASS, 61 PARTIAL, 27 NOT_TESTED, 11 BLOCKED** (testo non più coerente col CSV della PR). **Rettifica autorevole al 26/10: 12 PASS, 60 PARTIAL, 27 NOT_TESTED, 11 BLOCKED**; fare riferimento al CSV aggiornato e al checkpoint di fase sopra. `CC-CAP-023/024` passano da `NOT_TESTED` a `PARTIAL` per i test temporali reali sul clone, mentre l'esecuzione del scheduler nel DEV resta da dimostrare. Le altre righe mantengono lo stato precedente con evidenze più precise; i requisiti trasversali non sono promossi a PASS sulla sola prova account.

## Addendum Owner UAT — AUDIT-04 Pazienti accettato funzionalmente (24/10/2026)

**Decisione Owner verificata:** «Tutto confermato procediamo». Accettazione tracciata nella [Issue #167](https://github.com/2008hitch-afk/centrochange_core/issues/167#issuecomment-6380921234), dopo walkthrough sulla **versione installata nel DEV**: PR #168 commit **applicativo** `114301effda320f1f4991e672444761d91b76bef`, immagine `sha256:c00dd69af4a0865aa37b9a5db50d0bfa739d065a0a37cad0bd076ea2cfb86091`. La CI sull'applicativo è SUCCESS; test browser/API **23 PASS, 17 SKIP previsti, 0 FAIL** sul clone Frappe/MariaDB, e smoke read-only sul DEV; backup cifrato/restore isolato/rollback readiness PASS secondo [rapporto Codex](https://github.com/2008hitch-afk/centrochange_core/issues/167#issuecomment-6380878876). L'accettazione Owner non equivale ad aver eseguito personalmente test di mutazione, segregazione API o contabilità: le prove mutative sono **PASS_ISOLATED_REAL**, non **OWNER_LIVE_WRITE_PASS**.

**Correzioni UX direttamente confermate dall'Owner:** UX-04-01 titolo paziente non duplicato, UX-04-04 plurali pacchetto, UX-04-06 azioni note, UX-04-08 storico singola seduta nello stesso drawer con ritorno/scroll, UX-04-09 un solo controllo ricercabile per professionista, UX-04-02 rimozione globale ricerca pazienti (ticket [#170](https://github.com/2008hitch-afk/centrochange_core/issues/170) chiuso). Apertura, consultazione e annullamento delle altre azioni Pazienti verificate visivamente; salvataggi complessi su clone isolato. Nessuna modifica autorizzata a pulsante blu o proposta UX-04-07 (rettifica identica).

**Matrice CSV:** 110 righe invariate, stati tecnici **11 PASS, 59 PARTIAL, 29 NOT_TESTED, 11 BLOCKED**. Otto righe `PASS` specifiche dell'area Pazienti (`CC-CAP-004/016/017/019/020`, `CC-ACT-001/002/003`) hanno ora Owner `OWNER_ACCEPTED_FUNCTIONAL_LIMITED`; il resto rimane con stato precedente e `OWNER PENDING` dove pertinente. Non promuovere a PASS i requisiti trasversali o non completamente esercitati: `CC-CAP-006.c` (storico oltre 100), `CC-CAP-018` (report/export privacy trasversali), `CC-CAP-005/033/038/039` (permessi e API su tutte le aree), anagrafiche/azioni fuori perimetro e processi contabili restano `PARTIAL` o `NOT_TESTED` secondo CSV.

**GitHub:** [PR #168](https://github.com/2008hitch-afk/centrochange_core/pull/168) ha integrato il codice routing della [PR #169](https://github.com/2008hitch-afk/centrochange_core/pull/169). Le due PR restano da disporre nel gate merge separato autorizzato dall'Owner, che richiede controllo dell'ultima HEAD e della CI; nessuna produzione né nuovo deploy DEV. Reviewer indipendente dichiarato PASS nel report Codex; nessuna review GitHub formale era presente al checkpoint di verifica. Tracker generale #156 non leggibile con l'identità attuale (GET 404): non dichiararlo aggiornato. Prossima area, dopo chiusura corretta AUDIT-04: **AUDIT-05 Professionisti e accessi per professionista**; non già iniziata.


## Esito installazione AUDIT-04 — 23/10/2026

La PR DRAFT #168 riconciliata con #169 è installata sul solo DEV come immagine `sha256:be800b7e2a72dc8e0d75b6d5fce205243cb0d8f2939b43d985dd7ef0247fe496` dal commit applicativo `373e6ccfa26ec86572c17c202b19c7ee2097fc02`. Gate cifrato, restore isolato, CI, UAT clone e smoke DEV: **PASS**. Owner UAT e merge: **PENDING**. La matrice CSV mantiene 110 righe e gli stati funzionali già circoscritti; le fotografie storiche sotto descrivono le fasi precedenti. [Rapporto finale](AUDIT-04-DEV-INSTALL-2026-10-23.md).

## Addendum UX-04 — 23/10/2026 (fotografia precedente all'installazione)

La prosecuzione Owner di #167 corregge tre difetti di presentazione: UX-04-01 titolo unico nella scheda Patient, UX-04-02 ricerca globale pazienti richiamabile dall'icona della topbar anziché campo permanente, UX-04-03 nomi Marley reali dove disponibili e riferimento opaco stabile per le anagrafiche sintetiche incomplete. Il Patient e il Customer restano distinti; gli ID canonici sono usati dalle API e non sono rinominati. L'Agenda riceve nome e cognome dei Patient presenti negli appuntamenti già autorizzati, senza dipendere dal bootstrap limitato a 500. La ricerca resta filtrata dal server per centro e ruolo. Dettagli e prove nel [rapporto UX-04](AUDIT-04-UX-REMEDIATION.md).

**Stato:** codice/test offline e Frappe isolato PASS; GitHub Actions `Offline premerge` PASS sul commit `5e23be2eacbf7259aef4ff5934ef538c7942152e` ([run 40019553473](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40019553473)). La HEAD dopo l’aggiornamento documentale richiede comunque checks PASS esatti. Candidato **non installato nel DEV**. Sul DEV è attiva la decisione `SINGLE_CLIENT_UI_PREMIUM_ONLY` da PR #169; prima di qualunque nuova immagine DEV occorre riconciliare il relativo routing con #168 e superare il gate di backup/restore/rollback della Issue #167. Nessun merge o switch è implicito.

La matrice CSV resta di 110 righe; le quattro righe toccate sono `CC-CAP-003`, `CC-CAP-019`, `CC-EXT-006` e `CC-EXT-019`. I conteggi di stato aggiornati sono **11 PASS, 59 PARTIAL, 29 NOT_TESTED, 11 BLOCKED**. `PASS` di una funzionalità Pazienti si riferisce soltanto al perimetro e alle prove indicate; Owner UAT resta `PENDING`.

## Addendum AUDIT-04 Pazienti — 23/10/2026

Issue [#167](https://github.com/2008hitch-afk/centrochange_core/issues/167), branch `issue-167/patients-audit`, baseline `main` `fa4ea4033e95301c25271d88d7d8c008b035f5c0`. Il candidato applicativo `c07b2c72eed7901abb51b0aac48e043df4b06c1f` è stato provato in un clone Frappe/MariaDB isolato con due centri e soli record sintetici. **Nessun deploy sul DEV condiviso e nessuna accettazione Owner.** Dettaglio e limiti nel [rapporto AUDIT-04](AUDIT-04-PATIENTS-TECHNICAL-REVIEW.md).

| Prova | Esito | Confine |
|---|---|---|
| Python offline, manifest, React typecheck/build | 72 PASS; source/image parity PASS | Verifiche codice/build, non collaudo DEV |
| Playwright sintetico | 132 PASS, 8 SKIP | Risposte simulate, non Frappe |
| Playwright Frappe/MariaDB isolato | 17 PASS, 15 SKIP per casi API desktop-only | Browser desktop 1440×900 e mobile 390×844; sette ruoli più Guest; centro A/B |
| Reviewer indipendente | Revisione statica `c07b2c7`; esito finale nel rapporto tecnico | CI GitHub e cleanup: vedere rapporto finale |

La matrice CSV mantiene 110 righe: **10 PASS, 59 PARTIAL, 29 NOT_TESTED, 12 BLOCKED**. `PASS` delle righe Pazienti significa prova tecnica nel perimetro #167, con Owner `PENDING`; i requisiti trasversali restano `PARTIAL` dove altri moduli o export non sono stati esercitati. Oltre 100 sedute, la UI dichiara il limite; la paginazione completa resta un gap distinto. La consultazione dopo l'ultima revoca è Manager-only nel centro autorizzato; l'operatività resta bloccata fino a una nuova assegnazione. Il backend conserva ID, permessi e fonte dati canonici.

## Addendum operativo verificato — 23/10/2026 (AUDIT-03)

Questo addendum **prevale per lo stato operativo** sui checkpoint storici AUDIT-00/01/02 del 22/10 sottostanti; non sostituisce i requisiti né trasforma evidenza parziale in PASS.

| Sequenza | GOAL / interfaccia | Stato aggiornato e gate |
|---|---|---|
| 01 | Login/autenticazione #158 | PR #160 integrata in `main`; UAT Owner limitato; gli eventuali scenari non provati restano tali |
| 02 | Shell/navigazione/ricerca #161 | **AUDIT-02 completato**, PR #163 integrata, fixture cleanup registrato |
| 03 | Agenda/prenotazioni #164 | **OWNER_ACCEPTED funzionale il 23/10**: Agenda e dettaglio/spostamento visti e approvati manualmente; deroga economica DECISION-032 accettata sulla base di UAT automatico su Site isolato, senza riproduzione manuale del popup sul DEV. PR **DRAFT #166**, SHA `e5b688a93b9218ed46091966bd794823a14e2274`, **non integrata**; DEV aggiornato secondo rapporto Codex. Lo stato `DONE` formale e il merge restano soggetti a gate separati |
| 04 | Pazienti, storico, assegnazioni, note e pacchetti | **QUEUED / non avviato**; prossimo GOAL proposto dopo chiusura formale AUDIT-03 e specifica autorizzazione Owner |
| 05–14 | Aree successive | Non iniziate come GOAL verticali in questo ciclo; mantenere l'ordine previsto sotto salvo decisioni Owner sulle dipendenze |

**Evidenze AUDIT-03:** [PR #166](https://github.com/2008hitch-afk/centrochange_core/pull/166), [commento Owner](https://github.com/2008hitch-afk/centrochange_core/pull/166#issuecomment-6368684104); CI automatico e manuale PASS dichiarati e commit CI automatico verificato; UAT browser reale su **copia isolata** con debiti fatturati/non fatturati, CSRF, autorizzazioni, audit e retry; eliminazione copie per ID; backup/restore e promozione dell'immagine DEV `sha256:b48f73861b5fa53a6c1b79d874409ae4f08dfbcd9d3e87621b19285c094095a6` documentati in PR. Sul DEV soltanto smoke e regressioni non mutative, **nessuna fixture contabile persistente**; lo specifico caso cross-center HTTP/CSRF congiunto rimane `NOT_TESTED`. La dichiarazione di reviewer indipendente PASS è nel rapporto Codex, ma **nessuna review GitHub formale** compare nella PR #166 al checkpoint.

**Confini:** l'accettazione funzionale Owner **non autorizza** automaticamente merge, produzione, attivazione `cc_premium_primary=1`, schema/DocPerm/ruoli, né il GOAL #04. Per chiudere #164 verificare report UAT finali, evidenze reviewer, stato fixture/DEV, aggiornamento matrice/tracker #156 e ottenere autorizzazione specifica al merge. Il 404 su Issue #164/PR #165 va trattato come limitazione di accesso, non prova della loro inesistenza.

**Stato storico AUDIT-00:** `AUDIT-00_COMPLETE / BASELINE_OPERATIVA_APPROVATA / PR_159_DRAFT_UNMERGED` — 22/10/2026. L'Owner ha autorizzato l'avvio del ciclo per interfaccia; **non** ha approvato come PASS le singole funzionalità, il merge della PR o il passaggio in produzione.
**Master:** [#156](https://github.com/2008hitch-afk/centrochange_core/issues/156) · **Inventario:** [#157](https://github.com/2008hitch-afk/centrochange_core/issues/157) · **Prima area:** [Login #158](https://github.com/2008hitch-afk/centrochange_core/issues/158).
**Regola:** questa matrice è un **indice verificabile di ciò che va controllato**, non un certificato di completezza, UAT o conformità. NESSUNA area è ancora `OWNER_DONE`.

**Dettaglio per funzione:** [110 righe CSV](FUNCTIONAL-COVERAGE-DETAIL.csv), con fonte, decisione, perimetro, UI/API/backend separati, DocType, ruoli, dipendenze, prova, stato, issue, gap e approvazione Owner. [Inventario delle schermate, controlli e 11 archivi](PREMIUM-REACT-INTERFACE-INVENTORY.md). I 50 ID originari sono tutti presenti: `CC-CAP-006` è scomposta in prenotazione, spostamento/cancellazione e storico; 28 requisiti/limiti successivi `CC-EXT-*` coprono decisioni, UAT e vincoli che non erano nell'indice iniziale; 30 azioni `CC-ACT-*` scompongono processi composti. **110 righe ≠ 110 nuove funzionalità approvate**: alcune sono escluse, rinviate, gate o verifiche trasversali.

| Stato puntuale | Righe | Significato in questo audit |
|---|---:|---|
| `PASS` | 2 | Solo due percorsi UAT mirati, con prova `LIVE-22` precedente; Owner ancora `PENDING` |
| `PARTIAL` | 61 | Codice e/o prove parziali; manca almeno una verifica del requisito completo |
| `NOT_TESTED` | 35 | Nessuna prova specifica sufficiente per l'azione o il processo |
| `BLOCKED` (storico) | 12 | **8 fuori perimetro/rinviati/sostituiti**, **3 non autorizzati**, **1 gate di attivazione React in attesa Owner**. Nessuno equivale automaticamente a difetto |
| `FAIL` | 0 | Nessun difetto funzionale riprodotto in questo audit documentale |

## A. Fonti e baseline

1. [Discovery — CLIENT-REQUESTS-SNAPSHOT](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/discovery/CLIENT-REQUESTS-SNAPSHOT.md), richieste originali e loro stato; molte voci erano ancora `DA VALIDARE` in discovery.
2. [MVP capability map](../MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml) — scope tecnico, `active`, `deferred`, `historical_replaced` al 03/10; non sostituisce decisioni successive.
3. [Finance/Admin delivery plan](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/delivery/DELIVERY-PLAN-WORK-PACKAGES-001.md) e [solution baseline](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/solution/EXECUTABLE-SOLUTION-BASELINE-001.md), capability 041–050.
4. [React #148](https://github.com/2008hitch-afk/centrochange_core/issues/148) / [PR draft #150](https://github.com/2008hitch-afk/centrochange_core/pull/150) / branch `issue-148/premium-react-frontend`: [React coverage](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/FUNCTIONAL-COVERAGE.md), [API/roles](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/API-ROLE-CONTRACT-MATRIX.md), [11 native list/form](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/NATIVE-ROUTE-DISPOSITION.md).
5. [UAT Owner storica #136](https://github.com/2008hitch-afk/centrochange_core/issues/136), [test UAT #137](https://github.com/2008hitch-afk/centrochange_core/issues/137), [React DEV delivery report](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/DECISION-066-DEV-DELIVERY-REPORT-2026-10-21.md) e [fixes live 22/10](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/UAT-PRIORITY-FIXES-LIVE-2026-10-22.md).
6. [HITCH HC-0005 decisions 003–066](https://github.com/2008hitch-afk/hitch-client-discovery/tree/main/clients/HC-0005/decisions), in particolare 003–012, 018, 027–034, 045, 053–054, 059–066. Discovery è **indice non contrattuale**; decisioni approvate e delivery successiva prevalgono. [AGENTS](../../AGENTS.md), [README](../../README.md), [Architecture](../../ARCHITECTURE.md), [Security](../../SECURITY.md), roadmap e codice API/DocType nella PR #150 completano il tracciato.

### Gerarchia delle decisioni per evitare falsi gap

| Tema | Stato vigente | Fonte |
|---|---|---|
| Primo rilascio operativo completo, una webapp, un modello multi-centro; master centrali Patient/Practitioner; catalogo centrale e tariffa del centro | Approvato | DECISION-003–009 |
| Ledger pacchetti, pagamento operativo distinto dall'accounting, confine 48h esatto in Europe/Rome, visibilità paziente fra centri limitata | Approvato | DECISION-010–012, 018 |
| Finance/Admin core: fatture, banca import manuale, compensi, XML passivi, reporting standard, documenti; SdI/TS con adapter simulati e TS ordinario in core | Approvato nei limiti delle policy, senza provider reale | DECISION-027–034, 045 e delivery 041–050 |
| Snapshot prezzo alla **data prenotazione**; soglia sedute non pagate parametrica per coppia paziente+professionista | Approvato | DECISION-053–054 |
| Correzione retroattiva dell'orario seduta (#78) | Rinviata; DECISION-058 non conferisce più autorità implementativa | DECISION-059 |
| React Premium, una sola installazione DEV; attivazione come interfaccia principale | UI/DEV autorizzati, routing `cc_premium_primary=1` solo dopo accettazione visiva Owner | DECISION-060–062, 064–066 |
| API scoped catalogo, tariffe, template, anagrafiche, pagamenti lettura, stampa | Approvate con whitelist, permessi server, audit; create standalone Patient/Practitioner/Item, Payment Entry allocation e mapping Customer arbitrario non autorizzati | DECISION-063 |
| Sito pubblico completo, provider/POS, payment links, OCR, dashboard di contabilità gestionale avanzata, analytics cliniche | Rinviati/esclusi dal core corrente | Capability map e DECISION-031–034 |

### Baseline e limiti della verifica odierna
- Al checkpoint GitHub di questo audit, la **PR #150 è open/draft/unmerged**, HEAD GitHub `96cecfc746cacba42aa25fbea2170736f6217821` (non dare per scontato che `main` abbia React).
- Il report dell'ultimo fix indica sorgente prodotto installato `749eef346e9d259ce59266a5455311b45d498a76`, immagine `sha256:54db4262375457bee60f497029f8cf05f38e99bfab6ec9caa6762078a5f74b6f`, runtime DEV e QA live **PASS nel perimetro provato**, `cc_premium_primary=0`, PR ancora draft. `git diff 749eef3..96cecfc` mostra solo report, screenshot e `frontend/premium/tests/live.spec.ts`: **nessun file applicativo o asset sorgente differisce** tra image-source e HEAD PR. Il manifest dell’immagine non è stato ricalcolato in AUDIT-00. Lettura locale **non mutativa** del 22/10: nove container `centrochange-dev` attivi, sei applicativi con immagine corrispondente; Site `centrochange.local`, flag sintetico true e `cc_premium_primary=false`. `HEAD /premium` come Guest risponde 301 verso `/login?redirect-to=/premium`. Non sono stati eseguiti login, POST o test funzionali sul runtime in AUDIT-00.
- L'Owner riferisce che la UI Premium è terminata: **dichiarazione di completamento UI**, da distinguere dalla riconciliazione Git/ambiente, dall'audit dei requisiti e dalla formale accettazione di ciascuna interfaccia.
- I report storici che riportano `NOT_VERIFIED` per le suite live precedono la consegna documentata il 22/10; non ricopiare tali limiti come stato corrente senza data/commit. I PASS live globali non provano automaticamente ogni singola riga della presente matrice.

## B. Codici di stato e policy

**Scope:** `BASE` = attivo nella capability map originale; `FIN` = Finance/Admin approvato nella delivery; `DEF` = differito nella baseline originale, da rivalutare con decisioni successive; `SOST` = sostituito; `EXCL` = escluso nell'ambito storico. Le autorità HC-0005 approvate più recenti prevalgono.

**Ricognizione UI:** `INDICATA` = il codice/documentazione React contiene un percorso plausibile, **non** significa funzione approvata; `DA_RICONCILIARE` = esiste flusso limitrofo o report con gap; `NO_UI` = lavoro infrastrutturale/di backend; `NON_RILEVATA` = nessuna corrispondenza puntuale stabilita.

**Separazione fondamentale per ogni prossima interfaccia:** lo **scope del requisito** (`APPROVATO`, `RINVIATO`, `ESCLUSO`, `NON_AUTORIZZATO`, `DA_VALIDARE`) è indipendente dall'**esito della verifica** (`PASS`, `FAIL`, `PARTIAL`, `NOT_TESTED`, `BLOCKED_BY_DEPENDENCY`). Le 12 righe storicamente etichettate `BLOCKED` conservano tale valore nel CSV come dato di AUDIT-00, ma durante l'audit per-area devono essere riportate nel registro di scope appropriato e **non conteggiate come 12 errori**. Le capacità `DA_VALIDARE` non autorizzano implementazioni finché l'Owner non ne conferma il perimetro.

**Verifica:** i prospetti D/E sono l'indice storico, con `AUDIT` come promemoria, non l'esito aggiornato. L'esito puntuale e l'approvazione Owner sono nel CSV. `PASS` vale solo per il controllo esatto associato alla prova indicata; `PARTIAL` include codice presente ma scenario non completamente verificato; `BLOCKED` identifica anche scope formalmente rinviato. Nessun esito `OWNER_DONE` in AUDIT-00.

## C. Indice AUDIT — numerazione canonica consecutiva 01–14

| AUDIT attuale | Interfaccia / area | Traccia React o integrazione | Issue | Stato verificato / gate |
|---:|---|---|---|---|
| 01 | Login e autenticazione | Login nativo Frappe `/login`, sessione e redirect verso `/premium`; logout in `frontend/premium/src/main.tsx` | [#158](https://github.com/2008hitch-afk/centrochange_core/issues/158) | PR #160 MERGED; issue #158 OPEN; Owner UAT limitato |
| 02 | Shell, navigazione, centro attivo e ricerca | `main.tsx`; shell/sidebar/header e fallback per ruolo | [#161](https://github.com/2008hitch-afk/centrochange_core/issues/161) | PR #163 MERGED; issue #161 CLOSED |
| 03 | Agenda e prenotazioni | `views.tsx`; `operations.workspace.*`, `scheduling.booking.*` | [#164](https://github.com/2008hitch-afk/centrochange_core/issues/164) | PR #166 MERGED; issue #164 OPEN; Owner acceptance scoped |
| 04 | Pazienti, storico, assegnazioni, note e pacchetti | `views.tsx`, `patient_assignments.tsx`, `patient_packages.tsx`, `note_history.tsx` | [#167](https://github.com/2008hitch-afk/centrochange_core/issues/167) | PR #168/#169 MERGED; issue #167 CLOSED; Owner acceptance scoped |
| 05 | Professionisti e accessi per professionista | `views.tsx`, `profiles.py`, `permissions.py`, `scoped_archive.tsx` | [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171) | PR #172 MERGED; issue #171 CLOSED; Owner acceptance scoped |
| 06 | Servizi/catalogo, prezzi e disponibilità | `views.tsx`, `scoped_archive.tsx` | Da creare | PIANIFICATO / NON AUTORIZZATO |
| 07 | Chiusure seduta, cancellazioni 48h, eccezioni, notifiche | Agenda, lifecycle, Notifiche; verificare i processi anche se distribuiti in più schermate | Da creare | PIANIFICATO / NON AUTORIZZATO; CORE #173 integrato in scope limitato, evitare duplicazioni |
| 08 | Report e dashboard | `views.tsx`, `finance_reports.tsx` | Da creare | PIANIFICATO / NON AUTORIZZATO (ex 10) |
| 09 | Archivi 11 liste + 11 schede e master-data editing | `scoped_archive.tsx`, `master_archive.tsx`; verificare permessi e completezza reali | Da creare | PIANIFICATO / NON AUTORIZZATO (ex 11) |
| 10 | Gestione accessi e registro modifiche | `views.tsx`, `audit_log.tsx` | Da creare | PIANIFICATO / NON AUTORIZZATO (ex 12) |
| 11 | Primo incontro pubblico (Guest) | `/premium-primo-incontro`, `first_meeting.tsx`, `public.tsx` | Da creare | PIANIFICATO / NON AUTORIZZATO (ex 13) |
| 12 | Finanza, fatture, incassi e banca | `finance_actions.tsx`, `finance_create.tsx`, `views.tsx` | Da creare | POSTICIPATO IN FONDO / NON AUTORIZZATO (ex 08); dopo #11, prima #13 e #14 |
| 13 | Compensi, fatture passive, SdI/TS e coda amministrativa | `finance_actions.tsx`, `finance_reports.tsx`, moduli finance | Da creare | POSTICIPATO IN FONDO / NON AUTORIZZATO (ex 09); dopo #12, prima #14 |
| 14 | Regressioni trasversali + UAT finale | Permessi, multi-centro, privacy, localizzazione, email/export/print, backup, performance | Da creare | UAT FINALE / NON AUTORIZZATO; solo dopo #12 e #13 |

**Precedenza:** questa tabella è il riferimento canonico per ogni NUOVO GOAL. Il numero storico si recupera nella corrispondenza della decisione all'inizio del documento; le etichette 08/09/10/11/12/13 dei documenti PRECEDENTI la rinumerazione non identificano automaticamente la stessa area della nuova roadmap. Una sola area `ACTIVE` per volta. I requisiti funzionali e le autorizzazioni pregresse restano invariati.

## D. Matrice delle capability originali (01–40)

Legenda colonne: `Rif.` ID in discovery e/o capability map; `Area` = destinazione per audit, non necessariamente una pagina autonoma; `Fonte` = sistema canonico previsto, da confermare a livello di campo; `UI` = ricognizione documentale preliminare; `Verifica` = NON ancora audit Owner per riga.

| Rif. | Scope | Funzione da dimostrare | Area | Fonte backend / dati candidata | UI | Verifica |
|---|---|---|---|---|---|---|
| CC-CAP-001 | BASE | Ambiente DEV isolato e riproducibile | Trasversale | Frappe/Compose | NO_UI | AUDIT |
| CC-CAP-002 | BASE | Professionisti, identità, stato | Professionisti/Accessi | User + Healthcare Practitioner | INDICATA | AUDIT |
| CC-CAP-003 | BASE | Anagrafica paziente, contatti e riferimenti amministrativi | Pazienti/Archivi | Marley Patient; mapping ERPNext ove previsto | DA_RICONCILIARE | AUDIT |
| CC-CAP-004 | BASE | Assegnazione/revoca/riassegnazione paziente | Pazienti/Accessi | CC Patient Assignment | INDICATA | AUDIT |
| CC-CAP-005 | BASE | Segregazione dati per professionista/centro | Tutte | Permessi Frappe + CC | NO_UI | AUDIT |
| CC-CAP-006 | BASE | Prenotare, spostare, cancellare, storico seduta | Agenda | Patient Appointment | INDICATA | AUDIT |
| CC-CAP-007 | BASE | Orari ricorrenti, ferie, assenze, eccezioni | Disponibilità | Practitioner Schedule/Availability | INDICATA | AUDIT |
| CC-CAP-008 | BASE | No doppia prenotazione stesso slot | Agenda | Booking service, Patient Appointment | INDICATA | AUDIT |
| CC-CAP-009 | BASE | Primo incontro pubblico consentito solo agli autorizzati | Guest | Public booking protetto | INDICATA | AUDIT |
| CC-CAP-010 | BASE | Sedute successive non prenotabili pubblicamente | Guest/Agenda | Public booking policy | INDICATA | AUDIT |
| CC-CAP-011 | BASE | Catalogo prestazioni/servizi | Servizi/Archivi | Item, Appointment Type, Center Service | DA_RICONCILIARE | AUDIT |
| CC-CAP-012 | BASE | Prezzi prestazioni | Servizi/Archivi | ERPNext Item Price | DA_RICONCILIARE | AUDIT |
| CC-CAP-013 | BASE | Snapshot immutabile durata/prezzo/servizio seduta | Agenda/Finanza | Patient Appointment + snapshot CC | INDICATA | AUDIT |
| CC-CAP-014 | BASE | Stato pagamento operativo informativo e metodo | Chiusure/Finanza | Stato seduta/settlement CC; distinto da contabilità | INDICATA | AUDIT |
| CC-CAP-015 | SOST | Percorso futuro verso accounting (baseline storica) | Finanza | Sostituito da 041–050 | NO_UI | SUPERSEDED |
| CC-CAP-016 | BASE | Pacchetti paziente: emissione, consumo, correzione | Pazienti/Pacchetti | CC Patient Package + ledger | INDICATA | AUDIT |
| CC-CAP-017 | BASE | Note organizzative | Pazienti/Agenda | CC Organizational Note | INDICATA | AUDIT |
| CC-CAP-018 | BASE | Note professionali riservate | Pazienti/Agenda | CC Private/Professional Note | INDICATA | AUDIT |
| CC-CAP-019 | BASE | Scheda paziente unificata | Pazienti/Archivi | Patient, appointment, package, note | DA_RICONCILIARE | AUDIT |
| CC-CAP-020 | BASE | Storico paziente e attività | Pazienti/Agenda | Patient Appointment + eventi audit | INDICATA | AUDIT |
| CC-CAP-021 | EXCL | Analytics cliniche / patient progress | Fuori MVP | Decisioni defer/esclusione | NO_UI | OUT_OF_SCOPE |
| CC-CAP-022 | BASE | Chiusura giornaliera, stati e riapertura | Agenda/Chiusure | Patient Appointment + lifecycle | INDICATA | AUDIT |
| CC-CAP-023 | BASE | Reminder sedute pendenti alle 21:00 | Notifiche/Processi | Worker/scheduler CC | DA_RICONCILIARE | AUDIT |
| CC-CAP-024 | BASE | Blocco automatico alle 07:00 | Agenda/Processi | Worker/scheduler CC | NO_UI | AUDIT |
| CC-CAP-025 | BASE | Disdetta entro/oltre 48h, debito e deroga auditata | Agenda/Finanza | Booking + economic disposition | INDICATA | AUDIT |
| CC-CAP-026 | BASE | Correzione/sblocco autorizzati con audit | Agenda/Accessi | Lifecycle + audit | INDICATA | AUDIT |
| CC-CAP-027 | BASE | Comunicazioni, reminder e notifiche operative | Notifiche | CC Notification + worker | INDICATA | AUDIT |
| CC-CAP-028 | BASE | Report operativi per ruolo | Report | Reporting CC | INDICATA | AUDIT |
| CC-CAP-029 | BASE | Export, stampa, email sicuri | Report/Finanza/Trasversale | API export/print/email con permessi | DA_RICONCILIARE | AUDIT |
| CC-CAP-030 | BASE | Dashboard gestionale | Report/Finanza | Aggregazioni autorizzate | INDICATA | AUDIT |
| CC-CAP-031 | DEF | Sito pubblico branded completo | Fuori area Premium / Guest | Website/brand; distinta da primo incontro #009 | DA_RICONCILIARE | SCOPE_REVIEW |
| CC-CAP-032 | DEF | Builder/Git pipeline originale | Trasversale | Build/versionamento | NO_UI | SCOPE_REVIEW |
| CC-CAP-033 | BASE | Permission model globale | Tutte | Permessi Frappe/CC | NO_UI | AUDIT |
| CC-CAP-034 | BASE | Audit immutabile azioni critiche | Registro | CC Audit Event + regole | INDICATA | AUDIT |
| CC-CAP-035 | BASE | Backup dati e configurazione | Trasversale | Backup site/files/config | NO_UI | AUDIT |
| CC-CAP-036 | DEF | Disaster recovery/restore testato | Trasversale | Recovery; report DEV già disponibili | NO_UI | SCOPE_REVIEW |
| CC-CAP-037 | DEF | Upgrade e migrazioni sicure | Trasversale | Frappe migration/rollback | NO_UI | SCOPE_REVIEW |
| CC-CAP-038 | BASE | Autorizzazione API e web endpoint | Tutte | Frappe API server-side | NO_UI | AUDIT |
| CC-CAP-039 | BASE | Anti-leakage API/query/report/export | Tutte | Test security Frappe/CC | NO_UI | AUDIT |
| CC-CAP-040 | BASE | Distribuzione da sorgente riproducibile | Trasversale | CI, immagini/versioni | NO_UI | AUDIT |

## E. Matrice Finance/Admin approvata (41–50)

| Rif. | Scope | Funzione da dimostrare | Area | Fonte backend / dati candidata | UI | Verifica |
|---|---|---|---|---|---|---|
| CC-CAP-041 | FIN | Ponte operativo-economico: paziente/cliente, professionista/fornitore, articoli e link seduta→economia | Finanza/Pazienti | Marley Patient/Appointment ↔ ERPNext Customer/Supplier/Item + CC Economic Link | INDICATA | AUDIT |
| CC-CAP-042 | FIN | Crediti, fatture attive, incassi, note di credito/rettifiche, insoluti | Finanza/Archivi | ERPNext Sales Invoice/Payment Entry | INDICATA | AUDIT |
| CC-CAP-043 | FIN | Import banca, riconciliazione e blocchi scaduti | Finanza/Banca | ERPNext Bank Transaction + regole CC | INDICATA | AUDIT |
| CC-CAP-044 | FIN | XML passivi, fornitori e approvazione controllata fatture passive | Finanza/Archivi | CC Incoming Invoice + ERPNext Purchase Invoice | INDICATA | AUDIT |
| CC-CAP-045 | FIN | Compensi professionisti attesi vs ricevuti, soglie e anomalie | Finanza/Report | CC Professional Expectation + Purchase Invoice | INDICATA | AUDIT |
| CC-CAP-046 | FIN | Coda amministrativa: eccezioni, responsabili, rinvii e audit | Finanza | CC Admin Exception | INDICATA | AUDIT |
| CC-CAP-047 | FIN | Report amministrativi, accessi contabili, audit e segregazione | Report/Finanza/Accessi | ERPNext GL/ledger + report protetti | INDICATA | AUDIT |
| CC-CAP-048 | FIN | Adapter SdI: stati, errori, retry, tracciabilità | Finanza/Trasmissioni | Adapter CC + Sales/Purchase Invoice | INDICATA | AUDIT_SIMULATO; LIVE_GATE |
| CC-CAP-049 | FIN | Adapter TS ordinario, eleggibilità/opposizione, correzioni e traccia | Finanza/Trasmissioni | Adapter CC + documenti fiscali | INDICATA | AUDIT_SIMULATO; LIVE_GATE |
| CC-CAP-050 | FIN | Collaudo finance integrato, UAT e release readiness | Trasversale | Test/recovery/evidenze | NO_UI | AUDIT |

**Nota sulle connessioni:** ad esempio `Patient`, `Customer` e i dati fiscali nelle fatture possono avere semantiche distinte: non aggiungere/duplicare campi senza verificare la fonte autorevole e gli snapshot storici richiesti. La mappatura DocType sopra è concettuale; i campi/API precisi devono essere documentati durante l'audit dell'area.

## F. Dettaglio completato e scheda di prova da allegare per ogni interfaccia

Il [CSV dettagliato](FUNCTIONAL-COVERAGE-DETAIL.csv) contiene già 110 righe, tutti i campi obbligatori e l'issue di provenienza. Le celle `PRESENT` significano presenza nel sorgente esaminato, non autorizzazione dimostrata o collaudo live. `LIMITED` indica solo una parte della funzione; `NONE` assenza di percorso; `N/A` non è un'interfaccia. `LIVE-21` e `LIVE-22` rimandano a report storici nominati nell'[inventario](PREMIUM-REACT-INTERFACE-INVENTORY.md); `MOCK` è solo prova con HTTP intercettato; `SRC` è ispezione statica. I due `PASS` riguardano esclusivamente griglia settimanale e navigazione/scheda professionisti provate nel report `LIVE-22`, sul candidato allora installato. Per questo HEAD il diff dal sorgente dell’immagine installata contiene solo prove/test/documenti; su una build applicativa successiva, riconciliare gli SHA.

Per la revisione di ogni riga, allegare una scheda di prova con:

| Campo | Valore richiesto |
|---|---|
| ID / autorità | Capability + decisione HC-0005 vigente + stato requisito |
| Area / URL / componente | Route reale, file React/controllo, azione operatore |
| Chi può / chi non può | Ruoli, centro, professionista, Guest, direct URL/API |
| Fonte dati | DocType/campo canonico; link tra modelli; snapshot autorizzati |
| Implementazione | UI `PRESENT / MOCK / MISSING`; endpoint `PRESENT / MISSING`; backend `PRESENT / MISSING` |
| Test verificabili | Caso positivo/negativo, device, Frappe live vs mocked, data, ambiente, SHA, logs/screenshot sanitizzati |
| Esito | `PASS / FAIL / PARTIAL / BLOCKED / NOT_TESTED` con motivazione |
| Correzione | Issue dedicata e PR, rischio schema/permessi, dipendenze, regressioni |
| Chiusura | CI PASS, merge autorizzato, build/dev allineati, Owner ACCEPTED |

Non considerare `PASS` un test non eseguito. Un endpoint HTTP 200 o uno screenshot non prova il processo end-to-end.

### Corrispondenza UI non dimostrata o limitata

| Requisito | Esito documentale / decisione necessaria |
|---|---|
| Creazione standalone Patient/Practitioner/Item; allocazione diretta Payment Entry; mapping fiscale Customer arbitrario | `BLOCKED`, fuori dal mandato DECISION-063. Backend può avere un vecchio intake Patient, ma non va esposto come nuovo workflow senza policy approvata. |
| Ricerca completa in ciascuno degli 11 archivi | `NOT_TESTED / DA_VALIDARE`: il filtro React agisce solo sulle pagine già caricate. Verificare aspettativa funzionale dell'Owner durante Archivi, senza inventare nuovo requisito. |
| Scheda completa Sales/Purchase Invoice e Bank Transaction negli Archivi | `NOT_TESTED / DA_VALIDARE`: il drawer usa la proiezione `finance.reporting.records`; le azioni sono nella sezione Finanza. Verificare campi e workflow richiesti nella singola interfaccia. |
| Consegna email/reminder ore 21 e auto-lock ore 07 | API/backend presenti, superficie di monitoraggio parziale. Job reali e confini di tempo `NOT_TESTED` in AUDIT-00. |
| Documenti non strutturati, allegati, handoff commercialista, email e stampe/esportazioni complete | Backend e ambito core previsti da DECISION-034; corrispondenza puntuale dei controlli React `NOT_VERIFIED` finché la relativa interfaccia non è auditata. La preview stampa scoped non copre ogni flusso documentale. |
| Alias demo per quattro Patient storici non nel manifest | `PARTIAL`, evidenza `LIVE-22`; non riscrivere ID o rinominare record senza prova di proprietà sintetica. |
| Correzione retroattiva orario seduta, sito pubblico branded completo, POS/feed bancario, payment links, OCR e analytics avanzate | Rinviati/esclusi; non sono difetti dell'attuale React MVP. |
| React come unica UI operativa primaria | Gate Owner visuale non superato: `cc_premium_primary=0`; non attivare nel lavoro #157. |

Il confronto con il modello dati esistente precede qualsiasi proposta futura: Patient e Practitioner sono Marley; Item/Item Price/Price List e documenti fiscali sono ERPNext; Branch/centro e membership sono Frappe/CC; note, package ledger, audit e bridge sono DocType CC. Non duplicare Customer, bilanci o snapshot storici. I ruoli nel CSV sono **contratti attesi**, non risultati di test multiruolo per ciascuna riga.

## G. Workflow Codex per interfaccia (ciclo replicabile)

1. Confermare commit/branch/immagine realmente serviti; **NON eseguire test mutativi** su dataset Owner prima di fixture isolata con cleanup verificato. Rispettare #148/DECISION-066 e gate successivi.
2. Leggere tutte le righe collegate alla schermata, inclusi ruoli, casi di errore, obblighi cross-screen e issue preesistenti.
3. Eseguire audit visivo/funzionale e backend, registrare ogni azione e relativi esiti con prove. Separare errore vero, mock, omissione, esclusione approvata e `NOT_TESTED`.
4. Creare/riusare issue correttive **solo per gap confermati**, con criteri di accettazione e dipendenze. Una sola interfaccia ACTIVE; non duplicare una issue già valida. #136/#137/#139/#148/#78 restano riferimenti esistenti, non da riaprire automaticamente.
5. Codex corregge, nella slice selezionata, `DocType/schema (se necessario) + backend/API + React + test`, verificando prima tutte le fonti dati esistenti, i contratti API e gli effetti sulle altre schermate.
6. Test/CI e review → PR piccole → merge approvato → distribuzione DEV solo se autorizzata → prova Owner. Report con SHA, CI/test, risultati e limiti.
7. Aggiornare matrice, issue #156 e issue area. Marcare `DONE` solo dopo criteri completi o defer approvato; **poi** passare alla prossima.

### Login — prime verifiche per #158
- `/premium` senza sessione → redirect login nativo Frappe; autenticazione corretta/errata; errori in italiano; logout; refresh, scadenza sessione, back/forward.
- Sessione server, cookie/CSRF; niente informazioni cliniche o contabili per utenti non autorizzati; accesso API diretto e hash manipolato.
- Routing per Manager, Secretariat, Professional, Finance, Accountant e Guest secondo decisioni/ruoli reali; cambio centro e autorizzazione coerente.
- Desktop/mobile, tastiera/focus, loading, feedback, regressione dalle altre route; screenshot non sensibili.
- Non creare una seconda login page React: verificare l'integrazione con Frappe. Nessun `PASS` senza prova sul candidato identificato.

**AUDIT-01, 22/10/2026, checkpoint tecnico precedente alla prova Owner:** [PR correttiva draft #160](https://github.com/2008hitch-afk/centrochange_core/pull/160), branch isolata sopra #150. Il [report live](https://github.com/2008hitch-afk/centrochange_core/blob/issue-158/login-auth-audit/docs/qa/AUDIT-01-LOGIN-2026-10-22.md) registra preflight, checkpoint cifrato nuovo `cc148-checkpoint-kwvawn4g`, **PASS_RESTORE reale** di Site e DB isolati, installazione dei soli sei servizi applicativi nell'unico DEV con immagine `sha256:569909d92601328a4f2f9cdef356fff547d84b28bc986321ff4aea30d9bca063`. Asset Login/React verificati via HTTP dal DEV senza intercettazioni o iniezioni nel browser. Playwright live **10/10 PASS** desktop/mobile: Guest, sette identità sintetiche, login valido/errato, redirect, refresh, route dirette, centri A/B e permessi campionati, CSRF, logout fallito/riuscito, cookie scaduto, sessione condivisa, italiano e grafica. Regressioni offline condivise **8/8 PASS**; typecheck/build PASS. Schema/indici e dati clinici/fiscali invariati dopo QA; solo sessioni/audit e stato login User cambiano. `cc_premium_primary=0`. A quel checkpoint `CC-EXT-001 = PARTIAL`, Owner `PENDING`; timeout reale di inattività, reset password via email e lockout `NOT_TESTED` senza provider/policy di test. PR #159/#160 DRAFT, nessun merge o avanzamento all'area 02.

**Riscontro Owner successivo:** [#158](https://github.com/2008hitch-afk/centrochange_core/issues/158) registra prova manuale DEV positiva per accesso, F5 ed Esci dopo ingresso in Agenda. `OWNER_UAT_PASS_LIMITED` vale **solo** per questi gesti; i test automatici multiruolo/negativi restano evidenza tecnica distinta. Timeout temporale reale, lockout e invio email reset rimangono `NOT_TESTED`, quindi `CC-EXT-001 = PARTIAL` e il campo Owner aggregato resta `PENDING`: non rappresenta un rifiuto dei tre gesti accettati. #158 resta aperta per gate d'integrazione e decisione sui controlli residui; [#161](https://github.com/2008hitch-afk/centrochange_core/issues/161) resta `QUEUED / NON AVVIATO`.

**AUDIT-02, 22/10/2026:** il testo precedente è un checkpoint storico. #149/#150/#159/#160 sono ora integrate in `main` a `335de5709e1c7b477be0b677f69913ecc2f6a9e6`; [#161](https://github.com/2008hitch-afk/centrochange_core/issues/161) è l'unica area `ACTIVE`. Il candidato shell corregge il filtro pazienti per centro anche per Manager, la ricerca globale, gli hash illeciti e la tastiera mobile. [Report per azione](AUDIT-02-NAVIGATION-REPORT.md) e CSV dettagliano prove offline e gate reali. `CC-EXT-002`, `CC-CAP-005/033/038/039` e `CC-EXT-026/027` restano `PARTIAL`: il DEV usa un'immagine precedente e le prove multiruolo/centro sulla nuova build sono `NOT_TESTED`. Nessuna accettazione Owner.

**Catena d'integrazione proposta, non eseguita:** PR documentale [#149](https://github.com/2008hitch-afk/centrochange_core/pull/149) → React [#150](https://github.com/2008hitch-afk/centrochange_core/pull/150) → Login [#160](https://github.com/2008hitch-afk/centrochange_core/pull/160). La presente [#159](https://github.com/2008hitch-afk/centrochange_core/pull/159) è documentale su `main` e può essere revisionata separatamente. Tutte sono DRAFT e non integrate. Simulazioni `git merge-tree` ai SHA correnti non rilevano conflitti tra `main` e #149/#150/#159/#160 o tra #159 e #160; un futuro merge richiede nuova verifica delle HEAD, review del diff #150 completo (397 file), rebase/retarget della base in ordine e autorizzazione Owner distinta. L'accettazione limitata del Login non equivale all'accettazione globale di #150.

## H. Regole anti-perdita di contesto

- **Una master:** #156. **Una matrice:** questo file. **Una area ACTIVE:** issue di audit dedicata. **Ogni fix:** issue figlia o issue già esistente + PR collegata.
- Alla fine di ogni sessione Codex aggiorna nel commento della issue attiva: commit/branch, risultato, test, evidenza, blocchi, prossimo passo concreto; il prossimo agente deve poter riprendere senza chat.
- Le PR aperte (compresa #150) non vengono automaticamente fuse per accelerare l'audit. Le decisioni di merge, uso server, cambio schema/policy, dati reali, provider e produzione mantengono i propri gate.
- Questo documento si aggiorna **insieme** alle prove dell'area, non prima di averle ottenute.
