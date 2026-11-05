# Centro Change — Missione C: Unified Desk experiment (C1 → C3)

**Documento:** `docs/plans/MISSION-C-UNIFIED-DESK-EXPERIMENT-2026-10-09.md`  
**Data:** 2026-10-09  
**Cliente:** HC-0005 — Centro Change  
**Owner authorization:** conferma esplicita **APPROVO** sulla proposta «Missione C con analisi, prototipo isolato e confronto completo, issue e PR DRAFT, senza cutover né modifiche UAT».  
**Tracking:** [issue #109](https://github.com/2008hitch-afk/centrochange_core/issues/109)  
**Status:** `OWNER_AUTHORIZED_FULL_UI_BUILD_AND_TEST` — precedente esperimento e suoi esiti storici preservati; vedi §7 (ampliamento Owner 2026-10-09). No architecture change/cutover.  
**Decisione vigente:** [HC-0005 DECISION-004](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-004-primary-operational-interface.md) — webapp operativa dedicata come interfaccia primaria; Desk per amministrazione/advanced.

## 1. Missione e risultati

Realizzare **un confronto concreto e verificabile** tra la webapp Centro Change attuale e un Unified Desk che riusi **nativamente** Frappe/ERPNext/Healthcare dove supportato, usando pagine custom soltanto quando serve. Il risultato finale autorizzato non è la sostituzione della webapp, ma un **prototipo funzionante isolato** e un confronto per la scelta Owner.

Non creare due database operativi permanenti, due workflow contabili o duplicazioni di business logic. Le transazioni devono riusare `centrochange_core` e i guard server-side, non aggirarli con UI.

### Roadmap ufficiale immutata

| Macro-goal | Stato formale |
|---|---|
| GOAL-01 [#22](https://github.com/2008hitch-afk/centrochange_core/issues/22) | OWNER ACCEPTED / DEV PASS |
| GOAL-02 [#23](https://github.com/2008hitch-afk/centrochange_core/issues/23) | AUTHORIZED_ACTIVE nella manifest HC-0005; issue GitHub chiusa tecnicamente; UAT/Owner final acceptance ancora pendente |
| GOAL-03 [#24](https://github.com/2008hitch-afk/centrochange_core/issues/24) | NOT_AUTHORIZED |
| GOAL-04 [#25](https://github.com/2008hitch-afk/centrochange_core/issues/25) | QUEUED |
| GOAL-05 [#26](https://github.com/2008hitch-afk/centrochange_core/issues/26) | QUEUED |

La Missione C non promuove automaticamente GOAL-02 né apre GOAL-03.

### Missioni tecniche

- **A [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95):** 35/35 merge codice prodotto su main verificati; clean G2D acceptance storica, main corrente `2fab181cd61cfc69e341d9fa1849038c6646e87e`.
- **B [#99](https://github.com/2008hitch-afk/centrochange_core/issues/99):** upgrade TARGET Frappe/ERPNext16.50.0, Healthcare16.6.1, Builder1.35.1 con `MISSION-B-R5-VALIDATION: PASS`; Finance9/9, browser14/14, backend240, HTTP55, hooks6, security38, real rollback189. Patch [PR #107](https://github.com/2008hitch-afk/centrochange_core/pull/107) e prove [PR #108](https://github.com/2008hitch-afk/centrochange_core/pull/108) rimangono **DRAFT/UNMERGED**. TARGET non è promosso all'UAT.
- **C (questa issue #109):** `OWNER_AUTHORIZED_EXPERIMENT_C1_C3`, non ancora implementata né completata.
- **D:** cutover e dismissione webapp, **NOT_AUTHORIZED**.

## 2. C1 — Matrice di fattibilità e architettura (primo output)

Codex legge prima il codice nel repo, i doctype, i servizi, i routes Frappe, gli hook, le permissions e le evidenze `docs/uat`, non inventa funzioni native. Per ciascuna superficie compila:

| Superficie | Webapp riferimento | Desk candidato da dimostrare | Esito |
|---|---|---|---|
| Login + menu per ruolo | login / Centro Change | Desk Workspace e accesso autenticato per profilo | DA VERIFICARE |
| Agenda settimanale e multi-professionista | Agenda RC22 | `CC_CUSTOM_DESK_PAGE` oppure nativo se provato equivalente | DA VERIFICARE |
| Prenotazioni, sedute, spostamento, annullamento, note | servizi operativi `centrochange_core` | moduli e azioni native/adattate oppure page | DA VERIFICARE |
| Pazienti / assegnazione / ricerca | vista pazienti UAT | nativo/adattato senza leakage centro/professionista | DA VERIFICARE |
| Professionisti / disponibilità | viste UAT | nativo/adattato dove adeguato | DA VERIFICARE |
| Fatture, crediti, incassi, banca, fornitori | Finanza UAT | liste native + workflow CC controllato | DA VERIFICARE |
| SdI e TS | simulazioni UAT | custom Desk Page con servizio canonico | DA VERIFICARE |
| Report ed export/stampa | viste e print UAT | report native/custom con pari restrizioni | DA VERIFICARE |
| Notifiche, accessi, audit | viste UAT | Workspace/custom Page, senza permessi tecnici elevati | DA VERIFICARE |
| Primo incontro pubblico | `/primo_incontro` | resta sito pubblico **fuori dal Desk** | ESCLUSO DAL CUTOVER DESK |

Per ciascuna riga associare `NATIVE`, `NATIVE_WITH_SUPPORTED_CUSTOMIZATION`, `CC_CUSTOM_DESK_PAGE`, `KEEP_WEBAPP` o `BLOCKED_NEEDS_OWNER_DECISION`; indicare API/DocType ufficiale versionato, differenze UX, guard server-side, test discriminante, sforzo qualitativo e rischio. Il benchmark UI è [Design System Centro Change v1](../ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md), non un generico Desk ERP.

**Gate C1:** la mappa prova fattibilità e priorità; niente automaticamente dichiarato nativo o risolto.

## 3. C2 — Prototipo isolato (solo se safety gate verde)

Target: una sola esperienza interna Desk Centro Change, con primo attraversamento **login/menu role-aware → Agenda → Pazienti → scenario Finance**. Aggiungere altre superfici per raggiungere confronto significativo quando supportate dai risultati C1, non inventare funzioni.

### Vincoli tecnici

1. Identificare esattamente il commit `main` e la base sperimentale da testare: PR #107 ancora draft/unmerged; non confondere codice MAIN/RC22/TARGET. Dove il prototipo richiede TARGET16.50, esporre branch base/dependency e SHA prima di implementare; nessun merge implicito.
2. Preferire `frappe.ui.form`, `frappe.ui.ListView`, `frappe.ui.Workspace` e custom `frappe.ui.make_app_page` **solo dove supportato dalla versione pinned**; convalidare API nel sorgente ufficiale e nel runtime. Niente patch al core Frappe/ERPNext.
3. Navigazione e visualizzazione **Cent­ro Change in italiano**, ruoli `Manager/Secretariat/Finance/Accountant/A/B/C/Guest`, differenza fra vista e autorizzazione documentata, privacy note cliniche invariata, data/query/list/API/report/export/print protetti dal server.
4. Nessuna duplicazione di master Patient, Practitioner, Customer, fatture, ledger, contabilità; modifiche devono usare i servizi canonici `centrochange_core` dove sono parte del contratto.
5. Prototipo reversibile solo su laboratorio sintetico dedicato. UAT RC22 (`centrochange-dev`, localhost8082), dataset Owner, container/lab precedenti, checkpoint e immagini protette intatti.
6. Ultima evidenza host R5 ~12.88GiB di disco libero e ~5.39GiB RAM disponibile: **fotografia, non preflight attuale**. Prima di mutazioni richiedere misura `df/docker`, cgroup/PSI/MemAvailable/OOM e budget incrementale con riserva di rollback; **NO nuove build né nuovi volumi se margine insufficiente**. Evitare duplicazioni di immagini e RAM peak, un solo builder/processo pesante; nessun `docker system prune` o delete indiscriminato.
7. Operare secondo attivazione temporale esplicita, bounded e tracciata C2: regole preflight, guardrail, safe stop e rollback descritti prima del primo write runtime. Non riciclare le scadenze ormai concluse della Missione B. Se una nuova finestra di host ad alto rischio o una modifica materiali sono necessarie, sottoporre quel solo gate all'Owner. L'autorizzazione della sperimentazione **non cancella** i safety gates HITCH.
8. Codice/versioni nei branch e PR DRAFT, screenshot e dati sintetici sanitizzati; niente segreti/DB dumps nel repository. No cambiamenti a `main` fino a separato approval.

**Gate C2:** funzionamento browser reale su clone, controlli sessioni/ruoli, script ricostruzione/stop/restore e baseline di integrità; un mockup statico non vale come prototipo.

## 4. C3 — Confronto misurabile

Produrre due demo confrontabili, usando **stessi casi sintetici e ruoli**. Non modificare e non resettare il dataset UAT RC22 per costruire il paragone.

- Scenari: calendario allineamento/giorni, ricerca paziente/professionista e singolo selettore, prenotazione/spostamento/cancellazione/nota, fatturazione e incasso/reconciliation, TS/SdI simulate, report, gestione eccezioni, percorso Accountant read-only.
- Prove: output funzionale e canonico, sicurezza negative cross-role/centro, error/stale/empty/loading, mobile390 e desktop1536, keyboard/focus, locali ITA, stampa/export, costo di manutenzione e riproducibilità.
- Matrice `WEBAPP_ACTUAL` vs `DESK_PROTOTYPE`: `PASS / PARTIAL / FAIL / NOT_TESTED` per scenario, tempi/azioni misurati dove sensato, annotazioni e immagini di confronto sintetiche, limiti.
- Evidenziare varianti: (A) tenere webapp esistente, (B) sostituire UI interna con Unified Desk, (C) ibrido se giustificato. Non assegnare valori/benefici non misurati.

**Gate C3:** `MISSION-C: READY_FOR_OWNER_COMPARISON / PARTIAL / BLOCKED`, raccomandazione motivata ma nessuna scelta automatica.

## 5. Confini e decisioni

Questa autorizzazione copre C1, C2 e C3. Non comprende **C4** (Decisione Owner su architettura), **D** (cutover/dismissione), approvazione visuale finale GOAL-02, merge PR, rollout TARGET su UAT, GOAL-03, produzione, credenziali dati reali o invio SdI/TS reale.

**HITCH Owner è autorità finale**. Se C1/C2 segnala necessità di cambio regole o permessi, negozia una sola decisione circoscritta anziché forzare il risultato.

## 6. Istruzioni e consegne Codex

Operare **per GOAL**, non in ping-pong tra micro-comandi. C1 può procedere da repo read-only subito. Prima del runtime C2 verificare preflight, piano temporale e isolate; continuare solo entro guardrail dell'autorizzazione.

Consegne versionate:
- `docs/evidence/mission-c/C1-NATIVE-CUSTOM-MATRIX.md`
- `docs/evidence/mission-c/C2-PROTOTYPE-REPORT.md` + codice e harness in PR DRAFT separata, dichiarando base e dipendenza da #107
- `docs/evidence/mission-c/C3-WEBAPP-VS-DESK-COMPARISON.md` + walkthrough/screenshot sintetici, tracciati
- `docs/evidence/mission-c/FINAL-REPORT.md` con raccomandazione, gate richiesto, regressioni, sicurezza, disco/RAM/PSI/OOM e attestazione RC22 invariato

**Non creare decisioni HITCH `APPROVATO` senza l'Owner. Non importare chat intere su GitHub.**

---

## 7. OWNER APPROVED — Estensione del mandato a UI COMPLETA (2026-10-09)

**Cronologia della decisione:** dopo il primo esito `MISSION-C: BLOCKED`, l'Owner ha ricevuto una proposta esplicita: «approvi l'aggiornamento della Missione C da *prototipo* a **UI completa, funzionante e tecnicamente collaudata**, con ripresa controllata dopo verifica delle risorse?». Risposta Owner: **«approvo»**.

Questa approvazione **supersede solo il limite di deliverable C2/C3 "prototipo/confronto parziale" dei paragrafi 1–6**, NON il registro storico, la decisione architetturale HITCH, le restrizioni operative o la distinzione tra tecnico PASS e accettazione Owner.

**Nuovo outcome tecnico di Missione C:**
`MISSION-C: READY_FOR_OWNER_UAT` soltanto quando l'**intera UI interna già prevista e compresa nel baseline GOAL-02** è accessibile, funzionante e tecnicamente verificata in un solo percorso Desk coerente (nativo/adattato/custom), con tutte le superfici cliente-facing italiane, ruoli/centri/professionisti segregati, responsività e accessibilità adeguate. Il test Owner e l'approvazione restano **PENDING** anche se i test tecnici sono PASS. Altrimenti `PARTIAL / BLOCKED / FAIL` onestamente motivato. Non presentare un prototipo di tre viste come UI completa.

### 7.1 Lavoro da preservare e punto di ripresa

- C1 **completa** con matrice 24 aree [PR DRAFT #111](https://github.com/2008hitch-afk/centrochange_core/pull/111): riusare; modificarla solo per evidenze necessarie.
- C2 primo prototipo [PR DRAFT #112](https://github.com/2008hitch-afk/centrochange_core/pull/112), source `6c2801cd2a7c3d17a0a58e93f58c379171fa39db`, stacked su [PR DRAFT #107](https://github.com/2008hitch-afk/centrochange_core/pull/107): Desk Page/Sidebar, Agenda, Pazienti, Finance read-only; NON ripartire da zero.
- C3 parziale: **69 HTTP PASS, 19 browser PASS, 1 test Manager FAIL da discriminare** (centro fisso non impostato nell'harness); browser Finance/Accountant, scenari mutativi, sicurezza completa e parity di tutte le viste non provati.
- Stop reale: **OOM QA 512MiB**, host `oom_kill +1`. C109 spento, dataset/immagini/checkpoint protetti; **RC22 HTTP200, 137 altri container invariati**. Tutti i vecchi FAIL/PSI/stop restano evidenza, mai mascherati.
- Ultime evidenze in `docs/evidence/mission-c/{C1-NATIVE-CUSTOM-MATRIX,C2-PROTOTYPE-REPORT,C3-WEBAPP-VS-DESK-COMPARISON,FINAL-REPORT}.md` sul branch `issue-109/unified-desk-evidence`. Nuove run append-only con SHA, image digest, risultati per suite, senza riscrivere il BLOCKED precedente.

### 7.2 Deliverable "tutte le schermate"

Completare la UI **per ogni area interna approvata della matrice C1**, con stesso ambito commerciale/funzionale già previsto in GOAL-02, distinguendo chiaramente NATIVE / SUPPORTED_ADAPTATION / CC_CUSTOM_DESK_PAGE. Aree obbligatorie secondo rilevanza del ruolo: login/navigazione; Agenda, filtro professionista/centro e geometria calendario; disponibilità; prenotare/spostare/annullare; sedute/stati/riapertura/chiusura; pazienti, professionisti, ricerca e note autorizzate; servizi/prezzi/pacchetti; fatture clienti e fornitori, incassi/pagamenti, crediti/rettifiche; banca/riconciliazione; report, print/export; SdI/TS **solo simulati**; comunicazioni/notifiche; accessi/centri; amministrazione/compensi/coda; audit.

Per ogni area **dimostrare** vista, ricerca/navigazione, azioni effettivamente esistenti, stati loading/empty/error/disabled, UX italiana, desktop/mobile, accesso per ruolo e negativo via direct/list/API/query/report/export/print. Riutilizzare senza duplicare documenti, ledger, DB, autorizzazioni o regole; preferire API e servizi canonici `centrochange_core`; nessun bypass dei permessi via Desk.

Una funzione classificata **BLOCKED_NEEDS_DECISION** (es. report nativi ERPNext che richiedono privilegi non concessi) **non viene sbloccata** per ottenere un PASS: mantenerne il percorso alternativo autorizzato attraverso servizi/pagina scoped; se il requisito approvato non è realizzabile senza variazione di policy/architettura, sospendere la parte e chiedere all'Owner una decisione mirata. Non dichiarare la UI completa con una funzione contrattualmente richiesta assente. Il primo incontro pubblico e le superfici DEV-only restano esclusi dalla conversione Desk, come documentato nella C1.

**Nessuna scorciatoia:** collegamenti temporanei alla vecchia webapp, placeholder, schermate vuote, screenshot, o pulsanti non collegati a workflow **non sono evidenza** di completamento della nuova UI interna. I riferimenti tra Desk e superfici native necessarie possono esistere se l'esperienza resta unica/coerente e la funzione è davvero coperta, documentando ogni integrazione.

La conformità visiva parte da `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md` (Owner approved, Tabler1.6.1/UI Centro Change) e dall'UAT RC22 come benchmark, senza presumere che Desk chrome standard rispetti automaticamente branding e lingua; localizzare **senza** patch upstream o CSS distruttivo al core.

### 7.3 Ripresa controllata post-OOM (vincolo prioritario)

L'Owner autorizza una **nuova continuazione C** limitata alla stessa sperimentazione isolata. Prima di qualsiasi riavvio/scrittura:

1. Inventario live read-only: versioni/immagini, commit/branch e chain #107/#112, container e volumi C109, dataset sintetici, disco libero, MemAvailable, PSI memoria/I/O, cgroup OOM/eventi, 137 container protetti e RC22.
2. Nuovo **manifest operativo di attivazione** distinto dal C109 BLOCKED: orario corrente, finestra limitata con margine verifica/stop/rollback, stop automatici, preflight di disponibilità, budget disco e reversibilità; **non** riutilizzare le finestre della Missione B né presumere nuove scadenze approvate. Se la governance richiede una nuova finestra Owner non derivabile dall'autorizzazione, fermarsi e richiedere il solo gate temporale.
3. Browser Chromium **fresco per ciascun ruolo/suite**, uno alla volta, chiusura pulita e raccolta memoria/cgroup prima di passare al successivo; test Manager con CentroA fissato esplicitamente senza indebolire asserzioni. Riprovare solo prove necessarie e conservare l'esito storico.
4. Limite aggregato **runtime+QA 2.5GiB invariato**. QA512MiB OOM non può essere ignorato; dopo misura ammettere una *redistribuzione interna* documentata, ad es. QA768MiB/runtime1792MiB **solo se** regge i servizi e mantiene l'identico totale, senza aumentare il cap host o le soglie. Preferire esecuzione seriale e reuse delle immagini, non build/clone ridondanti.
5. **Qualsiasi nuovo OOM, PSI/host safety stop, mancata riserva disco/rollback oppure mutazione inattesa di RC22/protetti ⇒ stop immediato**, contenimento e report; nessun retry incontrollato o allentamento dei guardrail.
6. Nessuna operazione distruttiva: niente prune globale, rimozione R1–R5/C109 o checkpoint, migrate/reset/seed UAT, modifica main, merge, deploy UAT o produzione. Nessun dato reale, credenziale in Git o provider live.

### 7.4 Exit gate aggiornato e documenti

Risultato Codex `MISSION-C: READY_FOR_OWNER_UAT / PARTIAL / FAIL / BLOCKED`, con:
- matrice tracciabile **24/24** che espliciti per area `IMPLEMENTED + TESTED / NOT_APPLICABLE_PUBLIC_DEV / BLOCKED_BY_OWNER_DECISION`, senza falsi PASS;
- registro di parità con webapp RC22/GOAL-02 per flusso, sette ruoli+Guest, aree/tenant, privacy, dati canonici/audit;
- test reali browser e sicurezza positivi/negativi, screenshot rappresentativi desktop/mobile; finance mutativa/reconciliation e TS/SdI simulati ove compresi, non simulare traffico provider reale;
- immagini, source SHA, parità codice/runtime, UI/asset, restart/restore lab, log sanitizzati, memoria/disco/PSI/OOM e conferma RC22 invariato;
- eventuali limiti residui e lista di verifiche Owner **senza dichiararle superate**.

**Missione D resta esclusivamente** cutover dell'UI selezionata, deploy sull'UAT nel percorso richiesto, reversibilità e cleanup governato dopo scelta Owner: **non** rinviare a D lo sviluppo di schermate previste che possono essere completate in C. Il gate definitivo di architettura (revisione della DECISION-004) e la chiusura GOAL-02 restano riservati all'Owner. Tutte le PR restano **DRAFT** finché non autorizzate separatamente.


---

## 8. MISSION C — R3 Owner-authorized bounded post-OOM continuation (2026-10-10)

**Owner decision:** following the R2 `MISSION-C: BLOCKED` outcome, the Owner was explicitly asked to authorize a **controlled R3 restart with fresh Chromium per native page, unchanged aggregate 2.5 GiB, unchanged safety guards and no changes to RC22**. The Owner replied **«approvo e autorizzo»** on 2026-10-10.

**Authority now:** `OWNER_AUTHORIZED_R3_SAFE_CONTINUATION` for the existing, isolated **Mission C full-UI** scope from §7, not for any new architecture decision or rollout. The R2 `BLOCKED` state remains a historical, valid safety stop. R3 is NOT started or PASS merely because this authorization is recorded.

### 8.1 Reuse exact evidence and software (no restart-from-zero)

- C1 24-area matrix, C2/C3 results and R2 report: [Evidence DRAFT PR #111](https://github.com/2008hitch-afk/centrochange_core/pull/111), `docs/evidence/mission-c/R2-FULL-UI-STOP-REPORT.md`.
- Product DRAFT [#112](https://github.com/2008hitch-afk/centrochange_core/pull/112), tested R2 HEAD `0c85d72d589c7eb59eca8ef949d18c87b9af2bc5`, image `sha256:1beab705b2511464212740a5fd2f87bc42ea64aff2b71058c35736392756c21e`, stacked on unmerged [compatibility #107](https://github.com/2008hitch-afk/centrochange_core/pull/107).
- R2 passed browser Manager 28 checks, Secretariat/Finance/Accountant Finance views 9/9 each, seven-role entry, mobile/keyboard, synthetic booking→reschedule→cancel, bank import/reconciliation and SdI/TS simulations. HTTP security 69/69 PASS **on the immediately preceding R2 image**, not automatically credited to the last locale-only image. Native Catalog direct List 7/7 PASS, but repeated navigation in one 512 MiB Chromium container produced a **confirmed QA cgroup OOM**; complete 24-area acceptance and print/export/write cases remain open. 137 non-C109 protected containers and RC22 remained unchanged, HTTP200.

### 8.2 Exact R3 post-OOM safety activation

1. Before touching containers or files, perform a read-only **live preflight** on server: original protected container names/images/IDs/state/start/restart/mount/network, RC22 HTTP, R2 C109 containers/volumes/assets/archives/source SHA/digest, host time, free disk and rollback reserve (at least established 4 GiB), available RAM, swap, PSI memory/I/O, cgroup `memory.events` OOM and OOMKilled flags. If any changed baseline, insufficient margin or unresolved running lab exists: `BLOCKED_PREFLIGHT`, no mutation.
2. Record a **fresh, versioned R3 activation manifest** on the new isolated operational/evidence branch with real clock times, finite bounded work window, explicit verification/stop/rollback margin, exact compose project/volumes/network/localhost port, safety thresholds from previous R2 unchanged, owner authorization link, initial measurements and stop conditions. This is not an extension/reopening of the stopped R2 activation. Do not invent an Owner-approved end clock time or reuse expired Mission B limits. Only execute work the measured time window can safely contain; if a new user-approved high-risk window is strictly required by policy, stop and request that single gate before changes.
3. Keep **runtime 2 GiB + QA 512 MiB = 2.5 GiB** combined caps (no cap changes, no hidden overlapping browser runners). Ensure runtime peak/headroom is measured, count browser child processes in QA cgroup, one browser at a time, serial tests and I/O. PSI/MemAvailable/OOM/rollback checks remain **unchanged and active**.
4. Split native Catalog and other high-memory paths into **one fresh Chromium/QA process/container per native page** (not just a new tab/context in one long-lived browser). Close and verify cgroup/containers exited before next page. Fix the harness to select expected center explicitly and maintain unchanged assertions; do not patch product merely to match a brittle test.
5. If **even one single-page QA at 512 MiB hits OOM**, any new host/cgroup OOM or safety/watchdog stop occurs, disk/rollback reserve fails, or protected RC22 changes: immediately stop **C109/R3 only**, preserve logs/checkpoints/data, mark `MISSION-C-R3: BLOCKED`; **no further runtime retries in this activation**. A proposed QA768MiB/runtime1792MiB redistribution inside 2.5 GiB is a **separate measured option for Owner review**, NOT implicitly authorized by this R3 approval. Do not raise memory/safety thresholds.
6. Never delete lab images/checkpoints, prune Docker globally, modify RC22/production, use real clinical/client data, real SdI/TS/provider traffic, alter role grants/server guards, push/merge main or perform Mission D. One Codex writer. Do not put secrets, private fixture files, dumps or unsanitized logs in GitHub.

### 8.3 R3 work and completion gates

After preflight and activation:
- Run **native Catalog** separately: Workspace→Item; Item Price; Appointment Type; CC Center Service; CC Package Template; Patient; Healthcare Practitioner. Test authorized native List/Form actions and negative role/center cases without creating generic native grants.
- Complete **all R2 PARTIALs** by scenario using real UI and synthetic data: clinical/organizational session state, note access/write, patient create and search, professional lifecycle, availability/absence, catalog supported writes, Finance invoice/receivables/Payment Entry/credit/rectification, banking/reconciliation, reports/drill-down/full-period totals, administration/access changes, compensation/queue overrides, communications/retry, audit before/after, logout and print/CSV/export. Preserve negative tests for seven roles+Guest, center A/B, note privacy and direct/API/query/report/export/print. Keep SdI/TS simulated.
- Rerun **actual final-image** HTTP security, browser, functional and layout suites (desktop/mobile/keyboard/Italian labels), identity/digest, supported native runtime and rollback/restore evidence as appropriate to R3 mutations. Do not count earlier suite PASS as evidence of an untested new final image.
- Track each of C1's 24 rows as `IMPLEMENTED_TESTED`, `NOT_APPLICABLE_PUBLIC_DEV`, `BLOCKED_BY_OWNER_DECISION` or `PARTIAL/FAIL`. Existing native ERPNext reports requiring new rights must remain denied; use authorized CC-scoped alternative where required without widening access.
- Outcome **`MISSION-C: READY_FOR_OWNER_UAT`** only when every approved internal UI requirement is implemented and tested end-to-end and mandatory security/recovery/isolation gates pass. Otherwise report `PARTIAL / FAIL / BLOCKED` with an exact remaining checklist and a single requested decision only if necessary. No Owner UAT acceptance is asserted.

**Required artifacts:** append-only `R3-ACTIVATION`, per-suite evidence and 24-area acceptance matrix, desktop/mobile synthetic screenshots, final `R3-REPORT`, protected-container and RC22 before/after snapshots, branch/PR SHA/digest, actual OOM/PSI/caps/disk proof, and (if needed) `BLOCKED` diagnosis. Update [#109](https://github.com/2008hitch-afk/centrochange_core/issues/109) and DRAFT #111/#112; **do not merge**. C4 Owner architecture choice, Mission D, GOAL-02 Owner acceptance, GOAL-03 and production all remain separate.


---

## 9. MISSION C — R4 Owner-authorized bounded continuation after CAP_NOT_ENFORCED (2026-10-10)

**Owner decision and scope:** when presented with the proposal to authorize **Missione C — R4** with QA container prestarted and real cgroup verification *before* launching Chromium, **runtime 2 GiB + QA 512 MiB = aggregate 2.5 GiB**, unchanged OOM/PSI/disk/rollback guardrails, UAT RC22 untouched and completion of existing PARTIAL acceptance cases, the Owner responded **«Procediamo»** on 2026-10-10. This reply directly follows that specific requested authorization. **Result:** `OWNER_AUTHORIZED_R4_BOUNDED_CONTINUATION`. It does **not** mean R4 executed, R3 has passed, UI accepted, or any target promoted.

### 9.1 Baseline and actual outstanding work

R3 must remain `MISSION-C-R3: BLOCKED` as recorded in [R3 append-only evidence PR #115](https://github.com/2008hitch-afk/centrochange_core/pull/115) / `docs/evidence/mission-c/R3-FULL-UI-STOP-REPORT.md`. R3 stop was the mandatory watchdog's `CAP_NOT_ENFORCED`: a newly starting QA cgroup reported `memory.max=max` while `docker inspect HostConfig.Memory=536870912`. QA exit 137, `OOMKilled=false`, host `oom_kill 7→7`. A transient cgroup setup race is a **hypothesis**, not an established diagnosis. R3 C109 is stopped, existing synthetic data/images/volumes retained. RC22 reported HTTP200, 137/137 non-C109 containers unchanged. **No new OOM in R3**, unlike historic R1/R2 OOM.

Reuse R3 product [DRAFT PR #112](https://github.com/2008hitch-afk/centrochange_core/pull/112), revision `d9c09e1d44795b068b4869c013263531dc53a936`, image `sha256:6855661acef0f98978cc969e3f12e418b68ff2744d5b47f625bc8afde5acdbae`; stacked on DRAFT #107. Reuse C1 matrix24 and prior R2/R3 positive evidence to target **only unverified or changed scenarios** first. R3 final-image tests already show native Catalog7/7, 69/69 HTTP guards, roles, session/patient/professional lifecycle, availability correction, invoice+Payment Entry, report basics, audit, four CSV, print, logout and mobile, but **not full GOAL-02 UI parity**. No renaming old PARTIAL/FAIL as PASS.

### 9.2 Safety and activation: mandatory before all runtime writes

1. **Live read-only preflight:** identify the exact main/PR/branch/image SHA and C109 stopped state; compare preexisting protected 137-container baseline (names/IDs/images/started-at/restart-count/mounts/networks) and RC22 HTTP; host `df`, MemAvailable, PSI memory/I/O, OOM/cgroup memory events, preexisting QA container status, disposable fixture state, free disk and existing ≥4 GiB recovery reserve. If any protection/budget discrepancy, report `BLOCKED_PREFLIGHT` and do not mutate.
2. **Distinct R4 activation manifest** on isolated operational branch / versioned report: explicit Owner authority link (issue #109), real local and UTC clock, finite bounded execution window with adequate safety verification/stop/rollback margin, preflight readings, exact Docker Compose project/site/networks/volumes, expected SHA, permitted commands/classes, prior blocked R3 marker retained, exit/safe-stop requirements. Do not reuse the R3 activation or expired earlier windows; if policy needs a separate Owner-approved risk/time window, stop at that gate.
3. **Never increase or waive limits:** runtime cap **2 GiB**, QA cap **512 MiB**, aggregate ≤**2.5 GiB**, one QA/browser at a time and I/O serialized; identical memory/PSI/disk/OOM guardrails enabled continuously. No masked watchdog, exempt QA process, ignored `memory.max=max`, or grace period that permits unbounded Chromium. Preserve existing host/project protections.
4. **Prestart & verify QA cgroup before Chromium**: create/init a dedicated QA container under the configured 512 MiB memory and swap constraints, and attest both Docker `HostConfig.Memory`/swap and the *effective running process cgroup* `memory.max=536870912` and applicable `memory.swap.max`. Wait only while **all existing safety checks permit it**, observing a bounded stabilization state with no browser and no unbounded memory-consuming workload. If the watchdog flags `CAP_NOT_ENFORCED`, if `memory.max=max` persists/appears under active policy, or cgroup path/limits cannot be independently established: **STOP R4**, do not bypass or exempt monitoring; save sanitized evidence for an infrastructure guard/race diagnosis. Before each browser run, reverify actual cap, cgroup path, browser child inheritance, OOM counter and host pressure.
5. Use **one fresh Chromium OS process per native page/test case**, started **serially inside the same already-verified QA cgroup**, fully terminated and reaped between cases; no fresh QA container startup per native page. Verify process absence, memory recovery, runtime/QA usage and no guard event before next. No product test assertion/authorization may be weakened to obtain PASS.
6. **Hard stop:** any real OOM/cgroup OOM, watchdog event including CAP_NOT_ENFORCED, failed cgroup verification, PSI/MemAvailable/disk/rollback trigger, changed RC22 or protected container → immediately stop **only C109**, retain images/volumes/checkpoints/logs, note failure and return `MISSION-C-R4: BLOCKED`. **No runtime retry in this activation**. No automatic QA768/runtime1792 redistribution: that remains an unapproved separate Owner decision.
7. **Strict exclusions:** no merge/main write, no UAT RC22 restart/migrate/deploy, no site cutover, no upstream Frappe/ERPNext patches, no global Docker cleanup/prune or historical evidence deletion, no new role grants/impersonation in business services, no production/GOAL-03, no real client/patient data or real SdI/TS/notification traffic. A single writer Codex.

### 9.3 Tests needed for actual complete UI

Continue on preserved synthetic C109 clone and named final product image; run the **remaining PARTIAL** checks with real UI/browser interactions and actual app tests as needed, especially:

- **Prenota → sposta → cancella** on exact final image, deterministic unused slot/center, correct idempotency and audit.
- Complete catalog native forms/approved master edits, including negative role/center permission checks and undo of synthetic writes, without native role broadening.
- Finance patient + supplier invoice, credit/correction, supplier payment, bank reconcile, compensi/manager override and queue lifecycle within existing CC service guards.
- Reports drill-down/reconciliation, **shared payer** using controlled synthetic fixture where available; print/CSV/export cross-center/role negative.
- Notifications failure/retry/idempotence with isolated simulated fixture (no real send), TS/SdI simulated end-to-end where relevant to final image; audit before/after actor/correction.
- Owner-relevant final UI Italian labels/native Desk surfaces, keyboard/search focus and mobile/day header geometry, seven role + Guest read/direct/API/report/export/query negatives.
- Re-run **final-image security and relevant end-to-end suites** after any new code changed; don't credit R2 suite as proof of an untested R4 final image. Maintain an honest 24-area `IMPLEMENTED_TESTED / PARTIAL / FAIL / NOT_APPLICABLE_PUBLIC_DEV / BLOCKED_BY_OWNER_DECISION` matrix.

`MISSION-C: READY_FOR_OWNER_UAT` may be declared **only** on full approved internal UI parity with complete technical evidence and safety verification. Else report `MISSION-C-R4: PARTIAL / FAIL / BLOCKED`, exact missing tests/risks and next narrow gate. **Mission D cutover, acceptance by Owner, DECISION-004 architecture change, GOAL-02 closure, TARGET promotion or UAT deployment remain NOT authorized.**

### 9.4 Deliverables and evidence

Append-only R4 activation, images/source/hash proof, test matrix 24/24 with per-scenario true outcomes, anonymized screenshots, runtime/QAcgroup limit verification, PSI/OOM/memory/disk, protected-container/RC22 diff and controlled stopping/recovery details in new **DRAFT evidence PR** stacked on #115 or clearly linked; update [#109](https://github.com/2008hitch-afk/centrochange_core/issues/109), product **DRAFT #112** and evidence DRAFT #111/#115 references. Avoid importing private logs, dumps or credentials to GitHub. **No merge/cutover**.


---

## 10. Owner requested P0 — alleggerimento e inventario sicuro server prima della ripresa C (2026-10-10)

**Priorità corrente su §7–§9:** l'Owner ha richiesto esplicitamente una **pre-fase P0 di razionalizzazione server**, per trovare ed eventualmente dismettere vecchi container, duplicati, bench/sites Frappe e laboratori obsoleti, prima di riprendere diagnosi del watchdog, prove browser o Missione C.

**Tracking dedicato:** [Issue #117 — FASE 0 Inventario/alleggerimento server](https://github.com/2008hitch-afk/centrochange_core/issues/117). **Stato corrente: `P0_AUDIT_REQUESTED / NO_DELETIONS_AUTHORIZED`.** Questa priorità non modifica i risultati storici R1–R4 (R4 rimane BLOCKED) né crea una nuova autorizzazione C/R5. Non alterare GOAL-02/HITCH, DECISION-004 o produzione.

### Sequenza vincolante e risultati

1. **P0-A SOLO READ-ONLY** — Codex/Sysadmin rileva inventario attuale Docker/Compose/container accesi/spenti, immagini/caches/volumi/reti, progetti, siti/bench, dipendenze, spazio recuperabile reale, uso RAM *effettivo* e cgroup/PSI/OOM; distingue risorse condivise, Centro Change e altri progetti. I 137 container dell'ultima prova sono la popolazione protetta, **non** 137 container necessariamente accesi né 137 duplicati.
2. **P0-B RETENTION E BACKUP** — classificare `KEEP_CRITICAL` RC22 attualmente funzionante e i suoi dati/config, `KEEP_TEMPORARY` minimo codice/ambiente sintetico Mission C e compatibilità TARGET per riprendere, `CANDIDATE_DELETE_AFTER_OWNER_GATE` solo risorse realmente inutilizzate e ricostruibili, `OUT_OF_SCOPE` progetti estranei. Prima della dismissione di un checkpoint/volume/bench verificare backup con checksum e **ripristino pratico**, preferibilmente in posizione indipendente dal disco che si pulisce. GitHub conserva il codice, non sostituisce database, file, secret o runtime.
3. **P0-C UNICO OWNER DELETE GATE** — preparare l'elenco nominativo di oggetti/digest/volumi/sites/bench esatti, ownership, bytes realmente recuperabili senza doppio conteggio, impatto, backup e rollback. Richiedere **una sola approvazione esplicita dell'Owner per il bundle prima di cancellare**. Nessuna delete implicita da «alleggerire». Non usare prune globali o wildcard; non toccare RC22/dati clienti, C109 indispensabile o servizi di altri progetti.
4. **P0-D CLEANUP AUTORIZZATO E MISURATO** — solo dopo gate, rimozioni puntuali per lotti a basso rischio e successiva verifica di `df/docker system df`, RAM, OOM e UAT RC22; confronto prima/dopo e rollback. Non assumere che la riduzione del disco risolva il watchdog; R3/R4 hanno `CAP_NOT_ENFORCED` senza nuovi OOM e con >5GiB di RAM host disponibile. I primi OOM erano reali nel cgroup QA512MiB.
5. **HANDOFF** — con P0 chiusa e verificata, fare diagnosi **mirata prima di un nuovo avvio del laboratorio C**: Docker HostConfig vs `memory.max`/cgroup path e sequenza transitoria worker R4/QA R3. Nessun R5 e nessun test runtime senza nuova attivazione/policy decision; preservare il limite aggregato runtime+QA **2.5GiB** e guardrail.

**Consegna iniziale:** inventario e proposta in PR DRAFT, senza cancellare nulla. **Fine P0:** server alleggerito per quanto autorizzato, un solo UAT corrente funzionante + il minimo necessario per concludere Unified Desk, backup/ripristino provati e misure live del beneficio. **Risultato principale del programma:** `MISSION-C: READY_FOR_OWNER_UAT` dopo i test mancanti, non anticipato dall'alleggerimento.


---

## 11. MISSION C — MANDATO UNICO OWNER APPROVED: INFRASTRUCTURE UNBLOCK + FULL UI + FINAL TESTS (2026-10-10)

**Decisione Owner:** a fronte della proposta esplicita di sostituire i continui tentativi isolati con **un unico mandato Codex** «MISSION-C — SBLOCCO INFRASTRUTTURA + COMPLETAMENTO UI + COLLAUDO FINALE», composto da (A) codice/UI senza Docker, (B) bootstrap sicuro dei test e (C) collaudo finale, l'Owner ha risposto **«Ok approvo unico mandato»**.

**Mandato operativo corrente:** `OWNER_APPROVED_SINGLE_GOAL_MANDATE`. Questo §11 governa priorità e modalità esecutive delle sezioni precedenti, che restano **registro storico** e non vengono retroattivamente cancellate. È approvata la continuazione **per obiettivi**, con una nuova attivazione controllata solo quando il preflight di sicurezza sia positivo. **Non** sono approvati a priori workaround insicuri, eccezioni mentre gira un workload applicativo, nuove infrastrutture a pagamento o l'avvio indefinito di container.

**Stato iniziale reale:** `MISSION-C: BLOCKED / READY_FOR_OWNER_UAT: NO`. [DIAG-01 #122](https://github.com/2008hitch-afk/centrochange_core/issues/122)/[DRAFT PR #123](https://github.com/2008hitch-afk/centrochange_core/pull/123) `INCONCLUSIVE`: cgroup Docker con `memory.max=max` (e swap max) 22.8/29.4ms dopo StartedAt anche con PID1 inerte; parser di antenati fallito leggendo un file assente alla root cgroup v2, **corretto in DRAFT ma non validato live sul QA**. Trigger effettivo, ROOT CAUSE non ancora provata; precedente R1/R2 OOM512MiB genuino, R3/R4 `CAP_NOT_ENFORCED` senza nuovi OOM. **La prova unica #122 è consumata**: questa decisione costituisce **un nuovo mandato distinto**, non un retry implicito della #122.

### 11.1 Stream A — completamento del prodotto SENZA avviare Docker

- Codex legge C1 24 aree, gap/PR #111/#115/#116, rapporto R3, prodotto [DRAFT PR #112](https://github.com/2008hitch-afk/centrochange_core/pull/112) (HEAD iniziale `d9c09e1d44795b068b4869c013263531dc53a936`) stacked su compatibilità [DRAFT #107](https://github.com/2008hitch-afk/centrochange_core/pull/107), e Design System v1, GOAL-02 RC22. Verifica `git status`, revisioni HEAD e local changes prima di qualunque file edit. Non ripartire da zero né perdere uncommitted work, evitare duplicazioni e mantenere dipendenze trasparenti.
- Mappa ciascuna delle **24 aree** a `IMPLEMENTED_TESTED / IMPLEMENTED_UNTESTED / PARTIAL / BLOCKED_BY_OWNER_DECISION / NOT_APPLICABLE_PUBLIC_DEV`; colmare con codice il **vero gap funzionale nel perimetro già approvato GOAL-02** usando ERPNext/Frappe nativo quando appropriato, custom Page scoped solo dove serve. Nessuna funzione finta, link temporaneo alla vecchia webapp, bypass login/ruoli o duplicazione del backend/ledger.
- Per ogni correzione prepara unit test, static checks, contract/policy tests con mock/synthetic fixture senza Docker ove fattibile. Indicare esattamente quali verifiche **non** sono prove end-to-end/runtime: non etichettarle PASS del prodotto finale.
- Preservare specificamente prenota→sposta→cancella, percorsi sessioni/assenze, Pazienti/professionisti/center, catalogo, contabilità Finance nativa scoped/receivables/crediti/fornitori/banca, compensi/coda/override, reports/shared payer, TS/SdI simulate, notifications retry, audit, stampa/export/mobile/IT/tastiera e accesso 7 ruoli+Guest. Non ampliare permessi generici per il PASS, non modificare policy senza decisione.
- Consegnare codice DRAFT su #112 (o nuova DRAFT collegata, spiegando dipendenza) e matrice 24 aree in aggiornamento; il blocco del laboratorio **non blocca** il lavoro statico.

### 11.2 Stream B — sblocco lab con PROTOCOLLO SICURO validato, non retry ciclici

- Prima fare review offline del protocollo `c109_diag01_probe.py` corretto in #123: test riproducibili del parser su gerarchia root senza `memory.max`, path effettivo da `/proc/PID/cgroup`, mount/namespace/antenati, PID assente/uscito, mismatch, cgroup falso, swap diverso, `max`, OOM/PSI, harness failure; il bug parser non deve consumare un'altra attivazione. Revisione dei guard reali/simultanei, mock negative tests, no log sensibili.
- Progettare un **two-phase bootstrap fail-closed** SOLO su C109: (1) PID1 inerte a risorse minime, nessun Frappe, worker o Chromium; (2) acquisire PID reale e scope inode + limite effettivo RAM/swap della gerarchia, confermare cap numerico applicato al processo e budget; **solo allora** rilasciare il workload applicativo normale. Il precedente rilevamento `max` va conservato come evento e indagato. Qualsiasi eventuale finestra di *osservazione* deve essere strettamente limitata alla **fase inerte**, finita e watchdog/monitor host attivi; MAI finestra di tolleranza o esenzione con workload attivo, e nessun rilascio se cap ignoto/assente. Non mascherare eventi di sicurezza, non assumere transient Docker senza prova.
- Mantenere invariato il budget **runtime ≤2 GiB + QA ≤512MiB = aggregato 2.5GiB**, i guardrail host MemAvailable/PSI RAM+I/O/OOM/disk ≥4GiB reserve, gli stop per RC22 e container protetti; niente privilegi extra o Docker daemon-wide changes. L'eventuale cambio del protocollo/strumentazione resta in **PR DRAFT**; solo il codice di laboratorio può essere applicato alla prova isolata entro il gate GREEN e la presente autorità.
- **Preflight live READ-ONLY** dopo sviluppo e test statici: confermare RC22, versioni/immagini, C109 fermo, stato delle risorse dopo FASE 0 (108/109, secondo volume cache conservato), archivi/checkpoint, disco/RAM/PSI/OOM; comparazione non-candidate. Registrare **nuova attivazione C-UNIFIED** con orari effettivi, finestra finita, margine verifiche/stop/rollback, un solo writer, prior `BLOCKED` preservato. Se manca margine, la finestra è scaduta, o il perimetro muta: stop.
- **Un solo ciclo di convalida del bootstrap** per la nuova attivazione: prova inerte, introspezione PID/limiti, negative tests per fail closed; se GREEN, attivare nel C109 isolato e passare al collaudo finale Stream C. Se `max` permane oltre la soglia di bootstrap inerte, CAP_NOT_ENFORCED o qualsiasi watchdog safety stop non previsto interviene, PID/swap cap non verificate, OOM/PSI/disco/RC22 cambiano: `BLOCKED_SAFETY`, arrestare **solo C109**, preservare dati/evidenza e **nessun retry** dentro la stessa attivazione.
- Se il modello di protezione non può essere soddisfatto in sicurezza sul server attuale, terminare con **una proposta tecnica alternativa** (p. es. laboratorio isolato diverso), includendo costi e rischio; **non acquistare, creare o usare** automaticamente un nuovo server/VM o modificare l'infrastruttura condivisa. Nuova scelta Owner solo su questa eccezione concreta.

### 11.3 Stream C — collaudo completo dopo gate bootstrap GREEN

- Eseguire test **sull'immagine finale effettiva** e sul dataset sintetico isolato, con SHA codice, immagine, dipendenze, ruoli/policy/schema. Test autonomi per suite, seriali, browser fresco per scenario/pagina nativa; ogni browser deve essere dentro il cgroup limitato e verificato, senza overlap pesanti. Nessun upgrade/merge del CURRENT UAT.
- C1 24 aree tracciate una a una: UI workflow business, test positivo/negativo per 7 ruoli+Guest e centro/professionista, direct/list/API/report/export/print/query, campi riservati, autorizzazione server-side, audit actor/before-after, idempotenza e rollback/isolation. Verificare le parti R3 PARTIAL e l'ultima revisione applicativa; evitare di riattribuire test R2/R3 a codice cambiato.
- Verificare UX di riferimento Centro Change / Tabler v1, italiano, Agenda day-column 0 drift, ricerca e selettori, desktop/mobile/keyboard, stati empty/error/loading, stampa e CSV/export. Recuperare screenshot **sintetici**, test numerici e walkthrough Owner riproducibile.
- Esito `MISSION-C: READY_FOR_OWNER_UAT` **solo** se tutti i criteri GOAL-02 approvati per l'UI interna sono coperti, test effettivamente PASS e sicurezza/reversibilità PASS. Altrimenti `MISSION-C: PARTIAL / FAIL / BLOCKED` con gap e causa singola. Nessun "READY" se non esiste un percorso praticabile affinché Owner provi la UI, o se una funzione richiesta rimane monca.
- Fornire **URL/accesso di prova** soltanto attraverso un canale isolato e già autorizzato; non esporre servizi pubblici, nuove porte esterne, tunnel, credenziali o modificare `/centrochange` senza decisione separata.

### 11.4 Consegne uniche, decisioni e limiti immutati

Report append-only in PR DRAFT su GitHub, issue #109 coordinatrice: `C-UNIFIED-IMPLEMENTATION-STATUS.md` (matrice 24 aree/gap), `C-UNIFIED-BOOTSTRAP-VERIFICATION.md` (harness correction, PID/cgroup/safety tests), `C-UNIFIED-FINAL-ACCEPTANCE.md` (esiti effettivi, asset screenshots sintetici, confronto RC22 e manifest SHA), `C-UNIFIED-OWNER-WALKTHROUGH.md` (click-by-click non tecnico), con log grezzi/secret/fixture cliniche **fuori GitHub**. Conservare la cronologia R1–R4 e DIAG-01, FASE0 PARTIAL, senza retrodatare PASS.

Lavorare **per GOAL** in autonomia sui task tecnici interni; niente microapproval per ogni file o prova nel perimetro approvato. **Stop e una sola decisione Owner** se un gate di sicurezza nuovo richiede deroga, un cambio di architettura/permesse/scope, ambiente a pagamento, promozione/merge o un'esplicita finestra di rischio non già valida. Vietati `docker prune`, nuove delete/cleanup, uptime/restart RC22, modifiche UAT/produzione, dati reali o provider live, aumenti cap, disattivazione watchdog, MAIN merge, GOAL-03 e Missione D.

**Importante:** questo mandato è l'autorizzazione all'esecuzione **nel rispetto dei gate**; non è prova che Codex sia già partito né promessa di PASS se i guardrail bloccano. 


---

## 12. OWNER CLARIFICATION — ORIGINAL ERPNext-NATIVE-FIRST ARCHITECTURE (2026-10-10)

**Fonte primaria prima degli stop C109:** versione originale di **questo piano** al commit `b803cf1f3a55168a8c1d2c01ae212259449b2da2`, §§1–4 (9 ottobre 2026), e roadmap A→B→C→D 8 ottobre in `docs/plans/CENTROCHANGE-MISSION-A-AND-UNIFIED-DESK-ROADMAP-2026-10-08.md`. La Missione C iniziale era **C1 analisi nativo/adattato/custom → C2 prototipo Desk isolato → C3 confronto operativo con RC22 → C4 decisione separata di adozione/cutover**. Il 9 ottobre l'Owner ha successivamente ampliato **l'ampiezza della realizzazione** a UI completa con prove, non cancellato la logica nativo-prima né autorizzato l'adozione della nuova interfaccia.

**Chiarimento Owner in chat, 10 ottobre 2026:** «Confermo A: Missione C deve essere ERPNext nativo prima di tutto, adattando direttamente le schermate native mediante estensioni supportate, con pagine custom solo se indispensabili. Verifica e riallinea il mandato prima di continuare.» Successivamente alla verifica della decisione **originale pre-blocchi** l'Owner ha confermato **«Perfetto ora procediamo»**. Questa è autorizzazione al **riallineamento operativo del mandato vigente**, non a un cambio della decisione formale sull'interfaccia primaria.

### 12.1 Regola architetturale vincolante: NATIVE FIRST, dimostrare l'eccezione

1. **Prima scelta:** schermate e funzioni Frappe/ERPNext/Healthcare **native**, `Workspace`/`Sidebar`, `ListView`, `Form`, `Report`, `Print`, `Dialog`, DocType e flussi standard compatibili con le API della versione **pinned** (TARGET B, ancora DRAFT).
2. **Seconda scelta:** **adattamenti supportati e mantenibili** in `centrochange_core` (metadata/Customize Form, Client Script o standard fixtures/versioned hooks/supportate API di estensione, permessi server-side, form/list customization), dopo verifica della disponibilità e stabilità delle API sul pin. Questo **non** significa modificare a mano i sorgenti originali Frappe/ERPNext/Healthcare o creare fork upstream.
3. **Terza scelta, per necessità dimostrata:** `CC_CUSTOM_DESK_PAGE` per casi in cui il nativo + estensioni non garantiscono workflow, UX o segregazione già approvati. Tipici candidati (non esclusiva predeterminata): Agenda settimanale multi-professionista, flussi finanziari protetti da controlli non esponibili tramite i Form nativi, simulazioni SdI/TS o report con permessi specifici. La sola presenza di una precedente webapp custom o l'avvenuta implementazione di una Page NON dimostra necessità.
4. **Divieti:** ricostruire indiscriminatamente una seconda interfaccia ERP, duplicare DocType/master/ledger, eseguire mutazioni dirette che aggirano servizi CC canonici, concedere permessi ampi per rendere visibili Form/List, mostrare informazioni cliniche private ad altri ruoli, aggiungere `Administrator` impersonation, patch upstream invasive, CDN runtime non versionata.
5. **Anche quando custom è giustificato:** riusare oggetti dati, transazioni, auth/permission guards, audit e servizi `centrochange_core`. Custom Page è parte del Desk ma **non è di per sé uso delle schermate ERP native**.

### 12.2 Audit anti-wrap su PR prodotto #112 prima di ulteriori feature

La revisione diretta dell'attuale `cc_unified_desk.js` in [DRAFT #112](https://github.com/2008hitch-afk/centrochange_core/pull/112) (HEAD verificato al chiarimento `d9c09e1d44795b068b4869c013263531dc53a936`) mostra un host Desk con `frappe.ui.make_app_page` che carica `/centrochange`, `/finanza`, `/professionista`, `/pazienti_report`, `/registro_modifiche` via `fetch` + `DOMParser`, riutilizza `workspace.js`, `finance_workspace.js`, ecc., e incapsula CSS nel Desk. Il **Catalogo** usa già almeno alcuni collegamenti diretti a List/Form native. Questo è un **bridge di riuso** e prova funzionale parziale, **non** prova di integrazione nativa adeguata in tutte le aree.

**Prima di estendere il bridge**, Codex deve:
- Fare `git status`, verificare source/branch/HEAD e preservare uncommitted work, checkpoint, dataset e test.
- Creare una **matrice di riallineamento architetturale append-only per tutte le 24 voci C1**: funzione/schermata nativa pinned disponibile; personalizzazione supportata specifica; vincoli CC di privacy/workflow/permessi; alternativa Page custom e perché nativo+adattato non basta; codice corrente su #112 classificato `NATIVE_ACTUAL / SUPPORTED_NATIVE_ADAPTATION / DESK_CUSTOM_JUSTIFIED / WEBAPP_WRAPPED_TEMPORARY / UNVERIFIED / BLOCKED_BY_OWNER_DECISION / KEEP_PUBLIC`; ref fonte/test e necessità o meno di refactor. Identificare le eccezioni **senza partire dal conteggio 13** come prova di errore.
- Dare **priorità ai flussi che ricadono nel prodotto nativo**: Patient/Healthcare Practitioner, catalogo Item/Item Price/Appointment Type, Sales Invoice/Purchase Invoice, Payment Entry, Bank Transaction/riconciliazione, report e print dove permessi effettivi lo consentono. Se le form native espongono vie non autorizzate, documentare test negativo e soluzione via servizio CC, senza grant o bypass.
- Mantenere il wrapper/shell come **prova storica reversibile** e riusare assets/controllers/servizi **solo quando apportano valore**; non dichiarare il rendering incapsulato della vecchia webapp come risultato finale nativo-first. Non eliminare retroattivamente evidenza #112 né reimplementare tutto da zero.
- Trasformare il refactor in sequenza mirata su PR DRAFT esistenti (o una nuova DRAFT esplicitamente stacked, se motivata) con test di non-regressione e mantenimento degli SHA di dipendenza. Non riscrivere in-place i report storici C1/R1-R4.
- Completare la UI italiana, brand Centro Change, UX Tabler dove appropriato e parità operativa **senza imporre lo stile webapp dove Frappe native è più appropriato**, restando nei vincoli Design System v1 del prodotto cliente.

### 12.3 Sequenza mantenuta e risultati verificabili

- Il **mandato unico del §11 resta APPROVATO** per il lavoro tecnico, ma nello **Stream A** la prima sottofase obbligatoria è audit/realignment architetturale di cui sopra; poi prodotto completo usando il riuso nativo-first dimostrato, con test statici senza Docker.
- Stream B cgroup/bootstrap safety **inalterato**; nessun tentativo incontrollato, nessun nuovo test browser finché limiti RAM/swap effettivi non sono verificati. Stop fail-closed invariato, budget C109 2GiB runtime+512MiB QA, RC22 intatto.
- Stream C collauda la **UI nativa/adattata/custom giustificata** sulla build finale, tutte le aree interne applicabili, sette ruoli+Guest, permessi server-side, workflow, Finance, report/export, responsive e audit. `READY_FOR_OWNER_UAT` è uno **stato tecnico**, non l'accettazione Owner.
- Ripristinare obbligatoriamente **C3 confronto documentato** `RC22 WEBAPP_ACTUAL` versus `NATIVE_FIRST_UNIFIED_DESK` negli stessi scenari sintetici/ruoli, con benefici, difetti e costi di manutenzione osservati e parità documentata; consegnare `READY_FOR_OWNER_COMPARISON` **solo** se confronto fattuale completo. Senza confronto e scelta Owner non si passa a C4 o Missione D.
- **DECISION-004 HC-0005** sulla webapp operativa primaria resta `APPROVATO` e vigente; il nuovo Desk è sperimentale fino a una **nuova decisione Owner esplicita di adozione** (fuori dal presente mandato). Non modificare manifest client HITCH, GOAL02/GOAL03, dati né UAT RC22 per far sembrare adottata l'UI.
- Deliverable aggiuntivo, prima dei nuovi feature changes: `docs/evidence/mission-c/C1-NATIVE-FIRST-REALIGNMENT-REVIEW.md` (DRAFT con matrice 24 e link ai codici/prove) e un breve *migration map* da ogni wrapper attuale a destinazione native/custom motivata, senza perdere il lavoro già eseguito. Evidenziare `ARCHITECTURE_CONFORMANCE: PASS / PARTIAL / BLOCKED` distinto dai test runtime.

**Conseguenza concreta:** fermare **la direzione di implementazione che estende indiscriminatamente il webapp wrapper**, non fermare l'intera Missione C; Codex prosegue autonomamente in modalità obiettivo con il riallineamento, la correzione del prodotto e i test permessi. Restano vietati merge, cutover, modifica RC22, GOAL03/produzione, provider reali, nuova infrastruttura e deroga ai safety gate senza autorizzazione specifica.
