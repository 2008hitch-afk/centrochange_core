# Centro Change — Missione C: Unified Desk experiment (C1 → C3)

**Documento:** `docs/plans/MISSION-C-UNIFIED-DESK-EXPERIMENT-2026-10-09.md`  
**Data:** 2026-10-09  
**Cliente:** HC-0005 — Centro Change  
**Owner authorization:** conferma esplicita **APPROVO** sulla proposta «Missione C con analisi, prototipo isolato e confronto completo, issue e PR DRAFT, senza cutover né modifiche UAT».  
**Tracking:** [issue #109](https://github.com/2008hitch-afk/centrochange_core/issues/109)  
**Status:** `OWNER_AUTHORIZED_EXPERIMENT_C1_C3 / NO_ARCHITECTURE_CHANGE / NO_CUTOVER`  
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