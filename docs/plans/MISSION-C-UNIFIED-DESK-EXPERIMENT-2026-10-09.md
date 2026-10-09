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

**Cronologia della decisione:** dopo il primo esito \`MISSION-C: BLOCKED\`, l'Owner ha ricevuto una proposta esplicita: «approvi l'aggiornamento della Missione C da *prototipo* a **UI completa, funzionante e tecnicamente collaudata**, con ripresa controllata dopo verifica delle risorse?». Risposta Owner: **«approvo»**.

Questa approvazione **supersede solo il limite di deliverable C2/C3 "prototipo/confronto parziale" dei paragrafi 1–6**, NON il registro storico, la decisione architetturale HITCH, le restrizioni operative o la distinzione tra tecnico PASS e accettazione Owner.

**Nuovo outcome tecnico di Missione C:**
\`MISSION-C: READY_FOR_OWNER_UAT\` soltanto quando l'**intera UI interna già prevista e compresa nel baseline GOAL-02** è accessibile, funzionante e tecnicamente verificata in un solo percorso Desk coerente (nativo/adattato/custom), con tutte le superfici cliente-facing italiane, ruoli/centri/professionisti segregati, responsività e accessibilità adeguate. Il test Owner e l'approvazione restano **PENDING** anche se i test tecnici sono PASS. Altrimenti \`PARTIAL / BLOCKED / FAIL\` onestamente motivato. Non presentare un prototipo di tre viste come UI completa.

### 7.1 Lavoro da preservare e punto di ripresa

- C1 **completa** con matrice 24 aree [PR DRAFT #111](https://github.com/2008hitch-afk/centrochange_core/pull/111): riusare; modificarla solo per evidenze necessarie.
- C2 primo prototipo [PR DRAFT #112](https://github.com/2008hitch-afk/centrochange_core/pull/112), source \`6c2801cd2a7c3d17a0a58e93f58c379171fa39db\`, stacked su [PR DRAFT #107](https://github.com/2008hitch-afk/centrochange_core/pull/107): Desk Page/Sidebar, Agenda, Pazienti, Finance read-only; NON ripartire da zero.
- C3 parziale: **69 HTTP PASS, 19 browser PASS, 1 test Manager FAIL da discriminare** (centro fisso non impostato nell'harness); browser Finance/Accountant, scenari mutativi, sicurezza completa e parity di tutte le viste non provati.
- Stop reale: **OOM QA 512MiB**, host \`oom_kill +1\`. C109 spento, dataset/immagini/checkpoint protetti; **RC22 HTTP200, 137 altri container invariati**. Tutti i vecchi FAIL/PSI/stop restano evidenza, mai mascherati.
- Ultime evidenze in \`docs/evidence/mission-c/{C1-NATIVE-CUSTOM-MATRIX,C2-PROTOTYPE-REPORT,C3-WEBAPP-VS-DESK-COMPARISON,FINAL-REPORT}.md\` sul branch \`issue-109/unified-desk-evidence\`. Nuove run append-only con SHA, image digest, risultati per suite, senza riscrivere il BLOCKED precedente.

### 7.2 Deliverable "tutte le schermate"

Completare la UI **per ogni area interna approvata della matrice C1**, con stesso ambito commerciale/funzionale già previsto in GOAL-02, distinguendo chiaramente NATIVE / SUPPORTED_ADAPTATION / CC_CUSTOM_DESK_PAGE. Aree obbligatorie secondo rilevanza del ruolo: login/navigazione; Agenda, filtro professionista/centro e geometria calendario; disponibilità; prenotare/spostare/annullare; sedute/stati/riapertura/chiusura; pazienti, professionisti, ricerca e note autorizzate; servizi/prezzi/pacchetti; fatture clienti e fornitori, incassi/pagamenti, crediti/rettefiche; banca/riconciliazione; report, print/export; SdI/TS **solo simulati**; comunicazioni/notifiche; accessi/centri; amministrazione/compensi/coda; audit.

Per ogni area **dimostrare** vista, ricerca/navigazione, azioni effettivamente esistenti, stati loading/empty/error/disabled, UX italiana, desktop/mobile, accesso per ruolo e negativo via direct/list/API/query/report/export/print. Riutilizzare senza duplicare documenti, ledger, DB, autorizzazioni o regole; preferire API e servizi canonici \`centrochange_core\`; nessun bypass dei permessi via Desk.

Una funzione classificata **BLOCKED_NEEDS_DECISION** (es. report nativi ERPNext che richiedono privilegi non concessi) **non viene sbloccata** per ottenere un PASS: mantenerne il percorso alternativo autorizzato attraverso servizi/pagina scoped; se il requisito approvato non è realizzabile senza variazione di policy/architettura, sospendere la parte e chiedere all'Owner una decisione mirata. Non dichiarare la UI completa con una funzione contrattualmente richiesta assente. Il primo incontro pubblico e le superfici DEV-only restano esclusi dalla conversione Desk, come documentato nella C1.

**Nessuna scorciatoia:** collegamenti temporanei alla vecchia webapp, placeholder, schermate vuote, screenshot, o pulsanti non collegati a workflow **non sono evidenza** di completamento della nuova UI interna. I riferimenti tra Desk e superfici native necessarie possono esistere se l'esperienza resta unica/coerente e la funzione è davvero coperta, documentando ogni integrazione.

La conformità visiva parte da \`docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md\` (Owner approved, Tabler1.6.1/UI Centro Change) e dall'UAT RC22 come benchmark, senza presumere che Desk chrome standard rispetti automaticamente branding e lingua; localizzare **senza** patch upstream o CSS distruttivo al core.

### 7.3 Ripresa controllata post-OOM (vincolo prioritario)

L'Owner autorizza una **nuova continuazione C** limitata alla stessa sperimentazione isolata. Prima di qualsiasi riavvio/scrittura:

1. Inventario live read-only: versioni/immagini, commit/branch e chain #107/#112, container e volumi C109, dataset sintetici, disco libero, MemAvailable, PSI memoria/I/O, cgroup OOM/eventi, 137 container protetti e RC22.
2. Nuovo **manifest operativo di attivazione** distinto dal C109 BLOCKED: orario corrente, finestra limitata con margine verifica/stop/rollback, stop automatici, preflight di disponibilità, budget disco e reversibilità; **non** riutilizzare le finestre della Missione B né presumere nuove scadenze approvate. Se la governance richiede una nuova finestra Owner non derivabile dall'autorizzazione, fermarsi e richiedere il solo gate temporale.
3. Browser Chromium **fresco per ciascun ruolo/suite**, uno alla volta, chiusura pulita e raccolta memoria/cgroup prima di passare al successivo; test Manager con CentroA fissato esplicitamente senza indebolire asserzioni. Riprovare solo prove necessarie e conservare l'esito storico.
4. Limite aggregato **runtime+QA 2.5GiB invariato**. QA512MiB OOM non può essere ignorato; dopo misura ammettere una *redistribuzione interna* documentata, ad es. QA768MiB/runtime1792MiB **solo se** regge i servizi e mantiene l'identico totale, senza aumentare il cap host o le soglie. Preferire esecuzione seriale e reuse delle immagini, non build/clone ridondanti.
5. **Qualsiasi nuovo OOM, PSI/host safety stop, mancata riserva disco/rollback oppure mutazione inattesa di RC22/protetti ⇒ stop immediato**, contenimento e report; nessun retry incontrollato o allentamento dei guardrail.
6. Nessuna operazione distruttiva: niente prune globale, rimozione R1–R5/C109 o checkpoint, migrate/reset/seed UAT, modifica main, merge, deploy UAT o produzione. Nessun dato reale, credenziale in Git o provider live.

### 7.4 Exit gate aggiornato e documenti

Risultato Codex \`MISSION-C: READY_FOR_OWNER_UAT / PARTIAL / FAIL / BLOCKED\`, con:
- matrice tracciabile **24/24** che espliciti per area \`IMPLEMENTED + TESTED / NOT_APPLICABLE_PUBLIC_DEV / BLOCKED_BY_OWNER_DECISION\`, senza falsi PASS;
- registro di parità con webapp RC22/GOAL-02 per flusso, sette ruoli+Guest, aree/tenant, privacy, dati canonici/audit;
- test reali browser e sicurezza positivi/negativi, screenshot rappresentativi desktop/mobile; finance mutativa/reconciliation e TS/SdI simulati ove compresi, non simulare traffico provider reale;
- immagini, source SHA, parità codice/runtime, UI/asset, restart/restore lab, log sanitizzati, memoria/disco/PSI/OOM e conferma RC22 invariato;
- eventuali limiti residui e lista di verifiche Owner **senza dichiararle superate**.

**Missione D resta esclusivamente** cutover dell'UI selezionata, deploy sull'UAT nel percorso richiesto, reversibilità e cleanup governato dopo scelta Owner: **non** rinviare a D lo sviluppo di schermate previste che possono essere completate in C. Il gate definitivo di architettura (revisione della DECISION-004) e la chiusura GOAL-02 restano riservati all'Owner. Tutte le PR restano **DRAFT** finché non autorizzate separatamente.
